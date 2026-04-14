# Projects — Agent Instructions

## What is a Project

A project is committed discrete work — it has a clear objective, connects to a goal, and produces real outputs. Projects originate from `knowledge/opportunities/` when you decide something is worth pursuing.

Use `templates/project-brief-template.md` when creating a new project brief.

**Folder naming:** `{topic-slug}/` (e.g., `checkout-redesign/`, `enterprise-sso/`)

## Creating a Project

Projects are created when you decide to commit to an opportunity — not during backlog processing.

1. Create `projects/{slug}/` folder and copy `templates/project-brief-template.md` to `projects/{slug}/brief.md`
2. Fill in Objective, Target Customer, and Success at minimum
3. Connect it to a goal in `GOALS.md`
4. If it originated from an opportunity, note the link in the project file

## Status

Track status in the file header: **Active** | **On Hold** | **Complete**

## Relationship to Tasks

Active projects generate tasks. Reference the project file when creating related tasks in `tasks/ACTIVE.md` or `tasks/BACKLOG.md` for context.

## Goals Alignment

Each project must connect to a goal from `GOALS.md`. If no goal fits, flag it and ask before proceeding.
