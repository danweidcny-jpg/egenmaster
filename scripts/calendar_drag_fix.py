from pathlib import Path
import re

FILES=[Path('index.html'), Path('egen-master-deck.html')]

CSS='''
  .cal-item[draggable="true"]{cursor:grab;}
  .cal-item[draggable="true"]:active{cursor:grabbing;}
  .cal-cell.drag-over{outline:2px dashed var(--teal);outline-offset:-4px;background:rgba(62,143,118,.08);}
'''

for path in FILES:
    s=path.read_text()

    if '.cal-cell.drag-over' not in s:
        s=s.replace('</style>', CSS+'\n</style>',1)

    # Fix timezone bug by formatting calendar loop dates from local components rather than UTC ISO conversion.
    s=s.replace("out.push(d.toISOString().slice(0,10));", "out.push(`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`);", 1)

    # Add a shared drag-update helper before renderCalendar.
    if 'function moveCalendarEntryToDate(' not in s:
        marker='function renderCalendar(){'
        helper=r'''function moveCalendarEntryToDate(kind, id, newDate){
  if(kind==='project'){
    const projectId = id.replace(/^project-/, '');
    const p = projects.find(x=>x.id===projectId);
    if(!p) return;
    p.dueDate = newDate;
    saveTasksToStorage();
  }else if(kind==='brief'){
    const b = briefs.find(x=>x.id===id);
    if(!b) return;
    b.dueDate = newDate;
    saveBriefsToStorage();
  }else{
    return;
  }
  renderBoard();
  renderCalendar();
}
'''
        if marker not in s:
            raise SystemExit(f'{path}: renderCalendar marker missing')
        s=s.replace(marker,helper+marker,1)

    # Make calendar cells explicit drop targets.
    old_cell="cell.innerHTML=`<div class=\"cal-daynum\">${d}</div>`+items.map(it=>`<div class=\"cal-item ${it.kind==='brief'?'clickable':''}\" ${it.kind==='brief'?`data-brief=\"${it.id}\"`:''} title=\"${escapeHtml(it.title)}\">${escapeHtml((it.time?it.time+' · ':'')+it.title)}</div>`).join('');"
    new_cell="cell.dataset.date=dateStr;\n    cell.innerHTML=`<div class=\"cal-daynum\">${d}</div>`+items.map(it=>`<div class=\"cal-item ${it.kind==='brief'?'clickable':''}\" draggable=\"${it.kind==='project'||it.kind==='brief'?'true':'false'}\" data-cal-kind=\"${it.kind}\" data-cal-id=\"${it.id}\" ${it.kind==='brief'?`data-brief=\"${it.id}\"`:''} title=\"${escapeHtml(it.title)}\">${escapeHtml((it.time?it.time+' · ':'')+it.title)}</div>`).join('');"
    if old_cell in s:
        s=s.replace(old_cell,new_cell,1)
    else:
        # fallback for slightly different current formatting
        s=s.replace("cell.innerHTML=`<div class=\"cal-daynum\">${d}</div>`+items.map(it=>`<div class=\"cal-item\" title=\"${escapeHtml(it.title)}\">${escapeHtml((it.time?it.time+' · ':'')+it.title)}</div>`).join('');", new_cell,1)

    # Install drag/drop listeners after existing brief click binding.
    anchor="grid.querySelectorAll('.cal-item[data-brief]').forEach(el=>el.addEventListener('click',()=>openBriefModal(el.dataset.brief)));"
    listeners=r'''grid.querySelectorAll('.cal-item[data-brief]').forEach(el=>el.addEventListener('click',()=>openBriefModal(el.dataset.brief)));
  grid.querySelectorAll('.cal-item[draggable="true"]').forEach(el=>{
    el.addEventListener('dragstart', e=>{
      e.dataTransfer.effectAllowed='move';
      e.dataTransfer.setData('text/plain', JSON.stringify({kind:el.dataset.calKind,id:el.dataset.calId}));
    });
  });
  grid.querySelectorAll('.cal-cell:not(.empty)').forEach(cell=>{
    cell.addEventListener('dragover', e=>{e.preventDefault();cell.classList.add('drag-over');});
    cell.addEventListener('dragleave', ()=>cell.classList.remove('drag-over'));
    cell.addEventListener('drop', e=>{
      e.preventDefault();
      cell.classList.remove('drag-over');
      let payload;
      try{payload=JSON.parse(e.dataTransfer.getData('text/plain'));}catch{return;}
      if(!payload || !cell.dataset.date) return;
      moveCalendarEntryToDate(payload.kind,payload.id,cell.dataset.date);
    });
  });'''
    if anchor in s and 'grid.querySelectorAll(\'.cal-item[draggable="true"]\')' not in s:
        s=s.replace(anchor,listeners,1)

    path.write_text(s)
    print('patched',path)
