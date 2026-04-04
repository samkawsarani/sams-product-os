# Meetings — Agent Instructions

Loaded automatically when working inside `meetings/`.

## File Convention

**Naming:** `YYYY-MM-DD-{title}.md`

Examples:
- `2026-04-04-sarah-1on1.md`
- `2026-04-04-q2-planning.md`
- `2026-04-04-design-review-checkout.md`

## Structure

```markdown
# {Title} — YYYY-MM-DD

**Attendees:** ...
**Context:** ...

## Notes

## Decisions Made

## Action Items
- [ ] [Owner] Action — due YYYY-MM-DD

## Follow-up
```

## After a Meeting

1. Extract decisions → log in `knowledge/decisions/` (follow Decision Journal protocol in `knowledge/AGENTS.md`)
2. Extract action items → create task files in `tasks/` (check priority caps)
3. Extract new facts or patterns → write to the relevant domain learning folder under `knowledge/`

Tell the user what you extracted and from where before creating anything.
