from pathlib import Path
import re

FILES=[Path('index.html'), Path('egen-master-deck.html')]

CSS=r'''
  .master-summary{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:18px 0 22px;}
  .master-stat{background:var(--glass);border:1px solid rgba(255,255,255,.6);border-radius:16px;padding:16px 18px;}
  .master-stat .n{font-family:'Plus Jakarta Sans',sans-serif;font-size:26px;font-weight:800;line-height:1;}
  .master-stat .l{font-size:11px;color:var(--muted);margin-top:7px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;}
  .master-table-wrap{overflow:auto;background:var(--glass);border:1px solid rgba(255,255,255,.6);border-radius:18px;}
  table.master-table{width:100%;border-collapse:collapse;min-width:760px;}
  .master-table th,.master-table td{padding:13px 15px;border-bottom:1px solid var(--line);text-align:left;font-size:12.5px;}
  .master-table th{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;background:rgba(255,255,255,.35);position:sticky;top:0;}
  .master-table tbody tr{cursor:pointer;}
  .master-table tbody tr:hover{background:rgba(255,255,255,.35);}
  .master-due.overdue{color:var(--coral-deep);font-weight:800;}
  .master-due.today{color:var(--gold);font-weight:800;}
  .master-status{display:inline-flex;padding:4px 8px;border-radius:999px;background:rgba(23,26,24,.06);font-weight:700;font-size:11px;}
  @media(max-width:700px){.master-summary{grid-template-columns:1fr;}}
'''

MASTER_SECTION=r'''
    <!-- ===================== MASTER VIEW (Manager / Senior only) ===================== -->
    <section class="view" id="view-master">
      <div class="eyebrow">Management only</div>
      <h2 class="page-title">Proposal &amp; Quotation Master View</h2>
      <p class="page-sub">Only items assigned from <strong>New Brief</strong> appear here. Manual projects and task deadlines are excluded.</p>
      <div id="masterViewWrap"></div>
    </section>
'''

JS=r'''
function updateMasterViewAccess(){
  const allowed = isLeadershipUser();
  document.querySelectorAll('[data-view="master"]').forEach(btn=>{
    btn.style.display = allowed ? '' : 'none';
  });
  const master = document.getElementById('view-master');
  if(!allowed && master && master.classList.contains('active')){
    switchView('team');
  }
}
function getMasterBriefs(){
  // `briefs` are created only through New Brief -> Assign. Projects/tasks are deliberately excluded.
  return briefs.slice().sort((a,b)=>{
    const ad=a.dueDate||'9999-12-31', bd=b.dueDate||'9999-12-31';
    const d=ad.localeCompare(bd);
    if(d) return d;
    return (a.title||'').localeCompare(b.title||'');
  });
}
function masterBriefType(b){
  const hay=((b.title||'')+' '+(b.rawBrief||'')).toLowerCase();
  if(hay.includes('quotation') || hay.includes('quote')) return 'Quotation';
  if(hay.includes('proposal')) return 'Proposal';
  return 'Proposal / Quotation';
}
function renderMasterView(){
  const wrap=document.getElementById('masterViewWrap');
  if(!wrap) return;
  if(!isLeadershipUser()){
    wrap.innerHTML='<div class="empty-state"><h3>Management access only</h3><p>This view is available to Danwei and Chen.</p></div>';
    return;
  }
  const all=getMasterBriefs();
  const active=all.filter(b=>b.status!=='Approved');
  const today=todayStr();
  const overdue=active.filter(b=>b.dueDate && b.dueDate<today).length;
  const dueToday=active.filter(b=>b.dueDate===today).length;
  const upcoming=active.filter(b=>b.dueDate && b.dueDate>today).length;

  const summary=`<div class="master-summary">
    <div class="master-stat"><div class="n">${active.length}</div><div class="l">Active</div></div>
    <div class="master-stat"><div class="n">${dueToday}</div><div class="l">Due today</div></div>
    <div class="master-stat"><div class="n">${overdue}</div><div class="l">Overdue</div></div>
  </div>`;

  if(!active.length){
    wrap.innerHTML=summary+'<div class="empty-state"><h3>No active proposal / quotation</h3><p>Assign one from New Brief and it will appear here automatically.</p></div>';
    return;
  }
  const rows=active.map(b=>{
    const member=TEAM.find(m=>m.id===b.assigneeId);
    const dueClass=b.dueDate<today?'overdue':(b.dueDate===today?'today':'');
    return `<tr data-master-brief="${b.id}">
      <td><strong>${escapeHtml(b.title)}</strong></td>
      <td>${escapeHtml(masterBriefType(b))}</td>
      <td>${member?escapeHtml(member.name):'—'}</td>
      <td class="master-due ${dueClass}">${b.dueDate?formatDate(b.dueDate):'—'}</td>
      <td><span class="master-status">${escapeHtml(b.status||'Assigned')}</span></td>
    </tr>`;
  }).join('');
  wrap.innerHTML=summary+`<div class="master-table-wrap"><table class="master-table">
    <thead><tr><th>Proposal / Quotation</th><th>Type</th><th>Assignee</th><th>Due date</th><th>Status</th></tr></thead>
    <tbody>${rows}</tbody>
  </table></div>`;
  wrap.querySelectorAll('[data-master-brief]').forEach(row=>row.addEventListener('click',()=>openBriefModal(row.dataset.masterBrief)));
}
'''

for path in FILES:
    s=path.read_text()

    if '.master-summary{' not in s:
        s=s.replace('</style>', CSS+'\n</style>',1)

    # Leadership-only tab in desktop and mobile nav.
    if 'data-view="master"' not in s:
        s=s.replace('<button data-view="calendar">Calendar</button>', '<button data-view="master" style="display:none;">Master View</button>\n      <button data-view="calendar">Calendar</button>',1)
        s=s.replace('<button data-view="calendar"><span class="dot"></span>Calendar</button>', '<button data-view="master" style="display:none;"><span class="dot"></span>Master</button>\n    <button data-view="calendar"><span class="dot"></span>Calendar</button>',1)

    if 'id="view-master"' not in s:
        anchor='    <!-- ===================== CALENDAR VIEW ===================== -->'
        if anchor not in s: raise SystemExit(f'{path}: calendar HTML anchor missing')
        s=s.replace(anchor, MASTER_SECTION+'\n'+anchor,1)

    # Tag all future New Brief assignments explicitly.
    brief_anchor="    approvedAt: null,\n  };"
    if "source: 'new-brief'" not in s:
        if brief_anchor not in s: raise SystemExit(f'{path}: brief object anchor missing')
        s=s.replace(brief_anchor,"    approvedAt: null,\n    source: 'new-brief',\n  };",1)

    # Add master functions before tab navigation.
    marker='/* ---------------------------------------------------------\n   TAB NAVIGATION'
    if 'function renderMasterView()' not in s:
        if marker not in s: raise SystemExit(f'{path}: tab navigation marker missing')
        s=s.replace(marker,JS+'\n'+marker,1)

    # Harden switchView access and render master view.
    old='function switchView(view){\n  document.querySelectorAll(\'.view\').forEach(v=>v.classList.remove(\'active\'));'
    new='function switchView(view){\n  if(view===\'master\' && !isLeadershipUser()) view=\'team\';\n  document.querySelectorAll(\'.view\').forEach(v=>v.classList.remove(\'active\'));'
    if old in s:
        s=s.replace(old,new,1)
    if "if(view === 'master') renderMasterView();" not in s:
        s=s.replace("  if(view === 'archive') renderArchive();", "  if(view === 'archive') renderArchive();\n  if(view === 'master') renderMasterView();",1)

    # Keep nav access in sync whenever board/user renders.
    if 'updateMasterViewAccess();\n  const allItems' not in s:
        s=s.replace("  renderMyStatusPicker();\n  const allItems", "  renderMyStatusPicker();\n  updateMasterViewAccess();\n  const allItems",1)

    # Init access + master render if active.
    if 'updateMasterViewAccess();\n  if(!currentUserId)' not in s:
        s=s.replace("  renderCurrentUserLabel();\n  if(!currentUserId)", "  renderCurrentUserLabel();\n  updateMasterViewAccess();\n  if(!currentUserId)",1)
    if "activeView.id === 'view-master'" not in s:
        s=s.replace("  if(activeView && activeView.id === 'view-archive') renderArchive();", "  if(activeView && activeView.id === 'view-archive') renderArchive();\n  if(activeView && activeView.id === 'view-master') renderMasterView();",1)

    path.write_text(s)
    print('patched',path)
