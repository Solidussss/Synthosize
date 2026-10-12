import io,re,secrets,tempfile,time,unittest
from pathlib import Path
from werkzeug.security import generate_password_hash
from engine.hosted import create_app

class HostedTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.password_hash=generate_password_hash('test-only-studio-password')
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.config={'TESTING':True,'SECRET_KEY':secrets.token_hex(32),'PASSWORD_HASH':self.password_hash,'DATA_DIR':self.tmp.name,'SESSION_COOKIE_SECURE':False,'PUBLIC_ORIGIN':'http://localhost'};self.app=create_app(self.config);self.client=self.app.test_client()
 def tearDown(self):self.tmp.cleanup()
 def login(self):
  page=self.client.get('/login');csrf=re.search(r'name="csrf" value="([^"]+)"',page.text).group(1)
  response=self.client.post('/login',data={'csrf':csrf,'password':'test-only-studio-password'},headers={'Origin':'http://localhost'});self.assertEqual(response.status_code,302)
  return self.client.get('/api/state').json['token']
 def test_health_without_auth_and_no_private_data(self):
  self.assertEqual(self.client.get('/health').json['status'],'ok');self.assertEqual(self.client.get('/api/state').status_code,401);self.assertEqual(self.client.get('/example.synth.zip').status_code,302)
 def test_login_requires_csrf_and_valid_password(self):
  self.assertEqual(self.client.post('/login',data={'password':'test-only-studio-password'}).status_code,403)
  page=self.client.get('/login');csrf=re.search(r'name="csrf" value="([^"]+)"',page.text).group(1)
  self.assertEqual(self.client.post('/login',data={'csrf':csrf,'password':'wrong'}).status_code,401)
  self.assertEqual(self.client.get('/api/state').status_code,401)
 def test_session_and_mutation_protection(self):
  token=self.login();s=self.client.get('/api/state').json['scene']
  self.assertEqual(self.client.post('/api/save',json={'scene':s}).status_code,403)
  self.assertEqual(self.client.post('/api/save',json={'scene':s},headers={'X-Studio-Token':token,'Origin':'https://evil.example'}).status_code,403)
  self.assertEqual(self.client.get('/api/state',headers={'Host':'evil.example'}).status_code,403)
  self.assertEqual(self.client.post('/api/save',json={'scene':s},headers={'X-Studio-Token':token}).status_code,200)
 def test_scene_persists_across_app_restart(self):
  token=self.login();s=self.client.get('/api/state').json['scene'];s['name']='Persistent world';self.client.post('/api/save',json={'scene':s},headers={'X-Studio-Token':token})
  self.app=create_app(self.config);self.client=self.app.test_client();self.login();self.assertEqual(self.client.get('/api/state').json['scenes'][0]['name'],'Persistent world')
 def test_restore_preview_export(self):
  token=self.login();headers={'X-Studio-Token':token,'X-Filename':'demo.synth.zip'};data=(Path(__file__).resolve().parents[1]/'ui/example.synth.zip').read_bytes();r=self.client.post('/api/restore',data=data,headers=headers);self.assertEqual(r.status_code,200,r.text);s=r.json
  r=self.client.post('/api/frame',json={'scene':s,'time':0,'width':180},headers=headers);self.assertEqual(r.status_code,200);self.assertEqual(r.mimetype,'image/jpeg')
  s.update(width=180,height=320,fps=24);r=self.client.post('/api/export',json={'scene':s,'duration':.5},headers=headers);self.assertEqual(r.status_code,200)
  deadline=time.monotonic()+20
  while time.monotonic()<deadline:
   job=self.client.get('/api/job?id='+r.json['id']).json
   if job['status']!='rendering':break
   time.sleep(.05)
  self.assertEqual(job['status'],'done',job);download=self.client.get(job['url']);self.assertEqual(download.status_code,200);self.assertGreater(len(download.data),1000);download.close()
 def test_logout_revokes_session(self):
  token=self.login();self.assertEqual(self.client.post('/api/logout',json={},headers={'X-Studio-Token':token}).status_code,200);self.assertEqual(self.client.get('/api/state').status_code,401)
 def test_cloud_cookies_are_secure(self):
  app=create_app({**self.config,'SESSION_COOKIE_SECURE':True});response=app.test_client().get('/login');cookie=response.headers['Set-Cookie'];self.assertIn('Secure;',cookie);self.assertIn('HttpOnly;',cookie);self.assertIn('SameSite=Strict',cookie)
if __name__=='__main__':unittest.main()
