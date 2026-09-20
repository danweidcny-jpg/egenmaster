#!/usr/bin/env node
/**
 * EGEN KV -> D1 migration dry-run validator.
 *
 * Usage:
 *   node scripts/validate-kv-backup.js /path/to/unzipped-backup
 *
 * This script NEVER writes to Cloudflare and NEVER changes production data.
 */
const fs = require('fs');
const path = require('path');

const dir = process.argv[2];
if (!dir) {
  console.error('Usage: node scripts/validate-kv-backup.js /path/to/unzipped-backup');
  process.exit(2);
}

function read(name) {
  return JSON.parse(fs.readFileSync(path.join(dir, name), 'utf8'));
}
function assert(cond, message) {
  if (!cond) throw new Error(message);
}
function validDate(v) {
  return !v || /^\d{4}-\d{2}-\d{2}$/.test(v);
}

const tasksData = read('brief-bar-tasks-data.json');
const briefData = read('brief-bar-data.json');

const TEAM = [
  {id:'m1',name:'Danwei',office:'JB',role:'Manager'},
  {id:'m2',name:'Xinyee',office:'JB',role:'Team'},
  {id:'m3',name:'Eunice',office:'JB',role:'Team'},
  {id:'m4',name:'Xiang Ting',office:'JB',role:'Team'},
  {id:'m5',name:'Danwei',office:'KL',role:'Manager'},
  {id:'m6',name:'Chen',office:'KL',role:'Senior'},
  {id:'m7',name:'Liwen',office:'KL',role:'Team'},
  {id:'m8',name:'Rachel',office:'KL',role:'Team'},
  {id:'m9',name:'Ethan',office:'KL',role:'Team'},
  {id:'m10',name:'Esther',office:'KL',role:'Team'},
];
const userIds = new Set(TEAM.map(x=>x.id));
const ids = new Set();

const projects = tasksData.projects || [];
const tasks = [];
for (const p of projects) {
  assert(p.id && !ids.has(p.id), 'Duplicate or missing project id: ' + p.id);
  ids.add(p.id);
  assert(userIds.has(p.ownerId), 'Unknown project owner: ' + p.id + ' -> ' + p.ownerId);
  assert(validDate(p.dueDate), 'Malformed project dueDate: ' + p.id + ' -> ' + p.dueDate);
  assert(validDate(p.createdAt), 'Malformed project createdAt: ' + p.id + ' -> ' + p.createdAt);

  for (let i=0; i<(p.tasks||[]).length; i++) {
    const t = p.tasks[i];
    assert(t.id && !ids.has(t.id), 'Duplicate or missing task id: ' + t.id);
    ids.add(t.id);
    assert(validDate(t.dueDate), 'Malformed task dueDate: ' + t.id + ' -> ' + t.dueDate);
    tasks.push({...t, projectId:p.id, sortOrder:i});
  }
}

const schedules = tasksData.schedules || [];
for (const s of schedules) {
  assert(s.id && !ids.has(s.id), 'Duplicate or missing schedule id: ' + s.id);
  ids.add(s.id);
  assert(userIds.has(s.ownerId), 'Unknown schedule owner: ' + s.id + ' -> ' + s.ownerId);
  assert(validDate(s.date), 'Malformed schedule date: ' + s.id + ' -> ' + s.date);
  assert(validDate(s.endDate), 'Malformed schedule endDate: ' + s.id + ' -> ' + s.endDate);
}

const briefs = briefData.briefs || [];
for (const b of briefs) {
  assert(b.id && !ids.has(b.id), 'Duplicate or missing brief id: ' + b.id);
  ids.add(b.id);
  assert(!b.assigneeId || userIds.has(b.assigneeId), 'Unknown brief assignee: ' + b.id + ' -> ' + b.assigneeId);
  assert(validDate(b.dueDate), 'Malformed brief dueDate: ' + b.id + ' -> ' + b.dueDate);
  assert(validDate(b.createdAt), 'Malformed brief createdAt: ' + b.id + ' -> ' + b.createdAt);
  assert(validDate(b.approvedAt), 'Malformed brief approvedAt: ' + b.id + ' -> ' + b.approvedAt);
}

for (const userId of Object.keys(tasksData.statuses || {})) {
  assert(userIds.has(userId), 'Status references unknown user: ' + userId);
}

const preview = {
  users: TEAM.length,
  projects: projects.length,
  tasks: tasks.length,
  schedules: schedules.length,
  briefs: briefs.length,
  statuses: Object.keys(tasksData.statuses || {}).length,
  counters: {
    projectCounter: tasksData.projectCounter,
    taskCounter: tasksData.taskCounter,
    scheduleCounter: tasksData.scheduleCounter,
    briefCounter: briefData.briefCounter,
  },
  knownChecks: {
    pro3c: projects
      .filter(p => p.title === 'PRO3C')
      .map(p => ({id:p.id, ownerId:p.ownerId, dueDate:p.dueDate})),
  }
};

console.log(JSON.stringify(preview, null, 2));
console.log('\nDRY-RUN VALIDATION PASSED — no data was written.');
