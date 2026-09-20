const { chromium } = require('playwright');

const PREVIEW = 'https://phase1-stabilise-2026-09-20.egenmaster.pages.dev';
const API = 'https://egen-master-deck-api.danwei.workers.dev';

const briefsPayload = {
  briefs: [
    {
      id:'b1',
      title:'Corporate / annual dinner — 70 pax — at Kuala Lumpur',
      rawBrief:'Client: Swisslog\nEvent type: Annual Dinner\nLocation: Kuala Lumpur',
      points:[
        {label:'Company / Client',value:'Swisslog'},
        {label:'Event type',value:'Annual Dinner'},
        {label:'Venue / Location',value:'Kuala Lumpur'}
      ],
      clientAsks:[], concepts:[], effortLevel:'boleh', effortReason:'',
      assigneeId:'m7', dueDate:'2026-09-24', status:'Assigned',
      createdAt:'2026-09-20', approvedAt:null, source:'new-brief'
    },
    {
      id:'b2',
      title:'Approved Test',
      rawBrief:'',
      points:[
        {label:'Company / Client',value:'Archived Client'},
        {label:'Event type',value:'Proposal'},
        {label:'Venue / Location',value:'KL'}
      ],
      clientAsks:[], concepts:[], effortLevel:'boleh', effortReason:'',
      assigneeId:'m7', dueDate:'2026-09-22', status:'Approved',
      createdAt:'2026-09-19', approvedAt:'2026-09-20', source:'new-brief'
    }
  ],
  briefCounter:3
};

const tasksPayload = {
  projects:[
    {
      id:'p1', ownerId:'m2', title:'PRO3C', dueDate:'2026-10-15', createdAt:'2026-09-01',
      tasks:[
        {id:'t1',text:'Today task',done:false,waiting:false,dueDate:'2026-09-20'},
        {id:'t2',text:'Upcoming task',done:false,waiting:false,dueDate:'2026-09-25'},
        {id:'t3',text:'Waiting task',done:false,waiting:true,dueDate:''}
      ]
    },
    {
      id:'p2', ownerId:'m7', title:'Harvey Norman Coalfields Opening', dueDate:'2026-09-25', createdAt:'2026-09-01',
      tasks:[
        {id:'t4',text:'KL team task',done:false,waiting:false,dueDate:'2026-09-21'}
      ]
    }
  ],
  projectCounter:3,
  taskCounter:5,
  statuses:{m2:'busy',m7:'free'},
  schedules:[],
  scheduleCounter:1
};

let mockStore = {
  'brief-bar-data': JSON.stringify(briefsPayload),
  'brief-bar-tasks-data': JSON.stringify(tasksPayload)
};

function assert(cond, msg){
  if(!cond) throw new Error(msg);
  console.log('PASS:', msg);
}

(async()=>{
  const browser=await chromium.launch({headless:true});
  const context=await browser.newContext({timezoneId:'Asia/Kuala_Lumpur'});
  const page=await context.newPage();

  const pageErrors=[];
  page.on('pageerror', e=>pageErrors.push(String(e)));

  await page.route(API + '/api/**', async route=>{
    const req=route.request();
    const url=new URL(req.url());

    if(url.pathname==='/api/storage' && req.method()==='GET'){
      const key=url.searchParams.get('key');
      if(!(key in mockStore)){
        await route.fulfill({status:404,contentType:'application/json',body:JSON.stringify({value:null})});
        return;
      }
      await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({value:mockStore[key]})});
      return;
    }

    if(url.pathname==='/api/storage' && req.method()==='POST'){
      const body=JSON.parse(req.postData()||'{}');
      if(body.key) mockStore[body.key]=body.value;
      await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({ok:true})});
      return;
    }

    if(url.pathname==='/api/generate-brief'){
      await route.fulfill({status:501,contentType:'application/json',body:JSON.stringify({error:'QA mock offline fallback'})});
      return;
    }

    throw new Error('Unexpected API request in QA: '+req.method()+' '+req.url());
  });

  async function asUser(id){
    await page.goto(PREVIEW,{waitUntil:'networkidle'});
    await page.evaluate(uid=>localStorage.setItem('egen-current-user',uid),id);
    await page.reload({waitUntil:'networkidle'});
  }

  // Xinyee personal board.
  await asUser('m2');
  assert((await page.locator('#currentUserLabel').innerText()).includes('Xinyee'),'Xinyee identity loads');
  assert(await page.locator('#countToday').innerText()==='1','Xinyee Today count is task-only and correct');
  assert(await page.locator('#countUpcoming').innerText()==='1','Xinyee Upcoming count is correct');
  assert(await page.locator('#countWaiting').innerText()==='1','Xinyee Pending count is correct');

  // Local-date regression at Malaysia 00:30, where UTC date is previous day.
  const localToday=await page.evaluate(()=>{
    const RealDate=Date;
    const fixed=new RealDate('2026-09-20T00:30:00+08:00').getTime();
    class MockDate extends RealDate {
      constructor(...args){ super(...(args.length?args:[fixed])); }
      static now(){ return fixed; }
    }
    window.Date=MockDate;
    return todayStr();
  });
  assert(localToday==='2026-09-20','todayStr uses Malaysia/local date at 00:30 MYT');

  // Reload to restore native Date.
  await page.reload({waitUntil:'networkidle'});

  // Ownership guard: Xinyee cannot mutate Liwen task by direct function call.
  const otherBefore=await page.evaluate(()=>projects.find(p=>p.id==='p2').tasks[0].done);
  await page.evaluate(()=>toggleTask('t4'));
  await page.waitForTimeout(100);
  const otherAfter=await page.evaluate(()=>projects.find(p=>p.id==='p2').tasks[0].done);
  assert(otherBefore===false && otherAfter===false,'staff ownership guard blocks another person task toggle');

  // Own task can still toggle.
  await page.evaluate(()=>toggleTask('t1'));
  await page.waitForTimeout(100);
  const ownAfter=await page.evaluate(()=>projects.find(p=>p.id==='p1').tasks.find(t=>t.id==='t1').done);
  assert(ownAfter===true,'own task toggle still works');

  // Xinyee calendar.
  await page.locator('button[data-view="calendar"]').first().click();
  assert((await page.locator('#calendarTitle').innerText())==='My Calendar','staff sees My Calendar');
  const xAgenda=await page.locator('#calAgenda').innerText();
  assert(xAgenda.includes('PRO3C'),'staff calendar contains own project');
  assert(!xAgenda.includes('Harvey Norman Coalfields Opening'),'staff calendar excludes other team projects');

  // Force October and verify PRO3C exact date.
  await page.evaluate(()=>{calCursor=new Date(2026,9,1);renderCalendar();});
  const oct15=page.locator('.cal-cell[data-date="2026-10-15"]');
  assert((await oct15.innerText()).includes('PRO3C'),'PRO3C is on 15 October');

  // Drag/drop on mocked storage only.
  const source=page.locator('.cal-cell[data-date="2026-10-15"] .cal-item[data-cal-id="project-p1"]');
  const target=page.locator('.cal-cell[data-date="2026-10-16"]');
  await source.dragTo(target);
  await page.waitForTimeout(150);
  const draggedDate=await page.evaluate(()=>projects.find(p=>p.id==='p1').dueDate);
  assert(draggedDate==='2026-10-16','calendar drag updates underlying project date in isolated QA');

  // Reset mocked project date for later tests.
  await page.evaluate(()=>{projects.find(p=>p.id==='p1').dueDate='2026-10-15';});

  // Danwei Manager.
  await asUser('m1');
  await page.locator('button[data-view="calendar"]').first().click();
  assert((await page.locator('#calendarTitle').innerText())==='JB + KL Team Calendar','Danwei sees JB + KL Team Calendar');
  const dAgenda=await page.locator('#calAgenda').innerText();
  assert(dAgenda.includes('Xinyee · PRO3C'),'Danwei calendar includes JB team');
  assert(dAgenda.includes('Liwen · Harvey Norman Coalfields Opening'),'Danwei calendar includes KL team');

  // Leadership checkboxes read-only.
  await page.locator('button[data-view="team"]').first().click();
  const leaderBoxes=page.locator('#leadershipOverview input[type="checkbox"]');
  assert(await leaderBoxes.count()>0,'leadership overview renders task status checkboxes');
  const enabledLeaderBoxes=page.locator('#leadershipOverview input[type="checkbox"]:not([disabled])');
  assert(await enabledLeaderBoxes.count()===0,'leadership overview checkboxes are read-only');

  // Master view sourcing and title.
  await page.locator('button[data-view="master"]').first().click();
  const masterText=await page.locator('#masterViewWrap').innerText();
  assert(masterText.includes('Swisslog - Annual Dinner - Kuala Lumpur'),'Master View uses Client - Event Type - Location');
  assert(!masterText.includes('Approved Test') && !masterText.includes('Archived Client'),'Approved brief excluded from active Master View');
  assert(!masterText.includes('PRO3C'),'manual project excluded from Master View');

  // Chen Senior, KL only.
  await asUser('m6');
  await page.locator('button[data-view="calendar"]').first().click();
  assert((await page.locator('#calendarTitle').innerText())==='KL Team Calendar','Chen sees KL Team Calendar');
  const cAgenda=await page.locator('#calAgenda').innerText();
  assert(cAgenda.includes('Liwen · Harvey Norman Coalfields Opening'),'Chen calendar includes KL team project');
  assert(!cAgenda.includes('Xinyee · PRO3C'),'Chen calendar excludes JB team project');

  // Regular staff must not see Master tab.
  await asUser('m2');
  const masterDisplay=await page.locator('nav.tabs button[data-view="master"]').first().evaluate(el=>getComputedStyle(el).display);
  assert(masterDisplay==='none','regular staff Master View tab is hidden');

  assert(pageErrors.length===0,'no uncaught browser JS errors during QA');

  console.log('ALL PHASE 1 PRE-PRODUCTION QA CHECKS PASSED');
  await browser.close();
})().catch(async err=>{
  console.error('QA FAILED:',err);
  process.exit(1);
});
