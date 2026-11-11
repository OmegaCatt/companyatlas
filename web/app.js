const $ = id => document.getElementById(id);
const state = {role: 'operations', files: [], searchFiles: null, folder: 'all', view: 'explorer', generation: 0, activeAsk: null, activeSearch: null, fileRequest: 0, previewFocus: null};
const groupLabels = {shared:'Sdílené', orders:'Objednávky', operations:'Provoz a dodavatelé', people:'Péče o lidi', leadership:'Vedení'};
const groupIcons = {shared:'▤', orders:'▣', operations:'◫', people:'♙', leadership:'◆'};
const examples = {
  operations:['Kolik objednávek bylo v roce 2024?','Kolik dokončených objednávek bylo v roce 2024 pro Studio Javor?','Jaká byla celková hodnota objednávek v roce 2024?','Kolik objednávek bylo v letech 2024 až 2025?','Kdo schvaluje nákup nad 80 000 Kč?','Kdy se eskaluje kritická závada?'],
  people:['Jak probíhá zaškolení nového kolegy?','Jak dlouho předem se žádá o dovolenou?','Co patří do prvního týdne zaškolení?','Jak se předává práce před dovolenou?','Kolik objednávek bylo v roce 2024?'],
  leadership:['Kolik objednávek 2024 bylo pro Novák?','Jaký je plán vedení na rok 2025?','Kdy se eskaluje kritická závada?','Jak probíhá zaškolení nového kolegy?','Kolik dokončených objednávek bylo v roce 2024?']
};

function el(tag, className='', text='') { const node=document.createElement(tag); if(className)node.className=className; if(text)node.textContent=text; return node; }
function showToast(message) { const node=$('toast'); node.textContent=message; node.classList.add('show'); clearTimeout(showToast.timer); showToast.timer=setTimeout(()=>node.classList.remove('show'),3500); }
async function api(path, options={}) { const response=await fetch(path,{credentials:'same-origin',...options}); let data; try { data=await response.json(); } catch { data={error:'Server nevrátil očekávanou odpověď.'}; } if(!response.ok) { if(response.status===401&&path!=='/api/login'){clearWorkspace();state.username=null;showLogin();} const error=new Error(data.error || data.answer || 'Požadavek se nezdařil.'); error.data=data; throw error; } return data; }
function clearWorkspace(){state.generation++;$('manage-panel').hidden=true;$('user-list').replaceChildren();$('qa-list').replaceChildren();$('audit-list').replaceChildren();$('qa-score').textContent='—';$('document-status').textContent='';resetImport();state.files=[];$('role-cases').replaceChildren();$('qa-checked').textContent='';state.searchFiles=null;renderFolders();renderFiles();state.activeAsk?.abort();state.activeAsk=null;state.activeSearch?.abort();state.activeSearch=null;clearTimeout(searchTimer);$('answer-section').classList.add('hidden');$('answer-text').textContent='';$('answer-sources').replaceChildren();$('answer-rows').replaceChildren();$('question').value='';$('file-filter').value='';closePreview(false);for(const id of ['stat-docs','stat-groups','stat-orders'])$(id).textContent='—';if(state.view==='qa'){state.view='explorer';$('qa-view').classList.add('hidden');$('explorer-view').classList.remove('hidden');$('current-section').textContent='Průzkumník';for(const button of document.querySelectorAll('.side-link'))button.classList.toggle('active',button.dataset.view==='explorer');}}
function showLogin(account='operations'){
  $('login-account').value=account;$('login-password').value='';$('login-error').textContent='';
  const guide=$('guide-dialog');if(guide?.open){guide.addEventListener('close',()=>{if(!state.username&&!$('login-dialog').open)$('login-dialog').showModal()},{once:true});return;}
  if(!$('login-dialog').open)$('login-dialog').showModal();
}
async function logout(){try{await api('/api/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'})}finally{clearWorkspace();state.username=null;showLogin();}}
async function login(account,password){
  clearWorkspace();const generation=state.generation;
  const data=await api('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:account,password})});
  if(generation!==state.generation)return;
  state.username=data.username;state.role=data.role;state.folder='all';$('role-select').value=data.username;
  $('login-dialog').close();await loadOverview(generation);
}
async function loadOverview(generation=state.generation) { const data=await api('/api/overview'); if(generation!==state.generation||data.role!==state.role)return; state.files=data.files;state.catalogRevision=data.catalogRevision;renderManagement(); $('stat-docs').textContent=data.metrics.documents; $('stat-groups').textContent=data.metrics.groups.length; $('stat-orders').textContent=data.metrics.orders ?? '—'; $('stat-orders-sub').textContent=data.metrics.orders===undefined?'Bez přístupu k objednávkám':'V dostupných letech'; $('role-select').value=data.role; renderFolders(); renderFiles(); renderExamples(); }
function renderFolders() { const root=$('folder-list'); root.replaceChildren(); const counts={}; for(const file of state.files)counts[file.group_name]=(counts[file.group_name]||0)+1; const folders=[['all','Všechny soubory',state.files.length],...Object.entries(counts).map(([group,count])=>[group,groupLabels[group]||group,count])]; for(const [key,label,count] of folders){const button=el('button','folder'+(state.folder===key?' active':'')); button.type='button'; button.append(el('span','folder-icon',key==='all'?'▥':groupIcons[key]||'▧'),el('span','folder-name',label),el('span','folder-count',String(count)));button.addEventListener('click',()=>{state.folder=key;renderFolders();renderFiles();});root.append(button);} $('folder-count').textContent=state.files.length; }
function renderFiles() { const grid=$('file-grid'); grid.replaceChildren(); const files=(state.searchFiles??state.files).filter(file=>state.folder==='all'||file.group_name===state.folder); if(!files.length){grid.append(el('p','empty','V této složce nejsou žádné odpovídající soubory.'));return;} for(const file of files){const button=el('button','file-card');button.type='button'; const icon=el('span','file-icon '+(file.kind==='csv'?'csv':'doc'),file.kind==='csv'?'▦':'▤'); const body=el('span','file-body');body.append(el('strong','',file.title),el('small','',file.description)); const foot=el('span','file-foot');foot.append(el('span','',groupLabels[file.group_name]||file.group_name),el('span','','↗'));button.append(icon,body,foot);button.addEventListener('click',()=>openFile(file.id));grid.append(button);} }
let searchTimer;
function searchFiles(){clearTimeout(searchTimer);state.activeSearch?.abort();state.activeSearch=null;const query=$('file-filter').value.trim();if(query.length<3){state.searchFiles=null;renderFiles();return;}const generation=state.generation;searchTimer=setTimeout(async()=>{const controller=new AbortController();state.activeSearch=controller;try{const data=await api('/api/search?q='+encodeURIComponent(query),{signal:controller.signal});if(generation===state.generation&&$('file-filter').value.trim()===query){state.searchFiles=data.files;renderFiles();}}catch(error){if(error.name!=='AbortError'&&generation===state.generation)showToast(error.message);}finally{if(state.activeSearch===controller)state.activeSearch=null;}},200);}

const roleCases={
 operations:[{title:'Uzávěrka objednávek',description:'Spočítat objednávky za rok a dohledat započítané řádky.',question:'Kolik objednávek bylo v roce 2024?',label:'Připravit SQL dotaz'},{title:'Schválení nákupu',description:'Otevřít platný podklad se schvalovacími limity.',file:'purchase-policy',label:'Otevřít pravidla nákupu'},{title:'Řešení závady dodavatele',description:'Dohledat servisní lhůty a postup eskalace.',file:'supplier-sla',label:'Otevřít servisní podmínky'}],
 people:[{title:'Nástup kolegy',description:'Projít konkrétní kroky prvního týdne.',file:'hr-onboarding',label:'Otevřít zaškolení'},{title:'Plánování dovolené',description:'Ověřit předstih žádosti a předání práce.',file:'hr-leave',label:'Otevřít pravidla dovolené'},{title:'Personální podklad',description:'Pracovat se složkou, která provoznímu účtu není dostupná.',file:'hr-record',label:'Otevřít fiktivní osobní složku'}],
 leadership:[{title:'Přehled obou let',description:'Spočítat objednávky přes více období.',question:'Kolik objednávek bylo v letech 2024 až 2025?',label:'Připravit SQL dotaz'},{title:'Interní plán',description:'Prohlédnout dokument vyhrazený vedení.',file:'leadership-plan',label:'Otevřít plán vedení'},{title:'Kontrola přístupů a čísel',description:'Ověřit aktuální výsledky osmi serverových kontrol.',qa:true,label:'Otevřít testy a ověření'}]
};
function renderRoleCases(){const root=$('role-cases');root.replaceChildren();const title=el('h2','','Vyzkoušejte práci svého týmu');title.id='role-cases-title';root.append(title,el('p','role-case-intro',{operations:'Provoz vidí objednávky, dodavatelské a sdílené podklady. Personální složky a interní plán vedení nejsou přístupné.',people:'Personální tým vidí složky lidí a sdílenou příručku. Objednávky, dodavatelé a interní plán vedení jsou mimo jeho přístup.',leadership:'Vedení má přístup ke všem pěti oblastem, správě dokumentů a kontrolnímu panelu.'}[state.role]));const grid=el('div','role-case-grid');for(const item of roleCases[state.role]){const card=el('article','role-case');card.append(el('h3','',item.title),el('p','',item.description));const button=el('button','',item.label);button.type='button';if(item.file){const file=state.files.find(f=>f.id===item.file);if(!file){card.append(el('p','','Podklad není v aktuálním indexu dostupný.'));button.disabled=true}else card.append(el('small','',file.title));}button.onclick=()=>{if(item.file)openFile(item.file);else if(item.qa)showView('qa').catch(error=>showToast(error.message));else{$('question').value=item.question;$('question').focus();}};card.append(button);grid.append(card)}root.append(grid,el('p','role-case-note','Jiný účet vyberete nahoře; změna vyžaduje nové přihlášení a vymaže dosavadní odpověď i náhled. Tlačítko dotaz pouze připraví. AI se volá až po odeslání textové otázky, pokud je nakonfigurovaná.'));}

function renderExamples() {renderRoleCases(); const root=$('examples');root.replaceChildren(el('span','example-label','ZKUSTE SE ZEPTAT'));for(const text of examples[state.role]){const button=el('button','example-chip',text);button.type='button';button.addEventListener('click',()=>{$('question').value=text;$('question').focus();});root.append(button);} }
function closePreview(restoreFocus=true) {
  state.fileRequest++;
  $('file-preview').hidden=true;
  document.querySelector('.app-shell').inert=false;
  document.querySelector('.main-wrap').classList.remove('preview-open');
  for(const id of ['dialog-title','dialog-path','dialog-content'])$(id).textContent='';
  if(restoreFocus&&state.previewFocus?.isConnected)state.previewFocus.focus();
  state.previewFocus=null;
}
async function openFile(id,quote,version) {
  const generation=state.generation,request=++state.fileRequest,focus=document.activeElement;
  try {
    const file=await api('/api/files/'+encodeURIComponent(id)+(version?'?version='+version:''));
    if(generation!==state.generation||request!==state.fileRequest)return;
    state.previewFocus=focus;state.openDocument=file;$('document-meta').textContent='Verze '+file.version+' · '+file.sourceType+' · index připraven';$('document-actions').hidden=state.role!=='leadership'||file.kind==='csv';
    $('dialog-title').textContent=file.title;
    $('dialog-path').textContent=file.path+' · '+(groupLabels[file.group_name]||file.group_name);
    const content=$('dialog-content');content.replaceChildren();
    const start=typeof quote==='string'&&quote.length?file.content.indexOf(quote):-1;
    if(start>=0)content.append(document.createTextNode(file.content.slice(0,start)),el('mark','',quote),document.createTextNode(file.content.slice(start+quote.length)));
    else content.textContent=file.content;
    $('file-preview').hidden=false;
    document.querySelector('.app-shell').inert=window.matchMedia('(max-width:1100px)').matches;
    document.querySelector('.main-wrap').classList.add('preview-open');
    $('dialog-close').focus();
    content.scrollTop=0;
    content.querySelector('mark')?.scrollIntoView({block:'nearest'});
  } catch(error) {if(generation===state.generation&&request===state.fileRequest)showToast(error.message);}
}
function renderAnswer(data) { $('answer-section').classList.remove('hidden');$('answer-text').textContent=data.answer;$('answer-kind').textContent={metric:'PŘESNÝ VÝPOČET',document:'AI + PODKLADY',sources:'NALEZENÉ PODKLADY',clarification:'UPŘESNĚNÍ',denied:'PŘÍSTUP OMEZEN',not_found:'BEZ PODKLADU'}[data.kind]||'VÝSLEDEK';$('answer-kind').dataset.kind=data.kind;$('answer-method').textContent=data.method||'';const sources=$('answer-sources');sources.replaceChildren();if(data.sources?.length){sources.append(el('span','source-heading','ZDROJE ODPOVĚDI'));for(const source of data.sources){const button=el('button','source-chip',source.title+(source.locator?' · '+source.locator:'')+(source.rows?.length?' · řádky '+source.rows.join(', '):''));button.type='button';button.addEventListener('click',()=>openFile(source.id,source.quote,source.version));sources.append(button);if(source.quote){sources.append(el('blockquote','source-quote',source.quote));}}}if(data.options?.length){for(const option of data.options){const button=el('button','source-chip',option);button.type='button';button.addEventListener('click',()=>{$('question').value='Kolik objednávek bylo v roce 2024 pro '+option+'?';$('question').focus();});sources.append(button);}}const rows=$('answer-rows');rows.replaceChildren();if(data.rows?.length){const title=el('h3','','Započítané záznamy');const wrap=el('div','table-wrap');const table=el('table');const head=el('thead');const header=el('tr');for(const label of ['ID','Datum','Zákazník','Stav','Zdroj'])header.append(el('th','',label));head.append(header);const body=el('tbody');for(const row of data.rows){const tr=el('tr');for(const value of [row.id,row.placed_date,row.customer,row.status,`ř. ${row.source_row}`])tr.append(el('td','',String(value)));body.append(tr);}table.append(head,body);wrap.append(table);rows.append(title,wrap);} $('answer-section').scrollIntoView({behavior:'smooth',block:'start'});}
async function ask(event){event.preventDefault();const question=$('question').value.trim();if(question.length<5){showToast('Napište dotaz alespoň o pěti znacích.');return;}const generation=state.generation;const controller=new AbortController();state.activeAsk=controller;const button=$('ask-button');button.disabled=true;button.firstChild.textContent='Zjišťuji… ';try{const data=await api('/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question}),signal:controller.signal});if(generation===state.generation)renderAnswer(data);}catch(error){if(generation!==state.generation||error.name==='AbortError')return;if(error.data?.kind==='denied')renderAnswer(error.data);else showToast(error.message);}finally{if(state.activeAsk===controller)state.activeAsk=null;button.disabled=false;button.firstChild.textContent='Zjistit odpověď ';}}
async function showView(view){const generation=state.generation;state.view=view;if(view==='qa')closePreview(false);const isQa=view==='qa';$('explorer-view').classList.toggle('hidden',isQa);$('qa-view').classList.toggle('hidden',!isQa);$('current-section').textContent=isQa?'Testy a ověření':'Průzkumník';for(const button of document.querySelectorAll('.side-link'))button.classList.toggle('active',button.dataset.view===view);if(isQa){if(state.role!=='leadership'){showToast('Kontrolní panel je dostupný roli vedení.');await showView('explorer');return;}const [evals,audit]=await Promise.all([api('/api/evals'),api('/api/audit')]);if(generation===state.generation&&state.view==='qa')renderQa(evals,audit);} }
function renderQa(evals,audit){const passed=evals.checks.filter(check=>check.passed).length;$('qa-score').textContent=passed+'/'+evals.checks.length;$('qa-checked').textContent='Výsledky získané ze serveru: '+new Date().toLocaleString('cs-CZ')+'. Bez AI volání.';const root=$('qa-list');root.replaceChildren();const value=v=>v==='denied'?'Přístup odmítnut':typeof v==='object'?JSON.stringify(v,null,2):String(v??'Chybí výsledek');for(const check of evals.checks){const row=el('details','qa-check'),summary=el('summary');summary.append(el('span','qa-icon '+(check.passed?'pass':'fail'),check.passed?'✓':'!'),el('strong','',check.name),el('span','qa-result',check.passed?'Prošlo':'Selhalo'));row.append(summary,el('p','qa-category',check.category),el('p','','Zadání: '+check.question));for(const [label,result]of [['Očekávání',check.expected],['Zjištěno',check.actual]]){const p=el('p');p.append(el('strong','',label+': '),el('code','',value(result)));row.append(p)}row.append(el('p','',check.method));root.append(row)}const list=$('audit-list');list.replaceChildren();if(!audit.events.length)list.append(el('p','empty','Zatím žádné události.'));for(const item of audit.events){const row=el('div','audit-row');row.append(el('span','audit-dot','●'),el('span','',item.role+' · '+item.event+' · '+item.result),el('time','',item.created_at));list.append(row)}}
$('qa-refresh').onclick=async()=>{const button=$('qa-refresh');button.disabled=true;try{await showView('qa')}catch(error){showToast(error.message)}finally{button.disabled=false}};

async function start(){try{const health=await api('/api/health');$('ai-status').textContent=health.aiConfigured?'AI dostupná':'AI není nastavena';const session=await api('/api/session');if(session.role){state.role=session.role;state.username=session.username;await loadOverview()}else{clearWorkspace();showLogin();}}catch(error){showToast(error.message)}}
function downloadAnswer(){
  if($('answer-section').classList.contains('hidden'))return;
  const lines=['CompanyAtlas – odpověď s podklady','',$('answer-text').textContent,'',$('answer-method').textContent,''];
  for(const item of $('answer-sources').children){
    if(item.classList.contains('source-chip'))lines.push('Zdroj: '+item.textContent);
    if(item.classList.contains('source-quote'))lines.push('Citát: '+item.textContent);
  }
  const rows=$('answer-rows').querySelectorAll('tbody tr');
  if(rows.length){lines.push('','Započítané záznamy:');for(const row of rows)lines.push([...row.cells].map(cell=>cell.textContent).join(' | '));}
  lines.push('','Ukázková data. Před použitím závěru ověřte zdroje.');
  const url=URL.createObjectURL(new Blob([lines.join('\n')+'\n'],{type:'text/plain;charset=utf-8'}));
  const link=el('a');link.href=url;link.download='companyatlas_odpoved.txt';document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),3000);
}
$('role-select').addEventListener('change',async event=>{const select=event.target;select.disabled=true;try{await api('/api/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});clearWorkspace();state.username=null;showLogin(select.value);}catch(error){showToast(error.message);}finally{select.disabled=false;}});
$('ask-form').addEventListener('submit',ask);
$('download-answer').addEventListener('click',downloadAnswer);
$('file-filter').addEventListener('input',searchFiles);
$('dialog-close').addEventListener('click',()=>closePreview());
document.addEventListener('keydown',event=>{
  if($('file-preview').hidden)return;
  if(event.key==='Escape'){event.preventDefault();closePreview();}
  else if(event.key==='Tab'&&window.matchMedia('(max-width:1100px)').matches){
    event.preventDefault();
    (document.activeElement===$('dialog-close')?$('dialog-content'):$('dialog-close')).focus();
  }
});
window.matchMedia('(max-width:1100px)').addEventListener('change',event=>{
  if(!$('file-preview').hidden)document.querySelector('.app-shell').inert=event.matches;
});
for(const button of document.querySelectorAll('.side-link'))button.addEventListener('click',()=>{window.scrollTo(0,0);showView(button.dataset.view).catch(error=>showToast(error.message));});
start();

$('login-form').onsubmit=async event=>{event.preventDefault();const button=$('login-submit');button.disabled=true;try{await login($('login-account').value,$('login-password').value)}catch(error){$('login-error').textContent=error.message}finally{button.disabled=false}};
$('login-dialog').addEventListener('cancel',event=>event.preventDefault());$('logout').onclick=logout;
async function syncSession(){if(!state.username)return;try{const session=await api('/api/session');if(session.username!==state.username||session.role!==state.role){clearWorkspace();state.username=null;showLogin();return}if(!state.importing&&session.catalogRevision!==state.catalogRevision){clearWorkspace();await loadOverview()}}catch{}}
setInterval(syncSession,5000);window.addEventListener('focus',syncSession);document.addEventListener('visibilitychange',()=>{if(!document.hidden)syncSession()});
async function renderManagement(){
 $('manage-panel').hidden=state.role!=='leadership';if(state.role!=='leadership')return;
 const generation=state.generation;
 try{const data=await api('/api/users');if(generation!==state.generation)return;const root=$('user-list');root.replaceChildren();for(const user of data.users){const row=el('div','user-row',user.username+' · '+(user.active?'Aktivní':'Deaktivovaný'));if(user.username!=='leadership'){const button=el('button','',user.active?'Deaktivovat':'Aktivovat');button.onclick=async()=>{try{await api('/api/users/toggle',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:user.username,active:!user.active})});renderManagement()}catch(error){showToast(error.message)}};row.append(button)}root.append(row)}}catch(error){if(generation===state.generation)showToast(error.message)}
}
function resetImport(){state.replacement=null;$('import-target').textContent='Přidat nový dokument';$('import-title').value='';$('document-file').value=''}
$('cancel-replacement').onclick=resetImport;
$('replace-document').onclick=()=>{const file=state.openDocument;if(!file)return;state.replacement={id:file.id,expectedVersion:file.version};$('import-target').textContent='Nahradit '+file.title+' · v'+file.version;$('import-title').value=file.title;$('import-group').value=file.group_name;closePreview(false);$('manage-panel').open=true;$('manage-panel').scrollIntoView({block:'start'})};
$('remove-document').onclick=async()=>{const file=state.openDocument;if(!file||!window.confirm('Odebrat dokument '+file.title+' z místního indexu?'))return;try{await api('/api/documents/remove',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:file.id,expectedVersion:file.version})});clearWorkspace();await loadOverview();resetImport();showToast('Dokument byl odebrán z indexu.')}catch(error){showToast(error.message)}};
$('document-form').onsubmit=async event=>{
 event.preventDefault();const file=$('document-file').files[0];if(!file)return;if(file.size>2000000){$('document-status').textContent='Limit souboru je 2 MB.';return}
 const generation=state.generation,button=$('document-submit');state.importing=true;button.disabled=true;$('document-status').textContent='Čtení a indexace…';
 try{const bytes=new Uint8Array(await file.arrayBuffer());if(generation!==state.generation)return;let binary='';for(let i=0;i<bytes.length;i+=32768)binary+=String.fromCharCode(...bytes.subarray(i,i+32768));
 const result=await api('/api/documents/import',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({filename:file.name,data:btoa(binary),title:$('import-title').value,group:$('import-group').value,...state.replacement})});
 if(generation!==state.generation)return;clearWorkspace();await loadOverview();resetImport();$('document-status').textContent='Index připraven · v'+result.version+(result.warnings.length?' · '+result.warnings.join(' '):'');
 }catch(error){if(generation===state.generation)$('document-status').textContent=error.message}finally{state.importing=false;button.disabled=false}
};
