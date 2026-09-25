# thinking/

Generated output. Two skills write here and nothing else does.

**Never hand-edit anything in this folder.** Both subfolders are regenerated or appended by
their skill, and both are pruned on a timer. An edit you make here is lost on the next run, and
a note you leave here is deleted rather than filed. Notes belong in `knowledge/`.

Everything below `thinking/` is gitignored except this file, so a prune is permanent: there is
no git history to recover a pruned brief or review from. That is intended.

| Path | Written by | Format | Retention |
|------|-----------|--------|-----------|
| `daily-briefs/daily-brief-YYYY-MM-DD.html` | `daily-brief`, one per run | HTML | 30 days |
| `daily-briefs/index.html` | `build-brief.py`, rewritten every run | HTML | current |
| `weekly-reviews/weekly-review-YYYY-MM-DD.md` | `weekly-review`, one per week | Markdown | 365 days |

## Reading these as context

**Read the weekly reviews. Do not read the daily briefs.**

`qmd` indexes this workspace with `pattern: "**/*.md"`, so the reviews are searchable and the
briefs are invisible to it by construction. That split is the point, not an oversight:

- A **weekly review** is a durable record of a week: what shipped, where each goal actually
  stood, what was blocked, what the user picked for the following week and why, and the
  stakeholder update that went out. It includes the user's own answers, not just the questions
  put to them. This is real historical context and is the right thing to search when you need to
  know what was true or decided in a given week.
- A **daily brief** is a snapshot of one morning, and it goes stale the same day by design: a
  calendar that has since changed, an inbox that has since been cleared, a status since
  superseded. Yesterday's brief is not evidence about today. Reading one to answer a question
  about the present will produce a confidently wrong answer.

The brief a run is *about to overwrite* has one legitimate use: `briefing-window.py` reads the
newest brief's `<meta name="generated">` stamp and its filename to derive the next window and to
tell whether this is the first run of the week. That is a mechanical read of a timestamp, done
by a script, not context-gathering.

## Related

- `tasks/_archived/YYYY-MM.md` is the separate ledger of what got done, appended per week from
  the same weekly-review sitting. The review is the analysis; the archive is the record. Both are
  kept, and the completed-work list appears in both on purpose so a review reads standalone.
- `knowledge/references/stakeholder-updates/YYYY-MM-DD.md` holds the sent stakeholder update,
  saved alongside the copy embedded in the review.
