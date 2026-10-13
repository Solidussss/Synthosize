"""Loopback-only editor service. Run: python -m engine.server"""
import argparse, io, json, mimetypes, os, secrets, shutil, tempfile, threading, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote
from .core import Studio, default_scene
from .host_bridge import HostBridge

UI=Path(__file__).resolve().parents[1]/'ui'

def serve(root,port=0,open_browser=False):
    studio=Studio(root); token=secrets.token_urlsafe(32); jobs={}; export_lock=threading.Lock()
    try: host_bridge=HostBridge()
    except OSError: host_bridge=None  # Another local editor owns the host bridge port.
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def reply(self,code,data,ctype='application/json'):
            if not isinstance(data,bytes): data=json.dumps(data).encode()
            self.send_response(code); self.send_header('Content-Type',ctype); self.send_header('Content-Length',str(len(data)))
            self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob:; media-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'; object-src 'none'")
            self.end_headers(); self.wfile.write(data)
        def authorized(self):
            host=self.headers.get('Host','')
            expected=f'127.0.0.1:{self.server.server_port}'
            if host!=expected: self.reply(403,{'error':'Invalid host'}); return False
            origin=self.headers.get('Origin')
            if origin and origin!='http://'+expected: self.reply(403,{'error':'Invalid origin'}); return False
            if self.command=='POST' and self.headers.get('X-Studio-Token')!=token:
                self.reply(403,{'error':'Invalid session'}); return False
            return True
        def file(self,p):
            if not p.is_file(): return self.reply(404,{'error':'File not found'})
            size=p.stat().st_size; start=0; end=size-1; status=200
            range_header=self.headers.get('Range','')
            if range_header.startswith('bytes='):
                try:
                    a,b=range_header[6:].split('-'); start=int(a or 0); end=min(size-1,int(b) if b else size-1)
                    if start<0 or start>end: raise ValueError()
                    status=206
                except ValueError: return self.reply(416,{'error':'Invalid byte range'})
            self.send_response(status); self.send_header('Content-Type',mimetypes.guess_type(p.name)[0] or 'application/octet-stream'); self.send_header('Accept-Ranges','bytes')
            self.send_header('Content-Length',str(end-start+1)); self.send_header('X-Content-Type-Options','nosniff')
            if status==206: self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
            self.end_headers()
            with p.open('rb') as f:
                f.seek(start); left=end-start+1
                while left:
                    chunk=f.read(min(left,1024*1024))
                    if not chunk: break
                    self.wfile.write(chunk); left-=len(chunk)
        def do_GET(self):
            if not self.authorized(): return
            try:
                parts=urlparse(self.path); path=unquote(parts.path); q=parse_qs(parts.query)
                if path=='/api/state':
                    recovery=None
                    try: recovery=json.loads((studio.root/'recovery.json').read_text())
                    except (OSError,ValueError): pass
                    return self.reply(200,{'token':token,'scenes':studio.scenes(),'scene':default_scene(),'recovery':recovery,'root':str(studio.root),'ffmpeg':bool(shutil.which('ffmpeg'))})
                if path=='/api/host':
                    return self.reply(200,host_bridge.snapshot() if host_bridge else {'connected':False})
                if path=='/api/assets':
                    items=[]
                    for p in (studio.root/'assets').glob('*/meta.json'):
                        a=json.loads(p.read_text()); items.append({k:v for k,v in a.items() if k not in ['envelope']})
                    return self.reply(200,items)
                if path=='/api/job': return self.reply(200,jobs.get(q.get('id',[''])[0],{'status':'missing'}))
                if path.startswith('/media/'):
                    _,_,ident,filename=path.split('/')
                    a=studio.asset(ident)
                    if filename=='audio.wav' and a['kind']=='audio': return self.file(studio.root/'assets'/ident/filename)
                    if filename=='thumb.png' and a['kind']=='visual': return self.file(studio.root/'assets'/ident/'frames'/'000001.png')
                    return self.reply(404,{'error':'Missing media'})
                if path.startswith('/exports/'):
                    name=path.removeprefix('/exports/')
                    if Path(name).name!=name: raise ValueError('Invalid filename')
                    return self.file(studio.root/'exports'/name)
                if path.startswith('/thumb/'):
                    ident=path.removeprefix('/thumb/')
                    if not __import__('re').fullmatch('[a-f0-9]{32}',ident): raise ValueError('Invalid scene')
                    return self.file(studio.root/'scenes'/(ident+'.jpg'))
                target=(UI/('index.html' if path=='/' else path.lstrip('/'))).resolve()
                if not target.is_relative_to(UI): return self.reply(403,{'error':'Invalid path'})
                if not target.is_file(): return self.reply(404,{'error':'Not found'})
                self.reply(200,target.read_bytes(),mimetypes.guess_type(target.name)[0] or 'text/plain')
            except (BrokenPipeError,ConnectionResetError): pass
            except Exception as e: self.reply(400,{'error':str(e)})
        def do_POST(self):
            if not self.authorized(): return
            try:
                path=urlparse(self.path).path; length=int(self.headers.get('Content-Length','0'))
                if length>300*1024*1024: raise ValueError('Import limit is 300 MB.')
                if path in ['/api/import','/api/restore']:
                    filename=Path(unquote(self.headers.get('X-Filename','media.bin'))).name
                    with tempfile.TemporaryDirectory() as tmp:
                        p=Path(tmp)/filename
                        with p.open('wb') as f:
                            left=length
                            while left:
                                chunk=self.rfile.read(min(left,1024*1024))
                                if not chunk: raise ValueError('Upload incomplete')
                                f.write(chunk); left-=len(chunk)
                        result=studio.import_file(p) if path.endswith('import') else studio.restore(p)
                    return self.reply(200,result)
                if length>2*1024*1024: raise ValueError('Scene request too large.')
                body=json.loads(self.rfile.read(length)); s=body.get('scene')
                if path=='/api/save':
                    saved=studio.save(s)
                    (studio.root/'recovery.json').unlink(missing_ok=True)
                    return self.reply(200,saved)
                if path=='/api/recovery':
                    studio.check(s)
                    with studio.lock:
                        p=studio.root/'recovery.tmp'; p.write_text(json.dumps(s)); os.replace(p,studio.root/'recovery.json')
                    return self.reply(200,{'ok':True})
                if path=='/api/frame':
                    studio.check(s); im=studio.render(s,float(body['time']),min(540,max(90,int(body.get('width',360)))))
                    buf=io.BytesIO(); im.save(buf,format='JPEG',quality=85); return self.reply(200,buf.getvalue(),'image/jpeg')
                if path=='/api/backup':
                    filename=uuid.uuid4().hex+'.synth.zip'; studio.backup(s,studio.root/'exports'/filename)
                    return self.reply(200,{'url':'/exports/'+filename})
                if path=='/api/export':
                    studio.check(s)
                    if not export_lock.acquire(blocking=False): raise ValueError('An export is already running.')
                    ident=uuid.uuid4().hex; jobs[ident]={'status':'rendering','progress':0}
                    def work():
                        try:
                            def progress(p): jobs[ident]['progress']=p
                            result=studio.export(s,studio.root/'exports'/(ident+'.mp4'),float(body['duration']),float(body.get('start',0)),body.get('audio',True),progress)
                            jobs[ident].update(status='done',url='/exports/'+ident+'.mp4',**result)
                        except Exception as e: jobs[ident].update(status='error',error=str(e))
                        finally: export_lock.release()
                    threading.Thread(target=work,daemon=True).start(); return self.reply(200,{'id':ident})
                self.reply(404,{'error':'Unknown operation'})
            except (BrokenPipeError,ConnectionResetError): pass
            except Exception as e: self.reply(400,{'error':str(e)})
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    url=f'http://127.0.0.1:{server.server_port}'
    print(json.dumps({'url':url}),flush=True)
    if open_browser:
        import webbrowser; webbrowser.open(url)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--data',default=str(Path.home()/'SynthosizeStudio')); parser.add_argument('--port',type=int,default=0); parser.add_argument('--open',action='store_true')
    args=parser.parse_args(); serve(args.data,args.port,args.open)
