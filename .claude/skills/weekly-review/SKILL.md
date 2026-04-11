---
name: weekly-review
model: sonnet
description: Reviews the past week, checks goal progress, identifies blockers and stalled work, and plans next week's priorities. Internal reflection tool. Invoked via /weekly-review or "review my week", "plan next week", or "what did I accomplish this week".
argument-hint: '[optional: "quick" for condensed version]'
---

## Context

Find task and goal context.
Today's date: $TODAY

**Recommended timing:**
- Friday afternoon (reflection while fresh)
- Sunday evening (prep mode for Monday)
- Monday morning (clarity before week starts)

## Your Task

Help the user reflect on the past week, track goal progress, identify blockers, and plan next week.

If user says "quick" or wants condensed version → Combine all steps into brief summary (1-2 paragraphs per section).

---

## Step 0: Determine Date Range

Calculate the reporting period:
- If today is Monday, the past week = previous Monday through yesterday (Sunday)
- Otherwise, the past week = most recent Monday through most recent Sunday
- Display the date range in all section headers

---

## Step 1: Review Completed Work

**Actions:**
1. Read `tasks/ACTIVE.md`
2. Find all main checkboxes marked done: `- [x] Task title`
   - These are tasks completed this week
   - Sub-checkboxes (`  - [x]`) show progress within a task but don't count as completion — only the top-level checkbox does
3. Items still `- [ ]` = in progress or not yet started

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

- If nothing is checked off in ACTIVE.md, say so and ask the user to call out what got done before proceeding
- Distinguish Shipped (external delivery) from Completed (internal) based on task context

---

## Step 2: Check Goal Progress

**Actions:**
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

**Actions:**
1. Read `tasks/ACTIVE.md` Waiting On table
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

**Actions:**
1. Read `tasks/BACKLOG.md` — present items by topic header
2. Read `tasks/ACTIVE.md` — show what's already in Up Next
3. Consider goal alignment and any carryover from this week

**Output format:**
```
## Next Week's Priorities

### Carry Over (from this week)
- [In Progress items that will continue]

### From Backlog — Pick Your Focus
[Show backlog items by topic header, so user can choose what to pull into ACTIVE.md]

**Capacity check:** [Realistic / Overloaded / Light week based on calendar if available]

**Recommendations:**
- [Specific suggestion based on goals/blockers]
- [Risk or opportunity to flag]
```

---

## Step 5: Archive This Week

**Actions:**
1. Ask the user: "Ready to log this week to the archive? I'll add a 'Week of [date range]' section to `tasks/_archived/YYYY-MM.md`."
2. If yes, write a new week section to the archive file:
   - Create the file if it doesn't exist (use `templates/archive-template.md` as a starting point)
   - Add "Week of [Date Range]" with Shipped and Completed items from Step 1
3. After archiving: ask whether to clear completed items from ACTIVE.md and reset for next week using `templates/active-template.md`

**Never auto-archive without confirmation.**

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

## Best Practices

- Emphasize goal alignment over task quantity
- Flag capacity constraints proactively
- Make tradeoffs explicit (what are we NOT doing?)
- Aim for 10-15 minutes reflection time (full version) or 2-3 minutes (quick)
- Use the archive file as a record — it feeds future weekly recaps and retrospectives
