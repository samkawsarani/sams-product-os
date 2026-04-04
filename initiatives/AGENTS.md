# Initiatives — Agent Instructions

Loaded automatically when working inside `initiatives/`.

## What is an Initiative

An initiative is a strategic idea or opportunity too large or uncertain to be a single task. Initiatives are explored and shaped before being broken into tasks. Use `templates/initiative-template.md`.

**File naming:** `{topic-slug}.md` (e.g., `enterprise-sso.md`, `mobile-perf.md`)
**Groomed requests** (work received from stakeholders): `initiatives/groomed-requests/{slug}.md`

## Status Flow

`Evaluating` → `Active` → `Shipped` / `Deferred` / `Cancelled`

## Creating Initiatives vs Tasks

- **Initiative** — strategic idea, no clear completion criteria yet → `initiatives/`
- **Task** — clear action with completion criteria → `tasks/`

When processing backlog items, err toward initiatives for anything ambiguous. It's easier to convert an initiative into tasks later than to undo a prematurely scoped task.

## Goals Alignment

Each initiative's Objective section should reference the relevant goal from `GOALS.md`. If no goal fits, ask whether to create one or reconsider whether the initiative should be active.

## Linking to Tasks

When an initiative is `Active`, tasks that implement it should reference the initiative file in their `resource_refs` frontmatter. When reviewing, flag any `Active` initiatives with no corresponding task activity.
