---
name: process-backlog
model: sonnet
description: Picks this week's priorities from the backlog. Reads BACKLOG.md + GOALS.md, recommends top 3–5 items with goal-alignment rationale, confirms with user, then writes ACTIVE.md. Invoked via /process-backlog or "triage the backlog", "what should I work on this week", "plan my week", or "organize my brain dump".
allowed-tools: Read, Write, Bash(qmd *)
argument-hint:
---

## Context

- Backlog: `tasks/BACKLOG.md`
- Active: `tasks/ACTIVE.md`
- Goals: `GOALS.md`
- Today's date: $TODAY

## Workflow

### Step 1: Read

Read `tasks/BACKLOG.md`, `GOALS.md`, and `tasks/ACTIVE.md` in parallel.

### Step 2: Score and recommend

For each backlog item, assess:
- **Goal alignment** — does it map to a current goal in `GOALS.md`? (strongest signal)
- **Urgency** — is there a deadline, blocker, or stakeholder waiting?
- **Known blockers** — is it waiting on someone else? (deprioritize)

Pick top 3–5 items. Flag any item with no clear goal alignment — surface it but don't block on it.

### Step 3: Present

Show recommendations in a simple table:

| # | Item | Goal | Why now |
|---|------|------|---------|
| 1 | ... | ... | ... |

Include any flagged items below with a note: "No clear goal match — worth doing anyway?"

Ask: "Does this work for the week, or do you want to swap anything?"

**Wait for confirmation before writing.**

### Step 4: Write ACTIVE.md

Update `tasks/ACTIVE.md` with confirmed items:

```markdown
# Active — Week of [DATE]
**Focus:** [one-line theme for the week]

## In Progress

## Up Next
- [ ] [item 1]
- [ ] [item 2]
...

## Waiting On

| Who | What | Since | Next step |
|-----|------|-------|-----------|
```

Move confirmed items under **Up Next** unless the user specified one as In Progress.

### Step 5: Wrap-up

Invoke the `wrap-up` skill. Announce it: "Running wrap-up."

---

## Key Reminders

- **Only `tasks/ACTIVE.md` gets written** — no other files created
- **Goal-linking is a signal, not a gate** — flag mismatches, don't block
