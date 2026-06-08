---
name: weekly-review
model: sonnet
description: Reviews the past week, checks goal progress, identifies blockers and stalled work, and plans next week's priorities. Internal reflection tool. Invoked via /weekly-review or "review my week", "plan next week", or "what did I accomplish this week".
argument-hint: '[optional: "quick" for condensed version]'
---

## Context

Today's date: $TODAY

If user says "quick" → use Quick Version.

---

## Step 0: Determine Date Range

Calculate the reporting period:
- If today is Monday, the past week = previous Monday through yesterday (Sunday)
- Otherwise, the past week = most recent Monday through most recent Sunday
- Display the date range in all section headers

---

## Step 1: Review Completed Work

1. Read `tasks/TASKS.md`
2. Find all checkboxes marked done: `- [x]`
   - Format varies — a task might be a heading with checkboxes under it, a standalone checkbox, or a mix
   - Use context to determine what "done" means for each item; don't rely on nesting structure
3. Items still `- [ ]` = active or not yet started

**Output format:**
```
## This Week's Completed Work ([Date Range])

### Shipped
- [Item that went live or was delivered externally]

### Completed (internal)
- [Item that was finished internally]

### Still In Progress
- [Task] — [brief status from context]

**Highlights:**
- [Major win or milestone]
- [Concerning pattern or gap, if any]
```

- If nothing is checked off in the Active section, say so and ask the user to call out what got done before proceeding
- Distinguish Shipped (external delivery) from Completed (internal) based on task context

---

## Step 2: Check Goal Progress

1. Find and read `GOALS.md`
2. For each goal, match completed and in-progress work from Step 1 to assess progress
3. Flag goals with no activity this week

**Output format:**
```
## Quarterly Goal Progress

### Goal: [Goal Name]
**Status:** On Track | At Risk | Behind

**This week:**
- Shipped/completed: [items]
- In progress: [items]
- No activity: [yes/no]

**Velocity:** [Assessment — "Ahead of schedule", "Need to accelerate", etc.]
```

---

## Step 3: Identify Blockers and Stalled Work

1. Read `tasks/TASKS.md` Waiting On table
2. Flag any items that have been waiting more than 7 days (compare "Since" date to today)
3. Flag any In Progress items that seem stale (check if they've been in the list for a while without movement — ask user if unclear)

**Output format:**
```
## Blockers & Stalled Work

### Waiting On (7+ days)
**[Who]** — [What] (since [date], [N] days)
- Impact: [Goal affected]
- Recommended action: [Nudge / escalate / find workaround]

### Stalled In Progress
**[Task]** — appears inactive
- Recommended: [Continue / Deprioritize / Break down / Ask for help]
```

- Skip section if nothing is blocked or stalled

---

## Step 4: Plan Next Week

1. Read `tasks/TASKS.md` — show Active section (Up Next/In Progress) for carryover, then present backlog items by topic header for new picks
2. Consider goal alignment and any carryover from this week

**Output format:**
```
## Next Week's Priorities

### Carry Over (from this week)
- [In Progress items that will continue]

### From Backlog — Pick Your Focus
[Show backlog items by topic header, so user can choose what to pull into the Active section]

**Capacity check:** [Realistic / Overloaded / Light week based on calendar if available]

**Recommendations:**
- [Specific suggestion based on goals/blockers]
- [Risk or opportunity to flag]
```

---

## Step 5: Archive This Week

1. Ask once: "Ready to archive this week? I'll log completed work and reset the Active section for next week."
2. If yes, do both in one step:
   - Write a new "Week of [Date Range]" section to `tasks/_archived/YYYY-MM.md` (create file if needed, using `templates/archive-template.md`)
   - Clear all `[x]` completed items from `## Active` in TASKS.md and reset In Progress, Up Next, and Waiting On for next week
3. Report what was archived and what the new Active section looks like.

**Never auto-archive without the single confirmation.**

---

## Quick Version

If user wants condensed output, combine all 5 steps into:

```
## Week in Review ([Date Range])

**Completed:** [Key items shipped or finished]
**Goal status:** [Goal A] on track, [Goal B] at risk
**Blockers:** [N days waiting on X] / [Stalled: Y]
**Next week focus:** [Top 2-3 priorities from backlog]
**Watch out for:** [Key risk or recommendation]
```

---

## Step 6: Re-index

Run `qmd update && qmd embed` to reindex any notes, retrospectives, or archive files written during this session.

---

## Best Practices

- Emphasize goal alignment over task quantity
- Flag capacity constraints proactively
- Make tradeoffs explicit (what are we NOT doing?)

---

## Final Step: Wrap-Up

Invoke the `wrap-up` skill.
