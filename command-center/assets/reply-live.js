const OWNER='pinolissimo';
const REPO='vds-commercial-intelligence';
const REF='main';
const GH='https://api.github.com';
const REFRESH_MS=15000;

const $=(id)=>document.getElementById(id);
const safe=(v)=>String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
const norm=(v)=>String(v??'').toLocaleLowerCase('it-IT');
const fmt=new Intl.NumberFormat('it-IT');
const timeFmt=new Intl.DateTimeFormat('it-IT',{timeZone:'Europe/Madrid',hour:'2-digit',minute:'2-digit'});

function decode64Utf8(value){
  const bytes=Uint8Array.from(atob(value.replace(/\n/g,'')),c=>c.charCodeAt(0));
  return new TextDecoder().decode(bytes);
}

async function jsonFile(name){
  const url=`${GH}/repos/${OWNER}/${REPO}/contents/api/v1/${name}?ref=${encodeURIComponent(REF)}&v=${Date.now()}`;
  const response=await fetch(url,{
    headers:{'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'},
    cache:'no-store'
  });
  if(!response.ok)throw new Error(`${name}: HTTP ${response.status}`);
  const payload=await response.json();
  if(payload?.encoding!=='base64'||!payload?.content)throw new Error(`${name}: formato inatteso`);
  return JSON.parse(decode64Utf8(payload.content));
}

function replyFresh(health,today){
  if(typeof health?.reply_source_fresh==='boolean')return health.reply_source_fresh;
  if(typeof today?.source_health?.reply_source_fresh==='boolean')return today.source_health.reply_source_fresh;
  const value=today?.provider_inbound_overlay_updated_at||health?.provider_inbound_overlay_updated_at;
  if(!value)return false;
  const dt=new Date(value);
  if(Number.isNaN(dt.getTime()))return false;
  const age=(Date.now()-dt.getTime())/3600000;
  return age>=0&&age<=1.5;
}

function render(today,health){
  const fresh=replyFresh(health,today);
  const replies=today?.replies||{};
  if(!fresh){
    if($('todayPositive'))$('todayPositive').textContent='—';
    if($('todayNegative'))$('todayNegative').textContent='—';
    if($('replyCount'))$('replyCount').textContent='—';
    if($('replyTimeline'))$('replyTimeline').innerHTML='<div class="empty-state">Inbox non riconciliata di recente. Nessuno zero viene assunto.</div>';
    return;
  }

  if($('todayPositive'))$('todayPositive').textContent=fmt.format(Number(replies.positive||0));
  if($('todayNegative'))$('todayNegative').textContent=fmt.format(Number(replies.negative||0));
  if($('replyCount'))$('replyCount').textContent=fmt.format(Number(replies.total||0));

  const items=Array.isArray(replies.events)?replies.events:[];
  if($('replyTimeline')){
    $('replyTimeline').innerHTML=items.length?items.slice(0,10).map(r=>{
      const c=norm(r.classification);
      const cls=c.includes('positive')?'positive':c.includes('negative')?'negative':'neutral';
      const dt=new Date(r.at);
      const at=Number.isNaN(dt.getTime())?'—':timeFmt.format(dt);
      const label=r.subtype&&r.subtype!=='ACK_ONLY'?`${r.classification} · ${r.subtype}`:(r.classification||'NEUTRAL');
      return `<div class="timeline-item"><div class="timeline-time">${safe(at)}</div><div class="timeline-copy"><strong>${safe(r.entity||'Risposta')}</strong><span>${safe(r.summary||r.subject||'')}</span><em class="reply-tag ${cls}">${safe(label)}</em></div></div>`;
    }).join(''):'<div class="empty-state">Nessuna risposta commerciale classificata oggi.</div>';
  }
}

async function refresh(){
  try{
    const [today,health]=await Promise.all([jsonFile('today.json'),jsonFile('health.json')]);
    render(today,health);
  }catch(error){
    console.debug('reply-live refresh',error);
  }
}

refresh();
setInterval(refresh,REFRESH_MS);
