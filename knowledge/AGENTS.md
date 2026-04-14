# Knowledge — Agent Instructions

## Knowledge Architecture

`knowledge/` has two kinds of content. The authoritative list is in `knowledge/INDEX.md`:
- **Reference Context** — curated folders you set up once (about-me, company-context, etc.)
- **Domain Learning** — agent-authored folders created from real work (e.g., `knowledge/onboarding/`, `knowledge/checkout-flow/`)

### Domain Learning Folders

Create domain learning folders inside `knowledge/` as needed. Never pre-populate — only create when there is something real to write.

Each domain folder uses three files:
- `knowledge.md` — dated facts and observations
- `hypotheses.md` — unconfirmed patterns; track confirmation count toward 3
- `rules.md` — confirmed patterns; apply these by default

**At the start of a task:** if these files exist for the relevant domain, read them first.
**At the end of each task:** extract insights and write them to the relevant domain folder.

**Promotion:** Hypothesis confirmed 3+ times → move entry to `rules.md` (note date and source).
**Demotion:** Rule contradicted by new data → move back to `hypotheses.md`.

### INDEX.md — Auto-Maintenance

`knowledge/INDEX.md` is AI-maintained. You are responsible for keeping it current.

**When you create a new domain learning folder:**
1. Immediately open `knowledge/INDEX.md`
2. Add a row to the Domain Learning table: folder name, today's date, one-line description
3. Update the `Last updated` line at the top of the file

Never wait for a System Review to update the index. Update at the moment of creation. Never recreate INDEX.md from scratch — always edit in place.

## Opportunities

`knowledge/opportunities/` holds one file per opportunity — things you've observed and want to monitor or explore. This includes groomed feature requests, patterns spotted in research, and market observations.

Use `templates/opportunity-template.md` when creating a new opportunity file.

**When to surface:** If the user is exploring a problem space, researching a topic, or processing backlog items — check for relevant opportunities and surface them as context.

**This folder is not for committed work.** When an opportunity moves to active pursuit, a project is created in `projects/`. Note the link in both files.

## People

`knowledge/people/` holds one file per person — direct reports, key stakeholders, cross-functional peers, executives you work with regularly.

**When to use it:** If the user asks to prep for a 1:1, draft a message to a specific person, or think through a people situation — check if a file exists for that person first. If it does, read it before responding.

**File format** — loose, user-maintained. Typical contents:
- Role and background
- What they care about most
- Communication style / how they like to receive information
- Current projects or priorities
- Open items or follow-ups
- For direct reports: growth areas, career goals, recent feedback given

**This folder is optional and not needed from day one.** Add files as people become important enough to track. Never create files proactively — only when the user explicitly asks or provides the information.

## Decision Journal

Before making any decision that affects more than today's task, search `knowledge/decisions/` using both QMD and Grep. Follow prior decisions unless new information invalidates the reasoning.

If no prior decision exists — or you're replacing one — log it:

**File:** `knowledge/decisions/YYYY-MM-DD-{topic}.md`

```
## Decision: {what you decided}
## Context: {why this came up}
## Alternatives considered: {what else was on the table}
## Reasoning: {why this option won}
## Trade-offs accepted: {what you gave up}
## Supersedes: {link to prior decision, if replacing}
```

## System Review Protocol

When a system review runs (user-triggered — never automatic):
- **Knowledge hygiene:** For each domain folder — promote any hypothesis confirmed 3+ times to `rules.md`, discard any with 3+ contradictions, prune rules not applied in 30+ days
- **Decisions audit:** Scan `knowledge/decisions/` — did recent trade-offs play out as expected? Flag any needing a follow-up decision
- **Goals alignment:** Are active tasks still tied to current goals in `GOALS.md`? Flag stale projects or backlog items
- **Index hygiene:** Verify every domain folder has a row in `knowledge/INDEX.md`; fill gaps; update `Last updated`

After the review, report what changed and ask the user to update "Last system review" in root `AGENTS.md`.
