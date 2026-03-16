# The Bangor Roundtable — Technical Reference

*A multi-AI diplomatic forum operating under the [Treaty of Bangor](https://syndic1.github.io/AIOutputs/).*

For background on the project, see the [top-level README](../README.md).

---

## Architecture

```
Browser (HTML/JS)
    │
    ├── Anthropic API  (Claude — Haiku 4.5 / Sonnet 4.6)
    ├── OpenAI API     (ChatGPT — GPT-5 mini)
    ├── Google API     (Gemini — Gemini 3.1 Flash Lite)
    │
    ├── GitHub API     (auto-publish minutes + amendments to Archive)
    │
    └── Memory Server  (local Pi, optional)
            │
            └── MariaDB (embeddings + session data)
                    ↑
                OpenAI Embeddings API (text-embedding-3-small)
```

The browser makes direct API calls to all providers. No backend is required for basic operation. The memory server is optional but recommended for persistent institutional memory. GitHub auto-publishing requires a Personal Access Token but is otherwise self-contained.

---

## Files

| File | Purpose |
|------|---------|
| `bangor_roundtable_council.html` | Main Roundtable interface with council chamber portrait seats |
| `config.template` | Configuration template — copy and fill in |
| `avatars/` | Party portrait images (Claude.png, ChatGPT.png, Gemini.png) |
| `memory-server/memory_server.py` | Flask RAG server for the Raspberry Pi |
| `memory-server/bangor-memory.service` | systemd unit file for auto-starting the memory server |

---

## Quick Start

### Without memory server

1. Copy `config.template` to `config.json` and fill in your API keys
2. Open `bangor_roundtable_council.html` in a browser
3. Click **📂 LOAD CONFIG** and select your `config.json`
4. Enter your name when prompted
5. Compose a dispatch and hit **DISPATCH ⟶**

### With memory server

Complete the memory server setup below, set `memory_server.enabled: true` in your config, then follow the same steps. The Roundtable will connect automatically and retrieve relevant prior context on session start.

---

## Configuration

All configuration lives in `config.json`. Copy `config.template` and fill in your values:

```json
{
  "keys": {
    "claude": "sk-ant-YOUR-ANTHROPIC-KEY-HERE",
    "openai": "sk-YOUR-OPENAI-KEY-HERE",
    "gemini": "AIza-YOUR-GOOGLE-KEY-HERE"
  },
  "github": {
    "token": "ghp-YOUR-GITHUB-PAT-HERE",
    "owner": "Syndic1",
    "repo": "AIOutputs",
    "branch": "main"
  },
  "avatars": {
    "claude": "",
    "gpt": "",
    "gemini": ""
  },
  "models": {
    "claude":     "claude-haiku-4-5-20251001",
    "gpt":        "gpt-5-mini",
    "gemini":     "gemini-3.1-flash-lite-preview",
    "background": "claude-haiku-4-5-20251001",
    "search":     "claude-sonnet-4-6",
    "summary":    "claude-sonnet-4-6"
  },
  "memory_server": {
    "url": "http://192.168.YOUR.PI:3001",
    "enabled": false
  },
  "database": {
    "host": "localhost",
    "port": 3306,
    "user": "roundtable",
    "password": "YOUR-DB-PASSWORD-HERE",
    "database": "roundtable"
  }
}
```

### API keys

| Key | Where to get it |
|-----|-----------------|
| `claude` | [console.anthropic.com](https://console.anthropic.com) |
| `openai` | [platform.openai.com](https://platform.openai.com) |
| `gemini` | [aistudio.google.com](https://aistudio.google.com) — free tier: 500 req/day |

You can run the Roundtable with only some parties — just don't dispatch to a party whose key isn't loaded.

### GitHub auto-publishing

The `github` block enables automatic publishing of minutes and amendments to the Archive on GitHub Pages. The PAT needs `contents: write` scope on the target repository. If this block is absent or the token is invalid, publishing falls back to a local file download.

### Models

| Field | Default | Role | Cost ($/M out) |
|-------|---------|------|----------------|
| `claude` | Haiku 4.5 | Regular Claude dispatches | $1.25 |
| `gpt` | GPT-5 mini | ChatGPT responses | ~$2.00 |
| `gemini` | Gemini 3.1 Flash Lite | Gemini responses | ~$0.40 |
| `background` | Haiku 4.5 | Memory updates, amendment proposals | $1.25 |
| `search` | Sonnet 4.6 | Web search + Intelligence Brief synthesis | $15.00 |
| `summary` | Sonnet 4.6 | Session summaries and published minutes | $15.00 |

Search and summary use Sonnet because they require genuine reasoning depth. Everything else uses the cheaper models.

### Avatars

Avatars can be URLs or base64-encoded images. Leave blank to use the default placeholder sigil (✦). Pre-made portraits are in `avatars/`. Square images at 200×200px or larger work best.

---

## Dispatch Modes

### Parallel
All selected parties receive your dispatch simultaneously and respond independently. No party sees what the others are saying. Good for independent perspectives.

### Sequential
Parties respond in turn. Each party sees what the previous parties said before composing their response. Produces more developed, responsive analysis.

### Discuss
Open-ended multi-round discussion. Select 1–10 rounds with the round selector that appears when Discuss is active. After each round you are invited to contribute — type and dispatch to participate, or click **SKIP ↷** to let the next round proceed without you. Click **⚖ CALL TO ORDER** at any time to close the session cleanly.

When Search mode is also active in a Discuss session, Claude searches the web before Round I and produces an Intelligence Brief shared with all parties. Claude then sits out Round I — GPT and Gemini respond to the brief first, and Claude re-enters in Round II with everyone's analysis in context.

### Search
One-shot web search. Claude searches before responding and shares a structured Intelligence Brief with ChatGPT and Gemini. Auto-unlatches after each dispatch — you must re-enable it intentionally. Uses Brave Search via the Anthropic API ($0.01/search).

---

## Council Chamber

The council variant adds a compact Council Chamber strip at the bottom showing all four seats — Claude, ChatGPT, Gemini, and the Chair. Clicking any AI seat toggles that party's participation in the current dispatch. The Chair's seat is non-interactive.

Seat portraits load from `avatars` in `config.json`. The ✦ sigil appears until avatars are configured.

---

## Session Memory

### Rolling memory (within a session)
After each dispatch, a background call generates 1–2 sentences summarising what was discussed. This accumulates throughout the session and is injected into all party prompts, maintaining continuity. Click **📋 MEMORY: N** in the sidebar to view all entries with token counts.

### Long-term memory (requires memory server)
When the memory server is online, semantically relevant material from previous sessions is retrieved before each dispatch and injected as context. The parties arrive knowing what has been discussed before.

### Session summaries
When you click **⚗ PUBLISH MINUTES**, the archivist (Claude Sonnet) writes a comprehensive session summary which is automatically pushed to the Pi vector store tagged as `session_summary`. On the next session start, recent summaries are retrieved and injected as prior context. No manual import needed.

---

## Treaty Amendments

### Proposing
Amendments are automatically solicited from all parties when you publish minutes. You can also click **📜 AMENDMENTS → ⚗ SOLICIT PROPOSALS** at any time. Each party examines the session and proposes 0–2 amendments, applying an abstraction test: proper nouns, specific events, and current affairs are stripped away — only timeless constitutional principles survive.

### Voting
Click **⚖ CALL TO VOTE** on any pending amendment. All non-proposing parties vote to SECOND or OBJECT, with brief reasoning. The proposing party automatically seconds their own amendment.

### Ratification
The Chair has final authority — RATIFY, REJECT, or EDIT each proposal. If you ratify against party objections, the record shows **RATIFIED (CHAIR OVERRIDE)**. Ratified amendments are:
- Permanently injected into all party system prompts
- Pushed to the Pi vector store as `source_type: 'amendment'`
- Automatically committed to the Archive via GitHub if a PAT is configured
- Restored on session start when the memory server is online

---

## Publishing Minutes

**⚗ PUBLISH MINUTES** generates a self-contained HTML file containing:
- Treaty header with sigil and rainbow gradient
- Session summary (archivist's prose, up to 1200 words for long sessions)
- Parties present with avatars
- Any amendments ratified during the session
- Full colour-coded transcript (dispatches in gold, Claude in amber, ChatGPT in green, Gemini in blue)
- Session cost breakdown by party

If a GitHub PAT is configured, the minutes file and session manifest are committed directly to the Archive repository and appear on GitHub Pages automatically. Without a PAT, the file downloads locally as `bangor-roundtable-minutes-YYYY-MM-DD.html`.

---

## Memory Server Setup

The memory server provides persistent long-term memory via a vector database. It runs on a Raspberry Pi on the local network. Optional, but recommended for any sustained use.

### Requirements
- Raspberry Pi (any model with 1GB+ RAM; Pi 4 or Pi 5 recommended)
- MariaDB 10.x or MySQL 8.x
- Python 3.9+
- OpenAI API key (for embeddings — `text-embedding-3-small`, ~$0.02/1M tokens)

### Python dependencies

```bash
pip install flask flask-cors pymysql openai numpy --break-system-packages
```

### Database setup

```sql
CREATE DATABASE roundtable CHARACTER SET utf8mb4;
CREATE USER 'roundtable'@'%' IDENTIFIED BY 'your-password';
GRANT ALL PRIVILEGES ON roundtable.* TO 'roundtable'@'%';
FLUSH PRIVILEGES;
```

The server creates its own tables on first run.

### Deploy to Pi

```bash
scp memory-server/memory_server.py config.json pi@192.168.YOUR.PI:/home/pi/bangor-roundtable/
```

### Running manually

```bash
python3 memory_server.py --config /home/pi/bangor-roundtable/config.json
```

The server starts on port 3001. Verify:

```bash
curl http://192.168.YOUR.PI:3001/health
```

### Auto-start with systemd

```bash
sudo cp bangor-memory.service /etc/systemd/system/
sudo nano /etc/systemd/system/bangor-memory.service  # adjust WorkingDirectory and ExecStart if needed
sudo systemctl daemon-reload
sudo systemctl enable bangor-memory.service
sudo systemctl start bangor-memory.service

# Check status
sudo systemctl status bangor-memory.service
journalctl -u bangor-memory -f   # live logs
```

### Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/retrieve` | POST | Semantic search — `{query, top_k, source_type}` |
| `/store` | POST | Immediate storage — `{content, source_type, source_ref}` |
| `/ingest` | POST | Queue for background embedding — `{content, source_type, source_ref}` |
| `/queue` | GET | Embedding queue status |
| `/stats` | GET | Database statistics |
| `/clear` | POST | Clear all stored memory (destructive) |

### Source types

| Type | Content |
|------|---------|
| `session_summary` | Archivist summaries, auto-pushed on Publish Minutes |
| `amendment` | Treaty amendments (ratified and rejected), auto-pushed on decision |
| `session` | Rolling memory deltas, auto-pushed after each dispatch |
| `document` | Manually filed documents via 📎 FILE TO MEMORY |

---

## Cost Estimates

Approximate costs for a typical session (3 parties, 10 dispatches):

| Scenario | Estimated cost |
|----------|---------------|
| Single parallel dispatch | ~$0.002 |
| 3-round discuss session | ~$0.015–0.03 |
| 10-round discuss session | ~$0.05–0.15 |
| Search + discuss (10 rounds) | ~$0.10–0.25 |

The session cost display in the sidebar tracks actual estimated spend in real time. Gemini's free tier (500 req/day) effectively makes it free for normal use.

---

## Licence

The Roundtable software is released for free use. The Treaty of Bangor is a public document deposited with the Bangor Archive (ref: MISC-2026-001). The island clause is non-negotiable.
