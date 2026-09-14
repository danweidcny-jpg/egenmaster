# Deploying EGEN Master Deck to Cloudflare

This package has 3 files:
- `egen-master-deck.html` — the app itself (upload this to Cloudflare Pages)
- `worker.js` — a small backend that gives the team shared, synced data
- `wrangler.toml` — config for deploying the Worker

You need **both** the Worker (for shared data) and the HTML file (for the app) —
they're separate Cloudflare products working together.

---

## Part 1 — Deploy the Worker (shared data backend)

You'll need Node.js installed and Cloudflare's CLI tool, `wrangler`.

1. **Install wrangler** (one-time):
   ```
   npm install -g wrangler
   ```

2. **Log in to Cloudflare**:
   ```
   wrangler login
   ```
   This opens a browser to authorize. If you don't have a Cloudflare account yet, sign up free at cloudflare.com first.

3. **Create the KV namespace** (this is where briefs/tasks/statuses get stored):
   ```
   cd cloudflare
   wrangler kv:namespace create EGEN_KV
   ```
   This prints something like:
   ```
   { binding = "EGEN_KV", id = "abcd1234..." }
   ```
   Copy that `id` value into `wrangler.toml`, replacing `PASTE_YOUR_KV_NAMESPACE_ID_HERE`.

4. **(Optional) Add your Anthropic API key**, only if you want the AI-powered
   brief translation/theme suggestions instead of the offline parser:
   ```
   wrangler secret put ANTHROPIC_API_KEY
   ```
   Paste your key (from console.anthropic.com) when prompted. You can skip
   this step entirely — the app works fine without it.

5. **Deploy**:
   ```
   wrangler deploy
   ```
   This prints a URL like:
   ```
   https://egen-master-deck-api.YOUR-SUBDOMAIN.workers.dev
   ```
   **Copy this URL** — you need it in Part 2.

---

## Part 2 — Point the app at your Worker

1. Open `egen-master-deck.html` in a text editor.
2. Find this line near the bottom (search for `API_BASE`):
   ```js
   const API_BASE = 'https://YOUR-WORKER-SUBDOMAIN.workers.dev';
   ```
3. Replace the placeholder URL with the real URL from Part 1, step 5.
4. Save the file.

---

## Part 3 — Host the HTML on Cloudflare Pages

1. Go to the Cloudflare dashboard → **Workers & Pages** → **Create** → **Pages**.
2. Choose **"Upload assets"** (the simplest option — no Git needed).
3. Drag in your edited `egen-master-deck.html` file.
   - Cloudflare Pages expects an `index.html` — rename the file to
     `index.html` before uploading, or set it as your custom entry point.
4. Deploy. Cloudflare gives you a URL like `https://your-project.pages.dev`.
5. Share that URL with your team — everyone opens the same link, picks their
   name on first visit, and their choice is remembered on their own device.

---

## Checking it worked

- Open the Pages URL, pick a name, add a test project/task.
- Open the same URL on a different device/browser (or an incognito window),
  pick a different name — you should see the first person's project appear
  in the Team section, confirming shared sync is live.
- Check the small sync indicator next to the app title in the header — it
  should say "Saved ✓" after any change, not "Not saved — check connection".

## If something's not syncing

- Double-check `API_BASE` in the HTML exactly matches your deployed Worker URL
  (no trailing slash).
- Open the browser console (F12) and look for errors — a CORS or 404 error
  usually means the Worker URL is wrong or the KV namespace ID in
  `wrangler.toml` wasn't set before deploying.
- Re-run `wrangler deploy` after any change to `worker.js` or `wrangler.toml`.

## Adding the AI brief generator later

If you skipped the API key earlier and want it later, just run:
```
wrangler secret put ANTHROPIC_API_KEY
```
then `wrangler deploy` again. No changes needed to the HTML file — it already
tries the AI path automatically and only falls back to the offline parser if
the key isn't set.
