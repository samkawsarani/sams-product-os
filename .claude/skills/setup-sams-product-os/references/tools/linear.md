# Work tracking: Linear

Template. Setup copies this to `knowledge/company-context/tools/work-tracking.md`, removes this
paragraph and the `## Setup` section, fills every `<...>` blank, and sets **Status**. Never ship
the copy with a blank left in.

## Setup

- **Requires**: a Linear MCP server (required), found in the scan by name.
- **Ready check**: `get_user(query: "me")` through that server. A failure means the server is not
  connected or not authorized; quote the error.
- **User does**: connect the Linear MCP server and authorize it in their agent. Say what is
  missing and record Linear as not ready until then.

**Status**: <ready | not ready (<reason>)>
**Access**: MCP server `<server name as the agent sees it, e.g. linear-server>`
*Last updated: <YYYY-MM-DD>*

Tool calls below are written without the server prefix (`list_projects`). Call them through the
server named in **Access**. Nothing in any need writes to Linear.

## Data model

Initiative → projects → issues. A project can sit in several initiatives; count its movement
toward **all** of them. A project with an empty `initiatives` array belongs to no initiative.

## General gotchas

- **Who is "me":** resolve the viewer's id once with `get_user(query: "me")` and compare
  `owner.id` / `lead.id` against it. Never match on names.
- **Links:** `url` comes back only if you list it in `fields`. Never build a Linear URL from a name
  or slug; use the one the API returned.
- **Empty fields are unset, not status.** An empty `lead: {}`, or a missing assignee, cycle, or due
  date, means nobody filled it in. Say "not set in Linear", never "unowned" or "unscheduled".
- **Time filters:** `list_*` calls accept an absolute ISO timestamp for `updatedAt` / `createdAt`.
  Prefer it to a duration like `-P3D`, which rounds to whole days.
- **Pagination:** when `hasNextPage` is true, follow `cursor` until exhausted. A truncated page is
  never the full record.

## Needs

### initiatives

```
list_initiatives(
  fields = ["name","url","status","health","targetDate","updatedAt","owner","projects"],
  limit = 50
)
```

One call covers a typical workspace. Build `project_id -> [initiative names]` from it.

### moved-since

Projects:

```
list_projects(
  updatedAt = "<since, ISO>",
  fields = ["name","url","status","initiatives","lead","targetDate","updatedAt","completedAt"],
  limit = 50
)
```

`health` is **not** a valid project field; requesting it is a validation error. Project health
reaches you only through `status-updates`.

Issues: two narrowed queries, never one broad one. A broad `list_issues(updatedAt=...)` in an active
workspace returns hundreds of backlog changes.

```
list_issues(state = "completed", updatedAt = "<since, ISO>", limit = 250,
            fields = ["title","status","statusType","project","assignee","priority","url","completedAt"])
list_issues(state = "started",   updatedAt = "<since, ISO>", limit = 250, fields = [ ...same... ])
```

Some issues have no project at all.

### status-updates

```
get_status_updates(type = "initiative", createdAt = "<since, ISO>", limit = 50)
get_status_updates(type = "project",    createdAt = "<since, ISO>", limit = 50)
```

`diffMarkdown` is the most useful field: Linear pre-writes the movement (health change, target date
change, completion). Quote it rather than paraphrasing, and note the author.

For the newest update per initiative, take one unfiltered
`get_status_updates(type = "initiative", limit = 50)` and group by initiative. An initiative with
no update at all has never posted one; report that, never "0 days".

Updates are usually posted every week or two, so an empty result on most days is expected.

### awaiting-my-reply

```
list_issues(assignee = "me", updatedAt = "<since, ISO>", limit = 100,
            fields = ["title","status","statusType","project","priority","url","updatedAt"])
```

For issues that moved, `list_comments(issueId = ...)`. Keep threads where the **last** comment is
from someone else and mentions the user or asks them a direct question.

## Rules

- Never write to Linear.
- Never name backlog, unstarted, or triage churn as movement.

## Scope

- **Workspace**: <workspace name>
- **Teams that matter**: <team names, or "all">
