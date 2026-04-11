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

**`tasks/ACTIVE.md`** — Structured checkboxes. Each item follows this shape:
```markdown
- [ ] Task title
  Project: [Initiative]  Due: [Date]   ← optional metadata line
  Context prose — why this matters, current status, what's needed.
  - [ ] Sub-task                        ← optional breakdown
  - [ ] Sub-task
```
The main checkbox (`- [ ]` / `- [x]`) is the signal: unchecked = active, checked = done this week.
Sub-checkboxes and metadata lines are optional — add them when they help, skip them when they don't.

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
- **Initiatives** (strategic ideas to explore) → `initiatives/`
- **References** (articles, research, competitor info) → `knowledge/references/` or related initiative folder

Use `/process-backlog` to classify and clean. Always present findings before creating anything.

## What Not To Do

- Do not create individual task files — tasks live in BACKLOG.md and ACTIVE.md only
- Do not use priority codes (P0/P1/P2/P3) — the three-bucket system replaces this
- Do not use status codes (n/s/b/d) — position in ACTIVE.md is the status indicator
- Do not assign due dates unless the user explicitly provides one
