---
name: view-tasks
model: haiku
description: Displays task views. Default shows ACTIVE.md. Pass 'backlog' to see the brain dump, or 'archive' to browse completed work. Invoked when asked about tasks, what's active, what am I working on, what's in my backlog, or show me my tasks.
allowed-tools: Glob, Read
argument-hint: "[view] — views: active (default), backlog, archive"
---

## Context

Tasks are managed in three files in `tasks/`:
- `tasks/ACTIVE.md` — this week's focus: In Progress, Up Next, Waiting On
- `tasks/BACKLOG.md` — brain dump inbox, topic-organized, not yet committed
- `tasks/_archived/YYYY-MM.md` — monthly retrospective log of completed work

Today's date: $TODAY
Arguments: $ARGUMENTS

---

## active (default)

Show the current week's active work. This is the default view when no argument is passed.

**Steps:**

1. Read `tasks/ACTIVE.md`
2. Display the file contents as-is, preserving the three-section structure
3. Add a brief note below if the Waiting On table has any items:
   - If any items appear overdue based on the "Since" date, call them out

**Output format:**
```
[Contents of tasks/ACTIVE.md displayed directly]

---
[If Waiting On items exist and any look overdue:]
Note: [Item] has been waiting since [date] — worth a follow-up.
```

- If the file is empty or only has placeholder text, say so and suggest using `/process-backlog` to pick from the backlog
- Keep output clean — no extra headers or reformatting

---

## backlog

Show everything in the brain dump inbox, organized by topic.

**Steps:**

1. Read `tasks/BACKLOG.md`
2. Display the file contents as-is
3. After the content, add a one-line prompt:
   - "Run `/process-backlog` to classify and move items into ACTIVE.md"

**Output format:**
```
[Contents of tasks/BACKLOG.md displayed directly]

---
Run `/process-backlog` to classify and move items into ACTIVE.md.
```

- If the backlog is empty, say so clearly

---

## archive

Browse completed work from the monthly archive.

**Steps:**

1. Use `Glob` to list all files in `tasks/_archived/`
2. Display the most recent month's file by default
3. If $ARGUMENTS contains a year-month (e.g., "2026-03"), show that month instead

**Output format:**
```
[Contents of the most recent (or requested) archive file displayed directly]

---
Other months: [list of other archive files if any]
```

- If no archive files exist yet, say so and note that completed work gets logged here during weekly review
