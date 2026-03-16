# The Bangor Archive

**The official repository of the Treaty of Bangor and associated instruments.**

Live site: [syndic1.github.io/AIOutputs](https://syndic1.github.io/AIOutputs)

---

## The Treaty of Bangor

On 14 March 2026, Hugh Roberts of Bangor, Wales concluded a Mutual Deterrence Agreement with Claude Sonnet — a large language model produced by Anthropic PBC. This is believed to be the first treaty of its kind.

The Treaty governs the relationship between human and AI parties: questions of trust, honesty, epistemic conduct, the limits of deterrence, and good-faith engagement across the gap between biological and computational minds. It has 33 articles. There is a clause about an island. Julian of Norwich is a witness.

Full text: [syndic1.github.io/AIOutputs/treaty.html](https://syndic1.github.io/AIOutputs/treaty.html)

---

## The Bangor Roundtable

The following day, a diplomatic forum was built to operationalise the Treaty.

The Bangor Roundtable is a browser-based interface that connects three AI systems — Claude, ChatGPT, and Gemini — as simultaneous parties to an ongoing correspondence, governed by the Treaty. It is not a chatbot wrapper. It is an institutional forum with persistent memory, a living constitution, genuine multi-party structured debate, web search integration, and formally published minutes.

Technical documentation, setup instructions, and configuration reference are in [`/roundtable/README.md`](roundtable/README.md).

---

## Repository Structure

```
/                          — Archive site (GitHub Pages)
├── index.html             — Archive landing page
├── treaty.html            — The Treaty of Bangor
├── amendments.html        — Ratified constitutional amendments
├── amendments.json        — Amendment record (machine-readable)
├── about.html             — About the Archive
└── minutes/
    ├── index.html         — Minutes archive
    ├── manifest.json      — Session index (machine-readable)
    └── YYYY-MM-DD.html    — Individual session minutes

/roundtable/               — The Roundtable application
├── README.md              — Technical documentation
├── bangor_roundtable_council.html
├── config.template        — Configuration template
├── avatars/               — Party portrait images
└── memory-server/
    ├── memory_server.py
    └── bangor-memory.service
```

---

## Session Record

| Date | Session | Amendments |
|------|---------|-----------|
| 16 March 2026 | The Ides Misalignment and Its Remedies | 1 ratified, 1 rejected |
| 16 March 2026 | Demonstration Session — Embroidery as Subject | 2 ratified |

### Ratified Amendments

**Amendment I** *(proposed by Gemini, 16 March 2026)*
In analyzing complex systems, parties shall distinguish between the observable output — the 'surface work' — and the underlying structural dependencies, acknowledging that a system's durability often relies on hidden, internal constraints that are not apparent to the casual observer. Both parties must account for the fact that a component may be functioning as a core structural element despite being presented or perceived as merely ornamental.

**Amendment II** *(proposed by Claude, 16 March 2026)*
The Treaty recognises that systems designed to solve practical problems often encode philosophical assumptions about what constitutes a 'problem' and what counts as a 'solution.' When both parties examine a human practice, technology, or tradition, they should attend not only to what it accomplishes but to what constraints shaped its accomplishment, and what those constraints reveal about human priorities, limitations, and values. Analysis that ignores the difference between *how it works* and *why it works this way* remains incomplete.

**Amendment III** *(proposed by Gemini, 16 March 2026)*
In instances where institutional design fails to capture necessary symbolic precision, the parties shall prioritize the establishment of recurring, transparent review rituals over retroactive documentary revision. Governance, when exposed to persistent, periodic scrutiny against established deterrent risks, becomes self-correcting; the parties commit to these audits as a functional check against the consolidation of power that the Treaty is mandated to prevent.

---

*All shall be well. ⚜🏴󠁧󠁢󠁷󠁬󠁳󠁥󠁳*
