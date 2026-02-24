# Knowledge Base

Context files for your AI assistant. **This entire directory is gitignored.**

## Directory Structure

```
knowledge/
├── about-me/             # Personal context, background, working style
├── company-context/      # Company info, mission, org structure
├── frameworks/           # PM frameworks, methodologies, mental models
├── processes/            # How your team works
├── product-analytics/    # KPIs, dashboards, performance data (content gitignored)
├── product-strategy/     # Vision, strategy, roadmap
├── references/           # Links, articles, competitive analysis
└── voice-samples/        # Personal writing samples for AI voice matching
```

**Note:** Active work artifacts live outside knowledge/:
- `meetings/` — Meeting transcripts organized by type
- `initiatives/` — Strategic initiatives with context, research, outputs
- `tasks/_archived/` — Archived backlog snapshots and completed tasks (`_archived/completed/`)

## What to Put Where

- **about-me/** - Role, experience, working style, frameworks (see `templates/about-me-template.md`)
- **company-context/** - Mission, vision, values, products, team structure
- **frameworks/** - PM methodologies (RICE, OKRs, Jobs-to-be-Done)
- **processes/** - Development process, sprint planning, decision-making
- **product-analytics/** - Metrics definitions, performance data, dashboards
- **product-strategy/** - Vision, strategic priorities, roadmap, OKRs
- **references/** - Competitive analysis, market research, articles
- **voice-samples/** - Writing samples for AI voice matching

## Getting Started

Run `./setup.sh` or manually create:

- `knowledge/about-me/about-me.md` - Background, working style
- `knowledge/company-context/company-overview.md` - Company info
- `knowledge/product-strategy/current-strategy.md` - Vision, priorities
- `knowledge/processes/how-we-work.md` - Team processes

## How AI Uses Context

AI reads files in order: AGENTS.md → about-me/ → product-strategy/ → frameworks/ → initiatives/

Reference files explicitly: `@knowledge/product-strategy/current-strategy.md`

**Examples:**
- Prioritization: AI reads your RICE framework, checks strategy, applies scoring
- Communication: AI reads your style preferences and voice samples, drafts accordingly

## Personal Context Setup

**Create essential files** (see `templates/` for full examples):

1. **about-me/about-me.md** - Role, experience, working style, strengths, current focus
2. **frameworks/my-prioritization.md** - RICE scoring rubric, when to use it
3. **product-strategy/current-strategy.md** - North star metric, strategic pillars, key metrics
4. **company-context/company-overview.md** - Mission, products, team, stage

## Testing Your Context

**Test prioritization:**
```
"Help me prioritize mobile performance vs dashboard redesign using @knowledge/frameworks/ and @knowledge/product-strategy/"
```
Expect: AI applies your RICE scoring, references strategy, shows math

**Test style matching:**
```
"Draft a Slack message about pushing launch date using @knowledge/about-me/"
```
Expect: Matches your formality, structure, phrases

**Test strategic alignment:**
```
"Create opportunity for real-time collaboration. Check @knowledge/product-strategy/"
```
Expect: AI checks fit with strategic pillars, flags if off-strategy

## Best Practices

- Be specific: "80%+ confidence in RICE before building" beats "data-driven decisions"
- Include examples from actual work
- Link related files with @ mentions
- Use `YYYY-MM-DD-description.md` naming
- Start small, add as you work
- Make scannable: headers, bullets, bold key points

## Maintenance

**Weekly**: Update analytics, add research, document decisions
**Monthly**: Archive old docs, review frameworks
**Quarterly**: Refresh product strategy

## Privacy & Security

**Safe:** Product strategy, anonymized research, process docs, metrics (no PII)
**Don't include:** Passwords, API keys, customer PII, financial details

Use `.env` files (gitignored) for secrets.

## Troubleshooting

- AI doesn't use context? Reference explicitly: `@knowledge/product-strategy/`
- Too much info? Archive old docs, create summaries
- Conflicts? Keep one source of truth, use "Last Updated" dates
