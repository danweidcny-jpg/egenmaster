# EGEN D1 API v2 Contract — Draft

This document defines the row-level API planned for Phase 2.

## Response rules

- JSON only
- successful single-row reads return `{ data: ... }`
- successful mutations return the updated row
- stale-version update returns HTTP 409
- invalid input returns HTTP 400
- missing row returns HTTP 404
- authorization rules are intentionally deferred to Phase 3, but endpoint shapes must be compatible with server-side auth later

## Bootstrap

`GET /api/v2/bootstrap?userId=m2`

Returns enough data for the current single-page app to render without whole-KV reads.

Suggested shape:

```json
{
  "users": [],
  "statuses": [],
  "projects": [],
  "tasks": [],
  "briefs": [],
  "serverTime": "2026-09-20T00:00:00Z"
}
```

## PATCH task

`PATCH /api/v2/tasks/t12`

```json
{
  "expectedVersion": 4,
  "changes": {
    "done": true
  },
  "actorUserId": "m2"
}
```

Worker:
- allowlist mutable fields
- update one row only
- increment version
- write audit log in the same D1 transaction where practical
- return 409 if version no longer matches

## PATCH project

`PATCH /api/v2/projects/p1`

Allowed Phase 2 changes:
- title
- dueDate

Calendar drag changes only `dueDate`.

## PATCH brief

`PATCH /api/v2/briefs/b1`

Allowed Phase 2 changes:
- assigneeId
- dueDate
- status
- approvedAt
- title only where current New Brief workflow already changes it

Calendar drag changes only `dueDate`.

## User status

`PUT /api/v2/users/m2/status`

```json
{
  "expectedVersion": 2,
  "status": "busy",
  "actorUserId": "m2"
}
```

## Conflict response

HTTP 409:

```json
{
  "error": "Version conflict",
  "code": "STALE_WRITE",
  "current": {
    "id": "t12",
    "version": 5
  }
}
```

Frontend should reload the changed entity instead of silently overwriting it.

## Phase 2 compatibility rule

Do not remove the current v1 KV endpoints during migration.
The preview frontend can use v2 while production stays on v1 until cutover is approved.
