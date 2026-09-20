/**
 * EGEN Master Deck — Cloudflare Worker backend
 *
 * Provides two things the frontend needs once it's hosted outside Claude:
 *
 *  1. GET/POST /api/storage
 *     A simple key-value store backed by Workers KV. This replaces Claude's
 *     in-artifact `window.storage` for SHARED team data (briefs, tasks,
 *     statuses) — everyone hitting this Worker reads/writes the same KV
 *     namespace, so the team stays in sync.
 *
 *  2. POST /api/generate-brief
 *     A secure server-side proxy to the real Anthropic API. This keeps your
 *     API key on the server (as a Worker secret) instead of exposing it in
 *     browser JS. This is OPTIONAL — if you don't set ANTHROPIC_API_KEY, this
 *     endpoint just returns an error and the frontend automatically falls
 *     back to its offline rule-based brief parser.
 *
 * ---------------------------------------------------------------------------
 * SETUP (run these from a terminal with `wrangler` installed):
 *
 *   1. wrangler kv:namespace create EGEN_KV
 *      → copy the returned "id" into wrangler.toml under [[kv_namespaces]]
 *
 *   2. (optional, for AI brief generation) wrangler secret put ANTHROPIC_API_KEY
 *      → paste your key from console.anthropic.com when prompted
 *
 *   3. wrangler deploy
 *      → note the printed *.workers.dev URL
 *
 *   4. Open egen-master-deck.html, find the line:
 *        const API_BASE = 'https://YOUR-WORKER-SUBDOMAIN.workers.dev';
 *      and replace it with the URL from step 3.
 * ---------------------------------------------------------------------------
 */

const ALLOWED_STORAGE_KEYS = new Set(["brief-bar-data", "brief-bar-tasks-data"]);

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", ...CORS_HEADERS },
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS_HEADERS });
    }

    // ---------------- Key-value storage (shared team data) ----------------
    if (url.pathname === "/api/storage") {
      if (request.method === "GET") {
        const key = url.searchParams.get("key");
        if (!key) return json({ error: "Missing key" }, 400);
        if (!ALLOWED_STORAGE_KEYS.has(key)) return json({ error: "Storage key not allowed" }, 403);
        const value = await env.EGEN_KV.get(key);
        if (value === null) return json({ value: null }, 404);
        return json({ value });
      }

      if (request.method === "POST") {
        let body;
        try {
          body = await request.json();
        } catch {
          return json({ error: "Invalid JSON body" }, 400);
        }
        const { key, value } = body || {};
        if (!key) return json({ error: "Missing key" }, 400);
        if (!ALLOWED_STORAGE_KEYS.has(key)) return json({ error: "Storage key not allowed" }, 403);
        const toStore = typeof value === "string" ? value : JSON.stringify(value);
        await env.EGEN_KV.put(key, toStore);
        return json({ ok: true });
      }


      return json({ error: "Method not allowed" }, 405);
    }

    // ---------------- AI brief generation proxy (optional) ----------------
    if (url.pathname === "/api/generate-brief" && request.method === "POST") {
      if (!env.ANTHROPIC_API_KEY) {
        return json(
          { error: "ANTHROPIC_API_KEY is not configured on this Worker yet — see the setup notes at the top of worker.js" },
          501
        );
      }
      let body;
      try {
        body = await request.json();
      } catch {
        return json({ error: "Invalid JSON body" }, 400);
      }
      const { prompt } = body || {};
      if (!prompt) return json({ error: "Missing prompt" }, 400);

      const anthropicRes = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": env.ANTHROPIC_API_KEY,
          "anthropic-version": "2023-06-01",
        },
        body: JSON.stringify({
          model: "claude-sonnet-5",
          max_tokens: 1500,
          messages: [{ role: "user", content: prompt }],
        }),
      });

      if (!anthropicRes.ok) {
        const detail = await anthropicRes.text();
        return json({ error: "Anthropic API request failed", detail }, 502);
      }
      const data = await anthropicRes.json();
      return json(data);
    }

    return json({ error: "Not found" }, 404);
  },
};
