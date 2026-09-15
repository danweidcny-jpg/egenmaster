from pathlib import Path

FILES=[Path('index.html'), Path('egen-master-deck.html')]
for path in FILES:
    s=path.read_text()
    old="""    cell.className='cal-cell'+(ds===today?' today':'')+(items.length?' has-items':'');
    cell.innerHTML=`<div class=\"cal-daynum\">${d}</div>`+items.map(it=>`<div class=\"cal-item ${it.kind==='brief'?'clickable':''}\" ${it.kind==='brief'?`data-brief=\"${it.id}\"`:''}>${escapeHtml((it.time?it.time+' · ':'')+it.title)}</div>`).join('');
    grid.appendChild(cell);"""
    new="""    cell.className='cal-cell'+(ds===today?' today':'')+(items.length?' has-items':'');
    cell.dataset.date=ds;
    cell.innerHTML=`<div class=\"cal-daynum\">${d}</div>`+items.map(it=>`<div class=\"cal-item ${it.kind==='brief'?'clickable':''}\" draggable=\"${it.kind==='project'||it.kind==='brief'?'true':'false'}\" data-cal-kind=\"${it.kind}\" data-cal-id=\"${it.id}\" ${it.kind==='brief'?`data-brief=\"${it.id}\"`:''}>${escapeHtml((it.time?it.time+' · ':'')+it.title)}</div>`).join('');
    grid.appendChild(cell);"""
    if old not in s:
        raise SystemExit(f'{path}: calendar cell markup anchor missing')
    s=s.replace(old,new,1)
    path.write_text(s)
    print('patched',path)
