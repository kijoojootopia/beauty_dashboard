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

function showExportPage(panel,page){
 const rows=[...panel.querySelectorAll('[data-export-row]')];
 if(!rows.length)return;
 page=Math.max(1,Math.min(Number(page)||1,Math.ceil(rows.length/50)));
 const start=(page-1)*50;
 rows.forEach((row,index)=>{row.hidden=index<start||index>=start+50;});
 panel.dataset.currentPage=String(page);
 panel.querySelectorAll('[data-export-page]').forEach(button=>{
  if(Number(button.dataset.exportPage)===page)button.setAttribute('aria-current','page');
  else button.removeAttribute('aria-current');
 });
 panel.querySelector('[data-export-range]').textContent=`전체 ${rows.length}개국 중 ${start+1}–${Math.min(start+50,rows.length)}위`;
}
document.addEventListener('click',event=>{
 const button=event.target.closest('[data-export-page]');
 if(!button)return;
 const panel=button.closest('[data-export-pages]');
 showExportPage(panel,button.dataset.exportPage);
 panel.querySelector('summary').focus({preventScroll:true});
 panel.scrollIntoView({block:'start'});
});

document.querySelectorAll('[data-live-section]').forEach(async container=>{
 const status=document.createElement('p');status.className='live-status';status.setAttribute('role','status');status.textContent='최신 자료를 불러오는 중입니다…';container.append(status);
 try{const response=await fetch(container.dataset.liveUrl,{headers:{Accept:'text/html'}});if(!response.ok)throw new Error();const html=await response.text();
 const previous=container.querySelector('[data-export-pages]');
 const page=previous?.dataset.currentPage||1,open=previous?.open;
 container.innerHTML=html;
 const panel=container.querySelector('[data-export-pages]');
 if(panel){panel.open=Boolean(open);showExportPage(panel,page);}
 }catch{status.textContent='자료를 불러오지 못했습니다. 새로고침해 다시 시도해 주세요.';}
});
