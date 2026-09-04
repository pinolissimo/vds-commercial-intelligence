const VDS_PAT_TEMPLATE = 'https://github.com/settings/personal-access-tokens/new?name=VDS%20Command%20Center&description=Private%20VDS%20dashboard%20access%20for%20one%20repository&target_name=pinolissimo&expires_in=90&contents=read&actions=write&secrets=write';

function installTokenHelper(){
  const card=document.querySelector('#authOverlay .auth-card');
  if(!card || document.getElementById('vdsPatHelper'))return;
  const helper=document.createElement('div');
  helper.id='vdsPatHelper';
  helper.className='token-helper';
  helper.innerHTML=`<a class="text-button token-helper-link" href="${VDS_PAT_TEMPLATE}" target="_blank" rel="noopener noreferrer">Crea token GitHub con permessi precompilati ↗</a><small>Nel modulo GitHub seleziona <strong>Only select repositories</strong> e scegli solo <strong>vds-commercial-intelligence</strong>. I permessi sono già precompilati: Contents read, Actions write, Secrets write. Scadenza proposta: 90 giorni.</small>`;
  const actions=card.querySelector('.auth-actions');
  if(actions)actions.insertAdjacentElement('afterend',helper); else card.appendChild(helper);
}

document.addEventListener('DOMContentLoaded',installTokenHelper,{once:true});
