
const { chromium } = require('playwright');
const assert=(c,m)=>{if(!c)throw new Error(m);console.log('PASS:',m);};

(async()=>{
  const browser=await chromium.launch({headless:true});
  const context=await browser.newContext({timezoneId:'Asia/Kuala_Lumpur'});
  const page=await context.newPage();
  const errors=[]; page.on('pageerror',e=>errors.push(String(e)));

  const SB='https://vpvtpqzjyneznhytiefr.supabase.co';
  const state={
    statuses:{m5:'free',m6:'busy',m7:'free',m8:'capacity',m9:'free',m10:'busy',m2:'busy'},
    workloads:{},
    counters:{projectCounter:30,taskCounter:90,scheduleCounter:20,briefCounter:5},
    schedules:[],
    projects:[
      {id:'pPast',ownerId:'m7',title:'Past KL Event',dueDate:'2026-09-10',createdAt:'2026-09-01',version:1,tasks:[
        {id:'tPast',text:'Old task',done:false,waiting:false,dueDate:'2026-09-10',version:1}
      ]},
      {id:'pFuture',ownerId:'m7',title:'Future KL Event',dueDate:'2026-09-25',createdAt:'2026-09-01',version:1,tasks:[
        {id:'t1',text:'Prepare deck',done:false,waiting:false,dueDate:'',version:1},
        {id:'t2',text:'Supplier reply',done:false,waiting:true,dueDate:'2026-09-22',version:1},
        {id:'t3',text:'Future setup',done:false,waiting:false,dueDate:'2026-09-25',version:1}
      ]},
      {id:'pJB',ownerId:'m2',title:'JB Project',dueDate:'2026-09-27',createdAt:'2026-09-01',version:1,tasks:[
        {id:'tJB',text:'JB task',done:false,waiting:false,dueDate:'',version:1}
      ]}
    ],
    briefs:[
      {id:'bPast',title:'Old Proposal',rawBrief:'',points:[],clientAsks:[],concepts:[],effortLevel:'boleh',effortReason:'',assigneeId:'m7',dueDate:'2026-09-15',status:'Assigned',createdAt:'2026-09-01',approvedAt:'',source:'new-brief',version:1},
      {id:'bFuture',title:'Future Proposal',rawBrief:'',points:[],clientAsks:[],concepts:[],effortLevel:'boleh',effortReason:'',assigneeId:'m7',dueDate:'2026-09-24',status:'Assigned',createdAt:'2026-09-01',approvedAt:'',source:'new-brief',version:1}
    ]
  };

  await page.route(SB+'/rest/v1/rpc/**',async route=>{
    const name=new URL(route.request().url()).pathname.split('/').pop();
    const body=JSON.parse(route.request().postData()||'{}');
    if(name==='egen_bootstrap'){
      let scoped=JSON.parse(JSON.stringify(state));
      if(body.p_actor_user_id==='m6'){
        scoped.projects=scoped.projects.filter(p=>['m5','m6','m7','m8','m9','m10'].includes(p.ownerId));
        scoped.briefs=scoped.briefs.filter(b=>['m5','m6','m7','m8','m9','m10'].includes(b.assigneeId));
      }
      await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(scoped)});
      return;
    }
    await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({ok:true})});
  });

  await page.addInitScript(()=>localStorage.setItem('egen-current-user','m6'));
  await page.goto('http://127.0.0.1:4173/index.html',{waitUntil:'networkidle'});

  const body=await page.locator('body').innerText();
  assert(body.includes('KL team availability & tasks'),'Chen sees simplified KL workload heading');
  assert(body.includes('Liwen'),'Chen sees KL member Liwen');
  assert(!body.includes('Xinyee'),'Chen dashboard excludes JB member Xinyee');
  const liwenCard=page.locator('details.leader-card').filter({hasText:'Liwen'}).first();
  await liwenCard.locator('summary').click();
  const liwenText=await liwenCard.innerText();
  assert(liwenText.includes('Prepare deck'),'Chen can review KL open tasks');
  assert(liwenText.includes('Old task'),'overdue unfinished work remains visible in task list');
  
  const masterButtons=page.locator('[data-view="master"]:visible');
  assert(await masterButtons.count()===0,'Master View hidden for Chen');

  await page.evaluate(()=>switchView('calendar'));
  await page.waitForTimeout(100);
  const calText=await page.locator('#view-calendar').innerText();
  assert(calText.includes('Future KL Event'),'future KL event remains on calendar');
  assert(calText.includes('Future Proposal'),'future brief remains on calendar');
  assert(!calText.includes('Past KL Event'),'past project event hidden from calendar');
  assert(!calText.includes('Old Proposal'),'past brief deadline hidden from calendar');

  const futureCard=page.locator('.cal-item').filter({hasText:'Future KL Event'}).first();
  assert(await futureCard.count()===1,'future calendar card rendered');
  assert((await futureCard.locator('.cal-item-owner').innerText()).includes('Liwen'),'calendar card shows owner');
  assert(errors.length===0,'no uncaught JS errors');

  await browser.close();
  console.log('ALL CALENDAR / CHEN QA CHECKS PASSED');
})().catch(e=>{console.error(e);process.exit(1);});
