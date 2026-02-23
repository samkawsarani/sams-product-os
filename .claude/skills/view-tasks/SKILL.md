---
name: view-tasks
description: Displays task views with optional arguments for different views. Pass 'today' for due/overdue tasks, 'upcoming' for next 7 days, or 'all' for complete task list with optional filters by priority, status, or category. Invoked when asked about tasks, what's due, or task status.
allowed-tools: find_overdue_tasks, list_tasks, get_task_summary, Glob, Read
argument-hint: "[view] — views: today, upcoming, all. Optional filters: priority, status, category"
---

## Context

Tasks are stored in markdown files in the `tasks/` directory with YAML frontmatter containing priority, status, due_date, category.
Today's date: $TODAY
Arguments: $ARGUMENTS

---

## today

Show all tasks that are due today or overdue, prioritized by urgency.

**Steps:**

1. **Try MCP first**: Use `find_overdue_tasks` and `list_tasks` MCP tools

2. **Failover if needed**: If MCP tools fail or aren't available:
   - Use `Glob` to find all files in `tasks/*.md`
   - Use `Read` to parse each task file's frontmatter
   - Filter for tasks where `due_date` is today ($TODAY) or earlier
   - Note: "Using direct file reading (MCP unavailable)"

3. **Combine and prioritize**: Sort by:
   - Overdue tasks first (most overdue at top)
   - Today's tasks second
   - Within each group, sort by priority (P0 → P1 → P2 → P3)

4. **Format output** (always use markdown tables):
```
## Due Today & Overdue Tasks

### OVERDUE

| Status | Task | Priority | Category | Overdue |
|--------|------|----------|----------|---------|
| `[s]` | Task name | P0 | category | 3 days |
| `[n]` | Task name | P1 | category | 1 day |

### DUE TODAY

| Status | Task | Priority | Category |
|--------|------|----------|----------|
| `[s]` | Task name | P0 | category |

---
Total: X overdue, Y due today
```

- If no tasks are due/overdue, say so clearly and suggest reviewing P0/P1 tasks
- Recommend specific next actions based on what's found

---

## upcoming

Show all tasks due in the next 7 days (or custom timeframe if specified).

**Steps:**

1. **Determine timeframe**:
   - Default: next 7 days
   - If $ARGUMENTS contains a number, use that many days instead

2. **Try MCP first**: Use `list_tasks` MCP tool and filter by date range

3. **Failover if needed**: If MCP tools fail:
   - Use `Glob` to find all files in `tasks/*.md`
   - Use `Read` to parse each task file's frontmatter
   - Filter for tasks where `due_date` is between today and end of timeframe
   - Exclude overdue tasks (those are shown in the `today` view)
   - Note: "Using direct file reading (MCP unavailable)"

4. **Group by date**: Organize tasks by their due date in chronological order

5. **Format output** (always use markdown tables, grouped by date):
```
## Upcoming Tasks (Next 7 Days)

### Tomorrow (YYYY-MM-DD)

| Status | Task | Priority | Category | File |
|--------|------|----------|----------|------|
| `[n]` | Task name | P0 | category | `tasks/filename.md` |

### Wednesday (YYYY-MM-DD)

| Status | Task | Priority | Category | File |
|--------|------|----------|----------|------|
| `[s]` | Task name | P1 | category | `tasks/filename.md` |
| `[n]` | Task name | P2 | category | `tasks/filename.md` |

---
Total: X tasks across Y days
```

- Use relative dates when helpful (Tomorrow, This Friday, etc.)
- Highlight P0/P1 tasks for visibility
- If no tasks in timeframe, suggest reviewing task priorities and deadlines

---

## all

Display all tasks with their details in a clear, organized format.

**Steps:**

1. **Try MCP first**: Use `get_task_summary` and `list_tasks` MCP tools

2. **Failover if needed**: If MCP tools fail:
   - Use `Glob` to find all files in `tasks/*.md`
   - Use `Read` to parse each task file's frontmatter
   - Note: "Using direct file reading (MCP unavailable)"

3. **Apply filters**: If $ARGUMENTS provided, filter by:
   - Priority: P0, P1, P2, P3
   - Status: n (not started), s (started), b (blocked), d (done)
   - Category

4. **Format output** (always use markdown tables, grouped by priority):
```
## All Open Tasks

**Task Summary:** X total tasks (P0: X/3, P1: X/7, P2: X/15, P3: X)

### P0 (Critical) — Max 3

| Status | Task | Category | Due | File |
|--------|------|----------|-----|------|
| `[s]` | Task name | category | YYYY-MM-DD | `tasks/filename.md` |

### P1 (High) — Max 7

| Status | Task | Category | Due | File |
|--------|------|----------|-----|------|
| `[n]` | Task name | category | — | `tasks/filename.md` |

...
```

5. **Highlight important items**:
   - Flag overdue tasks (compare due_date to $TODAY)
   - Show P0 tasks prominently
   - Indicate blocked tasks
   - Show priority cap status (P0: max 3, P1: max 7, P2: max 15)

- If no tasks found, suggest checking BACKLOG.md or creating new tasks
