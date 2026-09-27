'use strict';
const rows=document.getElementById('ingredient-rows');
const add=document.getElementById('add-ingredient');
if(add&&rows){add.addEventListener('click',()=>{if(rows.children.length>=500)return;const row=rows.querySelector('.ingredient-row').cloneNode(true);row.querySelectorAll('input').forEach(i=>i.value='');rows.append(row);row.querySelector('input').focus();});rows.addEventListener('click',event=>{const button=event.target.closest('.remove-row');if(!button)return;if(rows.children.length===1){button.parentElement.querySelectorAll('input').forEach(i=>i.value='');}else button.parentElement.remove();});}
document.querySelectorAll('[data-product-view]').forEach(button=>button.addEventListener('click',()=>{document.querySelectorAll('[data-product-view]').forEach(b=>b.classList.toggle('active',b===button));document.querySelectorAll('[data-product-card]').forEach(card=>{card.hidden=button.dataset.productView==='selected'&&card.dataset.productCard!==button.dataset.selected;if(!card.hidden&&button.dataset.productView==='selected')card.open=true;});}));
document.querySelectorAll('[data-preview-csv]').forEach(button=>{
 let current=null;
 button.addEventListener('click',async()=>{
  const form=button.closest('form'),status=form.querySelector('[data-csv-status]'),preview=form.querySelector('[data-csv-preview]');
  const upload=form.querySelector('[name=ingredients_csv]');if(!upload.files.length){status.textContent='CSV 파일을 선택해 주세요.';return;}
  button.disabled=true;status.textContent='성분 열을 분류하고 있습니다…';
  try{
   const body=new FormData();body.append('ingredients_csv',upload.files[0]);body.append('csrf_token',form.querySelector('[name=csrf_token]').value);
   const selects=preview.querySelectorAll('[data-csv-column]');
   if(selects.length){const mapping={};selects.forEach(el=>mapping[el.dataset.csvColumn]=el.value===''?null:Number(el.value));body.append('mapping',JSON.stringify(mapping));body.append('has_header',preview.querySelector('[data-csv-header]').checked?'1':'0');}
   else body.append('use_ai',form.querySelector('[data-ai-csv]').checked?'1':'0');
   const response=await fetch(button.dataset.url,{method:'POST',body});const data=await response.json();if(!response.ok)throw new Error(data.message||'분류에 실패했습니다.');
   current=data;preview.replaceChildren();
   const heading=document.createElement('p');heading.textContent='성분명·CAS·함량 열을 확인해 주세요. 수정한 뒤 다시 미리보기를 누를 수 있습니다.';preview.append(heading);
   const headerLabel=document.createElement('label'),headerInput=document.createElement('input');headerInput.type='checkbox';headerInput.checked=data.has_header;headerInput.dataset.csvHeader='';headerLabel.append(headerInput,document.createTextNode('첫 줄은 열 제목'));preview.append(headerLabel);
   [['inci_name','성분명'],['cas_no','CAS 번호'],['concentration','배합 비율 (%)']].forEach(([key,title])=>{
    const label=document.createElement('label');label.append(document.createTextNode(title));const select=document.createElement('select');select.dataset.csvColumn=key;const blank=document.createElement('option');blank.value='';blank.textContent='없음 / 미입력';select.append(blank);
    data.columns.forEach((column,i)=>{const option=document.createElement('option');option.value=i;option.textContent=`${i+1}: ${column}`;select.append(option);});select.value=data.mapping[key]??'';select.addEventListener('change',()=>{current=null;status.textContent='변경한 열로 미리보기를 다시 실행해 주세요.';});label.append(select);preview.append(label);
   });
   headerInput.addEventListener('change',()=>{current=null;});
   const table=document.createElement('table'),tbody=document.createElement('tbody');
   data.ingredients.slice(0,12).forEach(row=>{const tr=document.createElement('tr');[row.inci_name,row.cas_no,row.concentration===null?'미입력':row.concentration+'%'].forEach(value=>{const td=document.createElement('td');td.textContent=value;tr.append(td);});tbody.append(tr);});table.append(tbody);preview.append(table);
   if(data.ingredients.length){const apply=document.createElement('button');apply.type='button';apply.className='button subtle small';apply.textContent=`확인한 ${data.ingredients.length}개 성분을 입력칸에 적용`;apply.addEventListener('click',()=>{
    if(!current){status.textContent='열 설정을 바꿨으니 미리보기를 다시 실행해 주세요.';return;}
    const template=rows.querySelector('.ingredient-row').cloneNode(true);rows.replaceChildren();current.ingredients.forEach(item=>{const row=template.cloneNode(true);row.querySelector('[name=inci_name]').value=item.inci_name;row.querySelector('[name=cas_no]').value=item.cas_no;row.querySelector('[name=concentration]').value=item.concentration??'';rows.append(row);});upload.value='';form.querySelector('[name=ingredients_text]').value='';preview.replaceChildren();status.textContent='입력칸에 반영했습니다. 값을 확인한 뒤 저장하고 분석하기를 눌러 주세요.';current=null;
   });preview.append(apply);}
   status.textContent=data.message||`${data.ingredients.length}개 성분을 인식했습니다. 원본과 비교해 확인해 주세요.`;
  }catch(error){status.textContent=error.message;}finally{button.disabled=false;}
 });
 button.closest('form').querySelector('[name=ingredients_csv]').addEventListener('change',()=>{current=null;button.closest('form').querySelector('[data-csv-preview]').replaceChildren();});
});
