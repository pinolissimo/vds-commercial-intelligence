const OWNER='pinolissimo';
const REPO='vds-commercial-intelligence';
const REF='main';
const GH='https://api.github.com';
const TOKEN_KEY='vds_cc_gh_token';
const $=(id)=>document.getElementById(id);

const state={
  dashboard:null,
  today:null,
  companies:[],
  territory:null,
  opportunities:[],
  sources:null,
  health:null,
  companyPage:1,
  companyPageSize:18,
  territoryView:'territories',
  token:sessionStorage.getItem(TOKEN_KEY)||''
};

const fmt=new Intl.NumberFormat('it-IT');
const dtFmt=new Intl.DateTimeFormat('it-IT',{timeZone:'Europe/Madrid',hour:'2-digit',minute:'2-digit'});
const stampFmt=new Intl.DateTimeFormat('it-IT',{timeZone:'Europe/Madrid',day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'});
const dayFmt=new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Madrid',year:'numeric',month:'2-digit',day:'2-digit'});
const pct=(v)=>v==null?'—':`${Number(v).toLocaleString('it-IT',{maximumFractionDigits:1})}%`;
const num=(v)=>v==null?'—':fmt.format(Number(v));
const safe=(v)=>String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
const norm=(v)=>String(v??'').toLocaleLowerCase('it-IT');

function toast(message){
  const el=$('toast');
  if(!el)return;
  el.textContent=message;
  el.classList.add('show');
  clearTimeout(toast.t);
  toast.t=setTimeout(()=>el.classList.remove('show'),2300);
}

function publicHeaders(){
  return {
    'Accept':'application/vnd.github+json',
    'X-GitHub-Api-Version':'2022-11-28'
  };
}

function authHeaders(token=state.token){
  return {
    ...publicHeaders(),
    'Authorization':`Bearer ${token}`
  };
}

function decode64Utf8(value){
  const bytes=Uint8Array.from(atob(value.replace(/\n/g,'')),c=>c.charCodeAt(0));
  return new TextDecoder().decode(bytes);
}

async function fetchGithubFile(url,withAuth){
  return fetch(url,{headers:withAuth?authHeaders():publicHeaders(),cache:'no-store'});
}

async function ghFile(path){
  const url=`${GH}/repos/${OWNER}/${REPO}/contents/${path}?ref=${encodeURIComponent(REF)}&v=${Date.now()}`;
  let r=await fetchGithubFile(url,Boolean(state.token));
  if(state.token&&(r.status===401||r.status===403)){
    r=await fetchGithubFile(url,false);
  }
  if(!r.ok)throw new Error(`${path}: HTTP ${r.status}`);
  const data=await r.json();
  if(data&&data.encoding==='base64'&&data.content){
    return JSON.parse(decode64Utf8(data.content));
  }
  throw new Error(`${path}: formato inatteso`);
}

async function validateToken(token){
  const r=await fetch(`${GH}/repos/${OWNER}/${REPO}`,{
    headers:authHeaders(token),
    cache:'no-store'
  });
  if(r.status===401||r.status===403)throw new Error('AUTH_FAILED');
  if(!r.ok)throw new Error(`AUTH_HTTP_${r.status}`);
}

function setText(id,value){
  const el=$(id);
  if(el)el.textContent=value;
}

function setWidth(id,value,max){
  const el=$(id);
  if(!el)return;
  const p=max>0?Math.min(100,Math.max(0,(Number(value||0)/max)*100)):0;
  requestAnimationFrame(()=>{el.style.width=`${p}%`;});
}

function formatTime(value){
  if(!value)return'—';
  const d=new Date(value);
  return Number.isNaN(d.getTime())?'—':dtFmt.format(d);
}

function formatStamp(value){
  if(!value)return'—';
  const d=new Date(value);
  return Number.isNaN(d.getTime())?'—':stampFmt.format(d);
}

function sameMadridDay(value){
  if(!value)return false;
  const d=new Date(value);
  if(Number.isNaN(d.getTime()))return false;
  return dayFmt.format(d)===dayFmt.format(new Date());
}

function providerStamp(){
  return state.health?.provider_live_overlay_updated_at
    ||state.today?.provider_live_overlay_updated_at
    ||state.dashboard?.provider_live_overlay_updated_at
    ||state.dashboard?.provider_live_overlay?.updated_at
    ||null;
}

function outboundFresh(){
  if(typeof state.health?.outbound_source_fresh==='boolean')return state.health.outbound_source_fresh;
  if(typeof state.today?.source_health?.outbound_source_fresh==='boolean')return state.today.source_health.outbound_source_fresh;
  return sameMadridDay(providerStamp());
}

function setAuthUI(){
  const icon=$('authButton')?.querySelector('.material-symbols');
  if(icon)icon.textContent=state.token?'lock_open':'lock';
  $('authButton')?.setAttribute('title',state.token?'Disconnetti GitHub':'Connetti GitHub per i comandi AI');
}

function showAuth(){
  const o=$('authOverlay');
  if(!o)return;
  o.hidden=false;
  requestAnimationFrame(()=>o.classList.add('show'));
  $('githubToken').value='';
  $('authError').hidden=true;
  setTimeout(()=>$('githubToken')?.focus(),80);
}

function hideAuth(){
  const o=$('authOverlay');
  if(!o)return;
  o.classList.remove('show');
  setTimeout(()=>{o.hidden=true;},180);
}

async function connectToken(){
  const token=$('githubToken').value.trim();
  if(!token)return;
  const old=state.token;
  $('authConnect').disabled=true;
  $('authError').hidden=true;
  try{
    await validateToken(token);
    state.token=token;
    sessionStorage.setItem(TOKEN_KEY,token);
    setAuthUI();
    hideAuth();
    toast('GitHub connesso per i comandi AI');
  }catch(e){
    state.token=old;
    $('authError').textContent=e.message==='AUTH_FAILED'
      ?'Token non valido o permessi insufficienti.'
      :'Connessione autenticata a GitHub non riuscita.';
    $('authError').hidden=false;
  }finally{
    $('authConnect').disabled=false;
  }
}

function disconnect(){
  if(!state.token){
    showAuth();
    return;
  }
  if(!confirm('Disconnettere i comandi AI da GitHub per questa sessione?'))return;
  sessionStorage.removeItem(TOKEN_KEY);
  state.token='';
  setAuthUI();
  toast('Comandi AI disconnessi; i dati restano disponibili');
}

function renderHeader(){
  const d=state.dashboard||{};
  const h=state.health||{};
  const generated=d.generated_at||h.generated_at;
  setText('generatedAt',formatStamp(generated));

  const pill=$('healthPill');
  let projectionFresh=false;
  if(generated){
    const age=Math.max(0,(Date.now()-new Date(generated).getTime())/60000);
    projectionFresh=Number.isFinite(age)&&age<25;
    setText('dataAge',age<1?'aggiornati ora':age<60?`${Math.round(age)} min fa`:`${Math.round(age/60)} h fa`);
  }else{
    setText('dataAge','proiezione non disponibile');
  }

  const providerOk=outboundFresh();
  const overall=projectionFresh&&providerOk&&h.status!=='DEGRADED';
  if(pill){
    pill.classList.toggle('is-good',overall);
    pill.classList.toggle('is-stale',!overall);
    const label=pill.querySelector('span');
    if(label){
      label.textContent=!providerOk?'Provider da sincronizzare':overall?'Dati live':'Dati da aggiornare';
    }
  }
  setText('engineStatus',h.production_search_independent===true?'Attivo · indipendente':'Verifica stato');
}

function renderToday(){
  const t=state.dashboard?.today||state.today||{};
  const fresh=outboundFresh();
  setText('todaySent',fresh?num(t.sent??state.today?.sent_count):'—');
  setText('todayFirstContacts',fresh?num(t.first_contacts_sent??state.today?.first_contact_count):'—');
  setText('todayPositive',num(t.replies_positive??state.today?.replies?.positive));
  setText('todayNegative',num(t.replies_negative??state.today?.replies?.negative));
  const rate=t.messages_per_active_hour??state.today?.messages_per_active_hour;
  setText('todayRate',fresh&&rate!=null?Number(rate).toLocaleString('it-IT',{maximumFractionDigits:2}):'—');
  setText('companiesIndexed',num(state.dashboard?.headline?.companies_indexed??state.companies.length));
  setText('sendingWindow',fresh?(t.sending_window||'09:00–19:00 Europe/Madrid'):'Outbound provider non sincronizzato');
}

function renderEngine(){
  const h=state.dashboard?.headline||{};
  setText('semanticInput',num(h.semantic_input_last_run));
  setText('semanticPass',num(h.semantic_pass_last_run));
  setText('semanticRate',pct(h.semantic_pass_rate_pct));
  setText('queryVariants',num(state.sources?.multi_engine_router?.query_variants_count));
  const active=Number(h.active_opportunities||0);
  setText('activeOppsChip',`${num(active)} attive`);
  setText('readyCount',num(h.ready));
  setText('manualCount',num(h.manual_action));
  setText('contactedCount',num(h.contacted_in_active_view));
  setText('successIndex',pct(h.success_index_pct));
  setText('clientProxy',pct(h.new_client_probability_proxy_pct));
  const max=Math.max(active,Number(h.ready||0),Number(h.manual_action||0),Number(h.contacted_in_active_view||0),1);
  setWidth('readyBar',h.ready,max);
  setWidth('manualBar',h.manual_action,max);
  setWidth('contactedBar',h.contacted_in_active_view,max);
}

function renderTerritory(){
  const box=$('territoryHeatmap');
  if(!box)return;
  const rows=(state.territoryView==='countries'?(state.territory?.countries||[]):(state.territory?.territories||[])).slice(0,24);
  if(!rows.length){
    box.innerHTML='<div class="empty-state">Dati territoriali non disponibili.</div>';
    return;
  }
  const max=Math.max(...rows.map(r=>Number(state.territoryView==='countries'?r.best_score:r.score)||0),1);
  box.innerHTML=rows.map((r,i)=>{
    const score=Number(state.territoryView==='countries'?r.best_score:r.score)||0;
    const heat=Math.max(8,Math.round(score/max*100));
    const title=state.territoryView==='countries'?r.country:(r.territory&&r.territory!=='UNRESOLVED'?r.territory:r.region||r.country);
    const subtitle=state.territoryView==='countries'?`${r.territories} territori · media ${r.average_score}`:`${r.country} · ${r.region}`;
    const meta=state.territoryView==='countries'?(r.top_territory||''):(r.mode||'');
    return `<article class="heat-cell" style="--heat:${heat}%"><div><small>${safe(title)} · ${safe(subtitle)}</small><strong>${score.toLocaleString('it-IT',{maximumFractionDigits:2})}</strong><div class="heat-meta"><span>#${i+1}</span><span>${safe(meta)}</span></div></div></article>`;
  }).join('');
}

function populateCompanyCountries(){
  const sel=$('companyCountry');
  if(!sel)return;
  const current=sel.value;
  const countries=[...new Set(state.companies.map(c=>c.country).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'it'));
  sel.innerHTML='<option value="">Tutti i paesi</option>'+countries.map(c=>`<option value="${safe(c)}">${safe(c)}</option>`).join('');
  sel.value=current;
}

function companyFiltered(){
  const q=norm($('companySearch')?.value);
  const country=$('companyCountry')?.value||'';
  const contacted=$('companyContacted')?.value||'';
  return state.companies.filter(c=>{
    const text=c.search_text||norm([c.organization,c.company_id,c.domain,...(c.emails||[])].join(' '));
    return(!q||text.includes(q))&&(!country||c.country===country)&&(!contacted||(contacted==='contacted'?c.contacted:!c.contacted));
  });
}

function renderCompanies(){
  const rows=companyFiltered();
  const total=rows.length;
  const pages=Math.max(1,Math.ceil(total/state.companyPageSize));
  state.companyPage=Math.min(Math.max(1,state.companyPage),pages);
  const start=(state.companyPage-1)*state.companyPageSize;
  const page=rows.slice(start,start+state.companyPageSize);
  setText('companyResultCount',`${num(total)} risultati`);
  setText('companyPaginationInfo',total?`${start+1}–${Math.min(start+page.length,total)} di ${total}`:'0 risultati');
  if($('companyPrev'))$('companyPrev').disabled=state.companyPage<=1;
  if($('companyNext'))$('companyNext').disabled=state.companyPage>=pages;
  if($('companyRows'))$('companyRows').innerHTML=page.map(c=>{
    const contact=(c.emails||[])[0]||c.domain||'—';
    const org=c.organization||c.company_id||c.domain||'Azienda non nominata';
    const priority=c.max_priority;
    return `<tr><td class="cell-primary"><strong>${safe(org)}</strong><span>${safe(c.website||c.domain||c.company_id||'')}</span></td><td class="cell-muted">${safe(c.country||'—')}</td><td class="cell-primary"><strong>${safe(contact)}</strong><span>${(c.contacts||[]).length?`${c.contacts.length} contatti nominativi`:''}</span></td><td>${num(c.opportunity_count||0)}</td><td>${priority==null?'—':`<span class="priority-pill">${safe(priority)}</span>`}</td><td><span class="status-dot-label ${c.contacted?'contacted':''}">${c.contacted?'Contattata':'Non contattata'}</span></td></tr>`;
  }).join('');
  if($('companyEmpty'))$('companyEmpty').hidden=total!==0;
}

function populateOpportunityStatus(){
  const sel=$('opportunityStatus');
  if(!sel)return;
  const current=sel.value;
  const values=[...new Set(state.opportunities.map(o=>o.status).filter(Boolean))].sort();
  sel.innerHTML='<option value="">Tutti gli stati</option>'+values.map(v=>`<option value="${safe(v)}">${safe(v)}</option>`).join('');
  sel.value=current;
}

function renderOpportunities(){
  const q=norm($('opportunitySearch')?.value);
  const s=$('opportunityStatus')?.value||'';
  const rows=state.opportunities.filter(o=>(!q||norm([o.id,o.company_id,o.type,o.status,o.country].join(' ')).includes(q))&&(!s||o.status===s)).slice(0,120);
  setText('opportunityResultCount',`${num(rows.length)} visualizzate`);
  if($('opportunityRows'))$('opportunityRows').innerHTML=rows.map(o=>`<tr><td class="cell-primary"><strong>${safe(o.company_id||o.id||'—')}</strong><span>${safe(o.id||'')}</span></td><td class="cell-muted">${safe(o.country||'—')}</td><td class="cell-muted">${safe(o.type||'—')}</td><td>${o.priority==null?'—':`<span class="priority-pill">${safe(o.priority)}</span>`}</td><td>${o.freshness==null?'—':safe(o.freshness)}</td><td><span class="status-dot-label">${safe(o.status||'—')}</span></td></tr>`).join('');
}

function renderOutbound(){
  const box=$('outboundTimeline');
  if(!outboundFresh()){
    setText('outboundCount','—');
    if(box)box.innerHTML='<div class="empty-state">Dati provider di oggi non sincronizzati. Nessuno zero viene assunto.</div>';
    return;
  }
  const items=state.today?.sent||[];
  setText('outboundCount',num(items.length));
  if(box)box.innerHTML=items.length?items.slice(0,10).map(m=>`<div class="timeline-item"><div class="timeline-time">${safe(formatTime(m.sent_at_local||m.sent_at))}</div><div class="timeline-copy"><strong>${safe(m.organization||m.recipient||'Invio')}</strong><span>${safe(m.subject||m.recipient||'')}</span></div></div>`).join(''):'<div class="empty-state">Nessun invio provider verificato oggi.</div>';
}

function renderReplies(){
  const items=state.today?.replies?.events||[];
  setText('replyCount',num(state.today?.replies?.total??items.length));
  if($('replyTimeline'))$('replyTimeline').innerHTML=items.length?items.slice(0,10).map(r=>{
    const c=norm(r.classification);
    const cls=c.includes('positive')?'positive':c.includes('negative')?'negative':'neutral';
    return `<div class="timeline-item"><div class="timeline-time">${safe(formatTime(r.at))}</div><div class="timeline-copy"><strong>${safe(r.entity||'Risposta')}</strong><span>${safe(r.summary||'')}</span><em class="reply-tag ${cls}">${safe(r.classification||'NEUTRAL')}</em></div></div>`;
  }).join(''):'<div class="empty-state">Nessuna risposta classificata oggi.</div>';
}

function renderHourlyChart(){
  if(!window.Chart)return;
  window.vdsHourlyChart?.destroy();
  if(!outboundFresh())return;
  const bins={};
  for(let h=9;h<=19;h++)bins[h]=0;
  for(const m of state.today?.sent||[]){
    const d=new Date(m.sent_at_local||m.sent_at);
    if(Number.isNaN(d.getTime()))continue;
    const h=Number(new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/Madrid',hour:'2-digit',hour12:false}).format(d));
    if(h in bins)bins[h]++;
  }
  const css=getComputedStyle(document.documentElement);
  window.vdsHourlyChart=new Chart($('hourlyChart'),{
    type:'line',
    data:{
      labels:Object.keys(bins).map(h=>`${h}:00`),
      datasets:[{
        data:Object.values(bins),
        borderColor:css.getPropertyValue('--blue').trim(),
        backgroundColor:css.getPropertyValue('--blue-soft').trim(),
        fill:true,
        tension:.38,
        pointRadius:3,
        pointHoverRadius:5,
        borderWidth:2
      }]
    },
    options:{
      responsive:true,
      maintainAspectRatio:false,
      animation:{duration:420},
      plugins:{legend:{display:false},tooltip:{displayColors:false}},
      scales:{
        x:{grid:{display:false},ticks:{color:css.getPropertyValue('--muted').trim(),font:{family:'DM Sans Local',size:10}}},
        y:{beginAtZero:true,ticks:{precision:0,color:css.getPropertyValue('--muted').trim(),font:{family:'DM Sans Local',size:10}},grid:{color:css.getPropertyValue('--line').trim()}}
      }
    }
  });
}

function renderAll(){
  renderHeader();
  renderToday();
  renderEngine();
  renderTerritory();
  populateCompanyCountries();
  renderCompanies();
  populateOpportunityStatus();
  renderOpportunities();
  renderOutbound();
  renderReplies();
  renderHourlyChart();
}

async function load(){
  const files=['dashboard.json','today.json','companies.json','territory-productivity.json','opportunities.json','sources.json','health.json'];
  const results=await Promise.allSettled(files.map(f=>ghFile(`api/v1/${f}`)));
  const data={};
  results.forEach((r,i)=>{if(r.status==='fulfilled')data[files[i]]=r.value;});
  state.dashboard=data['dashboard.json']||{};
  state.today=data['today.json']||{};
  state.companies=data['companies.json']?.companies||[];
  state.territory=data['territory-productivity.json']||{};
  state.opportunities=data['opportunities.json']?.opportunities||[];
  state.sources=data['sources.json']||{};
  state.health=data['health.json']||{};
  renderAll();
  const failed=results.filter(r=>r.status==='rejected').length;
  if(failed)toast(`${failed} proiezioni non disponibili`);
}

async function dispatchCommand(command,requestId){
  const r=await fetch(`${GH}/repos/${OWNER}/${REPO}/actions/workflows/vds-ai-command.yml/dispatches`,{
    method:'POST',
    headers:{...authHeaders(),'Content-Type':'application/json'},
    body:JSON.stringify({ref:REF,inputs:{command,request_id:requestId}})
  });
  if(r.status===401||r.status===403)throw new Error('ACTION_PERMISSION');
  if(!r.ok)throw new Error(`DISPATCH_${r.status}`);
}

async function waitCommand(requestId){
  const result=$('commandResult');
  for(let i=0;i<24;i++){
    await new Promise(r=>setTimeout(r,i===0?3500:5000));
    try{
      const latest=await ghFile('api/v1/ai-command/latest.json');
      if(latest.command_id===requestId){
        result.hidden=false;
        result.innerHTML=`<div><span class="status-chip">${safe(latest.command_class||latest.status)}</span><strong>${safe(latest.summary||'Comando elaborato')}</strong><p>${safe(latest.answer||'La disposizione è stata registrata per il task bridge esistente.')}</p><small>${safe(latest.status||'')} · gate esistenti obbligatori</small></div>`;
        setText('commandStatus',latest.status||'Elaborato');
        return;
      }
    }catch(e){
      console.debug('poll command',e);
    }
  }
  result.hidden=false;
  result.textContent='Comando avviato. Aggiorna la dashboard per verificare il risultato.';
}

async function submitCommand(ev){
  ev.preventDefault();
  const text=$('commandText').value.trim();
  if(!text)return;
  if(!state.token){
    showAuth();
    return;
  }
  const id=`CMD-WEB-${new Date().toISOString().replace(/[-:.]/g,'').slice(0,15)}-${crypto.getRandomValues(new Uint32Array(1))[0].toString(16)}`;
  const btn=$('commandSubmit');
  btn.disabled=true;
  setText('commandStatus','Invio…');
  try{
    await dispatchCommand(text,id);
    $('commandText').value='';
    toast('Disposizione inviata a GitHub Actions');
    setText('commandStatus','Elaborazione AI');
    waitCommand(id);
  }catch(e){
    console.error(e);
    setText('commandStatus','Errore');
    toast(e.message==='ACTION_PERMISSION'?'Il token richiede Actions: Read and write':'Invio comando non riuscito');
  }finally{
    btn.disabled=false;
  }
}

$('authConnect')?.addEventListener('click',connectToken);
$('githubToken')?.addEventListener('keydown',e=>{if(e.key==='Enter')connectToken();});
$('authCancel')?.addEventListener('click',hideAuth);
$('authButton')?.addEventListener('click',disconnect);
$('refreshButton')?.addEventListener('click',()=>{toast('Aggiornamento dati…');load().catch(e=>{console.error(e);toast('Aggiornamento non riuscito');});});
$('commandForm')?.addEventListener('submit',submitCommand);

for(const id of ['companySearch','companyCountry','companyContacted']){
  $(id)?.addEventListener(id==='companySearch'?'input':'change',()=>{state.companyPage=1;renderCompanies();});
}
$('resetCompanyFilters')?.addEventListener('click',()=>{
  $('companySearch').value='';
  $('companyCountry').value='';
  $('companyContacted').value='';
  state.companyPage=1;
  renderCompanies();
});
$('companyPrev')?.addEventListener('click',()=>{state.companyPage--;renderCompanies();});
$('companyNext')?.addEventListener('click',()=>{state.companyPage++;renderCompanies();});
$('opportunitySearch')?.addEventListener('input',renderOpportunities);
$('opportunityStatus')?.addEventListener('change',renderOpportunities);
document.querySelectorAll('[data-territory-view]').forEach(btn=>btn.addEventListener('click',()=>{
  state.territoryView=btn.dataset.territoryView;
  document.querySelectorAll('[data-territory-view]').forEach(b=>{
    const active=b===btn;
    b.classList.toggle('active',active);
    b.setAttribute('aria-pressed',String(active));
  });
  renderTerritory();
}));

setAuthUI();
load().catch(e=>{
  console.error(e);
  toast('Impossibile caricare le proiezioni pubbliche');
});
