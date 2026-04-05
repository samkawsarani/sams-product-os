---
name: process-backlog
model: sonnet
description: Processes BACKLOG.md into organized tasks, initiatives, and references with categorization, deduplication, and priority cap enforcement. Presents findings for review before creating. Invoked via /process-backlog or "triage the backlog", "clean up the backlog", or "organize my brain dump".
allowed-tools: process_backlog, clear_backlog, check_duplicates, create_task, list_tasks, Glob, Read, Write, Bash(qmd *)
argument-hint:
---

## Context

- Config: `tools/mcp-servers/task-manager/config.yaml` (priority caps, category keywords, duplicate thresholds)
- Today's date: $TODAY

## Workflow

**Always present findings for user review before creating anything.**

### Step 1: Analyze Backlog

Read `BACKLOG.md` and categorize each item:

| Category | Destination | Examples |
|----------|-------------|----------|
| **Tasks** | `tasks/` | "Email Sarah about Q4", "Review PRD draft" - clear action + completion criteria |
| **Initiatives** | `initiatives/` | "Mobile perf issues", "Enterprise SSO" - strategic ideas to explore |
| **References** | `knowledge/references/` or related initiative folder | Articles, competitor info, research - context to save |
| **Notes** | Discard (summary only) | Meeting notes, incomplete thoughts |

If MCP available, use **process_backlog** (auto_create=false). Otherwise, read files directly.

### Step 2: Check for Duplicates

Compare against existing items in `tasks/`, `initiatives/`, `knowledge/references/`.

### Step 3: Present Findings

Show user a summary with:
- **Tasks**: Table with title, category, priority, due date
- **Initiatives**: Bullet list with name + description
- **References**: Bullet list (noting if any relate to an existing initiative folder)
- **Ambiguous items**: Items needing clarification
- **Possible duplicates**: Similar existing items
- **Notes**: Remaining content (will be discarded)

### Step 4: Get Confirmation

Ask: "How would you like to proceed?"

**Wait for user response before creating anything.**

### Step 5: Resolve Ambiguities

For vague items, ask:
- What specific action should be taken?
- When does this need to be done?
- Why does this matter?

### Step 6: Enforce Priority Caps

Check caps from `tools/mcp-servers/task-manager/config.yaml` before creating. If exceeded:
1. Show current tasks at that priority
2. Ask user to demote existing or downgrade new task
3. Wait for decision

### Step 7: Create Approved Items

**Tasks**: Create with frontmatter including:
- title, category (from `tools/mcp-servers/task-manager/config.yaml` keywords), priority, status: n, created_date, due_date
- `resource_refs: []` in frontmatter
- Full context from backlog item (description, sub-bullets) preserved in Context section
- `**Goal:** [Link to relevant goal from GOALS.md]` line in Context section

**Initiatives**: Create in `initiatives/` with format: Summary, Opportunity, Status, Open Questions

**References**: If related to an existing initiative folder (e.g., `initiatives/vertical-expansion/`), save there. Otherwise save in `knowledge/references/`.

### Step 8: Clear & Re-index

1. Clear `BACKLOG.md` using `clear_backlog`
2. Run `qmd update && qmd embed` (via Bash) to re-index collections with new content
3. Summarize what was created: tasks (by priority), initiatives, references (with locations)

## Key Reminders

- **Never auto-create** - Always present findings first
- **Ask for clarification** on ambiguous items before creating
- **Link to goals** - If no goal fits, ask user to clarify why it matters
- Fewer clear items > many vague ones
