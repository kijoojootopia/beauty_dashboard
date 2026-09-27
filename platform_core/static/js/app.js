'use strict';
document.querySelectorAll('[data-submit-change]').forEach(el=>el.addEventListener('change',()=>el.form.requestSubmit()));
document.querySelectorAll('[data-country-select]').forEach(el=>{
 const update=()=>el.closest('form').querySelectorAll('[data-member-group]').forEach(field=>{
   const active=field.dataset.memberGroup===el.value;field.hidden=!active;
   field.querySelector('select').disabled=!active;field.querySelector('select').required=active;
 });el.addEventListener('change',update);update();
});
document.querySelectorAll('[data-confirm]').forEach(form=>form.addEventListener('submit',event=>{if(!confirm(form.dataset.confirm))event.preventDefault();}));
document.querySelectorAll('[data-go-back]').forEach(el=>el.addEventListener('click',()=>history.back()));
function revealHash(){const id=decodeURIComponent(location.hash.slice(1));if(!id)return;const el=document.getElementById(id);if(el&&el.tagName==='DETAILS')el.open=true;}
window.addEventListener('hashchange',revealHash);revealHash();

document.querySelectorAll('[data-note-form]').forEach(form=>form.addEventListener('submit',async event=>{
 event.preventDefault();const button=form.querySelector('button'),status=form.querySelector('[data-note-status]');button.disabled=true;
 try{const response=await fetch(form.action,{method:'POST',body:new FormData(form),headers:{Accept:'application/json'}});if(!response.ok){let error;try{error=await response.json();}catch{}throw new Error(error?.message||'메모를 저장하지 못했습니다. 다시 시도해 주세요.');}
 const {note}=await response.json();const article=document.createElement('article');article.className='saved-note';const time=document.createElement('time');time.textContent=note.created_at.replace('T',' ').slice(0,19)+' UTC';const p=document.createElement('p');p.className='preserve-lines';p.textContent=note.content;article.append(time,p);const list=form.closest('section').querySelector('[data-note-list]');list.querySelector('[data-empty-notes]')?.remove();list.prepend(article);form.querySelector('textarea').value='';status.textContent='메모를 추가했습니다.';
 }catch(error){status.textContent=error.message;}finally{button.disabled=false;}
}));

document.querySelectorAll('[data-live-section]').forEach(async container=>{
 const status=document.createElement('p');status.className='live-status';status.setAttribute('role','status');status.textContent='최신 자료를 불러오는 중입니다…';container.append(status);
 try{const response=await fetch(container.dataset.liveUrl,{headers:{Accept:'text/html'}});if(!response.ok)throw new Error();const html=await response.text();container.innerHTML=html;}catch{status.textContent='자료를 불러오지 못했습니다. 새로고침해 다시 시도해 주세요.';}
});
