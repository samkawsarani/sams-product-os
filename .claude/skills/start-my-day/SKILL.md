---
name: start-my-day
model: sonnet
description: Generates a morning briefing combining calendar agenda, focus-time protection check, email and Slack triage, meeting prep, and active task priorities. Invoked via /start-my-day or "morning pulse", "daily pulse", "start my day", "what's my day look like". Supports week overview variation.
argument-hint: '[optional: "week"]'
---

## Context

Today's date: $TODAY
Arguments: `$ARGUMENTS` (optional — see variations: week)

If `$ARGUMENTS` == "week" → use Week Overview variation.

---

## Default: Full Morning Briefing

### Step 0: Refresh Index

If qmd is installed, run `qmd update && qmd embed` to ensure semantic search reflects any content added since last session. If qmd is unavailable, skip this step and note it.

### Step 1: Calendar Agenda

1. Fetch today's events. Use `gws calendar events list --params '{"calendarId":"primary","timeMin":"<start>","timeMax":"<end>","singleEvents":true,"orderBy":"startTime"}'` so the response includes `attendees[].responseStatus` — the `+agenda` helper does NOT expose it. Prefix-strip any keyring line before parsing JSON.
2. **Exclude meetings you declined.** Drop any event where your own attendee entry (`attendees[]` with `self: true`) has `responseStatus == "declined"`. Excluded declined meetings must NOT appear in the table and must NOT count toward conflicts, density, or focus math (Step 2). Note them only as a one-line aside if useful (e.g. "Hid 2 declined meetings").
3. Filter out **multi-day all-day events**. Single-day all-day events can be shown as context above the table.
4. Present as a **table** with columns: Time, Event
   - For events where you are marked as **optional**, append `*(you're optional)*` to the event name in italics
5. After the table, add a single **"A few things to note:"** section with bullets covering:
   - Any **cancelled** meetings (include who cancelled and their reason/proposed new time if available). Declined-by-you meetings are already excluded per step 2.
   - **Free blocks** — gaps of 30+ minutes between meetings within 9am–5pm (mention duration)
   - **Density observations** — if there's a packed stretch of back-to-back meetings, call it out (e.g. "Your morning is fairly packed back-to-back from 9:30 to 11:30")
   - Any **scheduling conflicts** (overlapping events)
   - Only include bullets that are relevant — don't pad with filler

### Step 2: Focus Check

**Rules:**

- **Detection:** event has `eventType == focusTime` OR title contains "focus" or "deep work" (case-insensitive)
- **Counting:** labeled focus blocks + open gaps ≥60min within 9am–5pm, excluding lunch and personal events (school, OOO, personal appointments)
- **Daily target:** 2–3h minimum
- **Action model:** flag + propose batch — never write to calendar without explicit approval
- **Conflict-fix order:** (1) propose moving your focus block to the next open same-day ≥60min slot; (2) if no open slot exists, flag the conflicting meeting and note if you are optional on it

1. Sum today's focus hours using detection + counting rules above
2. Check if any meeting overlaps a focus block
3. If at risk (projected <2h) or a conflict exists:
   - Generate proposed fixes as a numbered batch
   - Show `FOCUS` section with summary + proposals
   - Ask "Approve all, pick numbers, or skip?" — wait before any calendar write
4. If today looks protected (≥2h secured), note it briefly in the `FOCUS` section and move on

### Step 3: Gmail Triage

1. Surface unread email needing a reply, time-sensitive items, emails from key people, action items, meeting threads.
2. Ignore newsletters, automated notifications, FYI-only, read-only updates.
3. **Exclude tool notifications** (Linear, Figma, GitHub, Notion, Slack digests, etc.) **unless you are directly tagged** — then surface it.
4. **For emails with metrics/data**, extract key numbers inline rather than just listing the subject.
5. Cap at 5 most actionable if >10 unread.

Omit `INBOX` section if clear.

### Step 4: Slack Triage

1. Surface unanswered DMs, threads where you were mentioned but haven't replied, urgent key-channel items.
2. Needs-response only — not just reading. Cap at 5.

Omit `SLACK` section if nothing actionable.

### Step 5: Meeting Prep

1. For each meeting on today's calendar, check:
   - Is there an agenda or prep doc? Search `projects/` and `meetings/` by event name.
   - Is a decision or output expected from this meeting?
   - Are there open tasks in `TASKS.md` directly tied to this meeting's topic?
2. Flag meetings that look under-prepped (no agenda, decision-heavy, involves key stakeholders).
3. For flagged meetings, offer a one-line prep suggestion.

Omit `MEETING PREP` section if no meetings or all look prepared.

### Step 6: Active Task Priorities

1. Read `tasks/TASKS.md`
2. Extract:
   - Items in the **In Progress** section
   - Items in the **Up Next** section
   - Any items in the **Waiting On** table that look overdue (based on the "Since" date vs. today)
3. Read `GOALS.md` for goal alignment context

### Step 7: Synthesize

Combine calendar + focus status + inbox + slack + tasks into a unified briefing.

**Omit any section that would be empty — don't show headers or placeholder text for empty sections.**

See `references/output-format.md` for the full output structure and section examples.

The YOUR PLAN section should be opinionated — give a clear recommended sequence interleaving task work, communication responses, and meeting prep. Don't just list everything; prioritize.

### Step 8: Offer Support

After the briefing, show the ready-to-start prompt block from `references/output-format.md`.

---

## Variations

### Week Overview

**When to use:** User passes "week" argument

1. Fetch the next 7 days of calendar events using available calendar tools.
2. Filter out multi-day all-day events.
3. Summarize per-day: meeting count, total meeting time, focus hours
4. Compute weekly projected focus total — flag if <15h
5. Read `tasks/TASKS.md` and show all In Progress + Up Next items

See `references/output-format.md` for the Week Overview output structure.

---

## Best Practices

- If user seems stuck choosing, make a recommendation
- Each data source is optional — skip unavailable sources and note what was skipped
