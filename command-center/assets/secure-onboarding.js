const VDS_OWNER='pinolissimo';
const VDS_REPO='vds-commercial-intelligence';
const VDS_GH='https://api.github.com';
const VDS_TOKEN_KEY='vds_cc_gh_token';
const VDS_SECRET_NAME='OPENAI_API_KEY';
const VDS_API_VERSION='2022-11-28';

const token=()=>sessionStorage.getItem(VDS_TOKEN_KEY)||'';
const ghHeaders=()=>({
  'Accept':'application/vnd.github+json',
  'Authorization':`Bearer ${token()}`,
  'X-GitHub-Api-Version':VDS_API_VERSION
});

function setCommandStatus(text,kind=''){
  const el=document.getElementById('commandStatus');
  if(!el)return;
  el.textContent=text;
  el.classList.toggle('good',kind==='good');
}

async function gh(path,options={}){
  if(!token())throw new Error('AUTH_REQUIRED');
  const response=await fetch(`${VDS_GH}${path}`,{
    ...options,
    headers:{...ghHeaders(),...(options.headers||{})},
    cache:'no-store'
  });
  return response;
}

async function secretExists(){
  const response=await gh(`/repos/${VDS_OWNER}/${VDS_REPO}/actions/secrets/${VDS_SECRET_NAME}`);
  if(response.status===200)return true;
  if(response.status===404)return false;
  if(response.status===401)throw new Error('AUTH_FAILED');
  if(response.status===403)throw new Error('SECRETS_PERMISSION');
  throw new Error(`SECRET_STATUS_${response.status}`);
}

function setupMarkup(){
  const overlay=document.createElement('div');
  overlay.id='openaiSetupOverlay';
  overlay.className='auth-overlay';
  overlay.hidden=true;
  overlay.innerHTML=`<section class="auth-card" role="dialog" aria-modal="true" aria-labelledby="openaiSetupTitle">
    <div class="auth-icon"><span class="material-symbols" aria-hidden="true">key</span></div>
    <p class="eyebrow">Configurazione sicura · una sola volta</p>
    <h2 id="openaiSetupTitle">Collega OpenAI al Command Center</h2>
    <p>Inserisci la tua API key OpenAI. La dashboard la cifra localmente con la public key del repository e la salva direttamente come GitHub Actions Secret <strong>OPENAI_API_KEY</strong>. La chiave in chiaro non viene salvata nel browser, nei JSON o in GitHub Pages.</p>
    <label class="token-field"><span>OpenAI API key</span><input id="openaiApiKey" type="password" autocomplete="off" spellcheck="false" placeholder="sk-…"></label>
    <div id="openaiSetupError" class="auth-error" hidden></div>
    <div class="auth-actions">
      <button id="openaiChangeGitHub" class="text-button" type="button">Cambia token GitHub</button>
      <button id="openaiConfigure" class="primary-button" type="button"><span class="material-symbols" aria-hidden="true">encrypted</span><span>Configura in modo sicuro</span></button>
    </div>
    <small>Il fine-grained GitHub token deve essere limitato a questo repository con Contents: read, Actions: read/write e Secrets: read/write.</small>
  </section>`;
  document.body.appendChild(overlay);
  overlay.querySelector('#openaiChangeGitHub').addEventListener('click',()=>{
    sessionStorage.removeItem(VDS_TOKEN_KEY);
    location.reload();
  });
  overlay.querySelector('#openaiConfigure').addEventListener('click',configureSecret);
  overlay.querySelector('#openaiApiKey').addEventListener('keydown',event=>{
    if(event.key==='Enter')configureSecret();
  });
  return overlay;
}

function showSetup(message=''){
  const overlay=document.getElementById('openaiSetupOverlay')||setupMarkup();
  const error=overlay.querySelector('#openaiSetupError');
  error.hidden=!message;
  error.textContent=message;
  overlay.hidden=false;
  requestAnimationFrame(()=>overlay.classList.add('show'));
  setTimeout(()=>overlay.querySelector('#openaiApiKey')?.focus(),80);
}

function hideSetup(){
  const overlay=document.getElementById('openaiSetupOverlay');
  if(!overlay)return;
  overlay.classList.remove('show');
  setTimeout(()=>{overlay.hidden=true},180);
}

async function sodiumReady(){
  if(!window.__vdsSodiumReady)throw new Error('SODIUM_NOT_AVAILABLE');
  return window.__vdsSodiumReady;
}

async function configureSecret(){
  const overlay=document.getElementById('openaiSetupOverlay');
  if(!overlay)return;
  const input=overlay.querySelector('#openaiApiKey');
  const button=overlay.querySelector('#openaiConfigure');
  const error=overlay.querySelector('#openaiSetupError');
  let apiKey=input.value.trim();
  if(apiKey.length<20){
    error.textContent='Inserisci una API key OpenAI valida.';
    error.hidden=false;
    return;
  }
  button.disabled=true;
  error.hidden=true;
  setCommandStatus('Configurazione OpenAI…');
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
    const put=await gh(`/repos/${VDS_OWNER}/${VDS_REPO}/actions/secrets/${VDS_SECRET_NAME}`,{
      method:'PUT',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({encrypted_value:encryptedValue,key_id:publicKey.key_id})
    });
    if(put.status===403)throw new Error('SECRETS_PERMISSION');
    if(![201,204].includes(put.status))throw new Error(`SECRET_WRITE_${put.status}`);
    input.value='';
    apiKey='';
    if(!(await secretExists()))throw new Error('SECRET_VERIFY_FAILED');
    setCommandStatus('OpenAI pronta · GitHub Secret','good');
    const toast=document.getElementById('toast');
    if(toast){toast.textContent='OpenAI configurata in GitHub Actions Secrets';toast.classList.add('show');setTimeout(()=>toast.classList.remove('show'),2600)}
    hideSetup();
  }catch(err){
    const permission=err.message==='SECRETS_PERMISSION';
    error.textContent=permission
      ? 'Il token GitHub non dispone del permesso Secrets: read/write. Crea/usa un fine-grained token limitato a questo repository con Contents read, Actions read/write e Secrets read/write.'
      : `Configurazione non riuscita: ${err.message}`;
    error.hidden=false;
    setCommandStatus(permission?'Permesso Secrets richiesto':'OpenAI non configurata');
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

async function runSecureOnboarding(){
  if(!token())return;
  try{
    const exists=await secretExists();
    if(exists){
      setCommandStatus('OpenAI pronta · GitHub Secret','good');
      return;
    }
    setCommandStatus('OpenAI da configurare');
    showSetup();
  }catch(err){
    if(err.message==='SECRETS_PERMISSION'){
      setCommandStatus('Permesso Secrets richiesto');
      showSetup('Il token GitHub attuale non può verificare/configurare i repository secrets. Usa un fine-grained token con Secrets: read/write.');
    }
  }
}

function waitForGitHubSession(){
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
window.addEventListener('focus',()=>{if(token())runSecureOnboarding()});
