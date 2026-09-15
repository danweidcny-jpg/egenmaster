from pathlib import Path
import re

FILES=[Path('index.html'), Path('egen-master-deck.html')]

DAILY_BLOCK='''
      <div class="section-block" id="dailyWorkloadSection">
        <div style="display:flex;align-items:flex-end;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:10px;">
          <div>
            <h3 style="margin-bottom:2px;">Daily workload</h3>
            <div style="font-size:12px;color:var(--muted);">Check your task quantity, then update Free / Busy / At Capacity above.</div>
          </div>
        </div>
        <div class="priority-tabs" id="priorityTabs">
          <button type="button" class="priority-tab active" data-tab="today">Today <span class="tab-count" id="countToday">0</span></button>
          <button type="button" class="priority-tab" data-tab="upcoming">Upcoming <span class="tab-count" id="countUpcoming">0</span></button>
          <button type="button" class="priority-tab" data-tab="waiting">Pending <span class="tab-count" id="countWaiting">0</span></button>
        </div>
        <div id="priorityList"></div>
      </div>
'''

for path in FILES:
    s=path.read_text()

    # Restore the personal daily-workload section immediately before Project Progress.
    if 'id="dailyWorkloadSection"' not in s:
        anchor='''      <div class="section-block">\n        <h3>Project progress</h3>\n        <div id="sectionProjects"></div>\n      </div>'''
        if anchor not in s:
            raise SystemExit(f'{path}: project progress anchor missing')
        s=s.replace(anchor, DAILY_BLOCK+'\n'+anchor, 1)

    # Make the 3 tabs a clean partition of task workload only.
    pattern=r'''function renderPriorityList\(allItems\)\{.*?\n\}'''
    replacement=r'''function renderPriorityList(allItems){
  const wrap = document.getElementById('priorityList');
  if(!wrap) return;
  const today = todayStr();
  const tasks = (allItems || getAllItemsFlat())
    .filter(it=>it.type==='task' && !it.done && it.ownerId===currentUserId);

  const dataMap = {
    today: tasks.filter(it=>!it.waiting && (!it.dueDate || it.dueDate<=today)),
    upcoming: tasks.filter(it=>!it.waiting && it.dueDate && it.dueDate>today),
    waiting: tasks.filter(it=>it.waiting),
  };

  if(!['today','upcoming','waiting'].includes(activePriorityTab)) activePriorityTab='today';
  const rows = dataMap[activePriorityTab] || [];
  const emptyMap = {
    today:['Nothing on Today','No active tasks for today.'],
    upcoming:['Nothing upcoming','No future task deadlines yet.'],
    waiting:['Nothing pending','No tasks are waiting on client / supplier right now.'],
  };
  const [emptyTitle, emptyBody] = emptyMap[activePriorityTab];

  wrap.innerHTML = rows.length
    ? rows.map(it=>buildFlatRowHtml(it, activePriorityTab)).join('')
    : `<div class="empty-state" style="padding:28px 20px;"><h3>${emptyTitle}</h3><p>${emptyBody}</p></div>`;

  const counts = {Today:dataMap.today.length, Upcoming:dataMap.upcoming.length, Waiting:dataMap.waiting.length};
  Object.entries(counts).forEach(([key,val])=>{
    const el=document.getElementById('count'+key);
    if(el) el.textContent=val;
  });
}'''
    s,n=re.subn(pattern,replacement,s,count=1,flags=re.S)
    if n!=1:
        raise SystemExit(f'{path}: renderPriorityList replacement failed')

    path.write_text(s)
    print('patched',path)
