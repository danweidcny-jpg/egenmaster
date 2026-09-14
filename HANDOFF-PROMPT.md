# Handoff: Deploy "EGEN Master Deck" to Cloudflare

I need you to deploy a small app for me to Cloudflare. Please work through this
step by step, and **stop and ask me before doing anything that needs my
credentials, or that could affect any existing live/production data.**

## What this is
- `egen-master-deck.html` — a single-page web app (task board + client brief
  generator) for an event management team. No build step needed.
- `worker.js` — a Cloudflare Worker backend. It exposes:
  - `GET/POST/DELETE /api/storage` — a simple key-value API backed by
    Workers KV, used for shared team data (tasks, briefs, statuses).
  - `POST /api/generate-brief` — an optional proxy to the Anthropic API for
    AI-assisted brief writing. Only works if an `ANTHROPIC_API_KEY` secret is
    set; otherwise the app just falls back to its built-in offline parser
    automatically, so this secret is NOT required to deploy successfully.
- `wrangler.toml` — Worker config. It has a placeholder KV namespace id that
  needs to be replaced with a real one (see steps below).

## Safety rules — please follow these strictly
1. **Do not upload, commit, or paste any secrets** (API keys, `.dev.vars`
   files, tokens) into chat, logs, or version control. Secrets should only be
   set via `wrangler secret put` directly in my terminal session.
2. **Do not delete or overwrite any existing Cloudflare KV namespace, Worker,
   or Pages project** unless I explicitly confirm the exact name to reuse. If
   a namespace/Worker/Pages project with a similar name already exists,
   **stop and ask me** whether to reuse it or create a new one — never assume.
3. **Before running `wrangler deploy` or publishing Pages**, show me a
   summary of what will be created/changed (new KV namespace? new Worker?
   which Pages project?) and wait for my go-ahead.
4. If at any point you need me to log in (`wrangler login`), provide an API
   key, or confirm something that touches data that might already be live,
   **pause and ask me directly** rather than proceeding.
5. Don't run a "dry run"/deploy against a project name that isn't clearly
   brand new without confirming with me first.

## Steps

1. **Check environment**: confirm Node.js and `wrangler` are available
   (`wrangler --version`). Install `wrangler` if missing
   (`npm install -g wrangler`).
2. **Check login state**: run a safe, read-only wrangler command (e.g.
   `wrangler whoami`) to see if I'm already logged in. If not, tell me and
   wait — don't try to log in on my behalf without me present.
3. **Create the KV namespace**: `wrangler kv:namespace create EGEN_KV`.
   Show me the returned id before editing `wrangler.toml`.
4. **Update `wrangler.toml`** with that id (only after I confirm).
5. **Optional**: ask me whether I want to set `ANTHROPIC_API_KEY` now via
   `wrangler secret put ANTHROPIC_API_KEY`, or skip it (app works without it).
6. **Deploy the Worker**: `wrangler deploy`. Show me the resulting
   `*.workers.dev` URL.
7. **Update the HTML**: in `egen-master-deck.html`, find:
   ```js
   const API_BASE = 'https://YOUR-WORKER-SUBDOMAIN.workers.dev';
   ```
   and replace the placeholder with the real Worker URL from step 6.
8. **Deploy the HTML to Cloudflare Pages**: rename it to `index.html` and
   deploy via "Upload assets" (or ask me which method I prefer — Git-based
   deploy is also an option if I have a repo).
9. **Test it end-to-end**:
   - Open the deployed Pages URL, pick a team member name, add a test
     project and task.
   - Open the same URL in a second browser/incognito session, pick a
     different name, and confirm the first test project is visible in the
     Team section — this proves shared sync via the Worker is working.
   - Confirm the sync indicator in the header shows "Saved ✓", not an error.
10. **Report back to me**: the final public Pages URL, the Worker URL, and
    a plain-language summary of what you tested and confirmed working.

Full step-by-step reference with more detail is in `DEPLOY-README.md`,
included alongside this file — read that too before starting.
