from pathlib import Path
import re

FILES=[Path('index.html'),Path('egen-master-deck.html')]

for path in FILES:
    s=path.read_text()

    # Add ids to calendar heading/subtitle so renderCalendar can adapt by role.
    s=s.replace('<h2 class="page-title">My Calendar</h2>', '<h2 class="page-title" id="calendarTitle">My Calendar</h2>', 1)
    s=s.replace('<p class="page-sub">Project event dates and proposal / quotation due dates only.</p>', '<p class="page-sub" id="calendarSubtitle">Project event dates and proposal / quotation due dates only.</p>', 1)

    pattern=r'''function getPersonalCalendarEntries\(\)\{.*?\n\}\nfunction moveCalendarEntryToDate'''
    replacement=r'''function calendarScopeOwnerIds(){
  if(currentUserId==='m1' || currentUserId==='m5') return TEAM.map(m=>m.id); // Danwei: JB + KL
  if(currentUserId==='m6') return TEAM.filter(m=>m.office==='KL').map(m=>m.id); // Chen: KL only
  return [currentUserId];
}
function calendarScopeLabel(){
  if(currentUserId==='m1' || currentUserId==='m5') return {title:'JB + KL Team Calendar', sub:'All JB & KL project event dates and New Brief proposal / quotation due dates.'};
  if(currentUserId==='m6') return {title:'KL Team Calendar', sub:'KL team project event dates and New Brief proposal / quotation due dates.'};
  return {title:'My Calendar', sub:'Project event dates and proposal / quotation due dates only.'};
}
function getPersonalCalendarEntries(){
  const entries=[];
  const ownerIds=calendarScopeOwnerIds();
  const multi=ownerIds.length>1;
  const ownerName=id=>{ const m=TEAM.find(x=>x.id===id); return m?m.name:'Unassigned'; };

  briefs.filter(b=>b.status!=='Approved' && ownerIds.includes(b.assigneeId)).forEach(b=>{
    if(!b.dueDate) return;
    entries.push({
      id:b.id, kind:'brief', ownerId:b.assigneeId,
      title: multi ? `${ownerName(b.assigneeId)} · ${b.title}` : b.title,
      date:b.dueDate, endDate:b.dueDate, time:'',
      note:'Proposal / quotation due date'
    });
  });

  projects.filter(p=>ownerIds.includes(p.ownerId)).forEach(p=>{
    if(!p.dueDate) return;
    entries.push({
      id:'project-'+p.id, kind:'project', ownerId:p.ownerId,
      title: multi ? `${ownerName(p.ownerId)} · ${p.title}` : p.title,
      date:p.dueDate, endDate:p.dueDate, time:'',
      note:/proposal|quotation/i.test(p.title)?'Proposal / quotation due date':'Project event date'
    });
  });
  return entries;
}
function moveCalendarEntryToDate'''
    s,n=re.subn(pattern,replacement,s,count=1,flags=re.S)
    if n!=1:
        raise SystemExit(f'{path}: calendar entries replacement failed')

    # Update calendar heading every render.
    marker="function renderCalendar(){"
    insert="""function renderCalendar(){\n  const scope=calendarScopeLabel();\n  const titleEl=document.getElementById('calendarTitle');\n  const subEl=document.getElementById('calendarSubtitle');\n  if(titleEl) titleEl.textContent=scope.title;\n  if(subEl) subEl.textContent=scope.sub;"""
    if marker in s:
        s=s.replace(marker,insert,1)
    else:
        raise SystemExit(f'{path}: renderCalendar marker missing')

    path.write_text(s)
    print('patched',path)
