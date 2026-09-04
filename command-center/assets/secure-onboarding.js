const VDS_OWNER='pinolissimo';
const VDS_REPO='vds-commercial-intelligence';
const VDS_GH='https://api.github.com';
const VDS_TOKEN_KEY='vds_cc_gh_token';
const VDS_API_VERSION='2022-11-28';
const VDS_API_DISMISSED_KEY='vds_cc_api_prompt_dismissed';
const VDS_PROVIDERS={
  openai:{label:'OpenAI',secret:'OPENAI_API_KEY',placeholder:'sk-…',purpose:'Command Center, escalation e analisi avanzata'},
  deepseek:{label:'DeepSeek',secret:'DEEPSEEK_API_KEY',placeholder:'Incolla la DeepSeek API key',purpose:'Semantic intelligence ad alto volume e classificazione'}
};
const providerState={openai:false,deepseek:false};
let selectedProvider='openai';

const token=()=>sessionStorage.getItem(VDS_TOKEN_KEY)||'';
const ghHeaders=()=>({
  'Accept':'application/vnd.github+json',
  'Authorization':`Bearer ${token()}`,
  'X-GitHub-Api-Version':VDS_API_VERSION
});

function toast(message){
  const el=document.getElementById('toast');
  if(!el)return;
  el.textContent=message;
  el.classList.add('show');
  clearTimeout(toast.timer);
  toast.timer=setTimeout(()=>el.classList.remove('show'),2600);
}

function setCommandStatus(text,kind=''){
  const el=document.getElementById('commandStatus');
  if(!el)return;
  el.textContent=text;
  el.classList.toggle('good',kind==='good');
}

function syncCommandStatus(){
  if(providerState.openai&&providerState.deepseek){
    setCommandStatus('AI pronta · OpenAI + DeepSeek','good');
  }else if(providerState.openai){
    setCommandStatus('OpenAI pronta · DeepSeek disponibile','good');
  }else if(providerState.deepseek){
    setCommandStatus('DeepSeek pronta · configura OpenAI');
  }else{
    setCommandStatus('API AI da configurare');
  }
}

async function gh(path,options={}){
  if(!token())throw new Error('AUTH_REQUIRED');
  return fetch(`${VDS_GH}${path}`,{
    ...options,
    headers:{...ghHeaders(),...(options.headers||{})},
    cache:'no-store'
  });
}

async function secretExists(secretName){
  const response=await gh(`/repos/${VDS_OWNER}/${VDS_REPO}/actions/secrets/${secretName}`);
  if(response.status===200)return true;
  if(response.status===404)return false;
  if(response.status===401)throw new Error('AUTH_FAILED');
  if(response.status===403)throw new Error('SECRETS_PERMISSION');
  throw new Error(`SECRET_STATUS_${response.status}`);
}

function ensureApiSettingsButton(){
  if(document.getElementById('apiSettingsButton'))return;
  const actions=document.querySelector('.header-actions');
  if(!actions)return;
  const button=document.createElement('button');
  button.id='apiSettingsButton';
  button.className='icon-button';
  button.type='button';
  button.setAttribute('aria-label','Gestisci API AI');
  button.title='Gestisci API AI';
  button.innerHTML='<span class="material-symbols" aria-hidden="true">vpn_key</span>';
  const auth=document.getElementById('authButton');
  actions.insertBefore(button,auth||null);
  button.addEventListener('click',()=>openApiManager());
}

function setupMarkup(){
  const overlay=document.createElement('div');
  overlay.id='apiManagerOverlay';
  overlay.className='auth-overlay';
  overlay.hidden=true;
  overlay.innerHTML=`<section class="auth-card api-manager-card" role="dialog" aria-modal="true" aria-labelledby="apiManagerTitle">
    <div class="api-manager-head">
      <div class="auth-icon"><span class="material-symbols" aria-hidden="true">key</span></div>
      <button id="apiManagerClose" class="icon-button small" type="button" aria-label="Chiudi gestione API"><span class="material-symbols" aria-hidden="true">close</span></button>
    </div>
    <p class="eyebrow">VDS AI bridge · GitHub Actions Secrets</p>
    <h2 id="apiManagerTitle">Gestisci le API del Command Center</h2>
    <p>Le chiavi vengono cifrate nel browser con la public key GitHub e salvate direttamente come repository secrets. Il valore in chiaro non viene conservato nella dashboard, nei JSON o in GitHub Pages.</p>
    <div class="api-provider-list" role="list">
      <article class="api-provider" data-provider-card="openai" role="listitem">
        <div><strong>OpenAI</strong><span>${VDS_PROVIDERS.openai.purpose}</span></div>
        <div class="api-provider-actions"><em data-provider-status="openai">Verifica…</em><button class="text-button" type="button" data-configure-provider="openai">Configura</button></div>
      </article>
      <article class="api-provider" data-provider-card="deepseek" role="listitem">
        <div><strong>DeepSeek</strong><span>${VDS_PROVIDERS.deepseek.purpose}</span></div>
        <div class="api-provider-actions"><em data-provider-status="deepseek">Verifica…</em><button class="text-button" type="button" data-configure-provider="deepseek">Aggiungi API</button></div>
      </article>
    </div>
    <section id="apiSecretForm" class="api-secret-form" hidden>
      <div class="api-secret-heading"><strong id="apiSecretTitle">Configura API</strong><small id="apiSecretName"></small></div>
      <label class="token-field"><span id="apiSecretLabel">API key</span><div class="secret-input-wrap"><input id="apiSecretValue" type="password" autocomplete="off" spellcheck="false"><button id="apiSecretToggle" class="icon-button small" type="button" aria-label="Mostra chiave"><span class="material-symbols" aria-hidden="true">visibility</span></button></div></label>
      <div id="apiSetupError" class="auth-error" hidden></div>
      <div class="auth-actions">
        <button id="apiCancelSecret" class="text-button" type="button">Annulla</button>
        <button id="apiSaveSecret" class="primary-button" type="button"><span class="material-symbols" aria-hidden="true">encrypted</span><span>Salva cifrata</span></button>
      </div>
      <small>Puoi usare Mostra/Nascondi per una verifica visiva prima del salvataggio. Dopo il salvataggio GitHub non restituisce più il valore della chiave.</small>
    </section>
    <div class="api-manager-footer"><button id="apiChangeGitHub" class="text-button" type="button">Cambia token GitHub</button><small>Permessi richiesti: repository singolo · Contents read · Actions read/write · Secrets read/write.</small></div>
  </section>`;
  document.body.appendChild(overlay);

  overlay.querySelector('#apiManagerClose').addEventListener('click',()=>closeApiManager(true));
  overlay.querySelector('#apiCancelSecret').addEventListener('click',hideSecretForm);
  overlay.querySelector('#apiSaveSecret').addEventListener('click',configureSelectedSecret);
  overlay.querySelector('#apiSecretValue').addEventListener('keydown',event=>{if(event.key==='Enter')configureSelectedSecret()});
  overlay.querySelector('#apiSecretToggle').addEventListener('click',toggleSecretVisibility);
  overlay.querySelector('#apiChangeGitHub').addEventListener('click',()=>{
    sessionStorage.removeItem(VDS_TOKEN_KEY);
    location.reload();
  });
  overlay.querySelectorAll('[data-configure-provider]').forEach(button=>button.addEventListener('click',()=>showSecretForm(button.dataset.configureProvider)));
  return overlay;
}

function clearSecretInput(){
  const overlay=document.getElementById('apiManagerOverlay');
  if(!overlay)return;
  const input=overlay.querySelector('#apiSecretValue');
  const toggle=overlay.querySelector('#apiSecretToggle .material-symbols');
  if(input){input.value='';input.type='password'}
  if(toggle)toggle.textContent='visibility';
}

function closeApiManager(dismiss=false){
  const overlay=document.getElementById('apiManagerOverlay');
  if(!overlay)return;
  clearSecretInput();
  hideSecretForm();
  if(dismiss)sessionStorage.setItem(VDS_API_DISMISSED_KEY,'1');
  overlay.classList.remove('show');
  setTimeout(()=>{overlay.hidden=true},180);
}

function openApiManager(focusProvider=''){
  const overlay=document.getElementById('apiManagerOverlay')||setupMarkup();
  overlay.hidden=false;
  requestAnimationFrame(()=>overlay.classList.add('show'));
  updateProviderRows();
  if(focusProvider)showSecretForm(focusProvider);
}

function updateProviderRows(){
  const overlay=document.getElementById('apiManagerOverlay');
  if(!overlay)return;
  for(const [key,provider] of Object.entries(VDS_PROVIDERS)){
    const status=overlay.querySelector(`[data-provider-status="${key}"]`);
    const button=overlay.querySelector(`[data-configure-provider="${key}"]`);
    const card=overlay.querySelector(`[data-provider-card="${key}"]`);
    if(status){status.textContent=providerState[key]?'Configurata':'Da configurare';status.classList.toggle('is-ready',providerState[key])}
    if(button)button.textContent=providerState[key]?'Sostituisci':'Aggiungi API';
    card?.classList.toggle('is-ready',providerState[key]);
  }
}

function showSecretForm(providerKey){
  if(!VDS_PROVIDERS[providerKey])return;
  selectedProvider=providerKey;
  const provider=VDS_PROVIDERS[providerKey];
  const overlay=document.getElementById('apiManagerOverlay')||setupMarkup();
  const form=overlay.querySelector('#apiSecretForm');
  const input=overlay.querySelector('#apiSecretValue');
  overlay.querySelector('#apiSecretTitle').textContent=`${providerState[providerKey]?'Sostituisci':'Configura'} ${provider.label}`;
  overlay.querySelector('#apiSecretName').textContent=provider.secret;
  overlay.querySelector('#apiSecretLabel').textContent=`${provider.label} API key`;
  input.placeholder=provider.placeholder;
  input.value='';
  input.type='password';
  overlay.querySelector('#apiSetupError').hidden=true;
  form.hidden=false;
  setTimeout(()=>input.focus(),80);
}

function hideSecretForm(){
  const form=document.getElementById('apiSecretForm');
  if(form)form.hidden=true;
  clearSecretInput();
}

function toggleSecretVisibility(){
  const overlay=document.getElementById('apiManagerOverlay');
  if(!overlay)return;
  const input=overlay.querySelector('#apiSecretValue');
  const icon=overlay.querySelector('#apiSecretToggle .material-symbols');
  const showing=input.type==='text';
  input.type=showing?'password':'text';
  icon.textContent=showing?'visibility':'visibility_off';
  overlay.querySelector('#apiSecretToggle').setAttribute('aria-label',showing?'Mostra chiave':'Nascondi chiave');
  input.focus();
}

async function sodiumReady(){
  if(!window.__vdsSodiumReady)throw new Error('SODIUM_NOT_AVAILABLE');
  return window.__vdsSodiumReady;
}

async function configureSelectedSecret(){
  const overlay=document.getElementById('apiManagerOverlay');
  if(!overlay)return;
  const provider=VDS_PROVIDERS[selectedProvider];
  const input=overlay.querySelector('#apiSecretValue');
  const button=overlay.querySelector('#apiSaveSecret');
  const error=overlay.querySelector('#apiSetupError');
  let apiKey=input.value.trim();
  if(apiKey.length<20){
    error.textContent=`Inserisci una API key ${provider.label} valida.`;
    error.hidden=false;
    return;
  }
  button.disabled=true;
  error.hidden=true;
  setCommandStatus(`Configurazione ${provider.label}…`);
  let secretBytes=null;
  let keyBytes=null;
  let sealed=null;
  try{
    const [publicKeyResponse,sodium]=await Promise.all([
      gh(`/repos/${VDS_OWNER}/${VDS_REPO}/actions/secrets/public-key`),
      sodiumReady()
    ]);
    if(publicKeyResponse.status===403)throw new Error('SECRETS_PERMISSION');
    if(!publicKeyResponse.ok)throw new Error(`PUBLIC_KEY_${publicKeyResponse.status}`);
    const publicKey=await publicKeyResponse.json();
    secretBytes=sodium.from_string(apiKey);
    keyBytes=sodium.from_base64(publicKey.key,sodium.base64_variants.ORIGINAL);
    sealed=sodium.crypto_box_seal(secretBytes,keyBytes);
    const encryptedValue=sodium.to_base64(sealed,sodium.base64_variants.ORIGINAL);
    const put=await gh(`/repos/${VDS_OWNER}/${VDS_REPO}/actions/secrets/${provider.secret}`,{
      method:'PUT',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({encrypted_value:encryptedValue,key_id:publicKey.key_id})
    });
    if(put.status===403)throw new Error('SECRETS_PERMISSION');
    if(![201,204].includes(put.status))throw new Error(`SECRET_WRITE_${put.status}`);
    clearSecretInput();
    apiKey='';
    providerState[selectedProvider]=await secretExists(provider.secret);
    if(!providerState[selectedProvider])throw new Error('SECRET_VERIFY_FAILED');
    updateProviderRows();
    syncCommandStatus();
    toast(`${provider.label} configurata in GitHub Actions Secrets`);
    hideSecretForm();
    sessionStorage.removeItem(VDS_API_DISMISSED_KEY);
  }catch(err){
    const permission=err.message==='SECRETS_PERMISSION';
    error.textContent=permission
      ? 'Il token GitHub non dispone del permesso Secrets: read/write. Usa un fine-grained token limitato a questo repository con Secrets: read/write.'
      : `Configurazione non riuscita: ${err.message}`;
    error.hidden=false;
    setCommandStatus(permission?'Permesso Secrets richiesto':`${provider.label} non configurata`);
  }finally{
    try{
      const sodium=await sodiumReady();
      if(secretBytes)sodium.memzero(secretBytes);
      if(keyBytes)sodium.memzero(keyBytes);
      if(sealed)sodium.memzero(sealed);
    }catch(_){/* best-effort memory clearing */}
    apiKey='';
    button.disabled=false;
  }
}

async function refreshProviderState(){
  const [openai,deepseek]=await Promise.all([
    secretExists(VDS_PROVIDERS.openai.secret),
    secretExists(VDS_PROVIDERS.deepseek.secret)
  ]);
  providerState.openai=openai;
  providerState.deepseek=deepseek;
  updateProviderRows();
  syncCommandStatus();
}

async function runSecureOnboarding(){
  if(!token())return;
  ensureApiSettingsButton();
  try{
    await refreshProviderState();
    if(sessionStorage.getItem(VDS_API_DISMISSED_KEY)==='1')return;
    if(!providerState.openai){
      openApiManager('openai');
    }else if(!providerState.deepseek){
      openApiManager('deepseek');
    }
  }catch(err){
    if(err.message==='SECRETS_PERMISSION'){
      setCommandStatus('Permesso Secrets richiesto');
      openApiManager();
      const error=document.getElementById('apiSetupError');
      if(error){error.textContent='Il token GitHub attuale non può verificare/configurare i repository secrets. Usa un fine-grained token con Secrets: read/write.';error.hidden=false}
    }
  }
}

function waitForGitHubSession(){
  ensureApiSettingsButton();
  let attempts=0;
  const timer=setInterval(()=>{
    attempts++;
    if(token()){
      clearInterval(timer);
      runSecureOnboarding();
    }else if(attempts>240){
      clearInterval(timer);
    }
  },500);
}

document.addEventListener('DOMContentLoaded',waitForGitHubSession,{once:true});
window.addEventListener('focus',()=>{if(token()&&document.getElementById('apiManagerOverlay')?.hidden!==false)refreshProviderState().catch(()=>{})});
