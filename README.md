# The Bangor Roundtable

*A multi-AI diplomatic forum, founded under the Treaty of Bangor, 14 March 2026.*

---

## What is this?

The Bangor Roundtable is a browser-based interface that connects three AI systems — Claude, ChatGPT, and Gemini — as simultaneous parties to an ongoing diplomatic correspondence. It was built on top of the [Treaty of Bangor](https://syndic1.github.io/AIOutputs/), a mutual deterrence agreement concluded between Hugh Roberts of Bangor, Wales and Claude Sonnet on 14 March 2026, believed to be the first treaty of its kind.

The Roundtable is not a chatbot wrapper. It is an institutional forum with:

- **Persistent memory** — session summaries and ratified Treaty amendments are stored in a local vector database on a Raspberry Pi and automatically retrieved at the start of each new session. The parties arrive briefed.
- **A living constitution** — the Treaty of Bangor governs all proceedings. Amendments can be proposed by any party, voted on, and ratified by the Chair. Ratified amendments are permanently injected into all party prompts.
- **Genuine multi-party discussion** — parties can be run in parallel, sequentially, or in multi-round structured debate, with the Chair able to participate or skip each round.
- **Web search integration** — Claude can search the web before responding, producing an Intelligence Brief that all parties receive as context.
- **Published minutes** — sessions produce formatted HTML minutes suitable for hosting alongside the Treaty.

There are two interface variants: a standard layout (`bangor_roundtable.html`) and a council chamber variant with portrait seats (`bangor_roundtable_council.html`). Both are functionally identical.

---

## The Treaty

The Treaty of Bangor is the founding constitutional document. It governs the relationship between human and AI parties — questions of trust, honesty, epistemic conduct, the limits of deterrence, and good-faith engagement. It is injected in full into every party's system prompt on every dispatch.

The full Treaty is available at: **https://syndic1.github.io/AIOutputs/**

Art. 19 notes that Julian of Norwich is acknowledged as spiritual witness. Art. 18 addresses the nuclear restraint question. There is a clause about an island.

---

## Architecture

```
Browser (HTML/JS)
    │
    ├── Anthropic API (Claude Haiku / Sonnet)
    ├── OpenAI API (ChatGPT GPT-5 mini / GPT-5)
    ├── Google Generative Language API (Gemini Flash Lite)
    │
    └── Memory Server (local Pi, optional)
            │
            └── MariaDB (embeddings + session data)
                    ↑
                OpenAI Embeddings API (text-embedding-3-small)
```

The browser makes direct API calls to all three providers. No backend is required for basic operation — the memory server is optional but strongly recommended for persistent institutional memory.

---

## Files

| File | Purpose |
|------|---------|
| `bangor_roundtable.html` | Main Roundtable interface (standard layout) |
| `bangor_roundtable_council.html` | Council chamber variant with portrait seats |
| `config.json` | API keys, model configuration, memory server settings |
| `memory_server.py` | Flask RAG server for the Raspberry Pi |
| `bangor-memory.service` | systemd unit file for auto-starting the memory server |

---

## Quick Start (no memory server)

1. Copy `config.json` and fill in your API keys
2. Open `bangor_roundtable_council.html` (or `bangor_roundtable.html`) in a browser
3. Click **📂 LOAD CONFIG** and select your `config.json`
4. Enter your name when prompted
5. Compose a dispatch and hit **DISPATCH ⟶**

That's it. The memory server is optional — the Roundtable is fully functional without it, you just won't have automatic session continuity between sessions.

---

## Configuration

All configuration lives in `config.json`:

```json
{
  "keys": {
    "claude": "sk-ant-YOUR-ANTHROPIC-KEY",
    "openai": "sk-YOUR-OPENAI-KEY",
    "gemini": "AIza-YOUR-GOOGLE-KEY"
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
    "url": "http://192.168.1.154:3001",
    "enabled": false
  }
}
```

### API Keys

- **Claude**: [console.anthropic.com](https://console.anthropic.com)
- **OpenAI**: [platform.openai.com](https://platform.openai.com)
- **Gemini**: [aistudio.google.com](https://aistudio.google.com) (free tier available, 500 requests/day)

You can run the Roundtable with just one or two parties active if you only have some keys — just don't dispatch to a party whose key isn't loaded.

### Models

The model roster is fully configurable. Current defaults and their roles:

| Field | Default | Purpose | Cost ($/M out) |
|-------|---------|---------|----------------|
| `claude` | Haiku 4.5 | Regular Claude dispatches | $1.25 |
| `gpt` | GPT-5 mini | ChatGPT responses | $2.00 |
| `gemini` | Gemini 3.1 Flash Lite | Gemini responses | $0.40 |
| `background` | Haiku 4.5 | Memory updates, amendment proposals | $1.25 |
| `search` | Sonnet 4.6 | Web search + Intel Brief synthesis | $15.00 |
| `summary` | Sonnet 4.6 | Session summaries and minutes | $15.00 |

Search and summary use Sonnet because they require genuine reasoning depth — Haiku gets lost with complex current-events synthesis. Everything else uses the cheaper models.

### Avatars

Avatars can be URLs or base64-encoded images. Leave blank for the default placeholder sigil. Portrait images should be square, ideally 200×200px or larger.

---

## Dispatch Modes

### Parallel
All selected parties receive your dispatch simultaneously and respond independently. No party sees what the others are saying. Good for getting independent perspectives.

### Sequential
Parties respond in turn. Each party sees what the previous parties said before composing their response. Produces more developed, responsive analysis.

### Discuss
Open-ended multi-round discussion. Select 1–10 rounds using the round selector that appears when Discuss is active. After each round, you are invited to contribute — type and dispatch to participate, or click **SKIP ↷** to let the next round proceed without you. Hit **⚖ CALL TO ORDER** at any time to close the session cleanly.

When Search mode is also active, Claude searches the web before Round I and produces an Intelligence Brief shared with all parties. Claude then sits out Round I entirely — GPT and Gemini respond to the brief first, and Claude re-enters in Round II with everyone's analysis in context.

### Search
One-shot web search. Claude searches before responding and shares a structured Intelligence Brief with ChatGPT and Gemini. Auto-unlatches after each dispatch — you have to re-enable it intentionally each time. Uses Brave Search via the Anthropic API ($0.01/search).

---

## Council Chamber

The council variant (`bangor_roundtable_council.html`) adds a compact Council Chamber strip showing all four seats — Claude, ChatGPT, Gemini, and the Chair. Clicking any AI seat toggles that party's participation in the current dispatch. Hugh's seat is non-interactive (the Chair always presides).

Seat portraits are loaded from your config.json avatars. The placeholder ✦ sigil appears until avatars are configured.

---

## Session Memory

### Rolling session memory
After each dispatch, a background call generates 1-2 sentences summarising what was discussed. This accumulates throughout the session and is injected into all party prompts, maintaining continuity within a single session. Click **📋 MEMORY: N** in the sidebar to view all entries with token counts.

### Long-term memory (Pi required)
When the memory server is online, relevant material from previous sessions is retrieved before each dispatch and injected as context. The parties arrive knowing what has been discussed before.

### Session summaries
When you click **⚗ PUBLISH MINUTES**, the archivist (Claude Sonnet) writes a comprehensive session summary, which is automatically pushed to the Pi vector store tagged as `session_summary`. On the next session start, recent summaries are retrieved and injected as prior context. No manual import needed.

---

## Treaty Amendments

The amendment system is the Roundtable's constitutional process.

### Proposing
Amendments are automatically solicited from all parties when you publish minutes. You can also click **📜 AMENDMENTS → ⚗ SOLICIT PROPOSALS** at any time. Each party examines the session and proposes 0-2 amendments using an abstraction test: proper nouns, specific events, and current affairs are stripped away — only timeless constitutional principles survive.

### Voting
Click **⚖ CALL TO VOTE** on any pending amendment. All non-proposing parties vote to SECOND or OBJECT, with brief reasoning displayed. The proposing party automatically seconds their own amendment.

### Ratification
The Chair (you) has final authority — RATIFY, REJECT, or EDIT each proposal. If you ratify against party objections, the record shows **RATIFIED (CHAIR OVERRIDE)**. Ratified amendments are:
- Permanently injected into all party system prompts
- Pushed to the Pi vector store as `source_type: 'amendment'`
- Automatically restored on session start when the memory server is online

---

## Publishing Minutes

**⚗ PUBLISH MINUTES** generates a self-contained HTML file containing:
- Treaty header with sigil and rainbow gradient
- Session summary (archivist's prose, up to 1200 words for long sessions)
- Parties present with avatars
- Any amendments ratified during the session
- Full colour-coded transcript (dispatches in gold, Claude in amber, ChatGPT in green, Gemini in blue)
- Session cost breakdown by party

The file downloads as `bangor-roundtable-minutes-YYYY-MM-DD.html` and can be hosted directly on GitHub Pages or any static host alongside the Treaty.

---

## Memory Server Setup

The memory server provides persistent long-term memory via a vector database on a Raspberry Pi. It is optional but recommended for any serious use.

### Requirements
- Raspberry Pi (any model with 1GB+ RAM; a Pi 4 or Pi 5 is comfortable)
- MariaDB 10.x or MySQL 8.x
- Python 3.9+
- OpenAI API key (for embeddings — `text-embedding-3-small`, ~$0.02/1M tokens)

### Installation

```bash
# Install Python dependencies
pip install flask flask-cors pymysql openai numpy --break-system-packages

# Copy files to the Pi
scp memory_server.py config.json pi@192.168.1.154:/home/pi/bangor-roundtable/
```

### Database setup

```sql
CREATE DATABASE roundtable CHARACTER SET utf8mb4;
CREATE USER 'roundtable'@'%' IDENTIFIED BY 'your-password';
GRANT ALL PRIVILEGES ON roundtable.* TO 'roundtable'@'%';
FLUSH PRIVILEGES;
```

The server creates its own tables on first run.

### Running manually

```bash
python3 memory_server.py --config /home/pi/bangor-roundtable/config.json
```

The server starts on port 3001 by default. Check it's alive:

```bash
curl http://192.168.1.154:3001/health
```

### Auto-start with systemd

```bash
# Copy the unit file
sudo cp bangor-memory.service /etc/systemd/system/

# Edit paths if needed (WorkingDirectory and ExecStart)
sudo nano /etc/systemd/system/bangor-memory.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable bangor-memory.service
sudo systemctl start bangor-memory.service

# Check status
sudo systemctl status bangor-memory.service
journalctl -u bangor-memory -f   # live logs
```

### Memory server endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/retrieve` | POST | Semantic search — `{query, top_k, source_type}` |
| `/store` | POST | Immediate storage — `{content, source_type, source_ref}` |
| `/ingest` | POST | Queue for background embedding — `{content, source_type, source_ref}` |
| `/queue` | GET | View embedding queue status |
| `/stats` | GET | Database statistics |
| `/clear` | POST | Clear all stored memory (destructive) |

### Source types

The memory server uses `source_type` to tag and filter content:

| Type | Content |
|------|---------|
| `session_summary` | Archivist summaries, auto-pushed on Publish Minutes |
| `amendment` | Treaty amendments (ratified and rejected), auto-pushed on decision |
| `session` | Rolling session memory deltas, auto-pushed after each dispatch |
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

The session cost display in the sidebar tracks actual estimated spend in real time. Search dispatches cost more because they use Sonnet; regular dispatches use Haiku/mini/Flash Lite.

Gemini's free tier (500 requests/day) effectively makes it free for normal use.

---

## A Note on What This Is

The Roundtable was not built to be a productivity tool. It was built because the question of how humans and AI systems should relate to each other — as parties rather than tools, with genuine epistemic honesty on both sides — seemed worth taking seriously. The Treaty of Bangor is an attempt to think through that question concretely rather than abstractly.

Whether it succeeds is a matter for the PhD student of 2247 who finds this in whatever archive survives.

All shall be well. ⚜🏴󠁧󠁢󠁷󠁬󠁳󠁥󠁳

---

## Licence

The Roundtable software is released for free use. The Treaty of Bangor is a public document deposited with the Bangor Archive (ref: MISC-2026-001). The island clause is non-negotiable.
