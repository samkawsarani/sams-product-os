#!/usr/bin/env -S uv run python
"""
SAMS PRODUCT OS Task Management MCP Server

Provides programmatic access to task management through Model Context Protocol.
Exposes 10 tools for CRUD operations, deduplication, priority enforcement, and statistics.
"""

import asyncio
import re
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Optional

import yaml
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
TASKS_DIR = PROJECT_ROOT / "tasks"
CONFIG_FILE = PROJECT_ROOT / "config.yaml"

# Initialize MCP server
app = Server("pm-tasks")


# Helper Functions

def load_config() -> dict:
    """Load configuration from config.yaml"""
    if not CONFIG_FILE.exists():
        return {
            "priority_caps": {"P0": 3, "P1": 7, "P2": 15, "P3": 999},
            "task_aging": {"prune_completed_after": 90, "flag_stale_after": 14},
            "deduplication": {
                "similarity_threshold": 0.6,
                "check_categories": True,
                "check_keywords": True,
            },
            "category_keywords": {},
        }

    with open(CONFIG_FILE, "r") as f:
        return yaml.safe_load(f)


def parse_yaml_frontmatter(file_path: Path) -> tuple[dict, str]:
    """Parse YAML frontmatter and markdown body from a task file"""
    if not file_path.exists():
        return {}, ""

    with open(file_path, "r") as f:
        content = f.read()

    # Match YAML frontmatter between --- delimiters
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if not match:
        return {}, content

    frontmatter_str, body = match.groups()
    try:
        frontmatter = yaml.safe_load(frontmatter_str) or {}
    except yaml.YAMLError:
        frontmatter = {}

    return frontmatter, body.strip()


def write_task_file(file_path: Path, frontmatter: dict, body: str):
    """Write task file with YAML frontmatter"""
    yaml_str = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
    content = f"---\n{yaml_str}---\n\n{body}\n"

    with open(file_path, "w") as f:
        f.write(content)


def get_all_tasks() -> list[dict]:
    """Get all tasks with metadata"""
    tasks = []

    if not TASKS_DIR.exists():
        return tasks

    for task_file in TASKS_DIR.glob("*.md"):
        if task_file.name == "README.md":
            continue

        frontmatter, body = parse_yaml_frontmatter(task_file)
        task = {
            "file": task_file.name,
            "path": str(task_file),
            "title": frontmatter.get("title", ""),
            "priority": frontmatter.get("priority", "P3"),
            "status": frontmatter.get("status", "n"),
            "category": frontmatter.get("category", ""),
            "keywords": frontmatter.get("keywords", []),
            "due_date": frontmatter.get("due_date"),
            "created_date": frontmatter.get("created_date"),
            "updated_date": frontmatter.get("updated_date"),
            "body": body,
        }
        tasks.append(task)

    return tasks


def calculate_similarity(task1: dict, task2: dict, config: dict) -> float:
    """Calculate similarity score between two tasks (0-1 scale)"""
    # Title similarity using SequenceMatcher
    title1 = task1.get("title", "").lower()
    title2 = task2.get("title", "").lower()
    title_score = SequenceMatcher(None, title1, title2).ratio()

    # Keyword overlap if enabled
    keyword_score = 0.0
    if config["deduplication"]["check_keywords"]:
        keywords1 = set(k.lower() for k in task1.get("keywords", []))
        keywords2 = set(k.lower() for k in task2.get("keywords", []))

        if keywords1 and keywords2:
            overlap = len(keywords1 & keywords2)
            total = len(keywords1 | keywords2)
            keyword_score = overlap / total if total > 0 else 0.0

    # Category match if enabled
    category_match = 1.0
    if config["deduplication"]["check_categories"]:
        cat1 = task1.get("category", "").lower()
        cat2 = task2.get("category", "").lower()
        category_match = 1.0 if cat1 == cat2 else 0.5

    # Weighted average: title (60%), keywords (30%), category (10%)
    similarity = (title_score * 0.6 + keyword_score * 0.3) * category_match
    return similarity


def auto_categorize(title: str, body: str, config: dict) -> str:
    """Auto-categorize task based on keywords in config"""
    text = f"{title} {body}".lower()
    category_keywords = config.get("category_keywords", {})

    # Count keyword matches for each category
    matches = {}
    for category, keywords in category_keywords.items():
        count = sum(1 for keyword in keywords if keyword.lower() in text)
        if count > 0:
            matches[category] = count

    # Return category with most matches
    if matches:
        return max(matches, key=matches.get)

    return ""


def get_task_by_file(filename: str) -> Optional[dict]:
    """Get task by filename"""
    task_file = TASKS_DIR / filename
    if not task_file.exists():
        return None

    frontmatter, body = parse_yaml_frontmatter(task_file)
    return {
        "file": filename,
        "path": str(task_file),
        "title": frontmatter.get("title", ""),
        "priority": frontmatter.get("priority", "P3"),
        "status": frontmatter.get("status", "n"),
        "category": frontmatter.get("category", ""),
        "keywords": frontmatter.get("keywords", []),
        "due_date": frontmatter.get("due_date"),
        "created_date": frontmatter.get("created_date"),
        "updated_date": frontmatter.get("updated_date"),
        "body": body,
    }


def is_ambiguous(text: str) -> tuple[bool, str]:
    """
    Check if a backlog item is too vague/ambiguous to become a task.
    Returns (is_ambiguous, reason)
    """
    text = text.strip()

    # Too short
    if len(text) < 10:
        return True, "Item too short (less than 10 characters)"

    # Check for action verbs or urgency indicators
    action_verbs = [
        "add", "update", "fix", "create", "write", "review", "send", "email",
        "call", "schedule", "research", "analyze", "implement", "deploy",
        "design", "test", "document", "refactor", "contact", "follow up",
        "debug", "investigate", "explore", "consider", "evaluate", "assess",
        "patch", "restore", "resolve", "address", "handle", "complete", "finish"
    ]
    # Words that imply action is needed even without explicit verb
    urgency_indicators = [
        "bug", "vulnerability", "downtime", "outage", "broken", "failing",
        "urgent", "critical", "immediate", "asap", "need to", "needs to",
        "must", "required", "deadline", "due", "blocked", "blocking"
    ]
    has_action = any(verb in text.lower() for verb in action_verbs)
    has_urgency = any(indicator in text.lower() for indicator in urgency_indicators)

    if not has_action and not has_urgency:
        return True, "No clear action verb found"

    # Check for vague language
    vague_words = ["something", "maybe", "should", "might", "possibly", "think about"]
    has_vague = any(word in text.lower() for word in vague_words)

    if has_vague:
        return True, f"Contains vague language: {[w for w in vague_words if w in text.lower()]}"

    # Check for vague targets (has action verb but unclear what it applies to)
    vague_targets = [
        "the thing", "the issue", "the problem", "that thing", "this thing",
        "that problem", "this problem", "that issue", "this issue"
    ]
    has_vague_target = any(target in text.lower() for target in vague_targets)

    if has_vague_target:
        return True, "Contains vague target reference"

    return False, ""


def generate_clarification_questions(item: str) -> list[str]:
    """Generate questions to clarify an ambiguous backlog item"""
    questions = []

    item_lower = item.lower()

    # Check what's missing
    has_deadline_words = any(word in item_lower for word in ["by", "due", "deadline", "before"])
    has_context_words = any(word in item_lower for word in ["because", "for", "to help", "context"])

    if not has_deadline_words:
        questions.append("When does this need to be done? (today, this week, this month, no deadline)")

    if not has_context_words:
        questions.append("Why does this matter? What's the context or goal?")

    # Check for specific action
    is_vague, reason = is_ambiguous(item)
    if is_vague and "action verb" in reason:
        questions.append("What specific action should be taken?")

    if not questions:
        questions.append("Can you provide more details about what needs to be done?")

    return questions


def generate_task_content(title: str, category: str, context: str = "") -> str:
    """
    Generate category-specific task content with appropriate sections.
    Returns markdown body for the task.
    """
    # Base template
    content = f"## Context\n{context if context else '[Why this task matters]'}\n\n"

    # Category-specific sections
    if category == "technical":
        content += """## Technical Details
- **Tech Stack:** [List relevant technologies]
- **Dependencies:** [What this depends on]
- **Risks:** [Technical risks or blockers]

## Acceptance Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]

## Next Actions
- [ ] [First step]
- [ ] [Second step]
"""

    elif category == "outreach":
        content += """## Contact Details
- **Who:** [Name/organization]
- **Channel:** [Email/call/meeting]
- **Best time:** [When to reach out]

## Talking Points
- [Point 1]
- [Point 2]

## Follow-up
- [ ] [Schedule follow-up]
- [ ] [Document outcome]
"""

    elif category == "research":
        content += """## Questions to Answer
- [Question 1]
- [Question 2]

## Sources to Check
- [Source 1]
- [Source 2]

## Synthesis
[Document findings here]

## Next Actions
- [ ] [Research step 1]
- [ ] [Synthesize findings]
"""

    elif category == "writing":
        content += """## Audience
[Who is this for?]

## Key Points
- [Point 1]
- [Point 2]

## Outline
1. [Section 1]
2. [Section 2]

## Next Actions
- [ ] Draft outline
- [ ] Write first draft
- [ ] Review and edit
"""

    else:  # admin or other
        content += """## Details
[Additional details about this task]

## Next Actions
- [ ] [First step]
- [ ] [Second step]
"""

    content += "\n## Progress Log\n"
    content += f"- {datetime.now().strftime('%Y-%m-%d')}: Task created\n"

    return content


# MCP Tool Handlers

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools"""
    return [
        Tool(
            name="list_tasks",
            description="List and filter tasks by priority, status, category, or age. Returns task summaries.",
            inputSchema={
                "type": "object",
                "properties": {
                    "priority": {
                        "type": "string",
                        "description": "Filter by priority (P0, P1, P2, P3)",
                        "enum": ["P0", "P1", "P2", "P3"],
                    },
                    "status": {
                        "type": "string",
                        "description": "Filter by status (n=not started, s=started, b=blocked, d=done)",
                        "enum": ["n", "s", "b", "d"],
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter by category (technical, outreach, research, writing, admin, strategy, stakeholder, discovery)",
                    },
                    "days_old": {
                        "type": "integer",
                        "description": "Filter tasks created more than N days ago",
                    },
                },
            },
        ),
        Tool(
            name="get_task",
            description="Get full details of a specific task by filename",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Task filename (e.g., 'fix-auth-bug.md')",
                    }
                },
                "required": ["filename"],
            },
        ),
        Tool(
            name="create_task",
            description="Create a new task with YAML frontmatter. Auto-categorizes if category not provided. Checks priority caps.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Task title"},
                    "priority": {
                        "type": "string",
                        "description": "Priority (P0, P1, P2, P3)",
                        "enum": ["P0", "P1", "P2", "P3"],
                    },
                    "category": {
                        "type": "string",
                        "description": "Category (optional, will auto-categorize if not provided)",
                    },
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Keywords for deduplication and categorization",
                    },
                    "body": {
                        "type": "string",
                        "description": "Task description in markdown",
                    },
                    "due_date": {
                        "type": "string",
                        "description": "Due date (YYYY-MM-DD format)",
                    },
                },
                "required": ["title", "priority", "body"],
            },
        ),
        Tool(
            name="update_task_status",
            description="Update task status (n=not started, s=started, b=blocked, d=done)",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Task filename (e.g., 'fix-auth-bug.md')",
                    },
                    "status": {
                        "type": "string",
                        "description": "New status",
                        "enum": ["n", "s", "b", "d"],
                    },
                },
                "required": ["filename", "status"],
            },
        ),
        Tool(
            name="update_task_priority",
            description="Update task priority. Checks priority caps before updating.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Task filename (e.g., 'fix-auth-bug.md')",
                    },
                    "priority": {
                        "type": "string",
                        "description": "New priority",
                        "enum": ["P0", "P1", "P2", "P3"],
                    },
                },
                "required": ["filename", "priority"],
            },
        ),
        Tool(
            name="get_task_summary",
            description="Get task statistics (counts by priority, status, category)",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="find_stale_tasks",
            description="Find tasks marked as started but not updated recently (uses flag_stale_after from config)",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="find_overdue_tasks",
            description="Find tasks past their due date",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="prune_completed_tasks",
            description="Delete tasks with status 'd' (done) older than specified days (uses prune_completed_after from config)",
            inputSchema={
                "type": "object",
                "properties": {
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true, only list tasks that would be deleted without deleting them",
                    }
                },
            },
        ),
        Tool(
            name="check_duplicates",
            description="Check for similar existing tasks before creating a new one. Uses similarity scoring with actionable recommendations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Proposed task title"},
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Proposed keywords",
                    },
                    "category": {
                        "type": "string",
                        "description": "Proposed category",
                    },
                },
                "required": ["title"],
            },
        ),
        Tool(
            name="process_backlog",
            description="Process all items from BACKLOG.md with automated categorization, deduplication, and ambiguity detection. Returns summary of what would be created and flags any items needing clarification.",
            inputSchema={
                "type": "object",
                "properties": {
                    "auto_create": {
                        "type": "boolean",
                        "description": "If true, automatically create tasks/initiatives. If false (default), only return summary for review.",
                    }
                },
            },
        ),
        Tool(
            name="clear_backlog",
            description="Archive current BACKLOG.md content to tasks/_archived/ and reset backlog to empty state.",
            inputSchema={
                "type": "object",
                "properties": {
                    "archive": {
                        "type": "boolean",
                        "description": "If true (default), archive to tasks/_archived/. If false, just clear without archiving.",
                    }
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""
    config = load_config()

    if name == "list_tasks":
        tasks = get_all_tasks()

        # Apply filters
        if "priority" in arguments:
            tasks = [t for t in tasks if t["priority"] == arguments["priority"]]

        if "status" in arguments:
            tasks = [t for t in tasks if t["status"] == arguments["status"]]

        if "category" in arguments:
            tasks = [t for t in tasks if t["category"] == arguments["category"]]

        if "days_old" in arguments:
            cutoff = datetime.now() - timedelta(days=arguments["days_old"])
            tasks = [
                t
                for t in tasks
                if t.get("created_date")
                and datetime.fromisoformat(t["created_date"]) < cutoff
            ]

        # Format output
        result = f"Found {len(tasks)} tasks:\n\n"
        for task in tasks:
            result += f"- **{task['title']}** ({task['file']})\n"
            result += f"  Priority: {task['priority']} | Status: {task['status']} | Category: {task['category']}\n\n"

        return [TextContent(type="text", text=result)]

    elif name == "get_task":
        filename = arguments["filename"]
        task = get_task_by_file(filename)

        if not task:
            return [TextContent(type="text", text=f"Task not found: {filename}")]

        result = f"# {task['title']}\n\n"
        result += f"**File:** {task['file']}\n"
        result += f"**Priority:** {task['priority']}\n"
        result += f"**Status:** {task['status']}\n"
        result += f"**Category:** {task['category']}\n"
        result += f"**Keywords:** {', '.join(task['keywords'])}\n"
        result += f"**Due Date:** {task.get('due_date', 'None')}\n"
        result += f"**Created:** {task.get('created_date', 'Unknown')}\n"
        result += f"**Updated:** {task.get('updated_date', 'Unknown')}\n\n"
        result += f"## Description\n\n{task['body']}\n"

        return [TextContent(type="text", text=result)]

    elif name == "create_task":
        # Check priority caps
        priority = arguments["priority"]
        priority_caps = config["priority_caps"]
        current_tasks = get_all_tasks()
        current_count = len([t for t in current_tasks if t["priority"] == priority and t["status"] != "d"])

        if current_count >= priority_caps.get(priority, 999):
            return [
                TextContent(
                    type="text",
                    text=f"Cannot create task: {priority} cap ({priority_caps[priority]}) would be exceeded. Current {priority} tasks: {current_count}",
                )
            ]

        # Auto-categorize if category not provided
        category = arguments.get("category", "")
        if not category:
            category = auto_categorize(
                arguments["title"], arguments.get("body", ""), config
            )

        # Generate filename from title
        filename = re.sub(r"[^a-z0-9]+", "-", arguments["title"].lower())
        filename = filename.strip("-") + ".md"
        task_file = TASKS_DIR / filename

        # Check if file already exists
        if task_file.exists():
            return [
                TextContent(
                    type="text", text=f"Task file already exists: {filename}"
                )
            ]

        # Create frontmatter
        now = datetime.now().isoformat()
        frontmatter = {
            "title": arguments["title"],
            "priority": priority,
            "status": "n",
            "category": category,
            "keywords": arguments.get("keywords", []),
            "created_date": now,
            "updated_date": now,
        }

        if "due_date" in arguments:
            frontmatter["due_date"] = arguments["due_date"]

        # Write task file
        write_task_file(task_file, frontmatter, arguments["body"])

        result = f"Task created: {filename}\n"
        result += f"Priority: {priority}\n"
        result += f"Category: {category}\n"
        result += f"Status: n (not started)\n"

        return [TextContent(type="text", text=result)]

    elif name == "update_task_status":
        filename = arguments["filename"]
        task_file = TASKS_DIR / filename

        if not task_file.exists():
            return [TextContent(type="text", text=f"Task not found: {filename}")]

        frontmatter, body = parse_yaml_frontmatter(task_file)
        frontmatter["status"] = arguments["status"]
        frontmatter["updated_date"] = datetime.now().isoformat()

        write_task_file(task_file, frontmatter, body)

        return [
            TextContent(
                type="text",
                text=f"Updated {filename} status to: {arguments['status']}",
            )
        ]

    elif name == "update_task_priority":
        filename = arguments["filename"]
        new_priority = arguments["priority"]
        task_file = TASKS_DIR / filename

        if not task_file.exists():
            return [TextContent(type="text", text=f"Task not found: {filename}")]

        # Get current task
        frontmatter, body = parse_yaml_frontmatter(task_file)
        old_priority = frontmatter.get("priority", "P3")

        # Check priority caps (excluding current task from count)
        priority_caps = config["priority_caps"]
        current_tasks = get_all_tasks()
        current_count = len(
            [
                t
                for t in current_tasks
                if t["priority"] == new_priority and t["file"] != filename and t["status"] != "d"
            ]
        )

        if current_count >= priority_caps.get(new_priority, 999):
            return [
                TextContent(
                    type="text",
                    text=f"Cannot update priority: {new_priority} cap ({priority_caps[new_priority]}) would be exceeded. Current {new_priority} tasks: {current_count}",
                )
            ]

        frontmatter["priority"] = new_priority
        frontmatter["updated_date"] = datetime.now().isoformat()

        write_task_file(task_file, frontmatter, body)

        return [
            TextContent(
                type="text",
                text=f"Updated {filename} priority from {old_priority} to {new_priority}",
            )
        ]

    elif name == "get_task_summary":
        tasks = get_all_tasks()

        # Count by priority
        priority_counts = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
        for task in tasks:
            priority_counts[task["priority"]] += 1

        # Count by status
        status_counts = {"n": 0, "s": 0, "b": 0, "d": 0}
        for task in tasks:
            status_counts[task["status"]] += 1

        # Count by category
        category_counts = {}
        for task in tasks:
            cat = task["category"] or "uncategorized"
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # Format output
        result = f"# Task Summary\n\n"
        result += f"**Total Tasks:** {len(tasks)}\n\n"

        result += f"## By Priority\n"
        for priority in ["P0", "P1", "P2", "P3"]:
            cap = config["priority_caps"].get(priority, 999)
            count = priority_counts[priority]
            result += f"- {priority}: {count}/{cap}\n"

        result += f"\n## By Status\n"
        status_names = {"n": "Not Started", "s": "Started", "b": "Blocked", "d": "Done"}
        for status, count in status_counts.items():
            result += f"- {status_names[status]}: {count}\n"

        result += f"\n## By Category\n"
        for category, count in sorted(category_counts.items()):
            result += f"- {category}: {count}\n"

        return [TextContent(type="text", text=result)]

    elif name == "find_stale_tasks":
        tasks = get_all_tasks()
        flag_stale_after = config["task_aging"]["flag_stale_after"]
        cutoff = datetime.now() - timedelta(days=flag_stale_after)

        stale_tasks = [
            t
            for t in tasks
            if t["status"] == "s"
            and t.get("updated_date")
            and datetime.fromisoformat(t["updated_date"]) < cutoff
        ]

        if not stale_tasks:
            return [
                TextContent(
                    type="text",
                    text=f"No stale tasks found (started but not updated in {flag_stale_after}+ days)",
                )
            ]

        result = f"Found {len(stale_tasks)} stale tasks (started but not updated in {flag_stale_after}+ days):\n\n"
        for task in stale_tasks:
            days_old = (
                datetime.now() - datetime.fromisoformat(task["updated_date"])
            ).days
            result += f"- **{task['title']}** ({task['file']})\n"
            result += f"  Last updated: {days_old} days ago | Priority: {task['priority']}\n\n"

        return [TextContent(type="text", text=result)]

    elif name == "find_overdue_tasks":
        tasks = get_all_tasks()
        today = datetime.now().date()

        overdue_tasks = [
            t
            for t in tasks
            if t.get("due_date")
            and datetime.fromisoformat(t["due_date"]).date() < today
            and t["status"] != "d"
        ]

        if not overdue_tasks:
            return [TextContent(type="text", text="No overdue tasks found")]

        result = f"Found {len(overdue_tasks)} overdue tasks:\n\n"
        for task in overdue_tasks:
            days_overdue = (today - datetime.fromisoformat(task["due_date"]).date()).days
            result += f"- **{task['title']}** ({task['file']})\n"
            result += f"  Due: {task['due_date']} ({days_overdue} days overdue) | Priority: {task['priority']} | Status: {task['status']}\n\n"

        return [TextContent(type="text", text=result)]

    elif name == "prune_completed_tasks":
        tasks = get_all_tasks()
        prune_after = config["task_aging"]["prune_completed_after"]
        cutoff = datetime.now() - timedelta(days=prune_after)
        dry_run = arguments.get("dry_run", False)

        completed_tasks = [
            t
            for t in tasks
            if t["status"] == "d"
            and t.get("updated_date")
            and datetime.fromisoformat(t["updated_date"]) < cutoff
        ]

        if not completed_tasks:
            return [
                TextContent(
                    type="text",
                    text=f"No completed tasks older than {prune_after} days found",
                )
            ]

        result = f"{'Would delete' if dry_run else 'Deleting'} {len(completed_tasks)} completed tasks older than {prune_after} days:\n\n"
        for task in completed_tasks:
            days_old = (
                datetime.now() - datetime.fromisoformat(task["updated_date"])
            ).days
            result += f"- {task['title']} ({task['file']}) - completed {days_old} days ago\n"

            if not dry_run:
                task_file = TASKS_DIR / task["file"]
                task_file.unlink()

        if dry_run:
            result += f"\n(Dry run - no files deleted. Run without dry_run to delete)"

        return [TextContent(type="text", text=result)]

    elif name == "check_duplicates":
        existing_tasks = get_all_tasks()
        threshold = config["deduplication"]["similarity_threshold"]

        proposed_task = {
            "title": arguments["title"],
            "keywords": arguments.get("keywords", []),
            "category": arguments.get("category", ""),
        }

        # Find similar tasks
        similar_tasks = []
        for task in existing_tasks:
            similarity = calculate_similarity(proposed_task, task, config)
            if similarity >= threshold:
                similar_tasks.append((task, similarity))

        if not similar_tasks:
            return [
                TextContent(
                    type="text",
                    text=f"✓ No duplicate tasks found (threshold: {threshold}). Safe to create.",
                )
            ]

        # Sort by similarity (highest first)
        similar_tasks.sort(key=lambda x: x[1], reverse=True)

        result = f"⚠️  Found {len(similar_tasks)} similar tasks (threshold: {threshold}):\n\n"
        for task, similarity in similar_tasks:
            result += f"**{task['title']}** ({task['file']})\n"
            result += f"- Similarity: {similarity:.2f} ({int(similarity*100)}% match)\n"
            result += f"- Priority: {task['priority']} | Status: {task['status']} | Category: {task['category']}\n"

            # Explain why it matched
            title_match = SequenceMatcher(None, arguments["title"].lower(), task["title"].lower()).ratio()
            if title_match > 0.7:
                result += f"- Match reason: Very similar titles ({int(title_match*100)}% title match)\n"

            keyword_overlap = set(k.lower() for k in arguments.get("keywords", [])) & set(k.lower() for k in task.get("keywords", []))
            if keyword_overlap:
                result += f"- Shared keywords: {', '.join(keyword_overlap)}\n"

            # Suggest action based on status
            if task["status"] == "d":
                result += f"- **Suggestion:** This task is done. You may want to reopen it instead of creating new.\n"
            elif task["status"] == "b":
                result += f"- **Suggestion:** This task is blocked. Consider unblocking and updating it.\n"
            else:
                result += f"- **Suggestion:** Update existing task with new details instead of creating duplicate.\n"

            result += "\n"

        return [TextContent(type="text", text=result)]

    elif name == "process_backlog":
        backlog_file = PROJECT_ROOT / "BACKLOG.md"

        if not backlog_file.exists():
            return [TextContent(type="text", text="No BACKLOG.md found")]

        with open(backlog_file, "r") as f:
            backlog_content = f.read().strip()

        if not backlog_content or backlog_content == "":
            return [TextContent(type="text", text="BACKLOG.md is empty")]

        # Parse backlog items - supports two formats:
        # 1. Structured: ## Title followed by description lines
        # 2. Simple: bullet points (- item)
        lines = backlog_content.split('\n')
        items = []
        current_item = None

        for line in lines:
            stripped = line.strip()

            # Skip empty lines
            if not stripped:
                continue

            # Skip top-level header (# Backlog, # Test Backlog, etc.)
            if stripped.startswith('# ') and not stripped.startswith('## '):
                continue

            # New item: ## heading format
            if stripped.startswith('## '):
                # Save previous item if exists
                if current_item:
                    items.append(current_item)
                # Start new item with title from heading
                title = stripped[3:].strip()
                current_item = {"title": title, "description": ""}

            # Bullet point format (standalone items)
            elif stripped.startswith(('- ', '* ', '+ ')) and current_item is None:
                item_text = stripped.lstrip('- ').lstrip('* ').lstrip('+ ')
                if len(item_text) >= 5:
                    items.append({"title": item_text, "description": ""})

            # Description line for current structured item
            elif current_item is not None:
                # Skip sub-bullets within meeting notes, etc.
                if stripped.startswith(('- ', '* ', '+ ')):
                    # This is a sub-item, add to description
                    current_item["description"] += stripped + "\n"
                else:
                    # Regular description text
                    if current_item["description"]:
                        current_item["description"] += " " + stripped
                    else:
                        current_item["description"] = stripped

        # Don't forget the last item
        if current_item:
            items.append(current_item)

        if not items:
            return [TextContent(type="text", text="No actionable items found in BACKLOG.md")]

        # Analyze each item
        tasks_to_create = []
        initiatives = []
        references = []
        notes_to_archive = []
        ambiguous_items = []
        duplicates = []

        existing_tasks = get_all_tasks()

        for item in items:
            title = item["title"]
            description = item.get("description", "")
            full_text = f"{title} {description}".strip()

            # Auto-categorize using both title and description
            category = auto_categorize(title, description, config)

            # 1. Check if it's a reference (has URL) - these don't need action verbs
            url_pattern = r'https?://[^\s]+'
            has_url = bool(re.search(url_pattern, full_text))
            # Only classify as reference if it has a URL or explicit reference phrases
            reference_phrases = ["found article", "found link", "read this", "source:", "reference:"]
            has_reference_phrase = any(phrase in full_text.lower() for phrase in reference_phrases)
            is_reference = has_url or has_reference_phrase

            if is_reference:
                references.append({
                    "title": title,
                    "description": description,
                    "category": "reference"
                })
                continue

            # 2. Check if it's notes to archive (meeting notes, random notes)
            notes_keywords = ["notes", "meeting notes", "standup", "retrospective"]
            is_notes = any(kw in title.lower() for kw in notes_keywords) and description.startswith("-")

            if is_notes:
                notes_to_archive.append({
                    "title": title,
                    "description": description
                })
                continue

            # 3. Check if it's an initiative (strategic, user pain point, not immediately actionable)
            # More specific: requires combination of user-related + pain point keywords
            initiative_indicators = [
                "explore", "investigate", "consider", "opportunity", "idea", "strategy",
                "users complaining", "user feedback", "users want", "users requesting",
                "performance issue", "slow startup", "slow loading"
            ]
            is_initiative = any(indicator in full_text.lower() for indicator in initiative_indicators)

            if is_initiative:
                initiatives.append({
                    "title": title,
                    "description": description,
                    "category": category
                })
                continue

            # 4. Check ambiguity only for items that look like tasks
            is_amb, reason = is_ambiguous(full_text)
            if is_amb:
                questions = generate_clarification_questions(full_text)
                ambiguous_items.append({
                    "item": title,
                    "description": description,
                    "reason": reason,
                    "questions": questions
                })
                continue

            # Check for duplicates
            proposed = {
                "title": title,
                "keywords": [],
                "category": category
            }

            similar = []
            for task in existing_tasks:
                similarity = calculate_similarity(proposed, task, config)
                if similarity >= config["deduplication"]["similarity_threshold"]:
                    similar.append((task, similarity))

            if similar:
                duplicates.append({
                    "item": title,
                    "description": description,
                    "similar": similar
                })
                continue

            # This is a valid task
            tasks_to_create.append({
                "title": title,
                "description": description,
                "category": category,
                "priority": "P2"  # Default to P2, user can adjust
            })

        # Build summary
        result = f"# Backlog Processing Summary\n\n"
        result += f"**Total items:** {len(items)}\n\n"

        if tasks_to_create:
            result += f"## ✓ Tasks to Create ({len(tasks_to_create)})\n\n"
            for task in tasks_to_create:
                result += f"- **{task['title']}**\n"
                if task.get('description'):
                    result += f"  {task['description'][:100]}{'...' if len(task['description']) > 100 else ''}\n"
                result += f"  Category: {task['category'] or 'uncategorized'} | Priority: {task['priority']}\n\n"

        if initiatives:
            result += f"## 💡 Initiatives Identified ({len(initiatives)})\n\n"
            for init in initiatives:
                result += f"- **{init['title']}**\n"
                if init.get('description'):
                    result += f"  {init['description'][:100]}{'...' if len(init['description']) > 100 else ''}\n"
                result += f"  Category: {init['category'] or 'uncategorized'}\n\n"

        if references:
            result += f"## 📚 References to Save ({len(references)})\n\n"
            for ref in references:
                result += f"- **{ref['title']}**\n"
                if ref.get('description'):
                    result += f"  {ref['description'][:100]}{'...' if len(ref['description']) > 100 else ''}\n"
                result += "\n"

        if notes_to_archive:
            result += f"## 📝 Notes to Archive ({len(notes_to_archive)})\n\n"
            for note in notes_to_archive:
                result += f"- **{note['title']}**\n"
                if note.get('description'):
                    desc_preview = note['description'].replace('\n', ' ')[:80]
                    result += f"  {desc_preview}{'...' if len(note['description']) > 80 else ''}\n"
                result += "\n"

        if ambiguous_items:
            result += f"## ⚠️  Ambiguous Items Needing Clarification ({len(ambiguous_items)})\n\n"
            for amb in ambiguous_items:
                result += f"**Item:** {amb['item']}\n"
                if amb.get('description'):
                    result += f"**Description:** {amb['description'][:100]}{'...' if len(amb['description']) > 100 else ''}\n"
                result += f"**Issue:** {amb['reason']}\n"
                result += f"**Questions:**\n"
                for q in amb['questions']:
                    result += f"  - {q}\n"
                result += "\n"

        if duplicates:
            result += f"## 🔄 Possible Duplicates ({len(duplicates)})\n\n"
            for dup in duplicates:
                result += f"**Item:** {dup['item']}\n"
                if dup.get('description'):
                    result += f"**Description:** {dup['description'][:100]}{'...' if len(dup['description']) > 100 else ''}\n"
                result += f"**Similar to:**\n"
                for task, sim in dup['similar'][:2]:  # Show top 2
                    result += f"  - {task['title']} ({task['file']}) - {int(sim*100)}% match\n"
                result += "\n"

        # Auto-create if requested
        if arguments.get("auto_create", False) and tasks_to_create:
            result += f"\n## Creating Tasks...\n\n"

            for task_data in tasks_to_create:
                # Generate filename
                filename = re.sub(r"[^a-z0-9]+", "-", task_data["title"].lower())
                filename = filename.strip("-") + ".md"
                task_file = TASKS_DIR / filename

                if task_file.exists():
                    result += f"⚠️  Skipped {filename} (already exists)\n"
                    continue

                # Create frontmatter
                now = datetime.now().isoformat()
                frontmatter = {
                    "title": task_data["title"],
                    "priority": task_data["priority"],
                    "status": "n",
                    "category": task_data["category"],
                    "keywords": [],
                    "created_date": now,
                    "updated_date": now,
                }

                # Generate smart content using description as context
                body = generate_task_content(
                    task_data["title"],
                    task_data["category"],
                    task_data.get("description", "")
                )

                write_task_file(task_file, frontmatter, body)
                result += f"✓ Created {filename}\n"
        else:
            result += f"\n**Note:** Set auto_create=true to create tasks automatically.\n"

        return [TextContent(type="text", text=result)]

    elif name == "clear_backlog":
        backlog_file = PROJECT_ROOT / "BACKLOG.md"
        archive = arguments.get("archive", True)

        if not backlog_file.exists():
            return [TextContent(type="text", text="No BACKLOG.md found")]

        with open(backlog_file, "r") as f:
            content = f.read()

        if archive and content.strip():
            # Archive to tasks/_archived
            archive_dir = PROJECT_ROOT / "tasks" / "_archived"
            archive_dir.mkdir(parents=True, exist_ok=True)

            archive_file = archive_dir / f"{datetime.now().strftime('%Y-%m-%d')}-backlog.md"

            # If file exists, append
            if archive_file.exists():
                with open(archive_file, "a") as f:
                    f.write(f"\n\n## Backlog archived at {datetime.now().strftime('%H:%M:%S')}\n\n")
                    f.write(content)
            else:
                with open(archive_file, "w") as f:
                    f.write(f"# Notes - {datetime.now().strftime('%Y-%m-%d')}\n\n")
                    f.write(f"## Backlog archived at {datetime.now().strftime('%H:%M:%S')}\n\n")
                    f.write(content)

        # Clear backlog
        with open(backlog_file, "w") as f:
            f.write("# Backlog\n")

        if archive:
            return [TextContent(
                type="text",
                text=f"✓ Backlog cleared and archived to tasks/_archived/{datetime.now().strftime('%Y-%m-%d')}-backlog.md"
            )]
        else:
            return [TextContent(type="text", text="✓ Backlog cleared (not archived)")]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
