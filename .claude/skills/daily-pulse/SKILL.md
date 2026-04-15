---
name: daily-pulse
model: sonnet
description: Generates a morning briefing combining calendar agenda, email and Slack triage, meeting prep, and active task priorities. Invoked via /daily-pulse or "morning pulse", "what's my day look like". Supports variations (tomorrow, week).
argument-hint: '[optional: "tomorrow", "week"]'
---

## Context

Find task and goal context.
Today's date: $TODAY
Arguments: `$ARGUMENTS` (optional — see variations: tomorrow, week)

**Best timing:** Run first thing — it replaces your manual inbox/Slack scan.

## Your Task

Generate a morning pulse that combines calendar agenda, inbox and Slack triage, meeting prep, and active task priorities into a single plan for the day.

If user provided arguments: $ARGUMENTS
- "tomorrow" → Use Tomorrow Look-Ahead variation
- "week" → Use Week Overview variation

---

## Default: Full Morning Pulse

### Step 0: Refresh Index

Run `qmd update && qmd embed` to ensure semantic search reflects any content added since last session.

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

### Step 2: Gmail Triage

**Actions:**
1. Check unread email and surface messages that need attention today.
2. Filter to: emails needing a reply, time-sensitive items, emails from key people, action items, meeting-related threads.
3. Ignore newsletters, automated notifications, FYI-only threads, and read-only updates.
4. **Exclude system notifications from tools** (Linear, Figma, Miro, GitHub, Jira, Notion, Slack digest emails, etc.) **unless you are directly tagged or mentioned** in them — in that case, surface it.
5. **For emails containing metrics or data** (dashboards, reports, analytics summaries, weekly stats), extract and summarize the key numbers inline — don't just list the subject, give the headline figures.
6. If more than 10 unread, surface only the top 5 most actionable.

**Output section: `INBOX`**
```
INBOX
- [Sender] — [Subject] — [Why it needs attention / action needed]
- ...
```
Omit section if inbox is clear.

### Step 3: Slack Triage

**Actions:**
1. Check Slack for unanswered DMs, threads where you were mentioned or tagged but haven't replied, and anything urgent in key channels.
2. Surface messages that need a response, not just reading.
3. Cap at 5 items to avoid noise.

**Output section: `SLACK`**
```
SLACK
- [Channel/DM] — [Brief summary] — [Action needed]
- ...
```
Omit section if nothing actionable.

### Step 4: Meeting Prep

**Actions:**
1. For each meeting on today's calendar, check:
   - Is there an agenda or prep doc? Search `projects/` and `meetings/` by event name.
   - Is a decision or output expected from this meeting?
   - Are there open tasks in `ACTIVE.md` directly tied to this meeting's topic?
2. Flag meetings that look under-prepped (no agenda, decision-heavy, involves key stakeholders).
3. For flagged meetings, offer a one-line prep suggestion.

**Output section: `MEETING PREP`**
```
MEETING PREP
- [Meeting name] @ [time] — [Prep suggestion or "looks ready"]
  - Open: [relevant task or doc gap if any]
- ...
```
Omit section if no meetings today or all look prepared.

### Step 5: Active Task Priorities

**Actions:**
1. Read `tasks/ACTIVE.md`
2. Extract:
   - Items in the **In Progress** section
   - Items in the **Up Next** section
   - Any items in the **Waiting On** table that look overdue (based on the "Since" date vs. today)
3. Read `GOALS.md` for goal alignment context

### Step 6: Synthesize

Combine calendar + inbox + slack + tasks into a unified briefing.

**Omit any section that would be empty — don't show headers or placeholder text for empty sections.**

See `references/output-format.md` for the full output structure and section examples.

The YOUR PLAN section should be opinionated — give a clear recommended sequence interleaving task work, communication responses, and meeting prep. Don't just list everything; prioritize.

### Step 7: Offer Support

After the briefing, show the ready-to-start prompt block from `references/output-format.md`.

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

See `references/output-format.md` for the Week Overview output structure.

---

## Best Practices

- Keep this session under 2 minutes
- Focus on outcomes, not activity
- Update ACTIVE.md when you begin work on something
- If user seems stuck choosing, make a recommendation
- Each data source is optional — if a source is unavailable, proceed with the rest and note what was skipped
