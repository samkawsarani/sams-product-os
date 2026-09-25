# Linear Initiative Movement

What moved on the core initiatives since the last briefing. **Only work that belongs to an
initiative.** A project with an empty `initiatives` array is out of scope, no matter how active.

Use the Linear MCP tools (`mcp__linear-server__*` with the server name from
`.mcp.json.example`; match whatever your `.mcp.json` calls it). `scripts/run.sh` pre-allows that
prefix for the headless run, so a renamed server needs `BRIEFING_ALLOWED_TOOLS` updated too.
Nothing in this step or in `comms-owed.md` writes to Linear.

## Window

```bash
.claude/skills/daily-brief/scripts/briefing-window.py
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

- Prefer `since_iso` — Linear `list_*` accept an absolute ISO timestamp, which is exact.
- `iso_duration` rounds **up** to whole days, so it over-covers rather than missing items. Use it
  only where a duration is required.
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

Owner IDs matter more than names here. Resolve the viewer's own id once with
`get_user(query: "me")` and compare `owner.id` against it.

| Tier | Which | Detail |
|------|-------|--------|
| **Yours** | `status != Completed` and `owner.id` is the viewer | Project movement, issue counts, named completions, named blocks |
| **Others' active** | `status == Active`, different owner | One line each, and only when something actually moved |
| Completed initiatives | `status == Completed` | Excluded entirely |

Do not drop the other owners' initiatives: a project can sit in **multiple** initiatives, so an
owned initiative's movement often shows up under someone else's too.
Movement there can be movement on yours.

## Step 1: Initiative to project map

```
list_initiatives(
  fields = ["name","url","status","health","targetDate","updatedAt","owner","projects"],
  limit = 50
)
```

One call; a typical workspace has well under 50 initiatives, so no pagination is needed. Build `project_id -> [initiative names]`, and
keep each `url`: every initiative, project, and named issue in the brief is a link on its name.
`url` is a valid field on all three `list_*` calls but only comes back if you ask for it. Never
build a Linear URL from a name or a slug; use the one the API returned.
A project can map to several initiatives. Attribute movement to **all** of them.

## Step 2: Project-level movement

```
list_projects(
  updatedAt = "<window>",
  fields = ["name","url","status","initiatives","lead","targetDate","updatedAt","completedAt"],
  limit = 50
)
```

Keep only projects whose `initiatives` array is non-empty.

- Project movement is usually small (a handful over a few days). Cheap, and quiet by nature.
- `health` is **not** a valid field on projects. Requesting it is a validation error. Project health
  reaches you only through initiative `status update` diffs (Step 4).
- An empty `lead: {}` means unset, not unowned. Say "no lead set in Linear", never "unowned".

## Step 3: Issue-level movement

Two narrowed queries, not one broad one. A broad `list_issues(updatedAt=-P3D)` in an active workspace
returns hundreds with `hasNextPage: true`, mostly backlog churn.

```
list_issues(state = "completed", updatedAt = "<window>", limit = 250,
            fields = ["title","status","statusType","project","assignee","priority","url","completedAt"])
list_issues(state = "started",   updatedAt = "<window>", limit = 250, fields = [ ...same... ])
```

**Paginate both.** If `hasNextPage` is true, follow `cursor` until exhausted. A truncated page is
not the full record and must never be summarized as if it were.

Then group by project, map to initiatives, and drop any issue whose project is not in an initiative
(some issues have no project at all).

## Step 4: Status update diffs

```
get_status_updates(type = "initiative", createdAt = "<window>", limit = 50)
get_status_updates(type = "project",    createdAt = "<window>", limit = 50)
```

`diffMarkdown` is the highest-value field in this whole step: Linear pre-writes the movement in
exec language, e.g.

```
- **Migrate billing to the new payments API** at risk · target date changed Jun 30th → Aug 14th
- **Sandbox test credentials** marked as completed
```

Quote `diffMarkdown` rather than paraphrasing it. Note the author: a status update on an initiative
the user owns that was written by someone else is worth flagging.

Updates are posted roughly **biweekly**, so most days this returns nothing. That is expected, not a
failure. Omit the sub-section rather than saying "no updates".

## Step 5: Roll up

Per initiative with movement, in this order: yours first, ranked by health then target-date proximity.

- Counts: `N done, M in flight`
- Named: every completed issue title; every issue that moved into a blocked or canceled state.
  Every name that has a `url` is a link on that name
- Never name backlog, unstarted, or triage churn
- Health or target-date change from a status diff leads the entry, quoted
- Initiatives with zero movement do not appear at all

Cap the section at the 5 initiatives with the most movement. If more moved, close with
`+N more initiatives moved — say "initiatives" for the full list`.
