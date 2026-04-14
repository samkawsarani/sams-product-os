---
name: daily-pulse
model: haiku
description: Generates a morning briefing combining calendar agenda with active task priorities and goal alignment. Invoked via /daily-pulse or "morning pulse", "what's my day look like". Supports variations (tomorrow, week).
argument-hint: '[optional: "tomorrow", "week"]'
---

## Context

Find task and goal context.
Today's date: $TODAY
Arguments: `$ARGUMENTS` (optional — see variations: tomorrow, week)

**Best timing:** First thing in morning, before checking email/Slack

## Your Task

Generate a morning pulse that combines calendar agenda with active task priorities.

If user provided arguments: $ARGUMENTS
- "tomorrow" → Use Tomorrow Look-Ahead variation
- "week" → Use Week Overview variation

---

## Default: Full Morning Pulse

### Step 1: Calendar Agenda

**Actions:**
1. Fetch today's calendar agenda using available calendar tools.
2. Optionally fetch tomorrow for look-ahead context.
3. Filter out **multi-day all-day events** (where the event spans more than one day). Single-day all-day events can be shown as context above the table.
4. Parse the results and present as a **table** with columns: Time, Event
   - For events where you are marked as **optional**, append `*(you're optional)*` to the event name in italics
4. After the table, add a single **"A few things to note:"** section with bullet points covering:
   - Any **cancelled or declined** meetings (include who declined and their reason/proposed new time if available)
   - **Free blocks** — gaps of 30+ minutes between meetings within 9am–5pm (mention duration)
   - **Density observations** — if there's a packed stretch of back-to-back meetings, call it out (e.g. "Your morning is fairly packed back-to-back from 9:30 to 11:30")
   - Any **scheduling conflicts** (overlapping events)
   - Only include bullets that are relevant — don't pad with filler

### Step 2: Active Task Priorities

**Actions:**
1. Read `tasks/ACTIVE.md`
2. Extract:
   - Items in the **In Progress** section
   - Items in the **Up Next** section
   - Any items in the **Waiting On** table that look overdue (based on the "Since" date vs. today)
3. Read `GOALS.md` for goal alignment context

### Step 3: Synthesize

Combine calendar + tasks into a unified briefing.

**Omit any section that would be empty — don't show headers or placeholder text for empty sections.**

**Output format:**
```
Daily Pulse for [Day, Date]

CALENDAR
| Time | Event |
|------|-------|
| [Start]–[End] | [Event title] |
| [Start]–[End] | [Event title] *(you're optional)* |
| ... | ... |

A few things to note:
- [Person] declined [Meeting] and asked to move it to [new time] — "[reason]"
- You have a free block from [X]–[Y] (Xh Xm) and another from [Y]–[Z] (Xh Xm)
- Your [morning/afternoon] is fairly packed back-to-back from [X] to [Y]
- [Meeting A] and [Meeting B] overlap at [time] — you'll need to pick one

TOP PRIORITIES
1. [In Progress task with context]
   Goal: [Goal name]
   Why today: [Urgency/impact]

2. [Second In Progress or top Up Next item]
   ...

3. [Third priority]
   ...

UP NEXT
  - [Task] — [brief context]
  - ...

WAITING ON
  - [Who] — [What] (since [date], [N] days)
  [Flag if this looks overdue or needs a nudge]
```

### Step 4: Offer Support

```
Ready to start?
- Say "start [task name]" to move it to In Progress in ACTIVE.md
- Say "/daily-pulse tomorrow" for tomorrow's briefing
- Say "/daily-pulse week" for the week overview
```

---

## Variations

### Tomorrow Look-Ahead

**When to use:** User passes "tomorrow" argument

**Actions:**
1. Fetch tomorrow's calendar agenda using available calendar tools.
2. Filter out multi-day all-day events.
3. Present events as a **table** (same format as default pulse, with *(you're optional)* on optional events)
4. Add **"A few things to note:"** section with bullets for free blocks, cancellations/declines, back-to-back stretches, and conflicts
5. Read `tasks/ACTIVE.md` and show items in Up Next that might be worth tackling tomorrow

**Output:** Calendar table + notes + Up Next items relevant to tomorrow

### Week Overview

**When to use:** User passes "week" argument

**Actions:**
1. Fetch the next 7 days of calendar events using available calendar tools.
2. Filter out multi-day all-day events.
3. Summarize per-day: meeting count, total meeting time
4. Read `tasks/ACTIVE.md` and show all In Progress + Up Next items

**Output format:**
```
Week Overview ([Date Range])

[Day]  [N] meetings  [X]h
[Day]  [N] meetings  [X]h
...

BUSIEST DAY: [Day] -- [Context]
LIGHTEST DAY: [Day] -- Best for deep work

ACTIVE THIS WEEK
In Progress:
- [Task] — [brief context]

Up Next:
- [Task]
- [Task]

WAITING ON
| Who | What | Since | Next step |
|-----|------|-------|-----------|
```

---

## Best Practices

- Keep this session under 2 minutes
- Focus on outcomes, not activity
- Update ACTIVE.md when you begin work on something
- If user seems stuck choosing, make a recommendation
- If calendar fetch fails, proceed with task-only pulse and note the issue
