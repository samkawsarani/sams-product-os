---
name: process-backlog
model: sonnet
description: Processes tasks/BACKLOG.md into organized tasks, opportunities, and references. Presents findings for review before creating anything. Invoked via /process-backlog or "triage the backlog", "clean up the backlog", or "organize my brain dump".
allowed-tools: Glob, Read, Write, Bash(qmd *)
argument-hint:
---

## Context

- Backlog: `tasks/BACKLOG.md`
- Today's date: $TODAY

## Workflow

**Always present findings for user review before creating anything.**

### Step 1: Analyze Backlog

Read `tasks/BACKLOG.md` and categorize each item:

| Category | Destination | Examples |
|----------|-------------|----------|
| **Tasks** | Stay in `tasks/BACKLOG.md` | "Email Sarah about Q4", "Review PRD draft" — clear action, stays until moved to ACTIVE.md |
| **Opportunities** | `knowledge/opportunities/` | "Mobile perf issues", "Enterprise SSO pattern" — things observed worth exploring |
| **References** | `knowledge/references/` | Articles, competitor info, research — context to save |
| **Notes** | Discard (summary only) | Meeting notes, incomplete thoughts |

Read `tasks/BACKLOG.md` directly.

### Step 2: Check for Duplicates

Compare proposed items against existing content in `tasks/BACKLOG.md`, `tasks/ACTIVE.md`, and `knowledge/opportunities/`.

Scan `tasks/BACKLOG.md`, `tasks/ACTIVE.md`, and `knowledge/opportunities/` directly.

### Step 3: Present Findings

Show user a summary with:
- **Tasks** (staying in backlog): Bullet list with title
- **Opportunities**: Bullet list with name + description
- **References**: Bullet list
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

### Step 6: Create Approved Items

**Tasks**: Tasks stay as lines in `tasks/BACKLOG.md` — no individual files. Organize them under the appropriate topic header. Verify each task connects to a goal from `GOALS.md`. If no goal fits, flag it and ask user to clarify why it matters before adding.

**Opportunities**: Create in `knowledge/opportunities/` using `templates/opportunity-template.md`. Fill in what was observed and why it might matter.

**References**: Save in `knowledge/references/`.

### Step 7: Re-index

Run `qmd update && qmd embed` (via Bash) to re-index collections with new content.
Summarize what was organized: tasks kept (by topic), opportunities created, references saved.

## Key Reminders

- **Never auto-create** — Always present findings first
- **Ask for clarification** on ambiguous items before creating
- **Link to goals** — If no goal fits, ask user to clarify why it matters
- **Tasks stay in the backlog** — they move to ACTIVE.md during weekly planning, not into individual files
- **Opportunities ≠ Projects** — opportunities go to `knowledge/opportunities/`, projects are created separately when you commit
- Fewer clear items > many vague ones
