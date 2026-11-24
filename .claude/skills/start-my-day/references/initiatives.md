# Initiative Movement

What moved on the core initiatives since the last briefing. **Only work that belongs to an
initiative.** A project that sits in no initiative is out of scope, no matter how active.

How to query the tracker lives in the user's
`knowledge/company-context/tools/work-tracking.md`, under the `initiatives`, `moved-since`, and
`status-updates` needs, together with the tool's own gotchas (how to resolve "me", how to get
links, pagination). This file holds the rules that apply whatever the tracker is. Nothing in this
step or in `comms-owed.md` writes to the tracker.

If the tracker has no notion of initiatives (`initiatives` is `not supported`), omit the section.

## Window

```bash
.claude/skills/start-my-day/scripts/briefing-window.py
```

Returns the window as JSON. **Do not compute dates yourself.**

```json
{"since_iso":"2026-08-28T12:30:09Z","since_human":"Fri 8:30am",
 "iso_duration":"-P5D","days":5,"source":"last-briefing",
 "file":"thinking/daily-briefs/daily-brief-2026-08-28.html",
 "first_run_of_week":true,"week_start":"2026-08-31",
 "last_week":{"start":"2026-08-24","end":"2026-08-30",
              "prior_start":"2026-08-17","prior_end":"2026-08-23"}}
```

- Pass `since_iso` as the "since" of every need. It is exact.
- `iso_duration` rounds **up** to whole days, so it over-covers rather than missing items. Use it
  only where the tool requires a duration.
- `source` tells you where the window came from: `last-briefing` (the `generated` meta in the
  newest dated brief), `start-of-today` (a second run the same day, so the window still covers all
  of today rather than just the last hour), or `fallback` (no brief on disk yet, window is `-P1D`).
- `file` is the brief the stamp was read from, repo-relative, or `null` on a fallback.
- `first_run_of_week` and `last_week` are not used by this step. Its window already spans the
  weekend on a Monday, because `since` is the previous run's stamp. They exist for any
  week-opening section you add.
- **Run this before the gather writes today's brief.** On a second run the same day, the file it
  reads is the one about to be overwritten; write first and the stamp is gone.

State `since_human` in the output: `since Fri 8:30am`.

## Scope

Match the user by id, never by name. The category file says how to resolve "me".

| Tier | Which | Detail |
|------|-------|--------|
| **Yours** | not completed, and the user is the owner | Project movement, issue counts, named completions, named blocks |
| **Others' active** | active, different owner | One line each, and only when something actually moved |
| Completed initiatives | completed | Excluded entirely |

Do not drop the other owners' initiatives: a project can sit in **multiple** initiatives, so an
owned initiative's movement often shows up under someone else's too.

## Step 1: Initiative to project map

`initiatives`. Build `project -> [initiative names]`, and keep each URL: every initiative,
project, and named issue in the brief is a link on its name. A project can map to several
initiatives. Attribute movement to **all** of them.

## Step 2: Movement

`moved-since` with `since_iso`, for projects and for issues that completed or started. Keep only
work whose project is in an initiative (some issues have no project at all). An empty lead or
owner means unset, not unowned: say "not set in <tool>".

**A truncated result is not the full record.** Follow pagination until exhausted before
summarizing.

## Step 3: Status updates

`status-updates` with `since_iso`, for initiatives and projects. When the tool pre-writes the
change (a health or target-date diff), quote it rather than paraphrasing. Note the author: an
update on an initiative the user owns that was written by someone else is worth flagging.

Updates are often posted every week or two, so most days this returns nothing. That is expected,
not a failure. Omit the sub-section rather than saying "no updates".

## Step 4: Roll up

Per initiative with movement, in this order: yours first, ranked by health then target-date
proximity.

- Counts: `N done, M in flight`
- Named: every completed issue title; every issue that moved into a blocked or canceled state.
  Every name that has a URL is a link on that name
- Never name backlog, unstarted, or triage churn
- Health or target-date change from a status update leads the entry, quoted
- Initiatives with zero movement do not appear at all

Cap the section at the 5 initiatives with the most movement. If more moved, close with
`+N more initiatives moved — say "initiatives" for the full list`.
