"""Password-protected, single-owner Railway edition. Run with Waitress."""
import io,json,os,re,secrets,shutil,tempfile,threading,time,uuid
from datetime import timedelta
from pathlib import Path
from urllib.parse import unquote
from flask import Flask,abort,jsonify,redirect,render_template_string,request,send_file,send_from_directory,session
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash
from .core import Studio,default_scene

UI=Path(__file__).resolve().parents[1]/'ui'
CSP="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob:; media-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'; object-src 'none'; form-action 'self'"

def create_app(config=None):
    app=Flask(__name__,static_folder=None)
    app.config.update(SECRET_KEY=os.getenv('STUDIO_SESSION_SECRET'),PASSWORD_HASH=os.getenv('STUDIO_PASSWORD_HASH'),DATA_DIR=os.getenv('STUDIO_DATA_DIR','/data'),MAX_CONTENT_LENGTH=100*1024*1024,SESSION_COOKIE_NAME='synthosize_session',SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SECURE=True,SESSION_COOKIE_SAMESITE='Strict',PERMANENT_SESSION_LIFETIME=timedelta(days=7),PUBLIC_ORIGIN=os.getenv('STUDIO_PUBLIC_ORIGIN'))
    if config: app.config.update(config)
    if not app.config['SECRET_KEY'] or len(app.config['SECRET_KEY'])<32 or not app.config['PASSWORD_HASH']:
        raise RuntimeError('Set STUDIO_SESSION_SECRET (32+ characters) and STUDIO_PASSWORD_HASH before starting the hosted studio.')
    studio=Studio(app.config['DATA_DIR']);jobs={};export_lock=threading.Lock();attempt_lock=threading.Lock();failed=[]
    app.extensions['studio']=studio

    @app.before_request
    def authorize():
        if request.path=='/health' and request.method=='GET': return None
        origin=app.config['PUBLIC_ORIGIN']
        if origin and request.host!=__import__('urllib.parse',fromlist=['urlparse']).urlparse(origin).netloc: abort(403)
        if request.method=='POST':
            expected=origin or request.host_url.rstrip('/')
            if request.headers.get('Origin') and request.headers['Origin']!=expected: abort(403)
            if request.headers.get('Sec-Fetch-Site')=='cross-site': abort(403)
        if request.path in ['/login','/login.css']: return None
        if not session.get('authenticated'):
            if request.path.startswith('/api/'): return jsonify(error='Sign in to your studio.'),401
            return redirect('/login')
        if request.method=='POST' and not secrets.compare_digest(request.headers.get('X-Studio-Token',''),session.get('csrf','!')): abort(403)

    @app.after_request
    def headers(response):
        response.headers['Cache-Control']='no-store'
        response.headers['Content-Security-Policy']=CSP
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='same-origin'
        if app.config['SESSION_COOKIE_SECURE']: response.headers['Strict-Transport-Security']='max-age=31536000'
        return response

    @app.errorhandler(Exception)
    def error(exc):
        if isinstance(exc,HTTPException): return jsonify(error=exc.description),exc.code
        if isinstance(exc,(ValueError,KeyError,TypeError)): return jsonify(error=str(exc)),400
        app.logger.exception('Studio operation failed')
        return jsonify(error='The operation failed. Check the service logs.'),500

    @app.get('/health')
    def health(): return jsonify(status='ok',ffmpeg=bool(shutil.which('ffmpeg')))

    @app.route('/login',methods=['GET','POST'])
    def login():
        if session.get('authenticated'): return redirect('/')
        session.setdefault('login_csrf',secrets.token_urlsafe(32))
        error=None
        if request.method=='POST':
            if not secrets.compare_digest(request.form.get('csrf',''),session['login_csrf']): abort(403)
            with attempt_lock:
                now=time.monotonic();failed[:]=[t for t in failed if now-t<60]
                if len(failed)>=10: abort(429,description='Too many attempts. Wait a minute and try again.')
                if not check_password_hash(app.config['PASSWORD_HASH'],request.form.get('password','')):
                    failed.append(now);error='That password did not match.'
                else:
                    session.clear();session['authenticated']=True;session['csrf']=secrets.token_urlsafe(32);session.permanent=True
                    return redirect('/')
        return render_template_string((UI/'login.html').read_text(),csrf=session['login_csrf'],error=error),401 if error else 200

    @app.post('/api/logout')
    def logout(): session.clear();return jsonify(ok=True)

    @app.get('/api/state')
    def state():
        recovery=None
        try: recovery=json.loads((studio.root/'recovery.json').read_text())
        except (OSError,ValueError): pass
        return jsonify(token=session['csrf'],scenes=studio.scenes(),scene=default_scene(),recovery=recovery,hosted=True,ffmpeg=bool(shutil.which('ffmpeg')))

    @app.get('/api/assets')
    def assets():
        result=[]
        for p in (studio.root/'assets').glob('*/meta.json'):
            a=json.loads(p.read_text());result.append({k:v for k,v in a.items() if k!='envelope'})
        return jsonify(result)

    @app.get('/api/job')
    def job(): return jsonify(jobs.get(request.args.get('id'),{'status':'missing'}))

    @app.post('/api/<operation>')
    def operate(operation):
        if operation in ['import','restore']:
            filename=Path(unquote(request.headers.get('X-Filename','media.bin'))).name
            if not filename or filename in ['.','..']: abort(400)
            if shutil.disk_usage(studio.root).free<512*1024*1024: abort(507,description='Storage is nearly full. Back up and free space before importing.')
            with tempfile.TemporaryDirectory(dir=studio.root) as tmp:
                p=Path(tmp)/filename
                with p.open('wb') as f: shutil.copyfileobj(request.stream,f)
                result=studio.import_file(p) if operation=='import' else studio.restore(p)
            return jsonify(result)
        if request.content_length and request.content_length>2*1024*1024: abort(413)
        body=request.get_json();s=body.get('scene')
        if operation=='save':
            with studio.lock:
                result=studio.save(s);(studio.root/'recovery.json').unlink(missing_ok=True)
            return jsonify(result)
        if operation=='recovery':
            studio.check(s)
            with studio.lock:
                p=studio.root/'recovery.tmp';p.write_text(json.dumps(s));os.replace(p,studio.root/'recovery.json')
            return jsonify(ok=True)
        if operation=='frame':
            studio.check(s);im=studio.render(s,float(body['time']),min(420,max(90,int(body.get('width',300)))))
            buf=io.BytesIO();im.save(buf,format='JPEG',quality=82);buf.seek(0);return send_file(buf,mimetype='image/jpeg')
        if operation=='backup':
            name=uuid.uuid4().hex+'.synth.zip';studio.backup(s,studio.root/'exports'/name);return jsonify(url='/exports/'+name)
        if operation=='export':
            studio.check(s)
            if not export_lock.acquire(blocking=False): abort(409,description='An export is already running.')
            ident=uuid.uuid4().hex;jobs[ident]={'status':'rendering','progress':0}
            def work():
                try:
                    def progress(p): jobs[ident]['progress']=p
                    result=studio.export(s,studio.root/'exports'/(ident+'.mp4'),float(body['duration']),float(body.get('start',0)),body.get('audio',True),progress)
                    result.pop('path',None);jobs[ident].update(status='done',url='/exports/'+ident+'.mp4',**result)
                except Exception as e: jobs[ident].update(status='error',error=str(e))
                finally: export_lock.release()
            threading.Thread(target=work,daemon=True).start();return jsonify(id=ident)
        abort(404)

    @app.get('/media/<ident>/<filename>')
    def media(ident,filename):
        a=studio.asset(ident)
        if filename=='audio.wav' and a['kind']=='audio': return send_file(studio.root/'assets'/ident/filename)
        if filename=='thumb.png' and a['kind']=='visual': return send_file(studio.root/'assets'/ident/'frames'/'000001.png')
        abort(404)

    @app.get('/thumb/<ident>')
    def thumb(ident):
        if not re.fullmatch('[a-f0-9]{32}',ident): abort(404)
        return send_file(studio.root/'scenes'/(ident+'.jpg'))

    @app.get('/exports/<filename>')
    def output(filename):
        if not re.fullmatch(r'[a-f0-9]{32}\.(mp4|synth\.zip)',filename): abort(404)
        return send_from_directory(studio.root/'exports',filename,as_attachment=True)

    @app.get('/')
    def index(): return send_from_directory(UI,'index.html')

    @app.get('/<filename>')
    def static_file(filename):
        if filename not in ['style.css','app.js','example.synth.zip','login.css']: abort(404)
        return send_from_directory(UI,filename)
    return app

if __name__=='__main__':
    from waitress import serve
    serve(create_app(),host='0.0.0.0',port=int(os.getenv('PORT','8080')),threads=4,max_request_body_size=100*1024*1024,channel_timeout=180,expose_tracebacks=False)
