const {app,BrowserWindow,dialog}=require('electron');
const {spawn}=require('node:child_process');
const path=require('node:path');
let service, win;
app.whenReady().then(()=>{
  const python=process.env.SYNTHOSIZE_PYTHON || (process.platform==='win32'?'python':'python3');
  service=spawn(python,['-m','engine.server','--data',path.join(app.getPath('userData'),'studio')],{cwd:path.join(__dirname,'..'),stdio:['ignore','pipe','pipe'],windowsHide:true});
  let buffer='', errors='';
  service.stderr.on('data',b=>{errors=(errors+b.toString()).slice(-4000)});
  service.on('error',e=>{dialog.showErrorBox('Unable to start local engine',`${e.message}\nInstall Python and dependencies as described in README.md.`); app.quit()});
  service.on('exit',code=>{if(code && !app.isQuitting){dialog.showErrorBox('Local engine stopped',errors);app.quit()}});
  service.stdout.on('data',b=>{
    buffer+=b.toString(); if(win || !buffer.includes('\n'))return;
    let url; try{url=JSON.parse(buffer.split('\n')[0]).url}catch{return}
    win=new BrowserWindow({width:1480,height:960,minWidth:1100,minHeight:760,backgroundColor:'#0e1014',title:'Synthosize Visual Studio',webPreferences:{nodeIntegration:false,contextIsolation:true,sandbox:true}});
    win.webContents.setWindowOpenHandler(()=>({action:'deny'}));
    win.webContents.on('will-navigate',(e,target)=>{if(new URL(target).origin!==url)e.preventDefault()});
    win.webContents.session.setPermissionRequestHandler((_wc,_permission,cb)=>cb(false));
    win.loadURL(url);
  });
});
app.on('window-all-closed',()=>app.quit());
app.on('before-quit',()=>{app.isQuitting=true;service?.kill()});
