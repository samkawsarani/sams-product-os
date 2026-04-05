# Task Manager MCP Server

Detailed documentation for the Sams Product OS task management MCP server.

## Setup

### 1. Install Dependencies

From the project root:

```bash
uv sync
```

Dependencies are managed in the root `pyproject.toml`.

### 2. Configure MCP Client

Add to your MCP client configuration (e.g., Claude Code, Cursor):

**For Claude Code** (`.mcp.json` in project root):

```json
{
  "mcpServers": {
    "pm-tasks": {
      "command": "uv",
      "args": ["run", "python", "tools/mcp-servers/task-manager/server.py"]
    }
  }
}
```

**For Cursor** (`.cursor/mcp.json` in project root):

```json
{
  "mcpServers": {
    "pm-tasks": {
      "command": "uv",
      "args": ["run", "python", "tools/mcp-servers/task-manager/server.py"]
    }
  }
}
```

### 3. Restart Your MCP Client

Restart Claude Code, Cursor, or your MCP client to load the server.

---

## Tool Reference

### Task Operations

#### list_tasks
Filter and list tasks by various criteria.

**Parameters:**
- `priority` (optional): P0/P1/P2/P3
- `status` (optional): n/s/b/d
- `category` (optional): Filter by category
- `days_old` (optional): Created more than N days ago

**Returns:** List of matching tasks with title, file, priority, status, category

**Example:**
```
List all P0 tasks that are started
→ list_tasks(priority="P0", status="s")
```

#### get_task
Get full details of a specific task.

**Parameters:**
- `filename` (required): Task filename (e.g., "fix-auth-bug.md")

**Returns:** Full task details including frontmatter and body

**Example:**
```
→ get_task(filename="fix-auth-bug.md")
```

#### create_task
Create a new task with smart category templates.

**Parameters:**
- `title` (required): Task title
- `priority` (required): P0/P1/P2/P3
- `body` (required): Task description
- `category` (optional): Auto-categorizes if not provided
- `keywords` (optional): For deduplication
- `due_date` (optional): YYYY-MM-DD format

**Features:**
- Enforces priority caps
- Auto-categorization based on keywords
- Category-specific templates (technical, outreach, research, writing, admin)
- Generates structured markdown

**Example:**
```
→ create_task(
    title="Fix authentication bug",
    priority="P1",
    body="Users unable to login with SSO",
    category="technical"
  )
```

#### update_task_status
Change task status. When status is set to `d` (done), the task is automatically archived to `tasks/_archived/YYYY-MM-DD-filename.md`.

**Parameters:**
- `filename` (required): Task filename
- `status` (required): n/s/b/d

**Example:**
```
→ update_task_status(filename="fix-auth-bug.md", status="s")
→ update_task_status(filename="fix-auth-bug.md", status="d")
  # Auto-archives to tasks/_archived/2026-02-23-fix-auth-bug.md
```

#### update_task_priority
Change task priority with cap enforcement.

**Parameters:**
- `filename` (required): Task filename
- `priority` (required): P0/P1/P2/P3

**Example:**
```
→ update_task_priority(filename="fix-auth-bug.md", priority="P0")
```

### Task Intelligence

#### get_task_summary
Get statistics across all tasks.

**Returns:**
- Total task count
- Counts by priority (with caps)
- Counts by status
- Counts by category

**Example:**
```
→ get_task_summary()
```

#### find_stale_tasks
Find tasks started but not updated recently.

**Config:** `task_aging.flag_stale_after` (default: 14 days)

**Returns:** Tasks with status="s" inactive 14+ days

**Example:**
```
→ find_stale_tasks()
```

#### find_overdue_tasks
Find tasks past their due date.

**Returns:** Tasks with due_date < today and status != "d"

**Example:**
```
→ find_overdue_tasks()
```

#### prune_completed_tasks
Delete archived completed tasks older than the configured threshold. Scans `tasks/_archived/` and parses the date prefix from filenames (falls back to `updated_date` frontmatter).

**Parameters:**
- `dry_run` (optional): Preview without deleting (default: false)

**Config:** `task_aging.prune_completed_after` (default: 90 days)

**Example:**
```
Preview: prune_completed_tasks(dry_run=true)
Delete: prune_completed_tasks(dry_run=false)
```

#### check_duplicates
Check for similar tasks with actionable suggestions.

**Parameters:**
- `title` (required): Proposed task title
- `keywords` (optional): Proposed keywords
- `category` (optional): Proposed category

**Features:**
- Similarity scoring (title + keywords + category)
- Explains why tasks matched
- Status-aware suggestions

**Example:**
```
→ check_duplicates(
    title="Fix login bug",
    keywords=["auth", "bug"],
    category="technical"
  )
```

### Backlog Processing

#### process_backlog
Automated BACKLOG.md processing with intelligence.

**Parameters:**
- `auto_create` (optional): Create tasks automatically (default: false)

**Features:**
- Ambiguity detection (flags vague items)
- Duplicate detection
- Auto-categorization
- Opportunity vs. task classification
- Smart templates

**Returns:**
- Tasks to create
- Opportunities identified
- Ambiguous items with clarification questions
- Possible duplicates

**Workflow:**
```
1. process_backlog(auto_create=false)  # Preview
2. Review ambiguous items with user
3. process_backlog(auto_create=true)   # Create
4. clear_backlog()                      # Reset
```

**Example:**
```
→ process_backlog(auto_create=false)
```

#### clear_backlog
Reset BACKLOG.md to empty state.

**Parameters:** None

**Example:**
```
→ clear_backlog()
```

## Smart Task Templates

Tasks created via `create_task` or `process_backlog` use category-specific templates:

### Technical
```markdown
## Context
[Why this matters]

## Technical Details
- **Tech Stack:** [Technologies]
- **Dependencies:** [What this depends on]
- **Risks:** [Technical risks]

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Next Actions
- [ ] First step
- [ ] Second step

## Progress Log
- 2026-01-05: Task created
```

### Outreach
```markdown
## Context
[Why this matters]

## Contact Details
- **Who:** [Name/organization]
- **Channel:** [Email/call/meeting]
- **Best time:** [When to reach out]

## Talking Points
- Point 1
- Point 2

## Follow-up
- [ ] Schedule follow-up
- [ ] Document outcome

## Progress Log
- 2026-01-05: Task created
```

### Research
```markdown
## Context
[Why this matters]

## Questions to Answer
- Question 1
- Question 2

## Sources to Check
- Source 1
- Source 2

## Synthesis
[Document findings]

## Next Actions
- [ ] Research step 1
- [ ] Synthesize findings

## Progress Log
- 2026-01-05: Task created
```

### Writing
```markdown
## Context
[Why this matters]

## Audience
[Who is this for?]

## Key Points
- Point 1
- Point 2

## Outline
1. Section 1
2. Section 2

## Next Actions
- [ ] Draft outline
- [ ] Write first draft
- [ ] Review and edit

## Progress Log
- 2026-01-05: Task created
```

### Admin / Other
```markdown
## Context
[Why this matters]

## Details
[Additional details]

## Next Actions
- [ ] First step
- [ ] Second step

## Progress Log
- 2026-01-05: Task created
```

## Testing

### Running Tests

From the project root:

```bash
uv run pytest tools/mcp-servers/task-manager/test_server.py -v
```

### Test Coverage

Tests validate:
- ✓ Ambiguity detection (too short, no verbs, vague language)
- ✓ Clarification question generation
- ✓ Task content generation for each category
- ✓ Similarity calculation
- ✓ Auto-categorization
- ✓ Priority cap enforcement
- ✓ Duplicate detection
- ✓ Backlog parsing
- ✓ Task creation with templates
- ✓ Task archiving on completion
- ✓ Archived task retrieval (include_archived flag)

### Writing Tests

Add tests to `test_server.py` for new functionality:

```python
def test_new_feature():
    # Test setup
    result = your_function()
    assert result == expected
```

## Configuration

All settings in `tools/mcp-servers/task-manager/config.yaml`:

```yaml
priority_caps:
  P0: 3
  P1: 7
  P2: 15
  P3: 999

task_aging:
  prune_completed_after: 90
  flag_stale_after: 14

deduplication:
  similarity_threshold: 0.6
  check_categories: true
  check_keywords: true

category_keywords:
  technical: [code, api, bug, fix]
  outreach: [email, meeting, call]
  research: [research, study, analyze]
  writing: [write, draft, document]
  admin: [schedule, organize, calendar]
```

## Troubleshooting

**Ambiguity detection too sensitive?**
- Adjust `is_ambiguous()` thresholds in server.py
- Add more action verbs to the list

**Duplicates not detected?**
- Lower `similarity_threshold` in `config.yaml`
- Enable `check_keywords` and `check_categories` in `config.yaml`
- Add more keywords to tasks

**Priority caps hit?**
- Check `get_task_summary()` for current counts
- Adjust caps in `tools/mcp-servers/task-manager/config.yaml` or deprioritize tasks

**Category not auto-assigned?**
- Add keywords to `category_keywords` in `tools/mcp-servers/task-manager/config.yaml`
- Check keyword matching logic in `auto_categorize()`
