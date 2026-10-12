"""Deterministic local media engine. No services, accounts or API keys."""
from __future__ import annotations
import hashlib, io, json, math, os, re, shutil, subprocess, tempfile, threading, uuid, zipfile
from functools import lru_cache
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps

FPS_CACHE = 24
AUDIO_EXT = {'.wav','.mp3','.flac','.m4a','.ogg'}
VISUAL_EXT = {'.png','.jpg','.jpeg','.webp','.gif','.mp4','.mov','.webm'}

def run(args, **kw):
    p = subprocess.run(args, capture_output=True, **kw)
    if p.returncode: raise ValueError(p.stderr.decode(errors='replace')[-1800:])
    return p.stdout

def probe(path):
    return json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)]))

def loop_phase(t, bpm, offset, beats):
    cycle=(t-offset)*bpm/(60*beats)
    # Decimal tempos can land one ULP below an exact loop boundary.
    nearest=round(cycle)
    if abs(cycle-nearest)<1e-10: return 0.0
    return cycle-math.floor(cycle)

def sample_index(t, scene, layer, count):
    phase = loop_phase(t, scene['bpm'], scene['offset'], layer['beats'])
    if layer.get('mode') == 'pingpong': phase = 1-abs(2*phase-1)
    if layer.get('mode') == 'reverse': phase = 1-phase
    return min(count-1, max(0,int(phase*count)))

def analyse(samples, sr=22050):
    """Energy-onset autocorrelation; confidence is heuristic, not probability."""
    hop=220; n=len(samples)//hop
    if n < 10: raise ValueError('Audio is too short to analyze.')
    frames=samples[:n*hop].reshape(n,hop)
    rms=np.sqrt(np.mean(frames**2,axis=1))
    env=np.maximum(0,np.diff(rms,prepend=0))
    env=np.convolve(env,[.25,.5,.25],mode='same')
    rate=sr/hop
    lags=np.arange(round(rate*60/180),round(rate*60/65)+1)
    scores=np.array([np.dot(env[:-lag],env[lag:]) for lag in lags])
    if np.max(scores,initial=0)<1e-10:
        bpm=120.; confidence=0.; offset=0.
    else:
        best=int(np.argmax(scores)); lag=lags[best]; bpm=round(rate*60/lag,2)
        confidence=float(np.clip(scores[best]/(np.dot(env,env)+1e-10),0,1))
        # Refine periodicity from onset spacings to avoid integer-lag rounding drift.
        peaks=np.where((env[1:-1]>env[:-2]) & (env[1:-1]>=env[2:]) & (env[1:-1]>.2*env.max()))[0]+1
        diffs=np.diff(peaks)/rate
        close=diffs[np.abs(diffs-60/bpm)<.08*60/bpm]
        if len(close)>=3: bpm=round(60/float(np.mean(close)),2)
        period=60/bpm
        offsets=np.arange(0,period,1/rate)
        strength=[sum(env[min(n-1,int(round((o+k*period)*rate)))] for k in range(int((n/rate-o)/period))) for o in offsets]
        offset=float(offsets[int(np.argmax(strength))])
    stride=max(1,len(rms)//1200)
    wave=[float(x) for x in rms[::stride]/max(float(rms.max()),1e-8)]
    return {'bpm':bpm,'confidence':round(confidence,3),'offset':round(offset,4),'duration':len(samples)/sr,'waveform':wave,'envelope':(rms/max(float(rms.max()),1e-8)).tolist(),'envelopeRate':rate}

def default_scene():
    return {'version':1,'id':uuid.uuid4().hex,'name':'Untitled world','tags':[], 'created':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(), 'bpm':120.,'offset':0.,'beatsPerBar':4,'bars':2,'background':'#151827','width':1080,'height':1920,'fps':30,'audio':None,'layers':[]}

def validate(s):
    if s.get('version')!=1: raise ValueError('Unsupported scene version.')
    def num(v,lo,hi):
        if isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) or not lo<=v<=hi: raise ValueError(f'Number outside range {lo}–{hi}.')
    if not re.fullmatch(r'[a-f0-9]{32}',s.get('id','')): raise ValueError('Invalid scene ID.')
    if not isinstance(s.get('name'),str) or len(s['name'])>200: raise ValueError('Invalid name.')
    num(s['bpm'],20,400); num(s['offset'],-600,600); num(s['bars'],1,64); num(s['beatsPerBar'],1,12)
    for p in ['width','height']: num(s[p],64,3840)
    if s['fps'] not in [24,30,60]: raise ValueError('Choose 24, 30 or 60 fps.')
    if not re.fullmatch(r'#[0-9a-fA-F]{6}',s['background']): raise ValueError('Invalid background.')
    if len(s['layers'])>12: raise ValueError('This slice supports up to 12 layers.')
    for layer in s['layers']:
        num(layer['beats'],.25,256)
        for prop,lo,hi,default in [('x',-2,3,.5),('y',-2,3,.5),('scale',.01,4,1),('rotation',-3600,3600,0),('opacity',0,1,1),('bounce',0,.5,0),('react',0,.5,0)]: num(layer.get(prop,default),lo,hi)
        num(layer.get('trimStart',0),0,3600); num(layer.get('trimEnd',0),0,3600)
        if layer.get('mode','forward') not in ['forward','reverse','pingpong','freeze']: raise ValueError('Invalid loop mode.')
        for k in layer.get('keys',[]):
            num(k['beat'],0,256)
            for prop in ['x','y','rotation','opacity']:
                if prop in k: num(k[prop],-3600,3600)
    return s

class Studio:
    def __init__(self, root):
        self.root=Path(root).resolve()
        for name in ['assets','scenes','exports']: (self.root/name).mkdir(parents=True,exist_ok=True)
        self.lock=threading.Lock()
    @lru_cache(maxsize=128)
    def asset(self, ident):
        if not re.fullmatch('[a-f0-9]{64}',ident or ''): raise ValueError('Invalid asset ID.')
        p=self.root/'assets'/ident
        if not (p/'meta.json').exists(): raise ValueError('Missing asset; import its media or a portable backup.')
        return json.loads((p/'meta.json').read_text())
    def import_file(self,path,display_name=None):
        path=Path(path); ext=path.suffix.lower()
        if ext not in AUDIO_EXT|VISUAL_EXT: raise ValueError('Unsupported media. SVG is deferred; rasterize it to PNG first.')
        ident=hashlib.sha256(path.read_bytes()).hexdigest(); directory=self.root/'assets'/ident
        with self.lock:
            if (directory/'meta.json').exists(): return self.asset(ident)
            directory.mkdir(exist_ok=True); source=directory/('source'+ext); shutil.copyfile(path,source)
            try:
                meta={'id':ident,'name':display_name or path.name,'source':source.name}
                if ext in AUDIO_EXT:
                    info=probe(source); dur=float(info['format'].get('duration',0))
                    if dur>900: raise ValueError('This slice accepts audio up to 15 minutes.')
                    run(['ffmpeg','-v','error','-y','-i',str(source),'-vn','-ac','1','-ar','22050',str(directory/'audio.wav')])
                    raw=run(['ffmpeg','-v','error','-i',str(directory/'audio.wav'),'-f','f32le','-'])
                    meta.update(kind='audio',**analyse(np.frombuffer(raw,dtype='<f4')))
                else:
                    info=probe(source); stream=next(x for x in info['streams'] if x['codec_type']=='video')
                    still=ext in {'.png','.jpg','.jpeg'} or (ext=='.webp' and not getattr(Image.open(source),'is_animated',False))
                    dur=float(info['format'].get('duration',stream.get('duration',0)) or 0)
                    if not still and dur>20.01: raise ValueError('For this proof of concept, trim animated media to 20 seconds or less before import.')
                    frames=directory/'frames'; frames.mkdir(exist_ok=True)
                    if still:
                        im=Image.open(source).convert('RGBA'); im.thumbnail((1920,1920)); im.save(frames/'000001.png')
                    else:
                        run(['ffmpeg','-v','error','-y','-i',str(source),'-t','20','-vf',"fps=24,scale='min(960,iw)':'min(960,ih)':force_original_aspect_ratio=decrease",'-threads','1',str(frames/'%06d.png')])
                    files=sorted(frames.glob('*.png'))
                    if not files: raise ValueError('No decodable visual frames.')
                    with Image.open(files[0]) as im: w,h=im.size
                    meta.update(kind='visual',frames=len(files),width=w,height=h,duration=len(files)/FPS_CACHE,fps=FPS_CACHE)
                (directory/'meta.json').write_text(json.dumps(meta))
                return meta
            except Exception:
                shutil.rmtree(directory,ignore_errors=True); raise
    def refs(self,s): return set([l['asset'] for l in s['layers']]+([s['audio']] if s.get('audio') else []))
    def check(self,s):
        validate(s)
        for layer in s['layers']:
            if self.asset(layer['asset'])['kind']!='visual': raise ValueError('Layer requires visual media.')
        if s.get('audio') and self.asset(s['audio'])['kind']!='audio': raise ValueError('Audio track requires audio media.')
        return s
    def save(self,s):
        self.check(s); s=json.loads(json.dumps(s)); s['modified']=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
        p=self.root/'scenes'/(s['id']+'.json'); tmp=p.with_suffix('.tmp'); tmp.write_text(json.dumps(s,indent=2)); os.replace(tmp,p)
        self.render(s,0,180).save(p.with_suffix('.jpg')); return s
    def scenes(self): return [json.loads(p.read_text()) for p in sorted((self.root/'scenes').glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True)]
    def backup(self,s,dest):
        self.check(s)
        with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('scene.json',json.dumps(s))
            for ident in self.refs(s):
                for p in (self.root/'assets'/ident).rglob('*'):
                    if p.is_file(): z.write(p,p.relative_to(self.root))
    def restore(self,path):
        with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(path) as z:
            if sum(i.file_size for i in z.infolist())>1_500_000_000: raise ValueError('Backup too large.')
            for i in z.infolist():
                target=(Path(tmp)/i.filename).resolve()
                if not target.is_relative_to(Path(tmp).resolve()): raise ValueError('Unsafe backup path.')
            z.extractall(tmp); s=json.loads((Path(tmp)/'scene.json').read_text()); validate(s)
            # Rebuild media caches from originals; do not trust imported frame paths/metadata.
            mapping={}
            for old in self.refs(s):
                if not re.fullmatch('[a-f0-9]{64}',old): raise ValueError('Invalid backup asset.')
                files=list((Path(tmp)/'assets'/old).glob('source.*'))
                if len(files)!=1: raise ValueError('Missing original media.')
                display_name=None
                try:
                    name=json.loads((files[0].parent/'meta.json').read_text()).get('name')
                    if isinstance(name,str) and len(name)<=200: display_name=name
                except (OSError,ValueError): pass
                mapping[old]=self.import_file(files[0],display_name)['id']
            for l in s['layers']: l['asset']=mapping[l['asset']]
            if s.get('audio'): s['audio']=mapping[s['audio']]
            s['id']=uuid.uuid4().hex
            return self.save(s)
    @lru_cache(maxsize=32)
    def frame(self,ident,index):
        with Image.open(self.root/'assets'/ident/'frames'/f'{index+1:06d}.png') as im: return im.convert('RGBA')
    def render(self,s,t,width=None):
        w=int(width or s['width']); h=round(w*s['height']/s['width']); canvas=Image.new('RGBA',(w,h),s['background'])
        energy=0
        if s.get('audio'):
            a=self.asset(s['audio']); env=a['envelope']; energy=env[min(len(env)-1,max(0,int(t*a['envelopeRate'])))] if t<a['duration'] else 0
        for l in s['layers']:
            if l.get('hidden'): continue
            a=self.asset(l['asset']); start=min(a['frames']-1,round(l.get('trimStart',0)*a['fps'])); end=min(a['frames'],round((l.get('trimEnd') or a['duration'])*a['fps'])); end=max(start+1,end)
            idx=start if l.get('mode')=='freeze' else start+sample_index(t,s,l,end-start)
            im=self.frame(l['asset'],idx)
            phase=loop_phase(t,s['bpm'],s['offset'],l['beats']); beat=phase*l['beats']
            props={k:l.get(k,d) for k,d in [('x',.5),('y',.5),('rotation',0),('opacity',1)]}
            keys=sorted(l.get('keys',[]),key=lambda k:k['beat'])
            for prop in props:
                ks=[k for k in keys if prop in k]
                if ks:
                    props[prop]=float(np.interp(beat,[k['beat'] for k in ks],[k[prop] for k in ks]))
            base=min(w/im.width,h/im.height)*l.get('scale',1)
            im=im.resize((max(1,round(im.width*base)),max(1,round(im.height*base))),Image.Resampling.BILINEAR)
            opacity=max(0,min(1,props['opacity']))
            if opacity<1: im.putalpha(im.getchannel('A').point(lambda p:round(p*opacity)))
            if props['rotation']: im=im.rotate(-props['rotation'],Image.Resampling.BICUBIC,expand=True)
            bounce=l.get('bounce',0)*(1-math.cos(phase*2*math.pi))/2 + l.get('react',0)*energy
            x=round(props['x']*w-im.width/2); y=round((props['y']-bounce)*h-im.height/2)
            canvas.alpha_composite(im,(x,y))
        return canvas.convert('RGB')
    def export(self,s,out,seconds,start=0,include_audio=True,progress=lambda p:None):
        self.check(s)
        if not math.isfinite(seconds) or not 0<seconds<=900 or not math.isfinite(start) or start<0: raise ValueError('Export range must be 0–900 seconds.')
        fps=s['fps']; count=math.ceil(seconds*fps); w=int(s['width']); h=int(s['height'])
        if w%2 or h%2: raise ValueError('H.264 output dimensions must be even.')
        out=Path(out); temp=out.with_suffix('.part.mp4')
        cmd=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{w}x{h}','-r',str(fps),'-i','pipe:0']
        has_audio=include_audio and s.get('audio')
        if has_audio:
            a=self.asset(s['audio']); cmd+=['-ss',str(start),'-i',str(self.root/'assets'/s['audio']/a['source'])]
        cmd+=['-map','0:v','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-threads','2']
        if has_audio: cmd+=['-map','1:a:0','-af','apad','-c:a','aac','-b:a','192k']
        cmd+=['-t',str(count/fps),'-movflags','+faststart',str(temp)]
        with tempfile.TemporaryFile() as errors:
            p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=errors)
            try:
                for n in range(count):
                    p.stdin.write(self.render(s,start+n/fps).tobytes())
                    if n%fps==0: progress(n/count)
                p.stdin.close(); p.wait()
                if p.returncode:
                    errors.seek(0); raise ValueError(errors.read().decode()[-1500:])
                os.replace(temp,out); progress(1)
            except Exception:
                p.kill(); p.wait(); temp.unlink(missing_ok=True); raise
        return {'path':str(out),'frames':count,'duration':count/fps,'fps':fps}
