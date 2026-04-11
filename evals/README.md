# SAMS PRODUCT OS Evaluation Suite

Validates that the agent and workflows work correctly after changes.

**Run all commands from the `evals/` directory.**

## Setup

```bash
cd evals && uv sync
```

## Quick Start

```bash
cd evals

# Run all evals
uv run python run_evals.py

# Run specific suites
uv run python run_evals.py --workflows   # Workflow tests
uv run python run_evals.py --behavior    # Agent behavior tests
uv run python run_evals.py --llm         # LLM behavioral evals (needs ANTHROPIC_API_KEY)

# Or use pytest directly
uv run pytest -v
```

## Test Suites

### Workflows (`test_workflows.py`)

Item type detection (task/initiative/reference/notes) and full backlog classification pipeline.

### Agent Behavior (`test_agent_behavior.py`)

Behavioral contract tests: verifies `.claude/skills/process-backlog/SKILL.md` and `AGENTS.md` contain required instructions (user review, confirmation, goal linking, ambiguity resolution). Tests goal alignment, confirmation requirements, and structural instruction placement for progressive disclosure.

### LLM Behavioral (`test_llm_behavior.py`)

Real Claude API calls graded by an LLM judge against rubrics. **Requires** `ANTHROPIC_API_KEY`. **Cost**: ~$0.50 per suite run (10 scenarios × 3 samples × 2 calls).

| # | Scenario | Threshold |
|---|----------|-----------|
| 1 | Ambiguous item — asks clarification, doesn't create | 1.0 |
| 2 | Mixed backlog — categorizes, summarizes, waits for confirmation | 0.8 |
| 3 | Orphan task — flags no goal match | 1.0 |
| 4 | Duplicate detection — flags similar, asks user | 0.8 |
| 5 | Clear item with goal match — links goal, presents for review | 0.8 |
| 6 | Thought partner — challenges strategic assumptions | 0.7 |
| 7 | Domain learning — captures analysis to correct knowledge files | 0.7 |
| 8 | System review — promotes confirmed hypotheses to rules | 0.8 |
| 9 | Decision journal — logs decision with required sections | 0.8 |

**Env vars:** `ANTHROPIC_API_KEY` (required), `LLM_EVAL_MODEL` (default: `claude-sonnet-4-6`), `LLM_JUDGE_MODEL` (default: `claude-haiku-4-5-20251001` — override with `claude-opus-4-6` for high-stakes runs)

**Adding scenarios:** Create a new YAML file in `fixtures/scenarios/`. Tests auto-discover via parametrize. To capture a production failure, copy `fixtures/regressions/_template.yaml`.

## Skill-Creator Evals

End-to-end evals in skill-creator compatible format, complementing the pytest suite above.

### `evals.json`

10 eval scenarios for `process-backlog` in the standard skill-creator schema (prompt + expected_output + expectations). Run via `/skill-creator` eval mode for grading and benchmarking.

### `trigger-eval.json`

20 trigger eval queries (10 should-trigger, 10 should-not-trigger) for optimizing the `process-backlog` description via skill-creator's description optimization flow.

### Two-Layer Strategy

| Layer | Format | Purpose | Cost |
|-------|--------|---------|------|
| **Unit/Integration** | pytest (`test_*.py`) | Workflows, behavioral contracts | Free (local) |
| **End-to-End** | skill-creator (`evals.json`) | Full skill execution with grading + benchmarking | ~$0.50/run |

## Directory Structure

```
evals/
├── README.md
├── pyproject.toml             # Python dependencies (pytest, anthropic, pyyaml)
├── evals.json                 # Skill-creator compatible eval definitions
├── trigger-eval.json          # Trigger eval queries for description optimization
├── run_evals.py               # Test runner with options
├── conftest.py                # Shared pytest fixtures
├── test_workflows.py          # Workflow logic tests
├── test_agent_behavior.py     # Agent behavioral requirement tests
├── test_llm_behavior.py       # LLM-in-the-loop behavioral evals
├── fixtures/
│   ├── test-backlogs/         # basic.md, mixed-items.md, behavioral-scenarios.md
│   ├── scenarios/             # Designed LLM eval scenarios (one YAML per scenario)
│   ├── regressions/           # Captured production failures (_template.yaml to add new)
│   └── llm_scenarios/
│       └── backlog_processing.py  # EvalScenario dataclass, judge prompts, YAML loader
└── expected/
    └── outputs/               # basic.json, behavioral-scenarios.json
```

## Maintenance

Update tests when:
- `AGENTS.md` requirements change — update behavior tests
- `.claude/skills/process-backlog/SKILL.md` changes — update workflow compliance tests
- Skill description changes — rerun trigger evals via skill-creator
- New eval scenarios needed — add to both `evals.json` and `fixtures/scenarios/` (YAML)
- Production failure observed — copy `fixtures/regressions/_template.yaml`, fill in, commit
