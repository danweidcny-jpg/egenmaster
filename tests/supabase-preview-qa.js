
const { chromium } = require('playwright');
const assert = (cond,msg)=>{ if(!cond) throw new Error(msg); console.log('PASS:',msg); };

const SB='https://vpvtpqzjyneznhytiefr.supabase.co';
const KEY='sb_publishable_mmAr2D7l5NdfmRUvRJpBzw_p8BtVNjb';

async function rpc(name,body){
  const r=await fetch(SB+'/rest/v1/rpc/'+name,{
    method:'POST',
    headers:{'Content-Type':'application/json','apikey':KEY,'Authorization':'Bearer '+KEY},
    body:JSON.stringify(body)
  });
  const txt=await r.text();
  if(!r.ok) throw new Error(name+' '+r.status+': '+txt);
  return txt?JSON.parse(txt):null;
}

(async()=>{
  const x=await rpc('egen_bootstrap',{p_actor_user_id:'m2'});
  assert(Array.isArray(x.projects),'real bootstrap returns projects');
  assert(x.projects.some(p=>p.id==='p1'&&p.dueDate==='2026-10-15'),'Xinyee real bootstrap includes PRO3C on 15 Oct');
  assert(!x.projects.some(p=>p.ownerId==='m7'),'Xinyee real bootstrap excludes Liwen projects');

  const d=await rpc('egen_bootstrap',{p_actor_user_id:'m1'});
  assert(d.projects.some(p=>p.ownerId==='m2'),'Danwei real bootstrap includes JB projects');
  assert(d.projects.some(p=>p.ownerId==='m7'),'Danwei real bootstrap includes KL projects');

  const c=await rpc('egen_bootstrap',{p_actor_user_id:'m6'});
  assert(c.projects.some(p=>p.ownerId==='m7'),'Chen real bootstrap includes KL projects');
  assert(!c.projects.some(p=>p.ownerId==='m2'),'Chen real bootstrap excludes JB projects');

  const browser=await chromium.launch({headless:true});
  const context=await browser.newContext({timezoneId:'Asia/Kuala_Lumpur'});
  const page=await context.newPage();
  const errors=[];
  page.on('pageerror',e=>errors.push(String(e)));

  const base={
    statuses:{m2:'busy',m3:'free',m5:'free'},
    workloads:{m1:{activeBriefs:0},m2:{activeBriefs:0},m3:{activeBriefs:0},m4:{activeBriefs:0},m5:{activeBriefs:0},m6:{activeBriefs:0},m7:{activeBriefs:1},m8:{activeBriefs:0},m9:{activeBriefs:0},m10:{activeBriefs:0}},
    counters:{projectCounter:22,taskCounter:63,scheduleCounter:16,briefCounter:2},
    schedules:[],
    projects:[
      {id:'p1',ownerId:'m2',title:'PRO3C',dueDate:'2026-10-15',createdAt:'2026-09-15',version:1,tasks:[
        {id:'t5',text:'Follow up beach flag status',done:false,waiting:false,dueDate:'',version:1},
        {id:'t6',text:'PRO3C Grand Opening',done:true,waiting:false,dueDate:'2026-10-15',version:1}
      ]}
    ],
    briefs:[
      {id:'b1',title:'Corporate / annual dinner — 70 pax — at Kuala Lumpur',rawBrief:'',points:[
        {label:'Company / Client',value:'Swisslog'},
        {label:'Event type',value:'Corporate / annual dinner'},
        {label:'Venue / Location',value:'Kuala Lumpur'}
      ],clientAsks:[],concepts:[],effortLevel:'boleh',effortReason:'',assigneeId:'m7',dueDate:'2026-09-24',status:'Assigned',createdAt:'2026-09-15',approvedAt:'',source:'new-brief',version:1}
    ]
  };
  let state=JSON.parse(JSON.stringify(base));

  await page.route(SB+'/rest/v1/rpc/**',async route=>{
    const req=route.request();
    const name=new URL(req.url()).pathname.split('/').pop();
    const body=JSON.parse(req.postData()||'{}');
    if(name==='egen_bootstrap'){
      await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(state)});
      return;
    }
    if(name==='egen_patch_task'){
      const t=state.projects.flatMap(p=>p.tasks).find(t=>t.id===body.p_id);
      if(body.p_expected_version!==t.version){
        await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({ok:false,code:'STALE_WRITE',currentVersion:t.version})});
        return;
      }
      if(Object.prototype.hasOwnProperty.call(body.p_changes,'done')) t.done=body.p_changes.done;
      if(Object.prototype.hasOwnProperty.call(body.p_changes,'waiting')) t.waiting=body.p_changes.waiting;
      if(Object.prototype.hasOwnProperty.call(body.p_changes,'dueDate')) t.dueDate=body.p_changes.dueDate;
      t.version+=1;
      await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({ok:true,data:t})});
      return;
    }
    if(name==='egen_patch_project'){
      const p=state.projects.find(p=>p.id===body.p_id);
      if(body.p_expected_version!==p.version){
        await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({ok:false,code:'STALE_WRITE',currentVersion:p.version})});
        return;
      }
      if(Object.prototype.hasOwnProperty.call(body.p_changes,'dueDate')) p.dueDate=body.p_changes.dueDate;
      p.version+=1;
      await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({ok:true,data:p})});
      return;
    }
    if(name==='egen_set_status'){
      state.statuses[body.p_actor_user_id]=body.p_status;
      await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({ok:true})});
      return;
    }
    await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({ok:true,data:{id:'qa'}})});
  });

  await page.addInitScript(()=>localStorage.setItem('egen-current-user','m2'));
  await page.goto('http://127.0.0.1:4173/index.html',{waitUntil:'networkidle'});

  assert((await page.locator('#currentUserLabel').innerText()).includes('Xinyee'),'preview frontend loads selected user');
  assert((await page.locator('#syncStatus').innerText()).includes('Synced'),'preview frontend syncs via Supabase RPC');

  const toggle=page.locator('[data-task-toggle="t5"]');
  assert(await toggle.count()===1,'Xinyee task checkbox rendered');
  await toggle.check();
  await page.waitForTimeout(200);
  assert(state.projects[0].tasks[0].done===true && state.projects[0].tasks[0].version===2,'task toggle uses row-level versioned RPC');

  const date=page.locator('[data-project-event-date="p1"]');
  await date.fill('2026-10-16');
  await date.dispatchEvent('change');
  await page.waitForTimeout(200);
  assert(state.projects[0].dueDate==='2026-10-16'&&state.projects[0].version===2,'project date uses versioned row-level RPC');

  await page.locator('#myStatusPicker [data-status="free"]').click();
  await page.waitForTimeout(150);
  assert(state.statuses.m2==='free','status saves through dedicated RPC');

  state.projects[0].tasks[0].version=5;
  state.projects[0].tasks[0].done=true;
  await page.evaluate(()=>{
    const t=projects.find(p=>p.id==='p1').tasks.find(t=>t.id==='t5');
    t.version=2;
    t.done=true;
  });
  await page.evaluate(()=>toggleTask('t5'));
  await page.waitForTimeout(250);
  const toast=await page.locator('#celebrateToast').innerText();
  assert(toast.includes('Someone updated this first'),'stale write shows conflict instead of overwriting');

  assert(errors.length===0,'no uncaught JS errors');
  await browser.close();
  console.log('ALL SUPABASE PREVIEW QA CHECKS PASSED');
})().catch(err=>{ console.error(err); process.exit(1); });
