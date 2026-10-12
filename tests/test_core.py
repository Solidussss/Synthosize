import math,tempfile,unittest,wave,zipfile
from pathlib import Path
import numpy as np
from PIL import Image
from engine.core import Studio,analyse,default_scene,loop_phase,sample_index,validate,probe,run
class TimingTests(unittest.TestCase):
 def test_tempo_and_offset(self):
  sr=22050;x=np.zeros(sr*16)
  for t in np.arange(.13,16,.5):
   i=int(t*sr);n=min(441,len(x)-i);x[i:i+n]=np.hanning(n)
  a=analyse(x);self.assertAlmostEqual(a['bpm'],120,delta=.6);self.assertAlmostEqual(a['offset'],.13,delta=.03)
 def test_silence_uncertain(self):self.assertEqual(analyse(np.zeros(22050))['confidence'],0)
 def test_beat_boundaries(self):
  for bpm in [60,87.3,120,177]:
   length=8*60/bpm;self.assertAlmostEqual(loop_phase(.2+length,bpm,.2,8),0,places=8);self.assertAlmostEqual(loop_phase(.2+length/2,bpm,.2,8),.5)
 def test_pingpong(self):
  s=default_scene();l={'beats':4,'mode':'pingpong'};self.assertEqual([sample_index(t,s,l,10) for t in [0,.5,1,1.5,2]],[0,5,9,5,0])
 def test_nonfinite_rejected(self):
  s=default_scene();s['bpm']=math.nan
  with self.assertRaises(ValueError):validate(s)
class ProjectTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.studio=Studio(self.root/'data');self.media=self.root/'pulse.gif'
  ims=[Image.new('RGB',(64,64),c) for c in ['white','black','red','blue']];ims[0].save(self.media,save_all=True,append_images=ims[1:],duration=250,loop=0)
  self.a=self.studio.import_file(self.media);self.s=default_scene();self.s.update(width=64,height=64,fps=24,bars=1);self.s['layers']=[{'id':'test','name':'Pulse','asset':self.a['id'],'beats':2,'mode':'forward','x':.5,'y':.5,'scale':1,'keys':[]}]
 def tearDown(self):self.tmp.cleanup()
 def test_dedup(self):self.assertEqual(self.a['id'],self.studio.import_file(self.media)['id']);self.assertEqual(len(list((self.studio.root/'assets').iterdir())),1)
 def test_save_load(self):
  saved=self.studio.save(self.s);loaded=self.studio.scenes()[0];self.assertEqual(saved,loaded);self.assertEqual(self.studio.render(saved,0).tobytes(),self.studio.render(loaded,0).tobytes())
 def test_portable_roundtrip_after_original_deleted(self):
  path=self.root/'backup.zip';self.studio.backup(self.s,path);self.media.unlink();other=Studio(self.root/'other');loaded=other.restore(path);self.assertNotEqual(loaded['id'],self.s['id']);self.assertEqual(other.render(loaded,.25).tobytes(),self.studio.render(self.s,.25).tobytes())
 def test_archive_traversal_rejected(self):
  path=self.root/'bad.zip'
  with zipfile.ZipFile(path,'w') as z:z.writestr('../escape','bad')
  with self.assertRaises(ValueError):self.studio.restore(path)
 def test_loop_render_matches(self):self.assertEqual(self.studio.render(self.s,0).tobytes(),self.studio.render(self.s,1).tobytes())
 def test_keys_interpolate(self):
  l=self.s['layers'][0];l.update(scale=.2);l['keys']=[{'beat':0,'x':.25},{'beat':1,'x':.75},{'beat':2,'x':.25}];arr=np.asarray(self.studio.render(self.s,.125));mask=arr[:,:,0]>200;self.assertAlmostEqual(np.where(mask)[1].mean(),.375*64,delta=1)
 def test_mp4_sync_and_seek_range(self):
  sr=22050;pcm=np.zeros(sr*3,dtype=np.float32)
  for t in np.arange(0,3,.5):
   i=int(t*sr);pcm[i:i+300]=np.sin(np.arange(300)*.7)*.7
  wav=self.root/'click.wav'
  with wave.open(str(wav),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr);f.writeframes((pcm*32767).astype('<i2').tobytes())
  a=self.studio.import_file(wav);self.s['audio']=a['id'];out=self.root/'export.mp4';result=self.studio.export(self.s,out,2);self.assertEqual(result['frames'],48);p=probe(out);self.assertEqual(p['streams'][0]['codec_name'],'h264');self.assertEqual(p['streams'][1]['codec_name'],'aac');self.assertAlmostEqual(float(p['format']['duration']),2,delta=.05)
  raw=run(['ffmpeg','-v','error','-i',str(out),'-f','rawvideo','-pix_fmt','rgb24','-']);frames=np.frombuffer(raw,np.uint8).reshape(-1,64,64,3);self.assertEqual(len(frames),48)
  for n in [0,6,12,18,24,30,36,42]:
   expected=np.array(self.studio.render(self.s,n/24)).astype(float);self.assertLess(np.abs(frames[n].astype(float)-expected).mean(),4)
  raw=run(['ffmpeg','-v','error','-i',str(out),'-vn','-ac','1','-ar',str(sr),'-f','f32le','-']);samples=np.frombuffer(raw,dtype='<f4')
  for t in [0,.5,1,1.5]:
   section=samples[max(0,int((t-.02)*sr)):int((t+.04)*sr)];self.assertGreater(np.max(np.abs(section)),.25)
  out2=self.root/'range.mp4';self.studio.export(self.s,out2,.5,start=.25);raw=run(['ffmpeg','-v','error','-i',str(out2),'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-']);expected=np.array(self.studio.render(self.s,.25)).astype(float);self.assertLess(np.abs(np.frombuffer(raw,np.uint8).reshape(64,64,3).astype(float)-expected).mean(),4)
if __name__=='__main__':unittest.main()
