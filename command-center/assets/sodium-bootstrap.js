(()=>{
  let resolveReady;
  let rejectReady;
  window.__vdsSodiumReady=new Promise((resolve,reject)=>{resolveReady=resolve;rejectReady=reject});
  window.sodium={
    onload(instance){resolveReady(instance)}
  };
  window.setTimeout(()=>rejectReady(new Error('LibSodium initialization timeout')),15000);
})();
