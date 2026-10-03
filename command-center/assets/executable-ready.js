const VDS_EXEC_OWNER='pinolissimo';
const VDS_EXEC_REPO='vds-commercial-intelligence';
const VDS_EXEC_REF='main';
const VDS_EXEC_TOKEN_KEY='vds_cc_gh_token';
const VDS_EXEC_GH='https://api.github.com';

function vdsExecToken(){return sessionStorage.getItem(VDS_EXEC_TOKEN_KEY)||''}
function vdsDecode64(value){const bytes=Uint8Array.from(atob(String(value||'').replace(/\n/g,'')),c=>c.charCodeAt(0));return new TextDecoder().decode(bytes)}
async function vdsFetchJson(path){
  const publicPath=path.startsWith('views/')?`api/v1/${path.split('/').pop()}`:path;
  const r=await fetch(publicPath+`?v=${Date.now()}`,{cache:'no-store'});
  if(!r.ok)throw new Error(`HTTP_${r.status}`);
  return r.json();
}
function vdsSetWidth(el,value,max){if(!el)return;const p=max>0?Math.min(100,Math.max(0,(Number(value||0)/max)*100)):0;el.style.width=`${p}%`}
async function refreshExecutableReady(){
  try{
    const perf=await vdsFetchJson('views/acquisition-performance.json');
    const funnel=perf?.funnel_snapshot||{};
    const executable=Number(funnel.ready_queue??funnel.cross_signal_executable??0);
    const hotPlus=Number(funnel.cross_signal_hot_plus||0);
    const hot=Number(funnel.cross_signal_hot||0);
    const duplicateWaiting=Number(funnel.cross_signal_duplicate_or_waiting||0);
    const ready=document.getElementById('readyCount');
    if(ready){
      ready.textContent=new Intl.NumberFormat('it-IT').format(executable);
      ready.title=`READY realmente eseguibili ora: ${executable}. HOT+: ${hotPlus}; HOT: ${hot}; duplicate/waiting: ${duplicateWaiting}.`;
      ready.dataset.source='acquisition-performance-current';
    }
    const chip=document.getElementById('activeOppsChip');
    if(chip)chip.title=`Il numero READY mostrato è l'eseguibile corrente, non i record legacy/review-ready. Bottleneck: ${perf?.diagnosed_bottleneck||'n/d'}`;
    const active=Number(document.getElementById('activeOppsChip')?.textContent?.match(/\d+/)?.[0]||0);
    vdsSetWidth(document.getElementById('readyBar'),executable,Math.max(active,executable,1));
  }catch(_){/* fail-open: base dashboard remains available */}
}
function startExecutableReadyTruth(){
  refreshExecutableReady();
  setInterval(refreshExecutableReady,5000);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',startExecutableReadyTruth,{once:true});else startExecutableReadyTruth();
