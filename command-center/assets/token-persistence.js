const VDS_SESSION_TOKEN_KEY='vds_cc_gh_token';
const VDS_PERSISTENT_TOKEN_KEY='vds_cc_gh_token_persistent_v1';

function restorePersistentGitHubToken(){
  try{
    const sessionToken=sessionStorage.getItem(VDS_SESSION_TOKEN_KEY)||'';
    const persistentToken=localStorage.getItem(VDS_PERSISTENT_TOKEN_KEY)||'';
    if(sessionToken){
      if(persistentToken!==sessionToken)localStorage.setItem(VDS_PERSISTENT_TOKEN_KEY,sessionToken);
      return;
    }
    if(persistentToken)sessionStorage.setItem(VDS_SESSION_TOKEN_KEY,persistentToken);
  }catch(_){/* storage unavailable: existing session-only auth remains functional */}
}

function persistValidatedToken(candidate){
  if(!candidate)return;
  let attempts=0;
  const timer=setInterval(()=>{
    attempts++;
    try{
      const validated=sessionStorage.getItem(VDS_SESSION_TOKEN_KEY)||'';
      if(validated===candidate){
        localStorage.setItem(VDS_PERSISTENT_TOKEN_KEY,validated);
        clearInterval(timer);
      }else if(attempts>=30){
        clearInterval(timer);
      }
    }catch(_){clearInterval(timer)}
  },200);
}

restorePersistentGitHubToken();

window.addEventListener('pagehide',()=>{
  try{
    const token=sessionStorage.getItem(VDS_SESSION_TOKEN_KEY)||'';
    if(token)localStorage.setItem(VDS_PERSISTENT_TOKEN_KEY,token);
    else localStorage.removeItem(VDS_PERSISTENT_TOKEN_KEY);
  }catch(_){/* best effort */}
});

document.addEventListener('DOMContentLoaded',()=>{
  const connect=document.getElementById('authConnect');
  const input=document.getElementById('githubToken');
  if(connect&&input){
    connect.addEventListener('click',()=>persistValidatedToken(input.value.trim()),true);
    input.addEventListener('keydown',event=>{
      if(event.key==='Enter')persistValidatedToken(input.value.trim());
    },true);
  }
},{once:true});
