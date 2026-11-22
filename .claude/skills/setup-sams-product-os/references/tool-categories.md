# Tool Categories

The contract between setup and every skill that touches a work tool. Skills ask for a **need**
("today's events"); the user's category file says how to meet it with their tool.

Setup writes one file per category to `knowledge/company-context/tools/<category>.md`, either
from a template in `tools/` or from the user's own description. Either way the file answers the
needs listed for its category below. A need the tool cannot meet is written as `not supported`,
never left out, so a skill can tell "can't" from "forgot".

## User file shape

Every category file, template-based or not, has these sections:

```markdown
# <Category>: <Tool>

**Status**: ready | not ready (<what is missing>)
**Access**: <MCP server `name` | command-line tool `name` | local folder `path` | none>
*Last updated: YYYY-MM-DD*

## Needs
### <need name>
How to get it with this tool: the tool call or command, the filter, and any gotcha.

## Rules
Rules the skills must follow with this tool (what never to write, what to exclude).

## Scope
The user's specifics: account, calendar, workspace, team, project keys, channels.
```

## Categories

| File | Category | Common answers | Needs |
|------|----------|----------------|-------|
| `email-calendar.md` | Email + calendar | Google Workspace, Microsoft 365 | see below |
| `messaging.md` | Messaging | Slack, Microsoft Teams | see below |
| `work-tracking.md` | Initiatives, projects, issues | Linear, Jira, Asana | see below |
| `meeting-notes.md` | Meeting notes and transcripts | Granola, Otter, Zoom AI, local `meetings/` folder | see below |
| `metrics.md` | Product and customer metrics | BigQuery, Amplitude, Mixpanel, Looker | see below |
| `crm.md` | Customer and sales records | HubSpot, Salesforce | see below |
| `call-recordings.md` | Sales and customer call analysis | Gong, Avoma, Chorus | see below |
| `docs.md` | Docs and wiki | Notion, Confluence, Google Drive | see below |

Email and calendar are one category because they come as one suite. A user who mixes vendors
gets one file with a section per tool.

### Needs per category

**Email + calendar**
- `events-in-range`: events between two times, with the user's own response status, the
  optional flag, focus-time type, cancellations, and all-day events marked. Must also say how
  to write the result as the **plain event list** below, which `start-my-day`'s calendar script
  reads
- `create-event`: create or move an event. Only ever after explicit user approval
- `unread-to-me`: unread mail where the user is in To or Cc by their own address, since a time
- `read-thread`: full content of one thread
- `bulk-archive`: mark read and archive many messages in one call
- `invite-receipts` (optional): select meeting-invite emails, and how to tell an RSVP or a plain
  invitation (no answer needed) from a proposed new time, update, or cancellation (keep). Write
  `not supported` if the tool has no reliable way; inbox hygiene is then skipped

**Plain event list.** One JSON file, so the calendar script never needs to know the tool:

```json
{"events": [
  {"title": "Roadmap sync",
   "start": "2026-11-23T10:00:00-05:00", "end": "2026-11-23T10:30:00-05:00",
   "all_day": false, "declined": false, "optional": false, "focus": false,
   "cancelled": false, "organizer": "someone@example.com"}
]}
```

`start`/`end` are ISO datetimes, or `YYYY-MM-DD` when `all_day` is true. `declined` and
`optional` are about the user's own attendance. `focus` is the calendar's own focus-time type
(titles like "Deep work" are detected by the script). Prefer a command that writes the file
directly, so the raw calendar never enters the agent's context.

**Links.** Any need that returns named items (initiatives, projects, issues, threads, docs) also
returns each item's URL when the tool has one. The category file says how to get it.

**Messaging**
- `mentions-and-dms`: direct and group messages, and explicit mentions of the user, since a time
- `threads-awaiting-me`: threads the user posted in where someone replied after them

**Work tracking**
- `initiatives`: top-level initiatives with owner, status, and their projects
- `moved-since`: projects and issues updated since a time, with status changes and completions
- `status-updates`: written status updates on initiatives and projects since a time (health or
  target-date changes), and the newest one per initiative
- `awaiting-my-reply`: comments or mentions addressed to the user that they have not answered

**Meeting notes**
- `notes-in-range`: notes or transcripts for meetings in a time window
- `where-notes-land`: the folder or tool where finished notes end up

**Metrics**
- `query`: how to run a query, and which project or workspace to run it in

**CRM**
- `account-lookup`: an account or company with owner, stage, and recent activity
- `open-deals`: open opportunities for an account or owner

**Call recordings**
- `calls-in-range`: recorded calls in a time window, with participants
- `call-transcript`: transcript or summary of one call

**Docs**
- `search`: find documents by keyword
- `read-doc`: full content of one document

## Detection

Setup matches what the agent has against these. Match on any part of an MCP server or tool name,
case-insensitive.

| Name contains | Category | Tool |
|---------------|----------|------|
| `gmail`, `google_calendar`, `gcal` | Email + calendar | Google Workspace |
| `outlook`, `microsoft`, `m365`, `office365` | Email + calendar | Microsoft 365 |
| `slack` | Messaging | Slack |
| `teams` | Messaging | Microsoft Teams |
| `linear` | Work tracking | Linear |
| `jira`, `atlassian` | Work tracking | Jira |
| `asana` | Work tracking | Asana |
| `granola` | Meeting notes | Granola |
| `otter` | Meeting notes | Otter |
| `zoom` | Meeting notes | Zoom |
| `bigquery` | Metrics | BigQuery |
| `amplitude` | Metrics | Amplitude |
| `mixpanel` | Metrics | Mixpanel |
| `looker` | Metrics | Looker |
| `hubspot` | CRM | HubSpot |
| `salesforce` | CRM | Salesforce |
| `gong` | Call recordings | Gong |
| `avoma` | Call recordings | Avoma |
| `chorus` | Call recordings | Chorus |
| `notion` | Docs | Notion |
| `confluence`, `atlassian` | Docs | Confluence |
| `google_drive`, `gdrive` | Docs | Google Drive |

One server can match two categories (`atlassian` covers Jira and Confluence). Offer it for both.

**Command-line tools.** Check each with `command -v`:

| Command | Category | Tool |
|---------|----------|------|
| `gws` | Email + calendar | Google Workspace |
| `bq` | Metrics | BigQuery |

A non-empty `meetings/` folder counts as a detected local source for Meeting notes.

## Templates

A template exists only for a tool the agent cannot work out from its own tool list: a
command-line tool, or a data model with gotchas. Everything else gets a file written from the
detected MCP server and the user's answers.

| Template | Tool |
|----------|------|
| `tools/google-workspace.md` | Google Workspace via the `gws` command-line tool |
| `tools/linear.md` | Linear via its MCP server (data model and field gotchas) |

To support a new tool with gotchas, add `tools/<tool>.md` answering its category's needs, and
add its detection row above.

**Every template is self-contained.** Setup knows nothing about any tool; everything it needs is
in the template's `## Setup` section, which setup reads and does **not** copy into the user's
file:

```markdown
## Setup

- **Requires**: commands or servers that must exist, each with its check (`command -v x`), and
  whether it is required or optional
- **Ready check**: one read-only call that proves access, and how to read a failure
- **Version**: command whose output fills the version blank, if any
- **Skills to offer**: `npx skills add ...` command for skills the tool needs, if any
- **User does**: steps setup never performs (accounts, cloud projects, logins), and what to say
```
