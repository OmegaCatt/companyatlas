import {verifyGuide,verifyGuideLinks,dismissGuide} from './guide-qa.mjs';
import {spawn,execFileSync} from 'node:child_process';
import {once} from 'node:events';
import {mkdtemp,rm,mkdir} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const root=fileURLToPath(new URL('../',import.meta.url));
const temp=await mkdtemp(path.join(tmpdir(),'atlas-qa-'));
const child=spawn(process.env.ATLAS_PYTHON||'python',['-u','-c',
  'import sys;from pathlib import Path;from server import create_server;s=create_server(0,Path(sys.argv[1]),api_key="");print(s.server_port,flush=True);s.serve_forever()',
  path.join(temp,'test.sqlite')],{cwd:root,windowsHide:true,stdio:['ignore','pipe','pipe']});
let browser;
try{
  const port=await new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>reject(Error('QA server start timeout')),20000);
    child.once('error',error=>{clearTimeout(timer);reject(error)});
    child.once('exit',code=>{clearTimeout(timer);reject(Error('Server exited: '+code))});
    child.stdout.once('data',data=>{clearTimeout(timer);resolve(String(data).trim())});
  });
  assert.match(port,/^\d+$/);
  browser=await chromium.launch({headless:true,...(process.env.PLAYWRIGHT_EXECUTABLE_PATH?{executablePath:process.env.PLAYWRIGHT_EXECUTABLE_PATH}:{})});
  const p=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];
  p.on('pageerror',error=>errors.push(error.message));
  const login=async(account,initial=false)=>{if(!initial)await p.locator('#role-select').selectOption(account);await p.locator('#login-dialog').waitFor({state:'visible'});await p.locator('#login-account').selectOption(account);await p.locator('#login-password').fill('AtlasDemo-2026');await p.locator('#login-submit').click();await p.locator('#login-dialog').waitFor({state:'hidden'});};
  await p.goto('http://127.0.0.1:'+port);await verifyGuide(p,{login:true});await login('operations',true);await verifyGuideLinks(p);
  await p.waitForFunction(()=>document.querySelector('#stat-docs').textContent==='5');assert.equal(await p.locator('.role-case').count(),3);assert.equal((await p.request.get('http://127.0.0.1:'+port+'/api/evals')).status(),403);
  await mkdir(path.join(root,'docs'),{recursive:true});await p.screenshot({path:path.join(root,'docs','role-operations.png')});
  const ask=async(question,pattern)=>{
    await p.locator('#question').fill(question);await p.locator('#ask-button').click();
    await p.waitForFunction(()=>!document.querySelector('#ask-button').disabled);
    assert.match(await p.locator('#answer-text').innerText(),pattern);
  };
  await ask('Kolik objednávek bylo 2024 a 2025?',/15/);
  await p.locator('#answer-sources button').first().click();
  await p.locator('#file-preview').waitFor({state:'visible'});
  assert.match(await p.locator('#dialog-content').innerText(),/O-2401/);
  assert.ok(await p.locator('.main-wrap').evaluate(node=>node.classList.contains('preview-open')));
  assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await p.keyboard.press('Escape');assert.equal(await p.locator('#file-preview').isVisible(),false);
  assert.equal(await p.locator('#dialog-content').innerText(),'');
  assert.equal(await p.locator('#answer-sources button').first().evaluate(node=>node===document.activeElement),true);
  await ask('Jaká byla průměrná hodnota objednávek 2024?',/Tento typ filtru/);
  // UI-only quote fixture; this server cannot call an AI provider.
  const quote='Vyšší částky vyžadují dvě schválení: ředitelku a vlastníka společnosti.';
  await p.route('**/api/ask',route=>route.fulfill({json:{kind:'document',answer:'Ředitelka a vlastník.',sources:[{id:'purchase-policy',title:'Pravidla schvalování nákupu',quote}]}}));
  await ask('Kdo schvaluje nákup?',/Ředitelka/);
  await p.locator('#answer-sources button').click();await p.locator('#dialog-content mark').waitFor();
  assert.equal(await p.locator('#dialog-content mark').innerText(),quote);
  await mkdir(path.join(root,'docs'),{recursive:true});
  await p.screenshot({path:path.join(root,'docs','preview.png')});
  await p.unroute('**/api/ask');
  await p.locator('#dialog-close').click();
  // A response authorized before a role change must never reopen the old preview.
  let release,arrived;
  const gate=new Promise(resolve=>release=resolve),ready=new Promise(resolve=>arrived=resolve);
  await p.route('**/api/files/purchase-policy',async route=>{const response=await route.fetch();arrived();await gate;await route.fulfill({response})});
  await p.locator('#file-grid button').filter({hasText:'Pravidla schvalování nákupu'}).click();await ready;
  await login('people');
  await p.waitForFunction(()=>document.querySelector('#stat-docs').textContent==='4');assert.match(await p.locator('#role-cases').innerText(),/Nástup kolegy/);await p.screenshot({path:path.join(root,'docs','role-people.png')});await p.getByRole('button',{name:'Otevřít fiktivní osobní složku',exact:true}).click();await p.locator('#file-preview').waitFor({state:'visible'});assert.match(await p.locator('#dialog-content').innerText(),/Klár/);await p.locator('#dialog-close').click();
  const delivered=p.waitForResponse(r=>r.url().includes('/api/files/purchase-policy'));release();await delivered;
  await p.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
  assert.equal(await p.locator('#file-preview').isVisible(),false);
  assert.equal(await p.locator('#dialog-content').innerText(),'');
  assert.equal(await p.locator('#answer-section').isVisible(),false);
  assert.ok(!(await p.locator('#file-grid').innerText()).includes('Objednávky'));
  await p.unroute('**/api/files/purchase-policy');
  await ask('Kolik objednávek bylo 2024?',/nemáte přístup/);
  await p.locator('#file-grid button').filter({hasText:'Pravidla dovolené'}).click();
  await p.locator('#file-preview').waitFor({state:'visible'});
  await p.setViewportSize({width:390,height:844});
  assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  const bounds=await p.locator('#file-preview').boundingBox();assert.ok(bounds.width<=390&&bounds.x>=0);
  assert.equal(await p.locator('.app-shell').evaluate(node=>node.inert),true);
  await p.locator('#dialog-close').focus();await p.keyboard.press('Tab');
  assert.equal(await p.locator('#dialog-content').evaluate(node=>node===document.activeElement),true);
  await p.keyboard.press('Tab');assert.equal(await p.locator('#dialog-close').evaluate(node=>node===document.activeElement),true);
  await p.screenshot({path:path.join(root,'docs','preview-mobile.png')});
  await p.locator('#dialog-close').click();
  assert.equal(await p.locator('.app-shell').evaluate(node=>node.inert),false);
  // Document lifecycle and account revocation use the real HTTP API and parser.
  execFileSync(process.env.ATLAS_PYTHON||'python',['test/make_fixtures.py',temp],{cwd:root,windowsHide:true});
  await login('leadership');await p.waitForFunction(()=>document.querySelector('#stat-docs').textContent==='9');await p.setViewportSize({width:1440,height:1000});await p.getByRole('button',{name:'Otevřít testy a ověření',exact:true}).click();await p.waitForFunction(()=>document.querySelector('#qa-score').textContent==='8/8');await p.locator('.qa-check summary').first().click();assert.match(await p.locator('.qa-check').first().innerText(),/Očekávání: 12/);assert.match(await p.locator('.qa-check').first().innerText(),/Zjištěno: 12/);await p.locator('#qa-refresh').click();await p.waitForFunction(()=>!document.querySelector('#qa-refresh').disabled);assert.match(await p.locator('#qa-checked').innerText(),/Bez AI volání/);await p.locator('.qa-check summary').first().click();await p.screenshot({path:path.join(root,'docs','qa-details.png')});await p.locator('.side-link[data-view=explorer]').click();
  await p.locator('#manage-panel summary').click();
  async function upload(name,title,group){await p.locator('#import-title').fill(title);await p.locator('#import-group').selectOption(group);await p.locator('#document-file').setInputFiles(path.join(temp,name));await p.locator('#document-submit').click();await p.waitForFunction(()=>document.querySelector('#document-status').textContent.includes('Index připraven'));}
  await upload('demo.pdf','Fiktivní servisní PDF','operations');
  await p.locator('#file-grid button').filter({hasText:'Fiktivní servisní PDF'}).click();await p.locator('#document-meta').filter({hasText:'Verze 1'}).waitFor();assert.match(await p.locator('#dialog-content').innerText(),/Strana 1/);
  await p.locator('#replace-document').click();await upload('demo.docx','Fiktivní servisní PDF','operations');
  await p.locator('#file-grid button').filter({hasText:'Fiktivní servisní PDF'}).click();await p.locator('#document-meta').filter({hasText:'Verze 2'}).waitFor();assert.match(await p.locator('#dialog-content').innerText(),/Odstavec 1/);
  p.once('dialog',dialog=>dialog.accept());await p.locator('#remove-document').click();await p.waitForFunction(()=>!document.querySelector('#file-grid').textContent.includes('Fiktivní servisní PDF'));
  await upload('demo.docx','Fiktivní personální DOCX','people');
  await login('operations');await p.waitForFunction(()=>document.querySelector('#stat-docs').textContent==='5');assert.ok(!(await p.locator('#file-grid').innerText()).includes('Fiktivní personální DOCX'));
  const owner=await browser.newPage();await owner.goto('http://127.0.0.1:'+port);await dismissGuide(owner);await owner.locator('#login-dialog').waitFor({state:'visible'});await owner.locator('#login-account').selectOption('leadership');await owner.locator('#login-password').fill('AtlasDemo-2026');await owner.locator('#login-submit').click();await owner.locator('#login-dialog').waitFor({state:'hidden'});await owner.locator('#manage-panel summary').click();
  await owner.locator('.user-row').filter({hasText:'operations'}).getByRole('button',{name:'Deaktivovat',exact:true}).click();
  await p.locator('#login-dialog').waitFor({state:'visible',timeout:15000});assert.equal(await p.locator('#file-grid button').count(),0);assert.equal(await p.locator('#dialog-content').innerText(),'');
  await owner.screenshot({path:path.join(root,'docs','management.png')});await owner.close();
  assert.deepEqual(errors,[]);
  console.log('PASS: SQL, average clarification, nonmodal preview, mocked quote highlight, keyboard focus, stale preview after role change, denied orders, desktop/mobile, no JS errors; AI disabled; real login, PDF/DOCX import, version replacement/deletion, role filtering and live session revocation');
}finally{
  await browser?.close();if(child.exitCode===null){child.kill();await once(child,'exit')}
  const resolved=path.resolve(temp);if(!resolved.startsWith(path.resolve(tmpdir())+path.sep))throw Error('Unsafe cleanup path');
  await rm(resolved,{recursive:true,force:true});
}
