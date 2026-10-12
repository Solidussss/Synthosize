// Optional: npm install --no-save playwright; npx playwright install chromium
const {chromium}=require('playwright');
const {spawn}=require('node:child_process');
const path=require('node:path'),fs=require('node:fs'),os=require('node:os'),assert=require('node:assert/strict');
(async()=>{
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'synthosize-ui-'));
 const service=spawn(process.env.SYNTHOSIZE_PYTHON||'python',['-m','engine.server','--data',root],{cwd:path.join(__dirname,'..'),stdio:['ignore','pipe','inherit']});
 let browser;
 try{
 const url=await new Promise((resolve,reject)=>{let buffer='';service.stdout.on('data',b=>{buffer+=b;if(buffer.includes('\n'))resolve(JSON.parse(buffer.split('\n')[0]).url)});service.on('error',reject);service.on('exit',()=>reject(Error('Server exited before startup')))});
 browser=await chromium.launch({headless:true,executablePath:process.env.SYNTHOSIZE_TEST_BROWSER||undefined,args:['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader-webgl','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:1480,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(url);await page.locator('#demo').click();await page.waitForFunction(()=>document.querySelectorAll('.layerRow').length===2,null,{timeout:30000});await page.waitForFunction(()=>document.getElementById('preview').naturalWidth>0);
 console.log('PASS: load example, restore assets and render preview');
 const assetItems=await (await page.request.get(url+'/api/assets')).json();
 const audioAsset=assetItems.find(a=>a.kind==='audio'),visualAsset=assetItems.find(a=>a.kind==='visual');
 await page.locator('#fileAudio').setInputFiles(path.join(root,'assets',audioAsset.id,audioAsset.source));
 await page.waitForFunction(()=>document.getElementById('status').textContent.startsWith('Imported.'));
 await page.locator('#fileVisual').setInputFiles(path.join(root,'assets',visualAsset.id,visualAsset.source));
 await page.waitForFunction(()=>document.querySelectorAll('.layerRow').length===3);
 await page.locator('#remove').click();
 console.log('PASS: editor audio and visual file import controls');

 if(process.env.SYNTHOSIZE_SCREENSHOT)await page.screenshot({path:process.env.SYNTHOSIZE_SCREENSHOT});
 await page.locator('#bpm').fill('90');await page.locator('#bpm').dispatchEvent('change');await page.locator('#double').click();assert.equal(await page.locator('#bpm').inputValue(),'180');await page.locator('#half').click();assert.equal(await page.locator('#bpm').inputValue(),'90');
 await page.locator('#bpm').fill('120');await page.locator('#bpm').dispatchEvent('change');
 await page.locator('#play').click();await page.waitForTimeout(450);assert.notEqual(await page.locator('#clock').innerText(),'00:00.00');await page.locator('#play').click();await page.locator('#rewind').click();
 await page.locator('#addKey').click();await page.locator('#closeLoop').click();assert.equal(await page.locator('#keyCount').innerText(),'2');
 await page.locator('#sceneName').fill('UI verified scene');await page.locator('#sceneName').dispatchEvent('change');await page.locator('#save').click();await page.waitForFunction(()=>document.getElementById('saved').textContent==='saved');await page.reload();await page.waitForFunction(()=>document.getElementById('sceneName').value==='UI verified scene');
 console.log('PASS: tempo controls, audio playback, keyframes, save and reload');
 await page.locator('#tags').fill('recovered-tag');await page.locator('#tags').dispatchEvent('change');await page.waitForTimeout(800);await page.reload();await page.waitForFunction(()=>document.getElementById('saved').textContent==='recovered');assert.equal(await page.locator('#tags').inputValue(),'recovered-tag');
 console.log('PASS: unsaved scene recovery');
 await page.locator('#exportOpen').click();await page.locator('#exportWidth').fill('360');await page.locator('#exportHeight').fill('640');await page.locator('#exportDuration').fill('1');await page.locator('#exportFps').selectOption('24');await page.locator('#render').click();await page.locator('#download').waitFor({state:'visible',timeout:60000});const href=await page.locator('#download').getAttribute('href');const r=await page.request.get(url+href);assert.equal(r.status(),200);assert.ok((await r.body()).length>1000);
 console.log('PASS: editor MP4 export and download');
 const playback=await page.evaluate(async url=>{const v=document.createElement('video');v.muted=true;v.src=url;document.body.append(v);await new Promise((resolve,reject)=>{v.onloadedmetadata=resolve;v.onerror=()=>reject(Error('Video decode failed'))});await v.play();await new Promise(r=>setTimeout(r,300));const result={width:v.videoWidth,height:v.videoHeight,time:v.currentTime};v.remove();return result},href);
 assert.equal(playback.width,360);assert.equal(playback.height,640);assert.ok(playback.time>.1);console.log('PASS: exported MP4 decodes and plays in Chromium');

 const state=await (await page.request.get(url+'/api/state')).json();let unauthorized=await page.request.post(url+'/api/save',{data:{scene:state.scene}});assert.equal(unauthorized.status(),403);
 console.log('PASS: unauthenticated mutation rejected');
 assert.deepEqual(errors,[]);console.log('PASS: no browser JavaScript errors');
 }finally{await browser?.close();service.kill();fs.rmSync(root,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exitCode=1});
