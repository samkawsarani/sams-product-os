#!/usr/bin/env -S uv run python
"""
SAMS PRODUCT OS Task Management MCP Server

Provides programmatic access to backlog management through Model Context Protocol.
Exposes 2 tools: process_backlog, check_duplicates.
"""

import asyncio
import os
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
TASKS_DIR = PROJECT_ROOT / "tasks"
INITIATIVES_DIR = PROJECT_ROOT / "initiatives"
REFERENCES_DIR = PROJECT_ROOT / "knowledge" / "references"
BACKLOG_FILE = TASKS_DIR / "BACKLOG.md"
ACTIVE_FILE = TASKS_DIR / "ACTIVE.md"

DEDUP_THRESHOLD = float(os.environ.get("DEDUP_THRESHOLD", "0.6"))

# Initialize MCP server
app = Server("pm-tasks")


# Helper Functions

BULLET_RE = re.compile(r'^[-*+]\s+')
CHECKBOX_RE = re.compile(r'^[-*+]\s+\[(.)\]\s+')
HEADING_RE = re.compile(r'^(#{1,6})\s+(.*)')


def parse_backlog_items(content: str) -> list[dict]:
    """
    Parse backlog content into items using block-based splitting.

    Works with any format: headings + bullets, flat bullets, plain text,
    checklists, or any mix. Blank lines and headings both act as block
    separators.

    Returns list of {"title": str, "description": str}.
    """
    lines = content.split('\n')

    # Step 1: Split into blocks. A new block starts at a blank line or heading.
    blocks: list[list[str]] = []
    current: list[str] = []

    for line in lines:
        stripped = line.strip()

        # Skip blank lines — they end the current block
        if not stripped:
            if current:
                blocks.append(current)
                current = []
            continue

        # Headings always start a new block
        if HEADING_RE.match(stripped):
            if current:
                blocks.append(current)
                current = []

        current.append(stripped)

    if current:
        blocks.append(current)

    # Step 2: Convert blocks to items
    items: list[dict] = []

    for block in blocks:
        first = block[0]

        # Skip the top-level h1 header (# Backlog, etc.)
        heading_match = HEADING_RE.match(first)
        if heading_match and len(heading_match.group(1)) == 1:
            # h1 — skip. If the block has body lines after h1, process them
            # as a standalone block.
            rest_lines = block[1:]
            if rest_lines:
                blocks.append(rest_lines)
            continue

        # Case A: Block starts with a heading (h2+)
        if heading_match:
            title = heading_match.group(2).strip()
            desc_lines = block[1:]

            # If all body lines are bullets/checkboxes, expand each as its
            # own item (using the heading as context). This handles the common
            # pattern of a heading followed by a checklist.
            if desc_lines and all(BULLET_RE.match(l) for l in desc_lines):
                heading_context = title  # preserve heading as context
                for bline in desc_lines:
                    cb_match = CHECKBOX_RE.match(bline)
                    if cb_match and cb_match.group(1) == 'x':
                        continue  # skip checked items
                    text = CHECKBOX_RE.sub('', bline)
                    text = BULLET_RE.sub('', text).strip()
                    if len(text) >= 5:
                        items.append({"title": text, "description": f"(from: {heading_context})"})
            else:
                # Heading with prose description — keep as single item
                # Filter out checked checkbox lines from description
                filtered = [l for l in desc_lines
                            if not (CHECKBOX_RE.match(l) and CHECKBOX_RE.match(l).group(1) == 'x')]
                description = '\n'.join(filtered)
                if len(title) >= 3:
                    items.append({"title": title, "description": description})
            continue

        # Case B: Block is all bullets/checkboxes — each is its own item
        all_bullets = all(BULLET_RE.match(l) for l in block)
        if all_bullets:
            for bline in block:
                # Skip checked checkboxes
                cb_match = CHECKBOX_RE.match(bline)
                if cb_match and cb_match.group(1) == 'x':
                    continue
                # Strip bullet/checkbox prefix
                text = CHECKBOX_RE.sub('', bline)
                text = BULLET_RE.sub('', text).strip()
                if len(text) >= 5:
                    items.append({"title": text, "description": ""})
            continue

        # Case C: Plain text or mixed — first line is title, rest is description
        title = BULLET_RE.sub('', first).strip()
        desc_lines = block[1:]
        description = '\n'.join(desc_lines)
        if len(title) >= 3:
            items.append({"title": title, "description": description})

    return items


def calculate_similarity(title1: str, title2: str) -> float:
    """Calculate title similarity score (0-1 scale)"""
    return SequenceMatcher(None, title1.lower(), title2.lower()).ratio()


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

    # Check for vague targets
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

    has_deadline_words = any(word in item_lower for word in ["by", "due", "deadline", "before"])
    has_context_words = any(word in item_lower for word in ["because", "for", "to help", "context"])

    if not has_deadline_words:
        questions.append("When does this need to be done? (this week, this month, no deadline)")

    if not has_context_words:
        questions.append("Why does this matter? What's the context or goal?")

    is_vague, reason = is_ambiguous(item)
    if is_vague and "action verb" in reason:
        questions.append("What specific action should be taken?")

    if not questions:
        questions.append("Can you provide more details about what needs to be done?")

    return questions


def generate_initiative_content(title: str, description: str) -> str:
    """Generate markdown content for an initiative file."""
    return f"""# {title}

## Summary
{description if description else '[Brief description of this initiative]'}

## Opportunity
- [Key opportunity or pain point]

## Status
Early idea — needs further discovery and scoping.

## Open Questions
- [Question 1]
"""


def generate_reference_content(title: str, description: str) -> str:
    """Generate markdown content for a reference file."""
    url_match = re.search(r'https?://[^\s]+', description) if description else None
    source = url_match.group(0) if url_match else "[URL]"

    return f"""# {title}

**Source:** {source}

{description if description else '[Description of this reference]'}
"""


def find_related_initiative(title: str, description: str) -> Optional[Path]:
    """
    Scan initiatives/ for subfolder names matching keywords in the reference.
    Returns the initiative folder path if found, or None.
    """
    if not INITIATIVES_DIR.exists():
        return None

    text = f"{title} {description}".lower()
    words = set(re.findall(r'[a-z]{3,}', text))

    best_match = None
    best_score = 0

    for item in INITIATIVES_DIR.iterdir():
        if item.is_dir() and not item.name.startswith('.') and item.name != 'groomed-requests':
            folder_words = set(item.name.lower().replace('-', ' ').replace('_', ' ').split())
            overlap = len(words & folder_words)
            if overlap > best_score and overlap >= 1:
                best_score = overlap
                best_match = item

    return best_match


def slugify(title: str) -> str:
    """Convert a title to a URL-friendly slug."""
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def get_existing_titles() -> list[str]:
    """Collect titles from BACKLOG.md, ACTIVE.md, and initiatives/ for dedup."""
    titles = []

    # Parse BACKLOG.md
    if BACKLOG_FILE.exists():
        with open(BACKLOG_FILE) as f:
            for item in parse_backlog_items(f.read()):
                titles.append(item["title"])

    # Parse ACTIVE.md — extract checkbox and bullet items
    if ACTIVE_FILE.exists():
        with open(ACTIVE_FILE) as f:
            content = f.read()
        for line in content.split('\n'):
            stripped = line.strip()
            cb_match = CHECKBOX_RE.match(stripped)
            if cb_match:
                text = CHECKBOX_RE.sub('', stripped).strip()
                if text and len(text) >= 5:
                    titles.append(text)
            elif BULLET_RE.match(stripped):
                text = BULLET_RE.sub('', stripped).strip()
                if text and len(text) >= 5:
                    titles.append(text)

    # Initiative folder/file names
    if INITIATIVES_DIR.exists():
        for item in INITIATIVES_DIR.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                titles.append(item.name.replace('-', ' '))
            elif item.is_file() and item.suffix == '.md' and not item.name.startswith('.'):
                titles.append(item.stem.replace('-', ' '))

    return titles


# MCP Tool Handlers

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools"""
    return [
        Tool(
            name="check_duplicates",
            description="Check if a proposed title already exists in tasks/BACKLOG.md, tasks/ACTIVE.md, or initiatives/. Uses fuzzy title matching.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Proposed item title"},
                },
                "required": ["title"],
            },
        ),
        Tool(
            name="process_backlog",
            description="Parse tasks/BACKLOG.md and classify each item as a task (stays in backlog), initiative (goes to initiatives/), or reference (goes to knowledge/references/). Returns a summary for review. When auto_create=true, creates initiative and reference files only — tasks remain in BACKLOG.md as organized lines.",
            inputSchema={
                "type": "object",
                "properties": {
                    "auto_create": {
                        "type": "boolean",
                        "description": "If true, automatically create initiative and reference files. Tasks remain in BACKLOG.md. Default: false.",
                    }
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""

    if name == "check_duplicates":
        title = arguments["title"]
        existing = get_existing_titles()

        similar = [
            (t, calculate_similarity(title, t))
            for t in existing
            if calculate_similarity(title, t) >= DEDUP_THRESHOLD
        ]

        if not similar:
            return [TextContent(type="text", text=f"No duplicates found (threshold: {DEDUP_THRESHOLD}). Safe to add.")]

        similar.sort(key=lambda x: x[1], reverse=True)
        result = f"Found {len(similar)} similar items (threshold: {DEDUP_THRESHOLD}):\n\n"
        for existing_title, score in similar:
            result += f"- **{existing_title}** — {int(score * 100)}% match\n"
        result += "\nConsider updating the existing item instead of adding a duplicate."

        return [TextContent(type="text", text=result)]

    elif name == "process_backlog":
        if not BACKLOG_FILE.exists():
            return [TextContent(type="text", text="No tasks/BACKLOG.md found")]

        with open(BACKLOG_FILE) as f:
            content = f.read().strip()

        if not content:
            return [TextContent(type="text", text="tasks/BACKLOG.md is empty")]

        items = parse_backlog_items(content)

        if not items:
            return [TextContent(type="text", text="No actionable items found in tasks/BACKLOG.md")]

        tasks_to_keep = []
        initiatives = []
        references = []
        notes_to_discard = []
        ambiguous_items = []

        for item in items:
            title = item["title"]
            description = item.get("description", "")
            full_text = f"{title} {description}".strip()

            # Check if it's a reference
            url_pattern = r'https?://[^\s]+'
            has_url = bool(re.search(url_pattern, full_text))
            reference_phrases = [
                "found article", "found link", "read this", "source:", "reference:",
                "bookmark", "save this", "interesting read"
            ]
            has_reference_phrase = any(phrase in full_text.lower() for phrase in reference_phrases)
            title_is_url = bool(re.match(url_pattern, title.strip()))
            is_reference = has_reference_phrase or (has_url and title_is_url)

            if is_reference:
                references.append({"title": title, "description": description})
                continue

            # Check if it's notes to discard
            notes_keywords = ["notes", "meeting notes", "standup", "retrospective"]
            is_notes = any(kw in title.lower() for kw in notes_keywords) and description.startswith("-")
            if is_notes:
                notes_to_discard.append({"title": title, "description": description})
                continue

            # Check if it's an initiative
            initiative_indicators = [
                "explore", "investigate", "consider", "opportunity", "idea", "strategy",
                "users complaining", "user feedback", "users want", "users requesting",
                "performance issue", "slow startup", "slow loading"
            ]
            is_initiative = any(indicator in full_text.lower() for indicator in initiative_indicators)

            if is_initiative:
                initiatives.append({"title": title, "description": description})
                continue

            # Check ambiguity
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

            # Valid task — stays in backlog as an organized line
            tasks_to_keep.append({"title": title, "description": description})

        # Build summary
        result = "# Backlog Processing Summary\n\n"
        result += f"**Total items:** {len(items)}\n\n"

        if tasks_to_keep:
            result += f"## Tasks — Stay in Backlog ({len(tasks_to_keep)})\n\n"
            for task in tasks_to_keep:
                result += f"- **{task['title']}**\n"
                if task.get('description'):
                    preview = task['description'][:100]
                    result += f"  {preview}{'...' if len(task['description']) > 100 else ''}\n"
            result += "\n"

        if initiatives:
            result += f"## Initiatives to Create ({len(initiatives)})\n\n"
            for init in initiatives:
                result += f"- **{init['title']}**\n"
                if init.get('description'):
                    preview = init['description'][:100]
                    result += f"  {preview}{'...' if len(init['description']) > 100 else ''}\n"
            result += "\n"

        if references:
            result += f"## References to Save ({len(references)})\n\n"
            for ref in references:
                result += f"- **{ref['title']}**\n"
                if ref.get('description'):
                    preview = ref['description'][:100]
                    result += f"  {preview}{'...' if len(ref['description']) > 100 else ''}\n"
            result += "\n"

        if notes_to_discard:
            result += f"## Notes — Will Be Discarded ({len(notes_to_discard)})\n\n"
            for note in notes_to_discard:
                result += f"- **{note['title']}**\n"
            result += "\n"

        if ambiguous_items:
            result += f"## Ambiguous Items Needing Clarification ({len(ambiguous_items)})\n\n"
            for amb in ambiguous_items:
                result += f"**Item:** {amb['item']}\n"
                if amb.get('description'):
                    preview = amb['description'][:100]
                    result += f"**Description:** {preview}{'...' if len(amb['description']) > 100 else ''}\n"
                result += f"**Issue:** {amb['reason']}\n"
                result += "**Questions:**\n"
                for q in amb['questions']:
                    result += f"  - {q}\n"
                result += "\n"

        # Auto-create initiatives and references if requested
        if arguments.get("auto_create", False):
            if initiatives:
                result += "\n## Creating Initiatives...\n\n"
                INITIATIVES_DIR.mkdir(parents=True, exist_ok=True)
                for init_data in initiatives:
                    filename = slugify(init_data["title"]) + ".md"
                    init_file = INITIATIVES_DIR / filename
                    if init_file.exists():
                        result += f"Skipped {filename} (already exists)\n"
                        continue
                    content = generate_initiative_content(
                        init_data["title"], init_data.get("description", "")
                    )
                    with open(init_file, "w") as f:
                        f.write(content)
                    result += f"Created initiative: {filename}\n"

            if references:
                result += "\n## Saving References...\n\n"
                REFERENCES_DIR.mkdir(parents=True, exist_ok=True)
                for ref_data in references:
                    filename = slugify(ref_data["title"]) + ".md"
                    related_init = find_related_initiative(
                        ref_data["title"], ref_data.get("description", "")
                    )
                    ref_file = (related_init / filename) if related_init else (REFERENCES_DIR / filename)
                    if ref_file.exists():
                        result += f"Skipped {filename} (already exists)\n"
                        continue
                    content = generate_reference_content(
                        ref_data["title"], ref_data.get("description", "")
                    )
                    with open(ref_file, "w") as f:
                        f.write(content)
                    location = str(ref_file.relative_to(PROJECT_ROOT))
                    result += f"Saved reference: {location}\n"

            if not initiatives and not references:
                result += "\nNo initiative or reference files to create.\n"
        else:
            result += "\nSet auto_create=true to create initiative and reference files. Tasks remain in BACKLOG.md.\n"

        return [TextContent(type="text", text=result)]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
