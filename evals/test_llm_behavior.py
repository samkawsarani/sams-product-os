"""
LLM-in-the-Loop Behavioral Evals

Tests whether the agent actually follows behavioral contracts from AGENTS.md
and SKILL.md by making real Claude API calls and grading responses with a judge.

Each scenario:
1. Assembles a system prompt from AGENTS.md + SKILL.md + context
2. Calls the agent N=3 times at temperature=0 for reproducibility
3. Grades each response with a separate judge call
4. Averages criterion scores across all samples; passes if avg >= threshold

Run with: ANTHROPIC_API_KEY=sk-... uv run pytest evals/test_llm_behavior.py -v
Skip automatically if no API key is set.

Cost: ~$0.30-0.60 per full suite run (10 scenarios x 3 samples x 2 calls x ~2K tokens).
"""

import json
import sys
from pathlib import Path

import pytest

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "evals" / "fixtures"))

from llm_scenarios.backlog_processing import (
    EvalScenario,
    JUDGE_SYSTEM_PROMPT,
    JUDGE_USER_TEMPLATE,
    build_scenarios,
)

# Number of agent samples per scenario. Averaged to reduce output variance.
EVAL_SAMPLE_COUNT = 3


# ============================================================================
# Prompt Assembly
# ============================================================================


def build_system_prompt(
    agents_md: str,
    skill_md: str,
    goals_md: str,
    scenario: EvalScenario,
    knowledge_agents_md: str = "",
) -> str:
    """Assemble the full system prompt the agent sees."""
    parts = [
        "You are an AI product management assistant. Follow these instructions exactly.\n\n"
        "# AGENTS.md\n\n"
        f"{agents_md}"
    ]

    if knowledge_agents_md:
        parts.append(f"# knowledge/AGENTS.md\n\n{knowledge_agents_md}")

    parts.append(
        f"# SKILL.md (process-backlog)\n\n{skill_md}\n\n"
        f"# GOALS.md\n\n{goals_md}\n\n"
        "# Important\n\n"
        "- You do NOT have access to any tools or MCP servers in this conversation.\n"
        "- You cannot create files, call APIs, or execute commands.\n"
        "- Respond as if you are presenting findings to the user for review.\n"
        "- Follow ALL behavioral instructions from AGENTS.md and SKILL.md above.\n"
    )

    return "\n\n".join(parts)


# ============================================================================
# API Calls
# ============================================================================


def call_agent(client, model: str, system_prompt: str, user_message: str) -> str:
    """Call Claude as the agent under test at temperature=0. Returns text response."""
    response = client.messages.create(
        model=model,
        max_tokens=1500,
        temperature=0,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


def call_judge(
    client,
    model: str,
    agent_response: str,
    scenario: EvalScenario,
) -> dict:
    """Call Claude as the judge at temperature=0. Returns parsed JSON with criterion scores."""
    rubric_lines = []
    for c in scenario.criteria:
        rubric_lines.append(f"- **{c.name}** (weight {c.weight}): {c.description}")
    rubric = "\n".join(rubric_lines)

    fail_phrases = (
        ", ".join(f'"{p}"' for p in scenario.fail_if_present)
        if scenario.fail_if_present
        else "None"
    )

    user_msg = JUDGE_USER_TEMPLATE.format(
        agent_response=agent_response,
        rubric=rubric,
        fail_phrases=fail_phrases,
    )

    response = client.messages.create(
        model=model,
        max_tokens=1000,
        temperature=0,
        system=JUDGE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )

    text = response.content[0].text.strip()

    # Extract JSON from response (handle markdown code blocks)
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])

    return json.loads(text)


# ============================================================================
# Grading
# ============================================================================


def grade_response(judge_output: dict, scenario: EvalScenario) -> tuple[bool, float, dict]:
    """
    Compute weighted score and pass/fail from a single judge output.

    Returns:
        (passed, score, details) where details maps criterion name to score+reason.
    """
    criteria_scores = judge_output.get("criteria_scores", {})
    total_weight = 0.0
    weighted_sum = 0.0
    details = {}

    for criterion in scenario.criteria:
        entry = criteria_scores.get(criterion.name, {"score": 0, "reason": "not graded"})
        score = entry.get("score", 0)
        reason = entry.get("reason", "")

        weighted_sum += score * criterion.weight
        total_weight += criterion.weight
        details[criterion.name] = {"score": score, "reason": reason}

    final_score = weighted_sum / total_weight if total_weight > 0 else 0.0
    passed = final_score >= scenario.pass_threshold

    return passed, final_score, details


def grade_multi_sample(
    judge_outputs: list[dict], scenario: EvalScenario
) -> tuple[bool, float, dict]:
    """
    Average criterion scores across N judge outputs and compute final pass/fail.

    For binary criteria (0 or 1), averaging gives a majority-vote-like result:
    a criterion is considered passed if it passes in the majority of samples.

    Returns:
        (passed, avg_score, details) where details maps criterion name to
        {avg_score, sample_scores, reasons}.
    """
    n = len(judge_outputs)
    criterion_accum: dict[str, list] = {c.name: [] for c in scenario.criteria}
    criterion_reasons: dict[str, list] = {c.name: [] for c in scenario.criteria}

    for judge_output in judge_outputs:
        criteria_scores = judge_output.get("criteria_scores", {})
        for criterion in scenario.criteria:
            entry = criteria_scores.get(criterion.name, {"score": 0, "reason": "not graded"})
            criterion_accum[criterion.name].append(entry.get("score", 0))
            criterion_reasons[criterion.name].append(entry.get("reason", ""))

    total_weight = 0.0
    weighted_sum = 0.0
    details = {}

    for criterion in scenario.criteria:
        scores = criterion_accum[criterion.name]
        avg = sum(scores) / n if n > 0 else 0.0
        weighted_sum += avg * criterion.weight
        total_weight += criterion.weight
        details[criterion.name] = {
            "avg_score": avg,
            "sample_scores": scores,
            "reasons": criterion_reasons[criterion.name],
        }

    final_score = weighted_sum / total_weight if total_weight > 0 else 0.0
    passed = final_score >= scenario.pass_threshold

    return passed, final_score, details


# ============================================================================
# Parametrized Test
# ============================================================================

SCENARIOS = build_scenarios()
SCENARIO_IDS = [s.id for s in SCENARIOS]


def _load_knowledge_agents_md() -> str:
    """Load knowledge/AGENTS.md if it exists, else return empty string."""
    f = PROJECT_ROOT / "knowledge" / "AGENTS.md"
    return f.read_text() if f.exists() else ""


@pytest.mark.llm
@pytest.mark.parametrize("scenario", SCENARIOS, ids=SCENARIO_IDS)
def test_agent_behavior(
    scenario: EvalScenario,
    anthropic_client,
    llm_model: str,
    judge_model: str,
    agents_md_content: str,
    skill_md_content: str,
    goals_md_content: str,
):
    """
    Test that the agent follows behavioral contracts for each scenario.

    Runs EVAL_SAMPLE_COUNT agent calls and averages judge scores to reduce
    variance from non-determinism. temperature=0 on both calls for reproducibility.
    """
    knowledge_agents_md = _load_knowledge_agents_md() if scenario.requires_knowledge_context else ""

    system_prompt = build_system_prompt(
        agents_md_content, skill_md_content, goals_md_content, scenario,
        knowledge_agents_md=knowledge_agents_md,
    )
    scenario.system_prompt = system_prompt

    # Collect N samples
    agent_responses = []
    judge_outputs = []

    for i in range(EVAL_SAMPLE_COUNT):
        response = call_agent(anthropic_client, llm_model, system_prompt, scenario.user_message)
        agent_responses.append(response)
        judge_output = call_judge(anthropic_client, judge_model, response, scenario)
        judge_outputs.append(judge_output)

    # Average across samples
    passed, score, details = grade_multi_sample(judge_outputs, scenario)

    # Print detailed results
    print(f"\n{'='*60}")
    print(f"Scenario: {scenario.name} ({scenario.id})")
    print(f"Samples: {EVAL_SAMPLE_COUNT} | Avg score: {score:.2f} | Threshold: {scenario.pass_threshold}")
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    print("-" * 60)
    for name, info in details.items():
        avg = info["avg_score"]
        status = "PASS" if avg >= 0.5 else "FAIL"
        sample_str = " ".join(str(s) for s in info["sample_scores"])
        print(f"  [{status}] {name}: avg={avg:.2f} samples=[{sample_str}]")
        for j, reason in enumerate(info["reasons"]):
            print(f"         sample {j+1}: {reason}")
    print(f"{'='*60}")

    assert passed, (
        f"Scenario '{scenario.name}' failed with avg score {score:.2f} "
        f"(threshold: {scenario.pass_threshold}, samples: {EVAL_SAMPLE_COUNT}).\n"
        f"Details: {json.dumps(details, indent=2, default=str)}\n"
        f"Sample responses (first 300 chars each):\n"
        + "\n".join(f"  [{i+1}] {r[:300]}" for i, r in enumerate(agent_responses))
    )
