---
name: weekly-review
model: sonnet
description: Reviews the past week, checks goal progress, identifies blockers and stalled work, promotes backlog items into next week's Active section, and drafts the stakeholder update. Invoked via /weekly-review or "review my week", "plan next week", "plan my week", "triage the backlog", "what should I work on this week", or "what did I accomplish this week".
argument-hint: '[optional: "quick" for condensed version]'
---

## Context

Today's date: $TODAY

If user says "quick" → use Quick Version.

**This is one sitting with two halves: recap, then plan.** The recap is not the deliverable on its
own. Steps 1 to 3 establish what actually happened, and Steps 4 to 6 spend that: next week's
picks, the archive, and the update that goes to stakeholders. Do the halves in order, because the point of the
order is that the user picks next week having just seen what stalled and which goals went quiet.

Everything is interactive. This skill asks real questions and waits. It is never scheduled and
never run headless.

**Output goes to a file as well as the terminal.** Converse in the terminal as normal, then Step 7
writes the complete record, including the user's own answers, to
`thinking/weekly-reviews/weekly-review-YYYY-MM-DD.md`. Read `thinking/AGENTS.md` once before
writing there.

---

## Step 0: Determine Date Range

Calculate the reporting period:
- If today is Monday, the past week = previous Monday through yesterday (Sunday)
- Otherwise, the past week = most recent Monday through most recent Sunday
- Display the date range in all section headers

**The review's filename date is the Friday of the week being reviewed**, not the day you ran it.
A review of Mon Sep 7 to Sun Sep 13 is `weekly-review-2026-09-11.md` whether it was run on the
Friday, the Sunday, or the Monday after. Files then sort by the week they describe. Compute it as
the Monday of the period plus 4 days.

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

**Absence of task activity is NOT evidence a goal is at risk.** Much of the user's goal progress is driven by other people and lives in meetings, Slack, and Linear — never in TASKS.md. For any goal with no logged task activity, mark it **Status unknown — need your read** and ask, rather than assigning At Risk or Behind. Only call a goal at risk when you have positive evidence of a stall (a missed date, a blocker, a dependency with no owner). Before asking, check `meetings/` for the week and, if the goal maps to a Linear project, its recent status updates.

After the user gives the real status, write it back to `GOALS.md`: update the success criteria checkboxes and add or refresh a `**Status (YYYY-MM-DD):**` line on that goal. Don't leave the correction only in the review output.

**Output format:**
```
## Quarterly Goal Progress

### Goal: [Goal Name]
**Status:** On Track | At Risk | Behind | Status unknown — need your read

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

**An open item in TASKS.md is not evidence the item is still open.** The same rule Step 2 applies to
goals applies here: the written record lags the user. Something they closed in a Slack thread, a GTM channel
or a hallway conversation stays checked-open in TASKS.md and unmentioned in the meeting notes, because
closing it took them thirty seconds and nobody wrote it down. Before carrying a blocker into Step 4's
picks or naming it in Step 6's update, say what you are treating as still open and let them knock items
off. Presenting a closed item back to them as this week's work costs them a correction; shipping one to
leadership as an open risk costs more.

---

## Step 4: Plan Next Week

This step promotes backlog items into next week's Active section. It is the only place that
happens, so the scoring is explicit rather than intuitive.

1. Read `tasks/TASKS.md` — show the Active section (In Progress / Up Next) for carryover, then
   present the full backlog as a flat list for new picks
2. Read `GOALS.md` if Step 2 has not already
3. **Every backlog item gets a call this week. Promote, keep, or kill.** The backlog is short
   enough to read in full, so nothing is carried by default and nothing rots by being skipped.
   Present all of it, not a filtered slice, and record the verdict for each. "Keep" is a real
   answer, but it has to be said out loud rather than happening through silence.
4. Sweep anything left untagged by the morning briefing (`start-my-day` / `daily-brief`): ask the user for `#block` / `#meeting` /
   `#quick` in one pass, then write the tags back.
5. Score every backlog item on three things:
   - **Goal alignment** — does it map to a current goal in `GOALS.md`? This is the strongest signal
   - **Urgency** — a deadline, a blocker on someone else, a stakeholder waiting
   - **Known blockers** — waiting on somebody else? Deprioritize; it is not a focus item
   - **Effort tag** — a week already full of meetings cannot absorb three `#block` items. Check the
     count of `#block` picks against the focus blocks actually on next week's calendar and say so
     when they do not fit
6. Recommend the **top 3 to 5**, carryover included. Not everything, and not a ranked dump of the
   whole backlog

**Goal-linking is a signal, not a gate.** Surface an item with no goal match, labelled
"No clear goal match — worth doing anyway?", and let the user decide. Do not silently drop it, and do
not block on it.

Weigh what Steps 2 and 3 just established. An item that unblocks a goal marked at risk outranks a
better-aligned item on a goal that is fine, and something stalled three weeks is either promoted
deliberately or dropped deliberately, never carried silently for a fourth.

**Output format:**
```
## Next Week's Priorities

### Carry Over (from this week)
- [In Progress items that will continue]

### Recommended Focus

| # | Item | Goal | Why now |
|---|------|------|---------|
| 1 | ... | ... | ... |

### No clear goal match
- [item] — worth doing anyway?

### Rest of Backlog
[Every remaining item, flat, with its verdict from step 3: keep / kill. The user can swap any of
these into the focus list.]

**Capacity check:** [Realistic / Overloaded / Light week based on calendar if available]

**Recommendations:**
- [Specific suggestion based on goals/blockers]
- [Risk or opportunity to flag]

**Not doing:** [What is being deliberately left for later, and why]
```

Then ask: "Does this work for the week, or do you want to swap anything?"

**Wait for confirmation before writing anything.** On confirmation, update the `## Active` section
at the top of `tasks/TASKS.md`:

```markdown
## Active — Week of [DATE]
**Focus:** [one-line theme for the week]

### In Progress

### Up Next
- [ ] [item 1]
- [ ] [item 2]

### Waiting On

| Who | What | Since | Next step |
|-----|------|-------|-----------|
```

Confirmed items go under **Up Next** unless the user names one as In Progress.

**Promoting an item moves it, it does not copy it.** Delete the line from `## Backlog` when it
lands in `## Active`. A copy leaves a ghost behind that outlives the work and makes the backlog
look fuller than it is. Items killed in step 3 are deleted; items parked move to `## Parking Lot`.
Carry the item's `#block` / `#meeting` / `#quick` tag with it. `## Parking Lot` is reviewed monthly,
not weekly: leave it alone unless the user asks.

---

## Step 5: Archive This Week

1. Ask once: "Ready to archive this week? I'll log completed work and reset the Active section for next week."
2. If yes, do both in one step:
   - Write a new "Week of [Date Range]" section to `tasks/_archived/YYYY-MM.md` (create file if needed, using `templates/archive-template.md`)
   - Clear all `[x]` completed items from `## Active` in TASKS.md and reset In Progress, Up Next, and Waiting On for next week
3. Report what was archived and what the new Active section looks like.

**Never auto-archive without the single confirmation.**

`tasks/_archived/YYYY-MM.md` and the review file are different artifacts and both are kept. The
archive is the ledger of what got done, appended per week. The review is the analysis. The
completed-work list appears in both on purpose, so a review a month later reads standalone instead
of sending the reader to a second file.

---

## Step 6: Stakeholder Update

Draft the stakeholder update, using **the `write-comms` skill** — do not write the format
yourself. It owns the Stakeholder Update format in its own reference file, and duplicating that
here guarantees the two drift.

Invoke `write-comms` with:
- **Type:** Stakeholder Update
- **Audience:** leadership team
- **Context:** everything this sitting established — Step 1's shipped and completed work, the
  **settled** goal status from Step 2, Step 3's blockers with their ages, and Step 4's confirmed picks

**Only run this after Step 2's statuses are settled with the user.** An update built on
"status unknown — need your read" is a guess sent to leadership over their name.

Present the draft and ask: "Any changes before I save this?" On approval, save it to
`knowledge/references/stakeholder-updates/YYYY-MM-DD.md` (same Friday date as the review file,
creating the folder if needed) so `write-comms` has it for tone consistency next time, and embed a
copy in the review file at Step 7.

If the user does not want it sent this week, keep the draft in the review file and note that it was not
sent.

---

## Step 7: Write the Review File

Write the whole sitting to `thinking/weekly-reviews/weekly-review-YYYY-MM-DD.md`, using Step 0's
Friday date. Create the folder if needed. Read `thinking/AGENTS.md` first if you have not.

**Record the user's answers, not just the questions put to them.** The goal statuses they corrected, the
picks they swapped, what they chose not to do and why: that is the part worth having in six months,
and a file containing only my analysis is close to worthless as a record.

```markdown
# Weekly Review — Week of [Date Range]

_Reviewed [day it was actually run]._

## Completed
[Step 1, shipped vs internal vs still in progress]

## Goal Progress
[Step 2, with the status the user confirmed and, where they corrected me, what they said]

## Blockers & Stalled
[Step 3]

## Next Week
[Step 4's confirmed picks, what was deliberately not picked, and why]

## Stakeholder Update
[Step 6's approved message, verbatim. Note if it was not sent.]

## Notes
[Anything the user said in the sitting that does not fit above and is worth keeping]
```

One file per week. A re-run for the same week overwrites it rather than adding a second file.

**Then prune:** delete `weekly-review-*.md` in that folder dated more than 365 days ago. That
folder is gitignored, so the deletion is permanent and intended. Report how many went, if any.

---

## Quick Version

If the user wants condensed output, collapse Steps 1 to 4 into the block below. Still do Step 5
(archive), Step 6 (the update) and Step 7 (the file) — "quick" means less
narration, not a review that skips the leadership update or leaves no record:

```
## Week in Review ([Date Range])

**Completed:** [Key items shipped or finished]
**Goal status:** [Goal A] on track, [Goal B] at risk
**Blockers:** [N days waiting on X] / [Stalled: Y]
**Next week focus:** [Top 2-3 priorities from backlog]
**Watch out for:** [Key risk or recommendation]
```

The file it writes is marked `_(quick)_` under the heading.

---

## Best Practices

- **Never infer a goal's status from checkbox silence.** Step 2's rule is the important one in this
  skill; an empty week in TASKS.md is an absence of logging, not an absence of progress
- The recap exists to make the plan and the update honest. If Steps 1 to 3 turn up nothing real,
  say so plainly rather than padding them, and go straight to the questions for the user

---

## Final Step: Wrap-Up

Invoke the `wrap-up` skill. Announce it: "Running wrap-up."
