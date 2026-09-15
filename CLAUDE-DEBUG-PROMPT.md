# Claude Debug Prompt — EGEN Master Deck

You are reviewing a live internal event-management web app called **EGEN Master Deck**.

Please act as a senior full-stack engineer and perform a **careful audit before changing anything**.

## Read first
1. `README-FIRST.md`
2. `ARCHITECTURE-CURRENT.md`
3. `index.html`
4. `worker.js`
5. `wrangler.toml`
6. `DEPLOY-README.md`
7. `HANDOFF-PROMPT.md`

## Current architecture
- Frontend: single-file `index.html`
- Backend: Cloudflare Worker
- Shared storage: Cloudflare Workers KV
- No build step
- Live team usage already exists

## What I need from you
Audit the current code and identify:

1. Bugs or broken logic
2. Multi-user race conditions / lost-update risks
3. KV architecture problems
4. Security and authorization weaknesses
5. Calendar drag-and-drop bugs
6. Malaysia timezone / date-only bugs
7. Incorrect user visibility / permission logic
8. Duplicate functions, repeated code, dead code, stale comments, or patch residue
9. Mobile / responsive issues
10. Data-loss risks
11. CORS / Worker API issues
12. Input validation and destructive-operation risks
13. Whether Cloudflare KV should be replaced or supplemented by D1 and/or Durable Objects
14. Any other high-risk production issue you spot

## Product rules that must be preserved
- Ordinary staff see only their own Board/projects/tasks.
- Danwei (Manager) can see team workload for JB + KL.
- Chen (Senior) can see management information intended for KL scope.
- Calendar shows only Project Event Date and Proposal/Quotation Due Date; task due dates do not appear there.
- Danwei Calendar = JB + KL team.
- Chen Calendar = KL team only.
- Other users Calendar = personal only.
- Calendar project/brief items can be dragged to a new date, and the underlying event/due date must update.
- Master View is management-only and must contain only records created through `New Brief -> Assign`.
- Manual projects/tasks must never enter Master View.
- New Brief title format is `Client Name - Event Type - Location`.
- Approved New Brief records leave active Master View and appear in Archive.

## Safety constraints
- Do NOT ask for API keys or secrets.
- Do NOT delete or overwrite live Cloudflare resources.
- Do NOT redesign or rewrite the whole app yet.
- Do NOT change the storage schema until you provide a migration/rollback plan.
- Assume production KV already contains important live data.

## Deliverable format
Please return:

### 1. Executive summary
The 5-10 most important findings.

### 2. Prioritized issues
Use four sections:
- Critical
- High
- Medium
- Nice-to-have

For each issue include:
- exact file/function/area
- what is wrong
- why it matters
- reproduction scenario where possible
- safest fix
- whether it can affect live data

### 3. Multi-user/storage assessment
Explain specifically how the current whole-JSON KV read/modify/write pattern can lose data, and recommend a target architecture (KV vs D1 vs Durable Objects) with reasoning.

### 4. Security assessment
Review identity, authorization, Worker endpoints, CORS, direct API access, validation, and destructive operations.

### 5. Date/calendar assessment
Audit timezone/date-only handling and drag/drop persistence.

### 6. Technical-debt cleanup list
Identify duplicate/repeated/dead code that can be removed without changing behavior.

### 7. Safe remediation plan
Give a phased plan that minimizes risk to production data. Include backup/export, testing, migration, rollout, verification, and rollback.

### 8. First patch recommendation
Recommend only the first small patch you would make. Do not implement a broad rewrite unless I explicitly ask next.

If something cannot be proven from the attached code alone, say so instead of guessing.
