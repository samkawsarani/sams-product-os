---
name: end-my-day
model: sonnet
description: End-of-day skill. Checks rest-of-week focus-time protection, previews tomorrow's calendar, extracts action items from today's meeting notes, and surfaces insights worth capturing. Invoked via /end-my-day or "end my day", "wrap up my day", "day review", "what's happening tomorrow", "wind down".
---

## Context

Today's date: $TODAY

---

## Step 1: Rest-of-Week Focus Protection

Fetch calendar for remaining weekdays this week (tomorrow through Friday).

**Rules:**

- **Detection:** event has `eventType == focusTime` OR title contains "focus" or "deep work" (case-insensitive)
- **Counting:** labeled focus blocks + open gaps ≥60min within 9am–5pm, excluding lunch and personal events (school, OOO, personal appointments)
- **Targets:** daily floor 2–3h · weekly target 15–20h (flag if projected <15h; aim proposals to reach ~17h)
- **Action model:** flag + propose batch — never write to calendar without explicit approval
- **Conflict-fix order:** (1) propose moving your focus block to the next open same-day ≥60min slot; (2) if no open slot, flag the conflicting meeting and note if you are optional on it

1. For each remaining weekday, sum focus hours using the rules above
2. Compute weekly projected total (include today's actual hours)
3. Flag any day <2h and/or week <15h projected
4. If fixes needed, generate proposals as a numbered batch:
   - Move focus blocks away from conflicts where a same-day ≥60min slot is available
   - Create new focus blocks in open ≥60min slots to fill gaps toward ~17h
   - Flag meetings that conflict with focus blocks (note if you are optional)
5. Present focus summary table + proposals
6. Ask "Approve all, pick numbers, or skip?" — wait before any calendar writes

If focus looks healthy (all remaining days ≥2h, week projected ≥15h), note it briefly and skip proposals.

**Output section: `FOCUS THIS WEEK`**

---

## Step 2: Tomorrow Preview

Fetch tomorrow's calendar.

1. Filter out multi-day all-day events. Single-day all-day events shown as context above table.
2. Present as a **table** with columns: Time, Event
   - Append `*(you're optional)*` for optional events
3. Add **"A few things to note:"** section with bullets for:
   - Free blocks ≥30min (mention duration)
   - Back-to-back stretches
   - Cancelled or declined meetings
   - Scheduling conflicts
   - Only include relevant bullets — no filler
4. Flag any meetings that look under-prepped (no agenda, decision-heavy, key stakeholders)

---

## Step 3: Action Items from Today's Meetings

Read all `.md` files in `meetings/$TODAY/`.

If the folder is empty or missing: note it and suggest syncing/exporting meeting notes before proceeding. Continue with other steps.

1. For each meeting note, extract explicit action items:
   - Commitments you made ("I'll send...", "I'll follow up on...", "by [date]...")
   - Decisions that require follow-up from you
   - Open questions assigned to you
   - Skip items clearly owned by others unless you explicitly committed to follow up
2. Deduplicate across meetings
3. Present as a numbered list with the source meeting noted for each item
4. Ask "Add all to TASKS.md, pick numbers, or skip?"
5. On approval: append approved items to the brain-dump backlog section of `tasks/TASKS.md`

---

## Step 4: Insights

From the same meeting notes, extract non-actionable observations worth remembering:
- Directional signals or emerging themes
- Context shifts that might shape future decisions
- Notable things said that don't require action now
- Patterns across multiple meetings today

1. Surface as a short bulleted list (3–5 max; quality over quantity)
2. Skip anything purely factual or already captured in action items
3. For each insight worth filing, note a suggested `knowledge/domains/` path
4. Ask which (if any) to file — on approval, invoke wrap-up to route them

---

## Step 5: Synthesize + Offer Support

Combine all sections into a clean end-of-day summary. Omit empty sections entirely — no placeholder headers.

See `references/output-format.md` for the full output structure.

After the summary, show the ready-to-wrap prompt block.

---

## Best Practices

- Each data source is optional — if unavailable, proceed and note what was skipped
- Don't surface meeting content that's clearly personal or sensitive (health, HR conversations)
- Action-item extraction: 3 real items beats 10 noisy ones
- If it's Friday, weekly focus total is final — note how the week landed vs. target
