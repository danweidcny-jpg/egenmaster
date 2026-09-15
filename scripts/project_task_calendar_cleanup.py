from pathlib import Path
import re

FILES = [Path('index.html'), Path('egen-master-deck.html')]

CSS = r'''
  .project-title-line{display:flex;align-items:center;gap:12px;flex-wrap:wrap;min-width:0;}
  .project-date-editor{display:flex;align-items:center;gap:7px;font-size:11px;color:var(--muted);font-weight:600;}
  .project-date-editor input[type="date"]{width:auto;min-width:150px;padding:7px 9px;font-size:12px;background:rgba(255,255,255,.55);}
  .task-due-input{width:auto!important;min-width:145px;padding:6px 8px!important;font-size:11px!important;background:rgba(255,255,255,.55)!important;}
'''

for path in FILES:
    s = path.read_text()

    # 1) Remove duplicate Today / Overdue / Waiting / Upcoming dashboard and bento summary.
    s = s.replace('      <div class="bento-summary-row" id="bentoSummaryRow"></div>\n', '', 1)
    s, n = re.subn(
        r'\n      <div class="section-block">\s*<div class="priority-tabs" id="priorityTabs">.*?<div id="priorityList"></div>\s*</div>',
        '', s, count=1, flags=re.S
    )
    if n != 1:
        print(path, 'priority block already absent or pattern changed')

    # UI copy for calendar.
    s = s.replace('Your own deadlines and confirmed schedule in one place.', 'Project event dates and proposal / quotation due dates only.', 1)

    # CSS for editable dates.
    if '.project-title-line{' not in s:
        s = s.replace('</style>', CSS + '\n</style>', 1)

    # Change listeners for editable project/task dates.
    anchor = "document.addEventListener('change', (e)=>{\n  const toggle = e.target.closest('[data-task-toggle]');"
    repl = "document.addEventListener('change', (e)=>{\n  const projectDate = e.target.closest('[data-project-event-date]');\n  if(projectDate){ updateProjectEventDate(projectDate.dataset.projectEventDate, projectDate.value); return; }\n  const taskDue = e.target.closest('[data-task-due-edit]');\n  if(taskDue){ updateTaskDueDate(taskDue.dataset.taskDueEdit, taskDue.value); return; }\n  const toggle = e.target.closest('[data-task-toggle]');"
    if anchor in s:
        s = s.replace(anchor, repl, 1)

    # Add update helpers once.
    if 'function updateProjectEventDate(' not in s:
        marker = 'function buildProjectCardHtml(project, editable){'
        helpers = r'''function updateProjectEventDate(projectId, value){
  const p = projects.find(x=>x.id===projectId);
  if(!p) return;
  p.dueDate = value || '';
  saveTasksToStorage();
  renderBoard();
}
function updateTaskDueDate(taskId, value){
  for(const p of projects){
    const t = (p.tasks||[]).find(x=>x.id===taskId);
    if(t){ t.dueDate = value || ''; break; }
  }
  saveTasksToStorage();
  renderBoard();
}
'''
        if marker not in s:
            raise SystemExit(f'{path}: buildProjectCardHtml marker missing')
        s = s.replace(marker, helpers + marker, 1)

    # Add proposal-project flag for labels.
    pct = "  const pct = total ? Math.round((done/total)*100) : 0;"
    if pct in s and 'const isProposalProject' not in s[s.find('function buildProjectCardHtml'):s.find('function renderGreeting')]:
        s = s.replace(pct, pct + "\n  const isProposalProject = /proposal|quotation/i.test(project.title);", 1)

    # Editable task due date on every task row.
    old_due = "      ${t.dueDate ? `<span class=\"task-due ${isOverdue?'overdue':''}\">${isOverdue?'Overdue · ':''}${formatDate(t.dueDate)}</span>` : ''}"
    new_due = "      ${editable ? `<input type=\"date\" class=\"task-due-input\" value=\"${t.dueDate||''}\" data-task-due-edit=\"${t.id}\" title=\"Task due date\">` : (t.dueDate ? `<span class=\"task-due ${isOverdue?'overdue':''}\">${isOverdue?'Overdue · ':''}${formatDate(t.dueDate)}</span>` : '')}"
    if old_due in s:
        s = s.replace(old_due, new_due, 1)

    # Project title + editable event/due date beside name.
    old_title = "      <h4>${escapeHtml(project.title)}</h4>"
    new_title = "      <div class=\"project-title-line\"><h4>${escapeHtml(project.title)}</h4>${editable ? `<label class=\"project-date-editor\"><span>${isProposalProject?'Due date':'Event date'}</span><input type=\"date\" value=\"${project.dueDate||''}\" data-project-event-date=\"${project.id}\"></label>` : (project.dueDate ? `<span class=\"project-date-editor\">${isProposalProject?'Due':'Event'} ${formatDate(project.dueDate)}</span>` : '')}</div>"
    if old_title in s:
        s = s.replace(old_title, new_title, 1)

    # Remove second duplicate project due-date line under the heading.
    old_line = "    ${project.dueDate ? `<div style=\"font-size:12px; color:var(--muted); margin-top:2px;\">Due ${formatDate(project.dueDate)}</div>` : ''}\n"
    s = s.replace(old_line, '', 1)

    # 4) Calendar only project dates + proposal/quotation due dates. No task dates, no schedules.
    pattern = r"function getPersonalCalendarEntries\(\)\{.*?\n\}\nfunction renderCalendar\(\)\{"
    replacement = r'''function getPersonalCalendarEntries(){
  const entries=[];
  relevantBriefs().forEach(b=>{
    if(b.dueDate) entries.push({id:b.id,kind:'brief',title:b.title,date:b.dueDate,endDate:b.dueDate,time:'',note:'Proposal / quotation due date'});
  });
  projects.filter(p=>p.ownerId===currentUserId).forEach(p=>{
    if(p.dueDate) entries.push({id:'project-'+p.id,kind:'project',title:p.title,date:p.dueDate,endDate:p.dueDate,time:'',note:/proposal|quotation/i.test(p.title)?'Proposal / quotation due date':'Project event date'});
  });
  return entries;
}
function renderCalendar(){'''
    s, n = re.subn(pattern, replacement, s, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f'{path}: calendar function replacement failed')

    path.write_text(s)
    print('patched', path)
