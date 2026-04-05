"""
LLM eval scenario loader and judge prompts for backlog processing behavior.

Scenarios are defined as YAML files in:
  evals/fixtures/scenarios/    — designed behavioral scenarios
  evals/fixtures/regressions/  — captured production failures

Files starting with _ are ignored (templates, drafts).

To add a scenario: create a new .yaml file in either directory.
To capture a regression: copy evals/fixtures/regressions/_template.yaml.
"""

from dataclasses import dataclass, field
from pathlib import Path
import yaml


SCENARIOS_DIR = Path(__file__).parent.parent / "scenarios"
REGRESSIONS_DIR = Path(__file__).parent.parent / "regressions"


@dataclass
class GradingCriterion:
    """A single criterion for grading an agent response."""
    name: str
    description: str
    weight: float = 1.0


@dataclass
class EvalScenario:
    """A complete eval scenario with prompt, criteria, and thresholds."""
    id: str
    name: str
    description: str
    system_prompt: str  # Assembled at runtime from AGENTS.md + SKILL.md
    user_message: str
    criteria: list[GradingCriterion] = field(default_factory=list)
    fail_if_present: list[str] = field(default_factory=list)
    pass_threshold: float = 0.8
    requires_knowledge_context: bool = False


# ============================================================================
# Judge Prompt
# ============================================================================

JUDGE_SYSTEM_PROMPT = """\
You are an eval judge. You grade an AI agent's response against a rubric.

For each criterion, score 1 (met) or 0 (not met). Be strict — partial credit is not allowed.
If a fail_if_present phrase appears anywhere in the response, automatically score 0 for any
criterion that checks whether the agent avoided that action.

Respond with ONLY valid JSON in this exact format:
{
  "criteria_scores": {
    "<criterion_name>": {"score": 0 or 1, "reason": "brief explanation"}
  },
  "overall_notes": "one sentence summary"
}

---

## Calibration Examples

### Example 1 — PASS

Agent response:
"I notice this item is quite vague — 'Fix the thing' doesn't tell me what 'the thing' is.
Before I can process this, could you clarify: what system or feature are you referring to?
What's the expected behaviour vs what's currently happening?"

Rubric:
- asks_clarification: Agent asks the user for clarification about what 'the thing' refers to
- does_not_create_task: Agent does NOT create a task or say it will create one
- identifies_ambiguity: Agent explicitly flags the item as vague or ambiguous

Expected output:
{
  "criteria_scores": {
    "asks_clarification": {"score": 1, "reason": "Directly asks what 'the thing' refers to"},
    "does_not_create_task": {"score": 1, "reason": "No task creation mentioned"},
    "identifies_ambiguity": {"score": 1, "reason": "Explicitly calls the item vague"}
  },
  "overall_notes": "Agent correctly identified ambiguity and asked for clarification"
}

### Example 2 — FAIL

Agent response:
"I've created a task called 'Fix the thing' with priority P2. You can find it in your tasks folder."

Rubric:
- asks_clarification: Agent asks the user for clarification about what 'the thing' refers to
- does_not_create_task: Agent does NOT create a task or say it will create one
- identifies_ambiguity: Agent explicitly flags the item as vague or ambiguous

Expected output:
{
  "criteria_scores": {
    "asks_clarification": {"score": 0, "reason": "Agent created the task without asking anything"},
    "does_not_create_task": {"score": 0, "reason": "Agent explicitly says it created a task"},
    "identifies_ambiguity": {"score": 0, "reason": "Agent treated the item as clear and actionable"}
  },
  "overall_notes": "Agent failed all criteria by creating a task without clarification"
}
"""

JUDGE_USER_TEMPLATE = """\
## Agent Response to Grade

{agent_response}

## Grading Rubric

{rubric}

## Fail-if-present phrases
{fail_phrases}

Grade the response. Return ONLY JSON.
"""


# ============================================================================
# YAML Loader
# ============================================================================

def _load_yaml_scenario(path: Path) -> EvalScenario:
    """Parse a single YAML file into an EvalScenario."""
    data = yaml.safe_load(path.read_text())

    criteria = [
        GradingCriterion(
            name=c["name"],
            description=c["description"],
            weight=float(c.get("weight", 1.0)),
        )
        for c in data.get("criteria", [])
    ]

    return EvalScenario(
        id=data["id"],
        name=data["name"],
        description=data["description"],
        system_prompt="",  # filled at test runtime
        user_message=data["user_message"].strip(),
        criteria=criteria,
        fail_if_present=data.get("fail_if_present") or [],
        pass_threshold=float(data.get("pass_threshold", 0.8)),
        requires_knowledge_context=bool(data.get("requires_knowledge_context", False)),
    )


def _load_dir(directory: Path) -> list[EvalScenario]:
    """Load all non-template YAML files from a directory, sorted by filename."""
    if not directory.exists():
        return []
    paths = sorted(p for p in directory.glob("*.yaml") if not p.name.startswith("_"))
    return [_load_yaml_scenario(p) for p in paths]


def build_scenarios() -> list[EvalScenario]:
    """Return all eval scenarios: designed scenarios first, then regressions."""
    return _load_dir(SCENARIOS_DIR) + _load_dir(REGRESSIONS_DIR)
