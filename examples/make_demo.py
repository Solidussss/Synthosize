"""Original procedural fixture: layered paper character, midnight world, 120 BPM beat."""
import math,tempfile,wave,shutil,uuid,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from engine.core import Studio,default_scene,run
ROOT=Path(__file__).resolve().parents[1]
def make():
 out=ROOT/'examples'
 with tempfile.TemporaryDirectory() as tmp:
  tmp=Path(tmp);im=Image.new('RGB',(540,960),'#202b3b');d=ImageDraw.Draw(im);rng=np.random.default_rng(45)
  for _ in range(70):
   x,y=rng.integers(20,520),rng.integers(20,570);r=int(rng.choice([1,1,2]));d.ellipse((x-r,y-r,x+r,y+r),fill='#7c8b9a')
  d.ellipse((340,110,420,190),fill='#d6ddac');d.ellipse((357,96,437,176),fill='#202b3b')
  d.polygon([(0,620),(110,555),(260,650),(410,582),(540,620),(540,960),(0,960)],fill='#171d2c')
  d.polygon([(0,742),(220,665),(360,732),(540,680),(540,960),(0,960)],fill='#101722')
  for x in range(-30,550,60):d.line((270,625,x,960),fill='#27343d',width=1)
  for y in [765,810,866,936]:d.line((0,y,540,y),fill='#27343d',width=1)
  d.text((30,36),'S Y N T H O S I Z E',fill='#d5e6b4',font=ImageFont.load_default(size=16))
  d.text((30,880),'N I G H T   S H I F T',fill='#d5e6b4',font=ImageFont.load_default(size=23))
  d.text((31,916),'an original procedural test world',fill='#7e909a',font=ImageFont.load_default(size=12))
  bg=tmp/'Midnight world.png';im.save(bg);seq=tmp/'seq';seq.mkdir()
  for n in range(48):
   phase=n/48*2*math.pi;f=Image.new('RGBA',(380,440));q=ImageDraw.Draw(f);sway=math.sin(phase)*10
   q.ellipse((80,384,300,410),fill=(0,0,0,65));q.line((154,322,140,382),fill='#8b9e8c',width=13);q.line((224,322,239,382),fill='#8b9e8c',width=13)
   q.rounded_rectangle((116,375,158,396),radius=8,fill='#e1ebbf');q.rounded_rectangle((220,375,265,396),radius=8,fill='#e1ebbf')
   body=[(95+sway,122),(136+sway,50),(241+sway,65),(281+sway,138),(270+sway,298),(235,341),(131,338),(99+sway,285)]
   q.polygon(body,fill='#c6dc9f');q.line(body+[body[0]],fill='#eef6cc',width=3)
   q.polygon([(95+sway,122),(185+sway,160),(136+sway,50)],fill='#9db883');q.polygon([(185+sway,160),(281+sway,138),(241+sway,65)],fill='#d9e9b3');q.line((185+sway,160,190,324),fill='#a3bc87',width=2)
   blink=.08 if n in [23,24,25] else 1
   for ex in [151+sway,221+sway]:
    ey=205+math.sin(phase)*2;q.ellipse((ex-16,ey-23*blink,ex+13,ey+23*blink),fill='#1b2c31');q.ellipse((ex-5,ey-10*blink,ex+1,ey-3*blink),fill='#e8f6dc')
   q.arc((164+sway,240,210+sway,262),0,170,fill='#4e6652',width=3)
   q.line((101+sway,245,55,280+math.sin(phase)*20),fill='#c6dc9f',width=12);q.line((269+sway,245,320,248-math.sin(phase)*20),fill='#c6dc9f',width=12)
   f.save(seq/f'{n:04d}.png')
  clip=tmp/'Paper visitor.gif';run(['ffmpeg','-v','error','-y','-framerate','24','-i',str(seq/'%04d.png'),'-filter_complex','split[a][b];[a]palettegen=reserve_transparent=1[p];[b][p]paletteuse=alpha_threshold=128','-loop','0',str(clip)])
  sr=22050;signal=np.zeros(sr*8);rng=np.random.default_rng(6)
  for b in range(16):
   t=np.arange(int(sr*.22))/sr;hit=np.sin(2*np.pi*(55*t+35*.04*(1-np.exp(-t/.04))))*np.exp(-t*24)*.55
   if b%2:hit+=rng.normal(size=len(t))*np.exp(-t*36)*.18
   start=int(b*.5*sr);signal[start:start+len(t)]+=hit
   st=start+int(.25*sr);hat=rng.normal(size=int(.045*sr))*.045*np.exp(-np.arange(int(.045*sr))/sr*95);signal[st:st+len(hat)]+=hat
  beat=tmp/'120 BPM test beat.wav'
  with wave.open(str(beat),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr);f.writeframes((np.clip(signal,-1,1)*32767).astype('<i2').tobytes())
  store=Studio(tmp/'data');a=store.import_file(beat);background=store.import_file(bg);visual=store.import_file(clip)
  s=default_scene();s.update(name='Night shift',tags=['procedural','quiet','character'],audio=a['id'],bpm=120,offset=0,bars=2)
  def layer(asset,name):return dict(id=uuid.uuid4().hex,asset=asset,name=name,x=.5,y=.5,scale=1,opacity=1,rotation=0,beats=8,mode='forward',trimStart=0,trimEnd=0,bounce=0,react=0,keys=[])
  s['layers']=[layer(background['id'],'Midnight world'),layer(visual['id'],'Paper visitor')];s['layers'][1].update(scale=.62,y=.61,beats=4,bounce=.025)
  store.save(s);store.backup(s,out/'Night-shift.synth.zip');shutil.copyfile(out/'Night-shift.synth.zip',ROOT/'ui'/'example.synth.zip')
  (out/'detected-tempo.json').write_text(json.dumps({k:a[k] for k in ['bpm','confidence','offset','duration']},indent=2))
  store.export(s,out/'Night-shift-demo.mp4',4)
  print('Created original demo and 1080 × 1920 MP4')
if __name__=='__main__':make()
