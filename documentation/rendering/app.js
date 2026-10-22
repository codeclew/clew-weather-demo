const base='/clew-weather-demo/rendering/';
const $=id=>document.getElementById(id);
const text=(tag,value,cls)=>{const node=document.createElement(tag);node.textContent=value;if(cls)node.className=cls;return node;};
const link=(label,url,cls)=>{const node=text('a',label,cls);node.href=url;return node;};
const route=(page,id)=>base+page+'.html?id='+encodeURIComponent(id);
async function main(){
 const response=await fetch(base+'manifest.json');if(!response.ok)throw Error('The showcase manifest could not be loaded.');
 const manifest=await response.json();const rows=manifest.capabilities;
 const id=new URLSearchParams(location.search).get('id');
 if($('inventory')){
  for(const category of [...new Set(rows.map(x=>x.category))])$('category').append(new Option(category,category));
  const render=()=>{const query=$('search').value.toLowerCase().trim();const selected=rows.filter(x=>(!$('category').value||x.category===$('category').value)&&(!$('status').value||x.status===$('status').value)&&[x.title,x.description,x.family,x.id].join(' ').toLowerCase().includes(query));$('inventory').replaceChildren();$('count').textContent=`${selected.length} of ${rows.length} entries · ${manifest.historicalCount} retained historical entries plus explicitly scoped current capabilities`;
   for(const row of selected){const article=text('article','', 'capability');article.id=row.id;const body=document.createElement('div');body.append(text('span',row.category+' · '+row.status.replaceAll('_',' '),'badge'+(row.status.includes('GAP')||row.status==='UNSUPPORTED'?' gap':'')),text('h3',row.title),text('p',row.description),text('div',row.identityLabel,'meta'));const actions=text('div','','actions');if(row.example)actions.append(link('Open example',route('view',row.id),'button secondary'));actions.append(link(row.example?'How it was made':'Why no example',route('recipe',row.id)));article.append(body,actions);$('inventory').append(article);}
   if(!selected.length)$('inventory').append(text('p','No entries match these filters. Try another term or clear the filters.','empty'));
  };for(const name of ['search','category','status'])$(name).addEventListener(name==='search'?'input':'change',render);render();
  const showFormat=key=>{const row=rows.find(x=>x.id===key);$('format-title').textContent=row.title;$('format-description').textContent=row.description;$('format-identity').textContent=row.identityLabel;$('format-actions').replaceChildren(link('Open Save City',route('view',key),'button'),link('How it was made',route('recipe',key)));for(const button of document.querySelectorAll('[data-format]'))button.setAttribute('aria-pressed',String(button.dataset.format===key));};
  for(const button of document.querySelectorAll('[data-format]'))button.addEventListener('click',()=>showFormat(button.dataset.format));showFormat('format-standalone');
 }
 if($('recipe')){
  const row=rows.find(x=>x.id===id);if(!row)throw Error('Choose an example from the showcase index.');document.title=row.title+' · How it was made';$('page-title').textContent=row.title;$('page-description').textContent=row.description;
  const root=$('recipe');root.append(text('p',row.identityLabel,'note'));
  if(row.example)root.append(link('Open example',route('view',row.id),'button'));
  root.append(text('h2','Creation record'));const dl=document.createElement('dl');for(const [label,value]of Object.entries(row.recipe.identity)){const dd=document.createElement('dd');dd.append(typeof value==='string'&&value.startsWith('https://')?link(value,value):document.createTextNode(value||'Not recorded in the retained artifact.'));dl.append(text('dt',label),dd);}root.append(dl,text('h2','Command and prerequisites'),text('p',row.recipe.availability,'note warning'),text('p',row.recipe.commandAuthority),text('pre',row.recipe.command));
  root.append(text('p','Uppercase DOCS_ROOT, SNAPSHOT, PUBLICATION, EMPTY_OUTPUT_DIRECTORY and other uppercase paths are placeholders. A downloadable website is not an operational Codeclew documentation store. No command on this page was rerun to create these historical outputs.','meta'));
  for(const [heading,items]of [['Inputs and recipe source',row.recipe.inputs],['Retained output manifests and evidence',row.recipe.outputs],['Renderer implementation',row.recipe.source]]){root.append(text('h2',heading));const list=document.createElement('ul');for(const item of items){const li=document.createElement('li');li.append(link(item.label,item.href));list.append(li);}if(!items.length)list.append(text('li','No corresponding file was retained; this is a visible reproducibility gap.'));root.append(list);}
  if(row.action)root.append(text('h2','Try this interaction'),text('p',row.action));root.append(text('h2','Authority and limits'),text('p',row.recipe.limits));
 }
 if($('example-frame')){const row=rows.find(x=>x.id===id);if(!row?.example)throw Error('This capability has no demonstrated example. Read its gap record.');$('page-title').textContent=row.title;$('page-description').textContent=row.identityLabel;$('example-frame').src=row.example;$('example-frame').title=row.title+' — retained example';$('viewer-actions').append(link('How it was made',route('recipe',id),'button secondary'),link('Open original page',row.example));if(row.action)$('try-action').textContent=row.action;}
}
main().catch(error=>{const area=$('errors');area.hidden=false;area.textContent=error.message;});
