# Tasks — Agent Instructions

## Task System

**Priorities:** P0 (max 3) → P1 (max 7) → P2 (max 15) → P3 (unlimited)
**Status:** `n` = not started, `s` = started, `b` = blocked, `d` = done
**Storage:** Active tasks in `tasks/`, completed tasks in `tasks/_archived/`

Task files use YAML frontmatter:
```yaml
---
title: Task title
category: technical | outreach | research | writing | admin | strategy | stakeholder | discovery | other
priority: P1
status: n
created_date: YYYY-MM-DD
due_date: YYYY-MM-DD
resource_refs: []
---
```

See `templates/task-template.md` for the full task file format with required sections.

## Priority Caps

Priority caps are strict. Before creating a task, verify current counts. If a cap would be exceeded:
1. Show the user the current tasks at that priority level
2. Ask them to demote an existing task or lower the new task's priority
3. Wait for their decision before creating anything

## Goals Alignment

- Each task's Context section must reference the relevant goal from `GOALS.md`
- If no existing goal fits, ask whether to create a new goal entry or reconsider whether the task belongs now
- When reviewing tasks, flag any that no longer support a current goal

## Archiving

When a task status is set to `d`, move the file to `tasks/_archived/`. Never delete task files — they are a permanent record.
