# Follow-Ups and Comms Owed

What the user owes other people. Distinct from `inbox` (Email and Slack), which surfaces what needs a reply
right now. This section is about **commitments and cadence debt** that nothing else in the OS
catches, and that quietly rot.

Four sources. Merge into one ranked list, deduplicated.

Use the same Linear MCP tools as `linear-initiatives.md`. Nothing in this step writes to Linear.

---

## Source 1: Status-update debt on initiatives the user owns

Fully checkable from Linear, no inference.

1. Resolve the viewer's own Linear id once with `get_user(query: "me")`, then from the Step 7
   `list_initiatives` call keep initiatives where `owner.id` is that id and
   `status != "Completed"`.
2. For each, get the newest status update:
   `get_status_updates(type = "initiative", initiative = "<name or id>", limit = 1, orderBy = "createdAt")`
   Or take it from a single unfiltered `get_status_updates(type="initiative", limit=50)` call and
   group by initiative, which is cheaper.
3. Compute `days_since_last_update`. **Never posted at all is the strongest signal, not a blank.**
   Report it as "no status update ever posted", never as 0 days or as an empty field.

**Threshold:**

| Condition | Overdue at |
|-----------|------------|
| `health == "atRisk"` or `"offTrack"` | 7 days |
| `targetDate` within 30 days | 7 days |
| Everything else | 14 days |

Rank by: never-posted first, then days overdue relative to its own threshold, then target proximity.

Link every initiative on its name, using the `url` already fetched in Step 7. This section is
the one the user acts on directly, so the click has to be there.

On the first run, note the current per-initiative update dates and the workspace's apparent
cadence, so later runs can recognize drift against it.

For anything overdue, offer the action rather than just the flag:
`say "update [initiative]" to draft it` — that routes to the `write-comms` skill, which already
knows the 3P format.

---

## Source 2: Commitments in recent meeting notes

Read the notes under `meetings/` dated inside the window (`since_iso` from `briefing-window.py`;
on a Monday that reaches back to Friday). Notes only: open a transcript only when the notes are
thin, and then read it, do not skim for names.

Keep only action items **the user** owns: first person in the notes ("I'll send…"), or an action
item explicitly assigned to them by name. Attendee-list membership is not enough: they are on
meetings where they owe nothing.

**Never name the person owed unless the notes you read say who.** Speaker labels are often wrong,
voices merge, and a name near a line is proximity, not attribution (see AGENTS.md). When the
counterpart is unclear, write the commitment and the meeting, and drop the name.

Distinguish the two and label them:

- **Commitment** — they said they would produce or send something ("share the revised spec").
  Surface with the promised artifact and, if stated, the date.
- **Open question directed at them** — someone asked and the notes record no answer.

Link each one to its note file by the meeting name.

If a commitment already exists in `tasks/TASKS.md`, mark it `(tracked)` and do not duplicate it.
`end-my-day` is what files meeting follow-ups into the backlog; this source only surfaces what is
still owed. Nothing else in the brief catches these, so do not silently drop one because the
phrasing was loose.

If `meetings/` has nothing inside the window, skip the source silently.

---

## Source 3: Linear threads awaiting the user's reply

Gmail and Slack triage never see Linear.

```
list_issues(assignee = "me", updatedAt = "<window>", limit = 100,
            fields = ["title","status","statusType","project","priority","url","updatedAt"])
```

Then for issues that moved, `list_comments(issueId = ...)` and keep threads where the **last**
comment is from someone else and mentions the user or asks a direct question.

Guardrails:

- A missing assignee, cycle, or due date means the field is unset. Never report it as status.
- Cap at 5. Linear is not the morning's main channel.
- Skip issues where the last comment is the user's own.

---

## Source 4: Waiting On, inverted

`tasks/TASKS.md` has a `Waiting On` table for people the user is waiting on. This is the reverse:
items where **they** are the blocker.

Look for, in `TASKS.md` and in `projects/`:

- Items marked blocked or waiting whose blocker is the user or unnamed
- `In Progress` items with no movement in 7+ days that another person or project depends on
- Explicit "owes X" or "X is waiting on me" notes

This source depends on how the table is kept, so it is the softest of the four. When it yields
nothing, say nothing. Do not infer that the user is a blocker from a stale checkbox: a checkbox that
has not moved is silence, not status.

---

## Output rules

One merged, ranked list. Ranking:

1. Overdue exec comms on at-risk initiatives (highest: visible, and rots fastest)
2. Meeting commitments with a stated date
3. Never-posted status updates on Active initiatives with a target inside 90 days
4. Linear threads awaiting reply
5. Everything else

Each line names **who is owed**, **what**, and **how overdue**. Cap at 7 lines total, and close
with `+N more` when it overflows.

If a follow-up is already an Active item in `TASKS.md`, mark it `(tracked)` rather than repeating it
as new. If the user owes nothing, omit the whole section. Do not print a reassuring empty header.
