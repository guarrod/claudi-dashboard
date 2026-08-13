# Claude Code Telemetry — project brief

Cross-machine usage tracker for Claude Code, rendered on a 5" wall panel.
Reads local Claude Code logs from two machines (Mac + Windows), merges them on
a VPS, and serves a sci-fi HUD dashboard.

> This file is the source of truth. The mockup in `mockup/` shows the target look.
> Read both before writing code.

---

## Goal

One always-on 5" panel (800×480 landscape) that answers, at a glance:
how much Claude Code did I burn today, across both my machines, on which models
and which projects, and how is the current 5-hour block going.

## Scope and hard limits (read this before designing anything)

- **This is a Claude Code tracker, not a "subscription" tracker.** Chat (iOS/Mac/web)
  and Claude Design run server-side and leave **no local logs**. They will never
  appear here. Do not add placeholders for them.
- **There is no official Anthropic API for subscription usage.** The only data
  source is the local JSONL logs Claude Code writes to `~/.claude/projects/`
  (and the Xcode integration dir on Mac).
- **Flat-rate plan = no real dollar cost.** Any `$` shown is a *computed*
  "what this would cost at API rates" figure, not a bill. It MUST be labelled
  as an equivalent, never as spend.
- **The 5h/weekly limit % is unknowable.** Anthropic does not publish the cap and
  it varies by server load. Do NOT render a confident "% of limit" gauge from a
  hardcoded cap. See "Data honesty rules" below.

## Non-goals (for v1)

- Real-time streaming. A 30–60s poll is fine.
- Chat / Design / web usage.
- Auth/login UI. Single user, single panel.

---

## Architecture

Three pieces. Build them in this order.

```
[Mac]  ccusage --json ─┐
                       ├─►  [VPS]  collector (Node/Express) ─► SQLite ─► /api/telemetry ─►  [5" panel] HUD (vanilla HTML)
[Win]  ccusage --json ─┘
```

### 1. Collector (runs on each machine)
- A small script (`collector/collect.sh` or a Node script) that runs:
  - `ccusage daily --json --instances`  (tokens by day + by project)
  - `ccusage daily --json --breakdown`  (by model)
  - `ccusage blocks --json`             (current 5-hour window)
- Tags the payload with a `machine_id` ("mac-01" / "win-01") and a timestamp.
- Ships it to the VPS. Scheduled by cron (Mac) / Task Scheduler (Win), every ~5 min.
- **Do not reimplement JSONL parsing.** Stand on `ccusage --json`.

### 2. VPS collector + store + API
- Node/Express on the VPS (same box as the other apps).
- Receives snapshots from both machines, upserts into **SQLite** (one table for
  raw snapshots keyed by machine_id + window, plus derived aggregates).
- Exposes `GET /api/telemetry` returning the shape in "Data contract" below.
- Lives behind Nginx in the **443 server block** (location block, not the port-80
  redirect block). Served at e.g. `https://<domain>/telemetry/`.

### 3. HUD frontend
- The `web/index.html` is the dashboard from `mockup/`, with the mock numbers
  replaced by a `fetch('/api/telemetry')` + render.
- Vanilla HTML/CSS/JS, **no build step, no external runtime deps** (self-host the
  two Google fonts on the VPS instead of CDN if you want zero external calls).
- Auto-refresh every 30–60s. Point the panel's browser at the URL in kiosk mode.

---

## Transport decision (pick one — note the tradeoff)

How the collector gets snapshots to the VPS:

- **A. HTTP POST to a collector endpoint** (`POST /api/ingest`). Simple, near
  real-time. Risk: a public write endpoint — MUST require a shared bearer token
  (env var, never hardcoded). You flagged publicly-exposed backends before.
- **B. Git-based** — each machine commits its JSON snapshot to a private repo,
  VPS `pullall` ingests on a cron. Fits your existing pushall/pullall + git
  backbone, no public write endpoint. Tradeoff: git history bloats from frequent
  commits (mitigate by overwriting a single `snapshot.json` and squashing, or a
  separate throwaway branch).

Default recommendation: **B** for security + fit with your infra, unless you want
sub-minute freshness, then **A** with a bearer token.

---

## Data contract — `GET /api/telemetry`

Annotate each field's trust level in code comments. R = real (from logs),
C = computed by us, E = estimated/unknowable.

```jsonc
{
  "generated_at": "2026-06-25T21:46:00Z",      // R
  "sync": {                                     // R — about OUR system, not Anthropic
    "mac-01": { "last_seen": "2026-06-25T21:44:10Z" },
    "win-01": { "last_seen": "2026-06-25T21:32:00Z" },
    "vps_ok": true
  },
  "today": {
    "tokens": 4700000,                          // R
    "by_machine": { "mac-01": 3100000, "win-01": 1600000 }, // R
    "equiv_usd": 28.40,                          // C — tokens × API list price. NOT a bill.
    "vs_7d_avg_pct": 18                          // C
  },
  "block_5h": {
    "tokens": 1240000,                          // R
    "started_at": "2026-06-25T19:30:00Z",        // R
    "est_window_cap": 2200000,                   // E — optional, manual config only
    "cap_source": "manual_config"                // E — flag so UI can mark it
  },
  "week": {
    "daily": [ { "date": "2026-06-19", "tokens": 380000 } /* ... */ ],  // R
    "by_model": { "sonnet": 0.72, "opus": 0.24, "haiku": 0.04 },        // R
    "by_project": [ { "name": "content-correction", "tokens": 1900000 } ] // R
  }
}
```

## Data honesty rules (enforce in both API and UI)

1. **Never fabricate a limit percentage.** If `est_window_cap` is not set by me in
   config, the UI shows raw burn (tokens + tokens/hour rate), NOT a "56% of limit".
2. Any field tagged **E** (estimated) must be visually distinct in the HUD
   (e.g. an `EST` tag, dimmer styling) so I can tell at a glance it's a guess.
3. Any field tagged **C** (computed) — especially `equiv_usd` — must carry an
   "≈ API-rate equiv" label. It is not money I paid.
4. R fields can be shown plainly.

---

## Tech stack

- Node/Express, SQLite (no Postgres for v1 — single user, low volume).
- Vanilla HTML/CSS/JS frontend. No framework, no bundler.
- Nginx + SSL on the VPS (443 block). Deploy via existing pushall/pullall.
- All secrets in env vars (`.env`, gitignored; commit `.env.example`).
- Git from the first commit. Private repo.

## Suggested repo layout

```
claude-telemetry/
  CLAUDE.md            ← this file
  collector/
    collect.sh         ← runs ccusage --json, tags machine, ships to VPS
  server/
    index.js           ← Express: ingest + merge + /api/telemetry
    db.js              ← SQLite schema + queries
    .env.example
  web/
    index.html         ← the HUD (port the mockup, swap mock data for fetch)
  mockup/
    claude-code-telemetry.html   ← visual reference (mock data)
```

## Phased plan

- **P1 — one machine, end to end.** ccusage on the Mac → VPS collector → SQLite →
  `/api/telemetry` (with only `today`, `block_5h`, `by_model`). Verify numbers
  match `ccusage daily` on the Mac. Git commit.
- **P2 — second machine + merge.** Add the Windows collector. Make `by_machine`
  and the merge logic real. Handle stale machines (last_seen old → mark offline).
- **P3 — wire the HUD.** Replace mock numbers in `web/index.html` with the fetch.
  Apply the honesty rules (EST/equiv tags, no fake %).
- **P4 — panel + Nginx.** Add the 443 location block, kiosk the 5" browser at it.

## Open decisions for me (don't guess — ask)

- Transport: git-based (B) or POST+token (A)?
- Panel orientation confirmed landscape 800×480?
- Self-host fonts on VPS, or allow Google Fonts CDN?
- Do I want a manual `est_window_cap` per plan, or skip the gauge % entirely?