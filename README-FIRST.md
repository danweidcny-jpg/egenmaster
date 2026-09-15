# EGEN Master Deck — Claude Debug Pack

Start here.

This ZIP is a focused debugging snapshot of the current EGEN Master Deck. It is intended for code audit and debugging only.

## Read in this order
1. `ARCHITECTURE-CURRENT.md`
2. `index.html`
3. `worker.js`
4. `wrangler.toml`
5. `DEPLOY-README.md`
6. `HANDOFF-PROMPT.md`
7. `CLAUDE-DEBUG-PROMPT.md`

## Important safety rules
- Do **not** rewrite the app from scratch before auditing it.
- Do **not** change storage formats without a migration plan.
- Do **not** delete or overwrite live Cloudflare resources.
- Do **not** request or expose API keys, tokens, `.dev.vars`, or secrets.
- First identify bugs, race conditions, security issues, duplicate logic, and technical debt.
- Preserve compatibility with live data.

## Live architecture
- Frontend: Cloudflare Pages
- Backend: Cloudflare Worker
- Shared data: Cloudflare Workers KV
- Main frontend source: `index.html`
- No build step

The live system is already used for team projects/tasks and proposal/quotation tracking. Treat all storage changes as production-data-sensitive.
