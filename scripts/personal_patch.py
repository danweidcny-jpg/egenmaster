from pathlib import Path
import re

FILES = [Path('index.html'), Path('egen-master-deck.html')]

for path in FILES:
    s = path.read_text()

    # shared schedule state
    s = s.replace(
        "let statuses = {}; // memberId -> 'free' | 'busy' | 'capacity'\nlet currentUserId = null; // who is using this device right now",
        "let statuses = {}; // memberId -> 'free' | 'busy' | 'capacity'\nlet schedules = []; // {id,ownerId,title,date,endDate,time,note}\nlet scheduleCounter = 1;\nlet currentUserId = null; // who is using this device right now",
        1,
    )

    # calendar heading / copy
    s = s.replace('<h2 class="page-title">Calendar</h2>', '<h2 class="page-title">My Calendar</h2>', 1)
    s = s.replace(
        "<p class=\"page-sub\">Everyone's deadlines in one place — switch to a personal view to see just one person's plate.</p>",
        "<p class=\"page-sub\">Your own deadlines and confirmed schedule in one place.</p>", 1)
    s = s.replace('<div class="cal-toggle" id="calToggle">', '<div class="cal-toggle" id="calToggle" style="display:none;">', 1)
    s = s.replace('<div class="col" id="calPersonWrap" style="display:none; max-width:260px; min-width:180px;">', '<div class="col" id="calPersonWrap" style="display:none!important; max-width:260px; min-width:180px;">', 1)

    # board summaries only current user
    s = s.replace(
        "const allItems = getAllItemsFlat(); // computed once per render, shared below (was recomputed up to 8x)",
        "const allItems = getAllItemsFlat().filter(it=>it.ownerId===currentUserId); // personal board only",
        1,
    )

    # project progress only current user
    s = s.replace(
        """function renderProjectProgressSection(){
  const projectsWrap = document.getElementById('sectionProjects');
  if(!projectsWrap) return;
  if(!projects.length){
    projectsWrap.innerHTML = `<div class=\"empty-state\"><h3>No projects yet</h3><p>Add one using the quick-add card above — you can break it into tasks right after.</p></div>`;
    return;
  }
  const sorted = projects.slice().sort((a,b)=>{""",
        """function renderProjectProgressSection(){
  const projectsWrap = document.getElementById('sectionProjects');
  if(!projectsWrap) return;
  const mine = projects.filter(p=>p.ownerId===currentUserId);
  if(!mine.length){
    projectsWrap.innerHTML = `<div class=\"empty-state\"><h3>No projects yet</h3><p>Add one using the quick-add card above — you can break it into tasks right after.</p></div>`;
    return;
  }
  const sorted = mine.slice().sort((a,b)=>{""",
        1,
    )

    # active briefs only own
    marker = "function renderActiveBriefList(){"
    idx = s.find(marker)
    if idx >= 0:
        old = "const active = briefs.filter(b=>b.status !== 'Approved');"
        pos = s.find(old, idx)
        if pos >= 0:
            s = s[:pos] + "const active = briefs.filter(b=>b.status !== 'Approved' && b.assigneeId===currentUserId);" + s[pos+len(old):]

    # team section statuses only
    s = s.replace(
        "<p class=\"page-sub\">Everyone's status, projects, and active briefs, grouped by office — visible to the whole team, not just management.</p>",
        "<p class=\"page-sub\">Team availability only. Project and task details stay private to each person.</p>",
        1,
    )
    s = s.replace(
        "<div class=\"member-load\">${memberBriefs.length} brief${memberBriefs.length===1?'':'s'} &middot; ${memberProjects.length} project${memberProjects.length===1?'':'s'}</div>",
        "<div class=\"member-load\">${m.office} office · details private</div>",
        1,
    )
    if '.other-project-list,.member-briefs{display:none!important;}' not in s:
        s = s.replace(
            "  .other-project-list{list-style:none; margin:6px 0 0; padding:0;}",
            "  .other-project-list,.member-briefs{display:none!important;}\n  .other-project-list{list-style:none; margin:6px 0 0; padding:0;}",
            1,
        )

    # personal calendar only
    s = s.replace("let calMode = 'team'; // 'team' | 'personal'", "let calMode = 'personal'; // personal calendar only", 1)
    old_rel = re.compile(r"function relevantBriefs\(\)\{.*?\n\}", re.S)
    m = old_rel.search(s)
    if m:
        s = s[:m.start()] + """function relevantBriefs(){
  return briefs.filter(b=>b.status !== 'Approved' && b.assigneeId === currentUserId);
}
function getPersonalCalendarEntries(){
  const entries = [];
  relevantBriefs().forEach(b=>{
    if(!b.dueDate) return;
    entries.push({id:b.id,kind:'brief',title:b.title,date:b.dueDate,endDate:b.dueDate,time:'',status:b.status,effortLevel:b.effortLevel});
  });
  schedules.filter(x=>x.ownerId===currentUserId).forEach(x=>{
    if(!x.date) return;
    entries.push({id:x.id,kind:'schedule',title:x.title,date:x.date,endDate:x.endDate||x.date,time:x.time||'',note:x.note||''});
  });
  return entries;
}
function calendarDates(start,end){
  const out=[];
  let d=new Date(start+'T00:00:00');
  const e=new Date((end||start)+'T00:00:00');
  if(isNaN(d)||isNaN(e)) return out;
  for(;d<=e;d.setDate(d.getDate()+1)) out.push(d.toISOString().slice(0,10));
  return out;
}""" + s[m.end():]

    start = s.find('function renderCalendar(){')
    end = s.find('/* ---------------------------------------------------------\n   BRIEF DETAIL MODAL', start)
    if start >= 0 and end >= 0:
        cal = """function renderCalendar(){
  populateCalPersonSelect();
  calPersonId=currentUserId;
  const year=calCursor.getFullYear(), month=calCursor.getMonth();
  document.getElementById('calMonthLabel').textContent=calCursor.toLocaleDateString('en-GB',{month:'long',year:'numeric'});
  const relevant=getPersonalCalendarEntries();
  const byDate={};
  relevant.forEach(item=>calendarDates(item.date,item.endDate).forEach(d=>(byDate[d]=byDate[d]||[]).push(item)));
  const grid=document.getElementById('calGrid');
  grid.innerHTML='';
  ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].forEach(d=>{const el=document.createElement('div');el.className='cal-dow';el.textContent=d;grid.appendChild(el);});
  const firstDay=new Date(year,month,1); let startOffset=firstDay.getDay()-1; if(startOffset<0) startOffset=6;
  const daysInMonth=new Date(year,month+1,0).getDate(); const today=new Date().toISOString().slice(0,10);
  for(let i=0;i<startOffset;i++){const el=document.createElement('div');el.className='cal-cell empty';grid.appendChild(el);}
  for(let d=1;d<=daysInMonth;d++){
    const dateStr=`${year}-${String(month+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
    const items=byDate[dateStr]||[]; const cell=document.createElement('div');
    cell.className='cal-cell'+(dateStr===today?' today':'')+(items.length?' has-items':'');
    cell.innerHTML=`<div class=\"cal-daynum\">${d}</div>`+items.map(it=>`<div class=\"cal-item\" title=\"${escapeHtml(it.title)}\">${escapeHtml((it.time?it.time+' · ':'')+it.title)}</div>`).join('');
    grid.appendChild(cell);
  }
  renderAgenda(relevant);
}
function renderAgenda(relevant){
  const wrap=document.getElementById('calAgenda');
  const sorted=relevant.slice().sort((a,b)=>(a.date+(a.time||'')).localeCompare(b.date+(b.time||'')));
  if(!sorted.length){wrap.innerHTML=`<div class=\"empty-state\"><h3>Nothing scheduled</h3><p>No active brief deadlines or confirmed schedule entries yet.</p></div>`;return;}
  wrap.innerHTML=sorted.map(it=>{
    let meta='';
    if(it.kind==='brief'){const em=EFFORT_META[it.effortLevel]||EFFORT_META.boleh;meta=`${em.emoji} ${em.label} · ${it.status}`;}
    else{const range=it.endDate&&it.endDate!==it.date?` → ${formatDate(it.endDate)}`:'';meta=`${it.time?it.time+' · ':''}Schedule${range}${it.note?' · '+escapeHtml(it.note):''}`;}
    return `<div class=\"agenda-row ${it.kind==='brief'?'clickable':''}\" ${it.kind==='brief'?`data-brief=\"${it.id}\"`:''}><div class=\"agenda-date\">${formatDate(it.date)}</div><div class=\"agenda-info\"><h4>${escapeHtml(it.title)}</h4><div class=\"meta\">${meta}</div></div></div>`;
  }).join('');
  wrap.querySelectorAll('.agenda-row.clickable').forEach(row=>row.addEventListener('click',()=>openBriefModal(row.dataset.brief)));
}

"""
        s = s[:start] + cal + s[end:]

    # persist schedules
    s = s.replace(
        "const payload = JSON.stringify({ projects, projectCounter, taskCounter, statuses });",
        "const payload = JSON.stringify({ projects, projectCounter, taskCounter, statuses, schedules, scheduleCounter });", 1)
    s = s.replace(
        "statuses = parsed.statuses || {};",
        "statuses = parsed.statuses || {};\n      schedules = parsed.schedules || [];\n      scheduleCounter = parsed.scheduleCounter || 1;", 1)

    path.write_text(s)
    print('patched', path)
