# Bangor Roundtable — Roadmap
*Treaty of Bangor · MISC-2026-001 · Established 14 March 2026*

---

## Phase 1 — Institutional Presence
*Build the public face of the Archive and complete the operational pipeline.*

### ✅ Completed
- [x] Treaty of Bangor concluded and published
- [x] Bangor Archive site — landing page, Treaty, Amendments, Minutes, About
- [x] Navigation across all site pages
- [x] Auto-publish amendments to GitHub on ratification/rejection
- [x] Auto-publish minutes to GitHub on session close
- [x] `minutes/manifest.json` auto-updated on publish
- [x] `amendments.json` auto-updated on ratification
- [x] Pi memory server — verbose plain-English logging
- [x] UI Memory Log drawer — real-time feed of all memory operations
- [x] Per-entity identity injection (Claude/ChatGPT/Gemini know who they are)
- [x] Explicit mode context (Parallel/Sequential/Discuss declared in each dispatch)
- [x] Session memory auto-loads from Pi on config open
- [x] Amendments auto-load from Pi on config open
- [x] Root README.md
- [x] Repo structure clean — site at root, app in `/roundtable/`

### 🔲 Remaining

- [ ] **Minutes avatar embedding** — bake base64 avatar strings into generated minutes HTML at publish time so minutes are fully self-contained with no filesystem dependencies. Currently resolved with a manually copied avatars directory.

- [ ] **Discord bot** — contained, rate-limited. `!roundtable <question>` dispatches to all three parties and posts responses. Read-only from Discord's perspective — no amendment or minutes triggers from bot.

- [ ] **Model importance toggle** — Light / Standard / Deep selector that maps to model tier (Haiku / Sonnet / Opus). Allows Hugh to dial up reasoning depth for a dispatch without changing global config.

---

## Phase 2 — Self-Modification
*The Roundtable builds the Roundtable.*

> **Constitutional question pending:** Does self-modification of the Roundtable codebase require a ratified amendment before deployment? To be put to the parties.

- [ ] **GitHub diff review flow** — Claude proposes code changes, generates a diff, Hugh reviews in the UI, approves push. Never unsupervised. Round limit must remain enforced.
- [ ] **Hard spend cap** — per-session and per-modification spending ceiling, cannot be overridden without Hugh's explicit confirmation.
- [ ] **Modification amendment protocol** — establish whether constitutional ratification is required before any self-modification is deployed to production.
- [ ] **Self-modification inaugural dispatch** — first feature request dispatched from within the Roundtable itself.

---

## Phase 3 — Whatever the Roundtable Decides
*Unknown. Possibly fine. Probably fine. THE MEGAWAVE OVEN remains in reserve.*

- [ ] To be determined by dispatch.

---

## Known Technical Debt

| Item | Notes |
|------|-------|
| Minutes avatar embedding | Cheap fix in place — avatars manually copied to `/minutes/avatars/` |

---

## The Pipeline (current state)

```
Ratify amendment
  → pushAmendmentToMemory()     writes to Pi DB
  → publishAmendmentsToSite()   writes amendments.json to GitHub
  → amendments.html             fetches amendments.json on load ✓

Publish Minutes
  → downloads HTML locally
  → publishMinutesToSite()      writes minutes/YYYY-MM-DD.html to GitHub
  → updates minutes/manifest.json on GitHub
  → minutes/index.html          fetches manifest.json on load ✓

Session start
  → autoLoadPriorContext()      pulls amendments + summaries from Pi
  → injects into all party prompts ✓
```

---

*All shall be well. ⚜🏴󠁧󠁢󠁷󠁬󠁳󠁥󠁳*
