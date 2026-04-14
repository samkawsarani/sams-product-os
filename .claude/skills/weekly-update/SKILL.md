---
name: weekly-update
model: sonnet
description: Drafts a stakeholder update email summarizing project progress, blockers, and next week's priorities. Uses Linear projects and initiatives if MCP is connected, otherwise falls back to tasks/ACTIVE.md. Invoked via /weekly-update or "draft stakeholder update", "write my Friday update", "weekly email".
allowed-tools: Glob, Read, Write, Bash(qmd *), mcp__linear__*
argument-hint: '[optional: name or role of recipient, e.g. "for CEO" or "for board"]'
---

## Context

- Today's date: $TODAY
- Voice guide: `VOICE-GUIDE.md` (if present)
- Stakeholder preferences: `knowledge/people/`
- Goals: `GOALS.md`
- Past updates: `knowledge/references/stakeholder-updates/` (if present)

---

## Step 1: Identify Audience

If the user specified a recipient (e.g. "for CEO", "for board"), note it.
Otherwise ask: "Who is this update for?" — one person or a group (e.g. leadership team, board, cross-functional leads).

Read `knowledge/people/` for any matching stakeholder preference files. Note what each person cares about and what to avoid.

---

## Step 2: Gather Progress Data

**Try Linear first.** If Linear MCP tools are available:
- Pull **project status** — name, status (on track / at risk / behind), % complete, owner
- Pull **initiative status** — name, health, which projects roll up under it
- Note any projects that slipped, were completed, or changed status this week

**If Linear is not available**, fall back to:
- Read `tasks/ACTIVE.md` — extract completed (`- [x]`), in progress (`- [ ]`), and Waiting On items
- Read `projects/` — scan any active project briefs for current status

Also read:
- `GOALS.md` — map progress to quarterly goals
- `meetings/` — scan recent meeting notes for relevant decisions or outcomes worth surfacing

---

## Step 3: Assess Status

For each active project or initiative:
- **On Track** — progressing as expected
- **At Risk** — may slip without action
- **Blocked** — waiting on something external

Flag anything that needs stakeholder awareness or a specific ask.

---

## Step 4: Draft the Update

Keep it under 500 words. Lead with what matters most to the audience.

Use this structure:

```
Subject: Product Update — Week of [Date]

**TL;DR**
- [Most important outcome or milestone this week]
- [Key blocker or risk, if any]
- [Top focus next week]

**Progress**
[Initiative or project]: [Status] — [1-line summary of movement]
[Initiative or project]: [Status] — [1-line summary of movement]

**Metrics** *(if available)*
[Metric]: [Current] ([change vs last week], target: [X])

**Blockers & Risks**
[Blocker] — [Proposed next step or ask]

**Next Week**
- [Priority 1, tied to goal]
- [Priority 2, tied to goal]
- [Priority 3]
```

Adjust tone and depth based on:
- Audience (CEO = concise/strategic, CTO = include technical context, board = OKR-level)
- `VOICE-GUIDE.md` if present
- Past updates in `knowledge/references/stakeholder-updates/` for consistency

---

## Step 5: Review and Save

Present the draft to the user. Ask:
- "Any changes before I save this?"

If approved, save to `knowledge/references/stakeholder-updates/YYYY-MM-DD.md` for future tone reference.

---

## Key Reminders

- **Metrics over activity** — "Activation up 3% WoW" beats "worked on onboarding"
- **Specific asks** — if you need something, name it explicitly
- **Don't hide problems** — blockers go in the body, not a footnote
- **OKR-connected** — every priority should tie back to a goal from `GOALS.md`
- **Under 500 words** — leadership skims
