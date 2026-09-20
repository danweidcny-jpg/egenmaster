# Phase 2 D1 Dry-Run Result

Source: production KV backup created 2026-09-20.

This is a validation report only. No Cloudflare D1 database was created or modified by this dry run.

## Snapshot counts

- Users defined by current TEAM model: 10
- Projects: 21
- Tasks nested under projects: 60
- Schedules: 15
- Briefs: 1
- User status rows currently present: 3

## Domain checks

- Project owners present in backup: m2, m4, m7, m8, m9, m10
- Current user status values found: free, busy
- Brief status values found: Assigned
- Brief source values found: new-brief
- All task done/waiting values are booleans
- Schedule records use: id, ownerId, title, date, endDate, time, note

## Known regression check

PRO3C:
- id: p1
- owner: m2 / Xinyee
- event date: 2026-10-15
- nested tasks: 6

This matches the current product rule that PRO3C remains on 15 October 2026.

## Schema compatibility result

The proposed initial D1 schema is compatible with the inspected production snapshot:
- existing project/task/brief/schedule IDs can be preserved
- current status values fit the proposed constraints
- current brief source fits the proposed source column
- current task booleans map cleanly to D1 INTEGER 0/1
- JSON-heavy brief substructures can be preserved losslessly as JSON text during first migration

## Important migration note

The legacy numeric counters must be imported into app_meta even though D1 row IDs are preserved. This allows a low-risk cutover without changing the frontend ID-generation assumptions prematurely.

## Result

DRY-RUN DESIGN VALIDATION PASSED.

Next safe step:
1. review this schema/API contract
2. create a non-production D1 database
3. import the backup into that database only
4. compare row counts/content
5. test an API v2 preview branch
6. do not switch production until a second explicit approval
