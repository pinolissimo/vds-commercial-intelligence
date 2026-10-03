// Visual Design Studio — 2026
const VDS_SENDER_OWNER='pinolissimo';
const VDS_SENDER_REPO='vds-commercial-intelligence';
const VDS_SENDER_REF='main';
const VDS_SENDER_GH='https://api.github.com';
const VDS_SENDER_TOKEN_KEY='vds_cc_gh_token';
const VDS_SENDER_CONFIG_PATH='config/sender-settings.json';

const senderDefaults={
  schema_version:'2.0',
  mode:'DRY_RUN',
  provider:'SMTP',
  queue_file:'outreach/autonomous-send-queue.jsonl',
  state_file:'state/autonomous-sender-state.json',
  audit_dir:'data/autonomous-sender-runs',
  policy_adapter:'config/sender-policy.json',
  delivery:{max_batch:10,delay_seconds:2,max_attempts:3,retry_backoff_seconds:5,timeout_seconds:25,verify_provider_after_batch:true},
  schedule:{enabled:true,timezone:'Europe/Madrid',allowed_hours:{start:'09:00',end:'19:00'}},
  safety:{dedup_enabled:true,idempotency_enabled:true,single_writer_lock:true,fail_closed_on_missing_ledger:true},
  message:{owner_bcc_enabled:true,owner_bcc_env:'VDS_OWNER_BCC'},
  smtp:{host_env:'VDS_SMTP_HOST',port_env:'VDS_SMTP_PORT',user_env:'VDS_SMTP_USER',password_env:'VDS_SMTP_PASSWORD',from_env:'VDS_SMTP_FROM'}
};

const senderToken=()=>sessionStorage.getItem(VDS_SENDER_TOKEN_KEY)||'';
const senderHeaders=()=>({'Accept':'application/vnd.github+json','Authorization':`Bearer ${senderToken()}`,'X-GitHub-Api-Version':'2022-11-28'});

function senderToast(message){
  const el=document.getElementById('toast');
  if(!el)return;
  el.textContent=message; el.classList.add('show');
  clearTimeout(senderToast.t); senderToast.t=setTimeout(()=>el.classList.remove('show'),2600);
}
function deepMerge(base,over){
  if(Array.isArray(base)) return Array.isArray(over)?over:base;
  if(base&&typeof base==='object'){
    const out={...base};
    if(over&&typeof over==='object'){
      for(const [k,v] of Object.entries(over)) out[k]=(k in out)?deepMerge(out[k],v):v;
    }
    return out;
  }
  return over===undefined?base:over;
}
function utf8Base64(text){
  const bytes=new TextEncoder().encode(text); let binary='';
  for(const b of bytes)binary+=String.fromCharCode(b);
  return btoa(binary);
}
async function ghConfigGet(){
  if(!senderToken())throw new Error('AUTH_REQUIRED');
  const url=`${VDS_SENDER_GH}/repos/${VDS_SENDER_OWNER}/${VDS_SENDER_REPO}/contents/${VDS_SENDER_CONFIG_PATH}?ref=${VDS_SENDER_REF}&v=${Date.now()}`;
  const r=await fetch(url,{headers:senderHeaders(),cache:'no-store'});
  if(r.status===404)return {config:structuredClone(senderDefaults),sha:null};
  if(r.status===401||r.status===403)throw new Error('AUTH_FAILED');
  if(!r.ok)throw new Error(`CONFIG_READ_${r.status}`);
  const payload=await r.json();
  const raw=Uint8Array.from(atob(String(payload.content||'').replace(/\n/g,'')),c=>c.charCodeAt(0));
  return {config:deepMerge(structuredClone(senderDefaults),JSON.parse(new TextDecoder().decode(raw))),sha:payload.sha||null};
}
async function ghConfigPut(config,sha){
  if(!senderToken())throw new Error('AUTH_REQUIRED');
  const body={message:'config: update autonomous sender settings from Command Center',content:utf8Base64(JSON.stringify(config,null,2)+'\n'),branch:VDS_SENDER_REF};
  if(sha)body.sha=sha;
  const r=await fetch(`${VDS_SENDER_GH}/repos/${VDS_SENDER_OWNER}/${VDS_SENDER_REPO}/contents/${VDS_SENDER_CONFIG_PATH}`,{
    method:'PUT',headers:{...senderHeaders(),'Content-Type':'application/json'},body:JSON.stringify(body)
  });
  if(r.status===401||r.status===403)throw new Error('AUTH_FAILED');
  if(r.status===409)throw new Error('CONFIG_CONFLICT');
  if(![200,201].includes(r.status))throw new Error(`CONFIG_WRITE_${r.status}`);
  return r.json();
}
function ensureSenderButton(){
  if(document.getElementById('senderSetupButton'))return;
  const actions=document.querySelector('.header-actions'); if(!actions)return;
  const btn=document.createElement('button');
  btn.id='senderSetupButton'; btn.className='icon-button'; btn.type='button'; btn.title='Sender Setup'; btn.setAttribute('aria-label','Configura VDS Sender');
  btn.innerHTML='<span class="material-symbols" aria-hidden="true">tune</span>';
  actions.insertBefore(btn,document.getElementById('authButton')||null);
  btn.addEventListener('click',openSenderSetup);
}
function senderModalMarkup(){
  const overlay=document.createElement('div');
  overlay.id='senderSetupOverlay'; overlay.className='auth-overlay sender-setup-overlay'; overlay.hidden=true;
  overlay.innerHTML=`<section class="auth-card sender-setup-card" role="dialog" aria-modal="true" aria-labelledby="senderSetupTitle">
    <div class="sender-setup-head"><div><p class="eyebrow">VDS Delivery Core</p><h2 id="senderSetupTitle">Sender Setup</h2><p>Configura il sender autonomo senza modificare manualmente file JSON.</p></div>
    <button id="senderSetupClose" class="icon-button small" type="button" aria-label="Chiudi Sender Setup"><span class="material-symbols">close</span></button></div>
    <div id="senderSetupStatus" class="sender-setup-status">Caricamento configurazione…</div>
    <form id="senderSetupForm" class="sender-setup-form">
      <fieldset><legend>Modalità</legend><div class="sender-grid cols-3">
        <label><span>Mode</span><select id="ssMode"><option value="DRY_RUN">DRY_RUN</option><option value="LIVE">LIVE</option></select></label>
        <label><span>Provider</span><select id="ssProvider"><option value="SMTP">SMTP</option></select></label>
        <label><span>Queue file</span><input id="ssQueue" type="text"></label>
      </div></fieldset>
      <fieldset><legend>Delivery</legend><div class="sender-grid cols-5">
        <label><span>Batch</span><input id="ssBatch" type="number" min="1" max="500"></label>
        <label><span>Delay (s)</span><input id="ssDelay" type="number" min="0" step="0.1"></label>
        <label><span>Attempts</span><input id="ssAttempts" type="number" min="1" max="20"></label>
        <label><span>Backoff (s)</span><input id="ssBackoff" type="number" min="0"></label>
        <label><span>Timeout (s)</span><input id="ssTimeout" type="number" min="5" max="120"></label>
      </div><label class="sender-check"><input id="ssVerify" type="checkbox"><span>Verifica provider dopo ogni batch</span></label></fieldset>
      <fieldset><legend>Schedule</legend><div class="sender-grid cols-3">
        <label><span>Timezone</span><input id="ssTimezone" type="text"></label>
        <label><span>Da</span><input id="ssStart" type="time"></label>
        <label><span>A</span><input id="ssEnd" type="time"></label>
      </div><label class="sender-check"><input id="ssScheduleEnabled" type="checkbox"><span>Schedule abilitato</span></label></fieldset>
      <fieldset><legend>Controlli tecnici</legend><div class="sender-check-grid">
        <label class="sender-check"><input id="ssDedup" type="checkbox"><span>Dedup</span></label>
        <label class="sender-check"><input id="ssIdempotency" type="checkbox"><span>Idempotenza</span></label>
        <label class="sender-check"><input id="ssLock" type="checkbox"><span>Single writer lock</span></label>
        <label class="sender-check"><input id="ssFailClosed" type="checkbox"><span>Fail closed se manca il ledger</span></label>
        <label class="sender-check"><input id="ssBccEnabled" type="checkbox"><span>BCC owner</span></label>
      </div></fieldset>
      <fieldset><legend>Environment mapping</legend><div class="sender-grid cols-2">
        <label><span>SMTP host env</span><input id="ssHostEnv" type="text"></label>
        <label><span>SMTP port env</span><input id="ssPortEnv" type="text"></label>
        <label><span>SMTP user env</span><input id="ssUserEnv" type="text"></label>
        <label><span>SMTP password env</span><input id="ssPasswordEnv" type="text"></label>
        <label><span>SMTP from env</span><input id="ssFromEnv" type="text"></label>
        <label><span>Owner BCC env</span><input id="ssBccEnv" type="text"></label>
        <label><span>State file</span><input id="ssState" type="text"></label>
        <label><span>Audit dir</span><input id="ssAudit" type="text"></label>
        <label><span>Policy adapter</span><input id="ssPolicy" type="text"></label>
      </div></fieldset>
      <div id="senderSetupError" class="auth-error" hidden></div>
      <div class="sender-setup-actions">
        <button id="senderSetupReload" class="text-button" type="button">Ricarica</button>
        <button id="senderSetupReset" class="text-button" type="button">Default</button>
        <button id="senderSetupSave" class="primary-button" type="submit"><span class="material-symbols">save</span><span>Salva configurazione</span></button>
      </div>
    </form>
  </section>`;
  document.body.appendChild(overlay);
  overlay.querySelector('#senderSetupClose').addEventListener('click',closeSenderSetup);
  overlay.querySelector('#senderSetupReload').addEventListener('click',loadSenderSetup);
  overlay.querySelector('#senderSetupReset').addEventListener('click',()=>fillSenderForm(structuredClone(senderDefaults)));
  overlay.querySelector('#senderSetupForm').addEventListener('submit',saveSenderSetup);
  return overlay;
}
let senderConfigSha=null;
function fillSenderForm(c){
  const $=id=>document.getElementById(id);
  $('ssMode').value=c.mode||'DRY_RUN'; $('ssProvider').value=c.provider||'SMTP'; $('ssQueue').value=c.queue_file||'';
  $('ssState').value=c.state_file||''; $('ssAudit').value=c.audit_dir||''; $('ssPolicy').value=c.policy_adapter||'';
  $('ssBatch').value=c.delivery?.max_batch??10; $('ssDelay').value=c.delivery?.delay_seconds??2; $('ssAttempts').value=c.delivery?.max_attempts??3;
  $('ssBackoff').value=c.delivery?.retry_backoff_seconds??5; $('ssTimeout').value=c.delivery?.timeout_seconds??25; $('ssVerify').checked=Boolean(c.delivery?.verify_provider_after_batch);
  $('ssScheduleEnabled').checked=Boolean(c.schedule?.enabled); $('ssTimezone').value=c.schedule?.timezone||'Europe/Madrid';
  $('ssStart').value=c.schedule?.allowed_hours?.start||'09:00'; $('ssEnd').value=c.schedule?.allowed_hours?.end||'19:00';
  $('ssDedup').checked=Boolean(c.safety?.dedup_enabled); $('ssIdempotency').checked=Boolean(c.safety?.idempotency_enabled);
  $('ssLock').checked=Boolean(c.safety?.single_writer_lock); $('ssFailClosed').checked=Boolean(c.safety?.fail_closed_on_missing_ledger);
  $('ssBccEnabled').checked=Boolean(c.message?.owner_bcc_enabled); $('ssBccEnv').value=c.message?.owner_bcc_env||'VDS_OWNER_BCC';
  $('ssHostEnv').value=c.smtp?.host_env||'VDS_SMTP_HOST'; $('ssPortEnv').value=c.smtp?.port_env||'VDS_SMTP_PORT';
  $('ssUserEnv').value=c.smtp?.user_env||'VDS_SMTP_USER'; $('ssPasswordEnv').value=c.smtp?.password_env||'VDS_SMTP_PASSWORD'; $('ssFromEnv').value=c.smtp?.from_env||'VDS_SMTP_FROM';
}
function readSenderForm(){
  const $=id=>document.getElementById(id);
  return {
    schema_version:'2.0',mode:$('ssMode').value,provider:$('ssProvider').value,queue_file:$('ssQueue').value.trim(),
    state_file:$('ssState').value.trim(),audit_dir:$('ssAudit').value.trim(),policy_adapter:$('ssPolicy').value.trim(),
    delivery:{max_batch:Number($('ssBatch').value),delay_seconds:Number($('ssDelay').value),max_attempts:Number($('ssAttempts').value),retry_backoff_seconds:Number($('ssBackoff').value),timeout_seconds:Number($('ssTimeout').value),verify_provider_after_batch:$('ssVerify').checked},
    schedule:{enabled:$('ssScheduleEnabled').checked,timezone:$('ssTimezone').value.trim(),allowed_hours:{start:$('ssStart').value,end:$('ssEnd').value}},
    safety:{dedup_enabled:$('ssDedup').checked,idempotency_enabled:$('ssIdempotency').checked,single_writer_lock:$('ssLock').checked,fail_closed_on_missing_ledger:$('ssFailClosed').checked},
    message:{owner_bcc_enabled:$('ssBccEnabled').checked,owner_bcc_env:$('ssBccEnv').value.trim()},
    smtp:{host_env:$('ssHostEnv').value.trim(),port_env:$('ssPortEnv').value.trim(),user_env:$('ssUserEnv').value.trim(),password_env:$('ssPasswordEnv').value.trim(),from_env:$('ssFromEnv').value.trim()}
  };
}
function validateSenderConfig(c){
  if(!c.queue_file)throw new Error('Queue file obbligatorio');
  if(!Number.isFinite(c.delivery.max_batch)||c.delivery.max_batch<1)throw new Error('Batch non valido');
  if(!c.schedule.timezone)throw new Error('Timezone obbligatoria');
  if(!c.schedule.allowed_hours.start||!c.schedule.allowed_hours.end)throw new Error('Finestra oraria incompleta');
  for(const [k,v] of Object.entries(c.smtp)) if(!v)throw new Error(`Mapping SMTP mancante: ${k}`);
}
async function loadSenderSetup(){
  const status=document.getElementById('senderSetupStatus'),error=document.getElementById('senderSetupError');
  if(!senderToken()){status.textContent='Token GitHub necessario per leggere/salvare la configurazione.';return;}
  error.hidden=true; status.textContent='Caricamento configurazione…';
  try{
    const {config,sha}=await ghConfigGet(); senderConfigSha=sha; fillSenderForm(config);
    status.textContent=sha?'Configurazione caricata da GitHub.':'Configurazione non presente: valori default.';
  }catch(err){status.textContent='Impossibile caricare la configurazione.'; error.textContent=err.message; error.hidden=false;}
}
async function saveSenderSetup(event){
  event.preventDefault();
  const btn=document.getElementById('senderSetupSave'),error=document.getElementById('senderSetupError'); error.hidden=true;
  try{
    const config=readSenderForm(); validateSenderConfig(config); btn.disabled=true;
    await ghConfigPut(config,senderConfigSha);
    const refreshed=await ghConfigGet(); senderConfigSha=refreshed.sha; fillSenderForm(refreshed.config);
    document.getElementById('senderSetupStatus').textContent=`Salvata · ${config.mode} · batch ${config.delivery.max_batch}`;
    senderToast('Configurazione sender salvata su GitHub');
  }catch(err){
    error.textContent=err.message==='CONFIG_CONFLICT'?'La configurazione è cambiata nel repository. Ricarica e riprova.':err.message; error.hidden=false;
  }finally{btn.disabled=false;}
}
function openSenderSetup(){
  const overlay=document.getElementById('senderSetupOverlay')||senderModalMarkup();
  overlay.hidden=false; requestAnimationFrame(()=>overlay.classList.add('show')); loadSenderSetup();
}
function closeSenderSetup(){
  const overlay=document.getElementById('senderSetupOverlay'); if(!overlay)return;
  overlay.classList.remove('show'); setTimeout(()=>overlay.hidden=true,160);
}
document.addEventListener('DOMContentLoaded',ensureSenderButton,{once:true});
