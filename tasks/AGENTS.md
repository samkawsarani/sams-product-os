# Tasks — Agent Instructions

## Task System

Three files, no individual task documents:

| File | Purpose |
|------|---------|
| `tasks/BACKLOG.md` | Brain dump inbox. Topic-organized bullets. Not committed work. |
| `tasks/ACTIVE.md` | This week's focus: In Progress, Up Next, Waiting On. |
| `tasks/_archived/YYYY-MM.md` | Monthly retrospective log. Shipped vs. Completed. Key Learnings. |

## File Formats

**`tasks/BACKLOG.md`** — Free-form brain dump. Plain bullets, any format, unstructured. Not checkboxes — these are not yet committed.

**`tasks/ACTIVE.md`** — Uses checkboxes, but format is flexible. A task might be a heading with checkboxes underneath, a single checkbox with context below it, or just a flat list of checkboxes — whatever fits the work. The key signal is the checkbox state: `- [ ]` = active, `- [x]` = done this week. Don't enforce a rigid structure when reading or writing ACTIVE.md.

**`tasks/ACTIVE.md` Waiting On table** — stays as a markdown table, not checkboxes.

## How It Works

**Capture** → Brain dump into `tasks/BACKLOG.md` in whatever format comes naturally. Plain bullets, notes, links — just get it down.

**Plan** → During weekly planning, move items from `tasks/BACKLOG.md` into `tasks/ACTIVE.md` as structured checkboxes. In Progress = working on now. Up Next = committed this week. Waiting On = blocked on someone else.

**Archive** → At week's end, log completed work into the current month's `tasks/_archived/YYYY-MM.md` under the appropriate week section. Distinguish Shipped (delivered externally) from Completed (internal work done). Then reset ACTIVE.md for the next week.

## Goals Alignment

Before recommending what to work on or pull into ACTIVE.md, read `GOALS.md`. Flag backlog items that don't connect to a current goal — ask the user to clarify before adding them or to confirm they want to proceed anyway.

## Archiving

When logging completed work:
1. Find or create `tasks/_archived/YYYY-MM.md` for the current month
2. Add a "Week of [Date Range]" section if it doesn't exist
3. Log items under **Shipped** (went live / delivered externally) or **Completed** (internal work done)
4. Never delete ACTIVE.md content without user confirmation — ask first

Use `templates/archive-template.md` when creating a new monthly file.
Use `templates/active-template.md` when resetting ACTIVE.md for a new week.

## Backlog Processing

When processing `tasks/BACKLOG.md`:
- **Tasks** stay in the backlog as organized lines — no individual task files
- **Opportunities** (strategic ideas to explore) → `knowledge/opportunities/`
- **References** (articles, research, competitor info) → `knowledge/references/`

Use `/process-backlog` to classify and clean. Always present findings before creating anything.

