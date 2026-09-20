# EGEN Master Deck — Phase 2 D1 Architecture

Status: DESIGN ONLY. Do not deploy this branch to production yet.

## Objective

Replace whole-blob Workers KV writes with row-level D1 writes so concurrent team edits do not overwrite unrelated data.

Current live behavior to preserve:
- Personal Board and Daily Workload
- Danwei calendar scope = JB + KL
- Chen calendar scope = KL only
- Regular staff calendar = self only
- Calendar shows project event dates + New Brief proposal/quotation due dates only
- Master View sources New Brief assignments only
- New Brief title format remains `Client Name - Event Type - Location`
- Approved briefs remain available in Archive
- Existing IDs such as `p1`, `t1`, `b1`, `m1` are preserved

## Current KV snapshot verified on 2026-09-20

From the production backup:
- 21 projects
- 60 tasks
- 15 schedules
- 1 brief
- task storage keys: projects, projectCounter, taskCounter, statuses, schedules, scheduleCounter
- brief storage keys: briefs, briefCounter

The current frontend still saves the full task payload or full brief payload back to one KV key. This is the source of the lost-update risk.

## Recommended Cloudflare-native target

- Cloudflare Pages: keep
- Cloudflare Worker: keep as API boundary
- Cloudflare D1: primary structured application data
- Workers KV: keep temporarily as rollback/read-only migration source
- Durable Objects: not required for Phase 2
- R2: not required unless file uploads are added later

## Concurrency model

Every mutable D1 row gets a numeric `version`.

Client update flow:
1. Read row including `version`.
2. Send PATCH with `expectedVersion`.
3. Worker runs an update similar to:
   `UPDATE tasks SET done=?, version=version+1, updated_at=? WHERE id=? AND version=?`
4. If zero rows changed, return HTTP 409 Conflict.
5. Client reloads the fresh row and asks user to retry if necessary.

This prevents a stale browser from silently overwriting a newer edit.

## Table model

### users
Stable team identity/role metadata. This is NOT authentication yet.

### user_statuses
Free / Busy / At Capacity status per user.

### projects
One row per project. `due_date` retains the current overloaded meaning for compatibility during migration:
- regular project = event date
- proposal/quotation manual project = due date

A later cleanup can split these concepts after Phase 2 is stable.

### tasks
One row per task, linked to project. Updates are task-level rather than rewriting all projects.

### briefs
One row per New Brief assignment. Structured arrays/objects remain JSON text columns initially to minimize migration risk.

### schedules
Preserved because they exist in production data, even though current Calendar intentionally does not render them.

### audit_logs
Records state-changing API calls. Until Phase 3 authentication exists, `actor_user_id` is informational and not security-authoritative.

### app_meta
Stores legacy counters and migration markers.

## API contract — Phase 2 target

### Bootstrap / reads
- `GET /api/v2/bootstrap`
  - returns users, statuses, projects, tasks, active briefs, approved briefs
- `GET /api/v2/projects?ownerId=m2`
- `GET /api/v2/briefs?assigneeId=m7&status=Assigned`

### Projects
- `POST /api/v2/projects`
- `PATCH /api/v2/projects/:id`
- `DELETE /api/v2/projects/:id` — only after ownership/authorization design is enforced

### Tasks
- `POST /api/v2/projects/:projectId/tasks`
- `PATCH /api/v2/tasks/:id`
- `DELETE /api/v2/tasks/:id`

PATCH examples should update only changed columns:
- done
- waiting
- dueDate
- text

### Briefs
- `POST /api/v2/briefs`
- `PATCH /api/v2/briefs/:id`
- approving a brief updates that row only

### User status
- `PUT /api/v2/users/:id/status`

## Calendar drag/drop

Do not save the whole data set.

Project drag:
- PATCH only `projects.due_date`

Brief drag:
- PATCH only `briefs.due_date`

Management calendar visibility remains a frontend presentation rule in Phase 2, but server authorization must become authoritative in Phase 3.

## Migration strategy

### Step 0 — backup
Already completed before Phase 1. Create a fresh backup again immediately before any migration run.

### Step 1 — create D1 database/schema
Create D1 separately. Do not point production frontend to it.

### Step 2 — dry-run validation
Validate:
- unique IDs
- every task belongs to an existing project
- every project/brief owner or assignee exists in TEAM
- no malformed date fields
- counts match backup

### Step 3 — one-time import
Import users, statuses, projects, tasks, briefs, schedules, counters.
Preserve IDs exactly.

### Step 4 — verification
Compare:
- row counts
- project/task relationships
- dates
- statuses
- active/approved brief counts
- known records such as PRO3C 2026-10-15

### Step 5 — shadow reads
Production remains KV-backed.
A non-user-facing diagnostic endpoint compares D1 with KV.

### Step 6 — API v2 frontend branch
Switch a preview branch to D1 reads/writes and run isolated QA.

### Step 7 — controlled cutover
Before cutover:
- fresh KV backup
- short maintenance window if needed
- final KV -> D1 delta import
- switch production frontend to v2
- keep KV untouched as rollback snapshot

### Step 8 — rollback window
If critical issue:
- switch frontend back to v1 KV endpoints
- do not attempt reverse-sync automatically
- reconcile any D1-only writes manually before a second cutover

## Do not do in Phase 2

- Do not invent a frontend shared secret.
- Do not delete KV.
- Do not change existing IDs.
- Do not redesign Master View.
- Do not redesign New Brief parsing.
- Do not add realtime Durable Objects yet.
- Do not combine Phase 2 migration with Phase 3 authentication.
- Do not make the D1 database production-authoritative before count/content verification.

## Phase 3 boundary

Real authentication and server-side authorization come next.

At that point:
- Danwei Manager: JB + KL
- Chen Senior: KL
- Staff: self
- Worker derives user identity from authenticated session, not localStorage
- audit actor identity becomes trustworthy
