// Visual Design Studio — 2026
const QA_OWNER='pinolissimo',QA_REPO='vds-commercial-intelligence',QA_REF='main';
const QA_GH='https://api.github.com',QA_PATH='outreach/autonomous-send-queue.jsonl',QA_TOKEN='vds_cc_gh_token';
const q=id=>document.getElementById(id);
let qaSha=null,qaRows=[];

function qaToken(){return sessionStorage.getItem(QA_TOKEN)||'';}
function qaHeaders(){return {'Accept':'application/vnd.github+json','Authorization':`Bearer ${qaToken()}`,'X-GitHub-Api-Version':'2022-11-28'};}
function qaDecode(v){const b=Uint8Array.from(atob(String(v||'').replace(/\n/g,'')),c=>c.charCodeAt(0));return new TextDecoder().decode(b);}
function qaEncode(v){const b=new TextEncoder().encode(v);let s='';for(const x of b)s+=String.fromCharCode(x);return btoa(s);}
function qaEscape(v){return String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
function qaToast(m){const e=q('toast');if(!e)return;e.textContent=m;e.classList.add('show');clearTimeout(qaToast.t);qaToast.t=setTimeout(()=>e.classList.remove('show'),2500);}

async function qaRead(){
  const publicRead=await fetch(QA_PATH+`?v=${Date.now()}`,{cache:'no-store'});
  if(publicRead.ok){
    qaRows=(await publicRead.text()).split(/\r?\n/).filter(Boolean).map(x=>JSON.parse(x));
  }else{
    throw new Error(`QUEUE_PUBLIC_READ_${publicRead.status}`);
  }
  if(qaToken()){
    const meta=await fetch(`${QA_GH}/repos/${QA_OWNER}/${QA_REPO}/contents/${QA_PATH}?ref=${QA_REF}`,{headers:qaHeaders(),cache:'no-store'});
    if(meta.ok){const d=await meta.json();qaSha=d.sha;}
    else if(meta.status===401||meta.status===403){qaSha=null;}
  }
  return qaRows;
}
async function qaWrite(message){
  if(!qaToken())throw new Error('Connetti GitHub prima di approvare.');
  if(!qaSha){
    const latest=await fetch(`${QA_GH}/repos/${QA_OWNER}/${QA_REPO}/contents/${QA_PATH}?ref=${QA_REF}`,{headers:qaHeaders(),cache:'no-store'});
    if(latest.status===401||latest.status===403)throw new Error('Token GitHub senza accesso Contents. Serve Contents: Read and write.');
    if(!latest.ok)throw new Error(`QUEUE_META_${latest.status}`);
    qaSha=(await latest.json()).sha;
  }
  const content=qaRows.map(x=>JSON.stringify(x)).join('\n')+'\n';
  const body={message,content:qaEncode(content),branch:QA_REF,sha:qaSha};
  const r=await fetch(`${QA_GH}/repos/${QA_OWNER}/${QA_REPO}/contents/${QA_PATH}`,{method:'PUT',headers:{...qaHeaders(),'Content-Type':'application/json'},body:JSON.stringify(body)});
  if(r.status===409)throw new Error('La queue è cambiata: ricarico i dati, ripeti l’azione.');
  if(r.status===401||r.status===403)throw new Error('Il token GitHub deve avere Contents: Read and write sul repository.');
  if(!r.ok)throw new Error(`QUEUE_WRITE_${r.status}`);
  const d=await r.json();qaSha=d.content?.sha||qaSha;
}
function qaCounts(){
  const c={DRAFT:0,APPROVED_TO_SEND:0,SENT:0,FAILED:0,CANCELLED:0};
  for(const r of qaRows)c[r.status]=(c[r.status]||0)+1;
  for(const k of Object.keys(c)){const e=q('qa'+k.replaceAll('_',''));if(e)e.textContent=c[k]||0;}
}
function qaRender(){
  qaCounts();
  const body=q('approvalRows'),empty=q('approvalEmpty');if(!body)return;
  const drafts=qaRows.filter(x=>x.status==='DRAFT'&&x.action_type==='FIRST_CONTACT');
  q('approvalCount').textContent=`${drafts.length} da valutare`;
  empty.hidden=drafts.length>0;
  body.innerHTML=drafts.map(r=>`<tr>
    <td><input class="qa-select" type="checkbox" data-id="${qaEscape(r.queue_id)}" aria-label="Seleziona ${qaEscape(r.organization)}"></td>
    <td><strong>${qaEscape(r.organization||'—')}</strong><small class="qa-meta">${qaEscape(r.metadata?.source||'')}</small></td>
    <td><a href="mailto:${qaEscape(r.recipient)}">${qaEscape(r.recipient)}</a></td>
    <td><strong>${qaEscape(r.subject)}</strong><details><summary>Anteprima</summary><pre>${qaEscape(r.text)}</pre></details></td>
    <td>${qaEscape(r.metadata?.priority??'—')}</td>
    <td class="qa-actions"><button class="text-button qa-approve" type="button" data-id="${qaEscape(r.queue_id)}">Approva</button><button class="text-button qa-reject" type="button" data-id="${qaEscape(r.queue_id)}">Rifiuta</button></td>
  </tr>`).join('');
}
async function qaRefresh(){
  const status=q('approvalStatus');status.textContent='Caricamento queue…';
  try{await qaRead();qaRender();status.textContent='Queue GitHub sincronizzata.';}
  catch(e){status.textContent=e.message;}
}
async function qaChange(ids,status){
  if(!ids.length)return;
  const now=new Date().toISOString();
  for(const r of qaRows){
    if(!ids.includes(r.queue_id))continue;
    r.status=status;
    if(status==='APPROVED_TO_SEND'){
      r.approved_at=now;
      r.eligibility_basis=r.eligibility_basis||'OWNER_APPROVED_ONE_TO_ONE';
      r.metadata={...(r.metadata||{}),approved_via:'VDS_COMMAND_CENTER',approved_at:now};
    }else{
      r.metadata={...(r.metadata||{}),rejected_via:'VDS_COMMAND_CENTER',rejected_at:now};
    }
  }
  await qaWrite(status==='APPROVED_TO_SEND'?'queue: approve selected first contacts':'queue: reject selected first contacts');
  await qaRefresh();
  qaToast(status==='APPROVED_TO_SEND'?'Approvazione salvata: il sender GitHub è stato attivato.':'Contatti rifiutati.');
}
document.addEventListener('DOMContentLoaded',()=>{
  q('approvalRefresh')?.addEventListener('click',qaRefresh);
  q('approvalApproveSelected')?.addEventListener('click',async()=>{
    const ids=[...document.querySelectorAll('.qa-select:checked')].map(x=>x.dataset.id);
    try{await qaChange(ids,'APPROVED_TO_SEND');}catch(e){q('approvalStatus').textContent=e.message;}
  });
  q('approvalRows')?.addEventListener('click',async e=>{
    const a=e.target.closest('.qa-approve'),r=e.target.closest('.qa-reject');if(!a&&!r)return;
    try{await qaChange([(a||r).dataset.id],a?'APPROVED_TO_SEND':'CANCELLED');}catch(err){q('approvalStatus').textContent=err.message;}
  });
  qaRefresh();
});
