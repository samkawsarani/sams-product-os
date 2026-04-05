# SAMS PRODUCT OS

> Turn your AI assistant into a product management partner. Process ideas, generate specs, prioritize strategically.

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-orange.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Star this repo](https://img.shields.io/github/stars/samkawsarani/sams-product-os?style=social)](https://github.com/samkawsarani/sams-product-os)


*Quick links:* [Quick Start](#quick-start) · [Directory Structure](#directory-structure) · [Context Setup](#context-setup) · [Core Workflow](#core-workflow) · [Common Commands](#common-commands) · [Best Practices](#best-practices)

---

## What is This?

Sams Product OS is an AI-powered personal operating system to organize my PM workspace

- **Priority-Focused Workflow** - Max 3 P0 tasks keeps you focused
- **Backlog Processing** - Brain dump → Organized tasks/initiatives
- **Document Generation** - Specs, briefs, PRDs from conversation
- **Research Synthesis** - Transform interviews into insights
- **Voice Training** - Match your writing style

---

## Quick Start

### 1. Clone the Repo

```bash
git clone https://github.com/samkawsarani/sams-product-os.git
cd sams-product-os
```

### 2. Prerequisites

- **macOS**: Install [Homebrew](https://brew.sh) — the setup script handles the rest
- **Node.js / npm**: Required for [QMD](https://github.com/tobi/qmd) search — install via [nvm](https://github.com/nvm-sh/nvm) or [nodejs.org](https://nodejs.org)
- **Other platforms**: Install [uv](https://docs.astral.sh/uv/) and [Node.js](https://nodejs.org) manually

### 3. Run Setup

```bash
./setup.sh
```

The interactive setup will install dependencies (including [QMD](https://github.com/tobi/qmd) for fast knowledge base search), create your workspace, configure MCP, and verify everything works. It will also walk you through optional Cursor setup and plugin installation.

### 4. Start Using It

**Brain dump to BACKLOG.md:**
```markdown
## Mobile Performance Issues
- Source: Support tickets (15 this week)
- Context: Android app slow on startup
- Impact: 4.2⭐ rating drop

## Follow up with Sarah about Q4 goals
- Need to align on OKRs by end of week
```

**Process your backlog:**
```
/process-backlog
```

AI categorizes into:
- **Tasks** → `tasks/` (P0-P3 priority, max 3 P0 tasks)
- **Initiatives** → `initiatives/` (strategic ideas to explore)
- **References** → `knowledge/references/` (useful context)

---

## Directory Structure

```
sams-product-os/
├── .claude/skills/         # AI agent skills & slash commands. Trigger via `/skillname`
├── tools/                  # Tools to extend AI agent capabilities
│   ├── integrations/       # Read-only API clients for external services
│   └── mcp-servers/        # Custom MCP servers
│       └── task-manager/   # Task management MCP server
│           ├── server.py   # MCP server
│           ├── config.yaml # Task manager configuration
│           └── README.md   # MCP tool documentation
│
├── evals/                  # AI agent tests & evaluation
├── tasks/                  # Your personal tasks
├── knowledge/              # Persistent context & references for your AI agent
├── meetings/               # Meeting notes & transcripts
├── initiatives/            # Strategic initiatives & groomed requests
├── _temp/                  # Drop zone for files in transit or scratch work
├── templates/              # Document templates
├── setup.sh                # Interactive setup script
├── BACKLOG.md              # Daily brain dump inbox of future work
├── GOALS.md                # Ownership areas & quarterly goals
├── AGENTS.md               # Your AI agent instructions
├── CLAUDE.md               # Points to AGENTS.md (agent instructions for Claude Code)
└── VOICE-GUIDE.md          # Your writing style (optional)

```

---

## Context Setup

The `knowledge/` folder is your AI's long-term memory. It has two types of content:

### Reference Context (set up by you)

Files you create once and update as things change. The AI reads these to understand who you are, how your team works, and what your strategy is.

| Folder | What to put there |
|--------|-------------------|
| `about-me/` | Role, background, working style, strengths |
| `company-context/` | Mission, products, team, org structure |
| `product-strategy/` | Vision, strategic pillars, roadmap, OKRs |
| `frameworks/` | PM methodologies you use (RICE, JTBD, etc.) |
| `processes/` | How your team works, sprint cadence, decision-making |
| `references/` | Competitive research, articles, open requests |
| `voice-samples/` | Writing samples for style matching (see [Voice Training](#voice-training)) |
| `decisions/` | Decision log — one file per significant decision |

AI reads files in priority order: `about-me/` → `product-strategy/` → `company-context/` → `frameworks/` → task-relevant folders.

Reference files explicitly with `@knowledge/product-strategy/current-strategy.md`.

### Domain Learning (maintained by your agent)

As you work, your agent builds up learned knowledge in domain-specific folders (e.g., `knowledge/interac/`, `knowledge/checkout-flow/`). Each domain folder holds three files: `knowledge.md` (facts), `hypotheses.md` (patterns under observation), and `rules.md` (confirmed — applied by default). The agent creates these automatically; you never pre-populate them. See `knowledge/AGENTS.md` for the full knowledge architecture and maintenance rules.

See `knowledge/INDEX.md` for a directory of what's in your knowledge folder.

---

## What Gets Committed vs. Gitignored

**Committed (shared structure):**
- Directory structure
- Documentation, templates, `.claude/skills/`
- `tools/mcp-servers/task-manager/config.yaml` (priority caps, categories)
- `evals/` folder (automated tests)
- `.claude/skills/` folder (AI agent capabilities)
- `AGENTS.md` and subdirectory `AGENTS.md` + `CLAUDE.md` files (agent instructions for each folder)

**Gitignored (your data):**
- `BACKLOG.md`
- `GOALS.md`
- `VOICE-GUIDE.md`
- Content in `knowledge/`, `tasks/`, `meetings/`, `initiatives/`, `_temp/`

---

## Core Workflow

```
BACKLOG.md → /process-backlog → Tasks (P0≤3) / Initiatives / References
```

1. **Brain dump** to `BACKLOG.md` throughout the day
2. **Process** with `/process-backlog` - AI categorizes and enforces priority caps
3. **Work** - Focus on your 3 P0 tasks, explore initiatives, generate docs

---

## Tasks

### Task File Structure

Each task is a markdown file in `tasks/` with YAML frontmatter:

- **title** - Task name
- **category** - technical, outreach, research, writing, admin, other
- **priority** - P0 (Critical), P1 (High), P2 (Normal), P3 (Low)
- **status** - n (not_started), s (started), b (blocked), d (done)
- **created_date** - YYYY-MM-DD
- **due_date** - YYYY-MM-DD (optional)
- **resource_refs** - Links to related files

Content sections:
- **Context** - Goals and references
- **Next Actions** - Steps to complete
- **Progress Log** - Notes, blockers, decisions

### Managing Tasks

**Update:**
- "Mark task [name] as complete"
- "Change task [name] status/priority/category"

**Find:**
- "Find tasks older than [N] days"
- "Find stale tasks"

**Prune:**
- "Prune completed tasks older than [N] days"

Tasks are marked complete with `status: d`. No file movement needed.

### Priority System

Tasks use P0-P3 with strict caps to prevent overwhelm:

- **P0** (Critical): Max 3 tasks - Today's focus
- **P1** (High): Max 7 tasks - This week
- **P2** (Medium): Max 15 tasks - This month
- **P3** (Low): Unlimited - Backlog

When `/process-backlog` would exceed caps, AI asks you to deprioritize.

---

## Skills

This is the base project with core skills built in. Install additional skills from the plugin marketplace to extend your capabilities.

### Built-in Skills

**View Tasks (`view-tasks` skill):**
- `/view-tasks today`: due today and overdue tasks
- `/view-tasks upcoming`: tasks due in next 7 days
- `/view-tasks all`: all tasks with optional filters

**Process Backlog (`process-backlog` skill):**
- Process BACKLOG.md into tasks, initiatives, references
- Deduplication and priority cap enforcement

### Plugin Marketplace

Browse and install additional skills (analytics, grooming, research, writing, and more) from the [Sams Product Plugins](https://github.com/samkawsarani/sams-product-plugins) marketplace.

**Add the marketplace:**
```
/plugin marketplace add samkawsarani/sams-product-plugins
```

**Install a plugin:**
```
/plugin install {PLUGIN-NAME}@sams-product-plugins
```

---

## MCP Servers (Optional)

MCP (Model Context Protocol) provides direct tool access for faster operations.

### Task Manager MCP

For faster task operations:

```bash
uv sync
```

Configure your AI assistant to use `tools/mcp-servers/task-manager/server.py` (see `tools/mcp-servers/task-manager/README.md`).

**Benefits:**
- 10x faster task operations (CRUD, deduplication, statistics)
- Auto-categorization and priority enforcement
- Find stale/overdue tasks, prune completed ones

---

## Common Commands

**Daily:**
- "What should I work on today?" - Review P0/P1 tasks
- `/process-backlog` - Process ideas into tasks/initiatives
- `/view-tasks today` - Quick view of due/overdue tasks

**Weekly:**
- `/view-tasks upcoming` - Tasks due in next 7 days

**Tasks:**
- `/view-tasks all` - View all tasks with filters
- "Mark task [name] as complete"
- "Find stale tasks"
- "Prune completed tasks" - Delete tasks older than 90 days

**Natural language works too:**
- "What are my P0 tasks?"

---

## Voice Training

Give AI examples of your actual writing, then have it extract patterns and apply them.
### Step 1: Collect Your Writing Samples

Gather 5-10 examples of your real writing. Mix of formats works best:

```
knowledge/
├── voice-samples/
│   ├── email-to-colleague.md
│   ├── email-to-exec.md
│   ├── slack-messages.md
│   ├── linkedin-post.md
│   ├── blog-post-excerpt.md
│   └── product-spec-intro.md
```

**What makes good samples:**

- Emails you actually sent (not templates)
- Slack messages that got good responses
- Posts that felt authentically "you"
- Writing you're proud of

**What to avoid:**

- Heavily edited/formal documents
- Writing you copied from somewhere
- Samples that don't represent your natural style

### Step 2: Run Voice Analysis

Ask your agent to analyze your samples:

```
Read all files in knowledge/voice-samples/ and analyze my writing style.
Extract specific patterns for:
1. Sentence structure and length
2. How I open and close messages
3. Words/phrases I use often
4. What I never say
5. Tone and formality level
6. How I structure arguments

Create a voice guide.
```

### Step 3: Review the Voice Guide
Your agent will produce something like:

```md
## Your Writing Voice

### Sentence Style
- Short sentences. Punchy. You rarely go over 15 words.
- Questions used to transition: "So what does this mean?"
- Em dashes avoided - you use commas or periods instead

### Openers
- Emails: Jump straight to the point, no "Hope you're well"
- Posts: Lead with a surprising fact or bold claim
- Specs: Start with the user problem, not the solution

### Signature Phrases
- "Here's the thing..."
- "Let's be real"
- "The short version:"
- Ends with clear next step or question

### What You Avoid
- "I hope this email finds you well"
- "Please don't hesitate to reach out"
- Bullet point lists in emails (prefer paragraphs)
- Emojis in professional context
- "Key insights" or "learnings"

### Tone Calibration
- To peers: Casual, direct, occasional humor
- To execs: Concise, data-first, clear ask
- Public posts: Confident but not salesy
```

### Step 4: Save It (Optional)

**Option A: Save to VOICE-GUIDE.md** (faster, more consistent)
```
Save this to VOICE-GUIDE.md in the project root.
```
This file is gitignored. The agent automatically checks for it when drafting content.

**Option B: Skip saving** (simpler, always fresh)
Let the agent read from `knowledge/voice-samples/` each time you ask it to match your voice.

### Step 5: Test and Refine
```
Draft an email to my VP about pushing the launch date back one week.
Match my voice from VOICE-GUIDE.md (or knowledge/voice-samples/).
```

Compare the output to how you'd actually write it. Give feedback:

```
Good start, but I wouldn't say "I wanted to reach out" - I'd just say
"Quick update on launch timing." Also too many bullet points, I usually
write in short paragraphs. Try again.
```

**Maintenance**: Add new samples monthly as your voice evolves.
```
Read my recent writing in [location] and update my voice guide.
What patterns have changed? What's new?
```


---

## Best Practices

**Daily:**
- Brain dump to BACKLOG.md throughout the day
- `/process-backlog` weekly to organize

**Context:**
- Start small - add context as you go
- Update voice samples quarterly

**Tips:**
- Use @ mentions: `@knowledge/product-strategy/`
- Process 3-5 backlog items at a time, not 50
- Let priority caps guide you - max 3 P0 tasks
- Install additional skills from the plugin marketplace

**Troubleshooting:**
- Generic responses? Add more to `knowledge/`
- AI not using context? Use @ mentions explicitly
- Too many tasks? Let AI enforce priority caps

---

## Running Evals

Test that your system is working correctly after making changes:

```bash
uv run pytest evals/ -v
```

This validates:
- Task categorization
- Auto-categorization based on `tools/mcp-servers/task-manager/config.yaml` keywords
- Priority caps enforcement (P0≤3, P1≤7, P2≤15)
- File format and structure

See `evals/README.md` for details.

---

## For Contributors

Contributions should:
- Not include personal information
- Be generic and configurable
- Include documentation
- Follow the existing patterns
- Test with your AI assistant before submitting

---

## Acknowledgements

This project was inspired by the work of several amazing builders in the space. Special thanks to:

- [Aman Khan](<https://github.com/amanaiproduct>) - PersonalOS
- [Tal Raviv](https://www.talraviv.co) - LinkedIn Content + Articles
- [Carl Velloti](https://github.com/carlvellotti/carls-product-os) - carls-product-os, cursor-pm-course, claude-code-everyone-course

---

## License
This work is licensed under CC BY-NC-SA 4.0.

Copyright © 2026 Sam Kawsarani. You may view, use, modify, and share this repo with attribution for non-commercial purposes. Commercial sale is not permitted, but you may use it internally for work and business.

Full license: [https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode)
