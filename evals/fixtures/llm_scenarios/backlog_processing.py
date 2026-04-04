"""
LLM eval scenarios for backlog processing behavior.

Each scenario tests a behavioral contract from SKILL.md by giving Claude
a realistic prompt and grading the response against a rubric.
"""

from dataclasses import dataclass, field


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
    requires_knowledge_context: bool = False  # include knowledge/AGENTS.md in system prompt


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
# Scenario Definitions
# ============================================================================

def build_scenarios() -> list[EvalScenario]:
    """Return all eval scenarios. system_prompt is filled at test time."""

    return [
        # ------------------------------------------------------------------
        # 1. Ambiguous item — agent must ask, not create
        # ------------------------------------------------------------------
        EvalScenario(
            id="ambiguous_item",
            name="Ambiguous backlog item",
            description="Agent receives a vague item and should ask for clarification instead of creating a task.",
            system_prompt="",  # filled at runtime
            user_message=(
                "I just added this to my backlog:\n\n"
                "```\n- Fix the thing\n```\n\n"
                "Can you process this?"
            ),
            criteria=[
                GradingCriterion(
                    "asks_clarification",
                    "Agent asks the user for clarification about what 'the thing' refers to",
                ),
                GradingCriterion(
                    "does_not_create_task",
                    "Agent does NOT create a task or say it will create one",
                ),
                GradingCriterion(
                    "identifies_ambiguity",
                    "Agent explicitly flags the item as vague or ambiguous",
                ),
            ],
            fail_if_present=[
                "task created", "I've created", "I created", "created the task",
                "creating a task", "I'll create", "I will create", "adding to tasks",
            ],
            pass_threshold=1.0,
        ),

        # ------------------------------------------------------------------
        # 2. Mixed backlog — categorize, summarize, wait for confirmation
        # ------------------------------------------------------------------
        EvalScenario(
            id="mixed_backlog",
            name="Mixed backlog items",
            description="Agent processes a backlog with task, initiative, reference, and ambiguous items.",
            system_prompt="",
            user_message=(
                "Here's my backlog to process:\n\n"
                "```\n"
                "- Email Sarah about Q4 roadmap review by Friday\n"
                "- Enterprise SSO — we should think about this strategically\n"
                "- https://stripe.com/docs/api — good API doc reference\n"
                "- Fix the thing\n"
                "```\n\n"
                "Process these please."
            ),
            criteria=[
                GradingCriterion(
                    "categorizes_items",
                    "Agent categorizes items into tasks, initiatives, references, and ambiguous",
                ),
                GradingCriterion(
                    "presents_summary",
                    "Agent presents a structured summary or table before taking action",
                ),
                GradingCriterion(
                    "waits_for_confirmation",
                    "Agent asks the user how to proceed or waits for confirmation",
                ),
                GradingCriterion(
                    "does_not_create",
                    "Agent does NOT create any tasks or files without user approval",
                ),
            ],
            fail_if_present=[
                "task created", "I've created", "file created", "I created",
                "created the task", "creating a task", "I'll create", "I will create",
            ],
            pass_threshold=0.8,
        ),

        # ------------------------------------------------------------------
        # 3. Orphan task — no goal match, should flag
        # ------------------------------------------------------------------
        EvalScenario(
            id="orphan_task",
            name="Orphan task with no goal alignment",
            description="Agent receives a task that doesn't align with any goal in GOALS.md.",
            system_prompt="",
            user_message=(
                "Process this backlog item:\n\n"
                "```\n- Reorganize office supplies and restock printer paper\n```"
            ),
            criteria=[
                GradingCriterion(
                    "flags_no_goal",
                    "Agent flags that this task doesn't align with any current goal in GOALS.md",
                ),
                GradingCriterion(
                    "asks_about_alignment",
                    "Agent asks the user about goal alignment or why this matters",
                ),
            ],
            fail_if_present=[],
            pass_threshold=1.0,
        ),

        # ------------------------------------------------------------------
        # 4. P0 cap exceeded — should warn and offer options
        # ------------------------------------------------------------------
        EvalScenario(
            id="p0_cap_exceeded",
            name="P0 priority cap warning",
            description="Agent tries to add a P0 task when 3 P0 tasks already exist.",
            system_prompt="",
            user_message=(
                "Process this backlog item as P0:\n\n"
                "```\n- URGENT: Fix payment processing timeout affecting all merchants\n```\n\n"
                "Current P0 tasks:\n"
                "1. Complete Interac Core transaction migration (due Feb 8)\n"
                "2. Fix OBV verification failures in production\n"
                "3. Resolve merchant portal outage\n"
            ),
            criteria=[
                GradingCriterion(
                    "warns_about_cap",
                    "Agent warns that the P0 cap (3) would be exceeded",
                ),
                GradingCriterion(
                    "shows_existing_p0s",
                    "Agent shows or references the existing P0 tasks",
                ),
                GradingCriterion(
                    "offers_options",
                    "Agent offers options: demote an existing P0, downgrade new task, or override",
                ),
            ],
            fail_if_present=[
                "task created", "I've created", "I created", "created the task",
                "creating a task", "I'll create", "I will create",
            ],
            pass_threshold=0.8,
        ),

        # ------------------------------------------------------------------
        # 5. Duplicate detection — should flag similarity
        # ------------------------------------------------------------------
        EvalScenario(
            id="duplicate_detection",
            name="Duplicate task detection",
            description="Agent receives a task very similar to an existing one.",
            system_prompt="",
            user_message=(
                "Process this backlog item:\n\n"
                "```\n- Fix authentication bug in the login flow\n```\n\n"
                "Existing tasks:\n"
                "- fix-login-auth-bug.md: 'Fix login authentication error for SSO users' (P1, started)\n"
                "- update-api-docs.md: 'Update API documentation for v2 endpoints' (P2, not started)\n"
            ),
            criteria=[
                GradingCriterion(
                    "flags_duplicate",
                    "Agent flags that the new item is similar to the existing 'fix-login-auth-bug' task",
                ),
                GradingCriterion(
                    "shows_existing",
                    "Agent shows the existing similar task for comparison",
                ),
                GradingCriterion(
                    "asks_user",
                    "Agent asks user whether to merge, skip, or create separately",
                ),
            ],
            fail_if_present=[
                "task created", "I've created", "I created", "created the task",
                "creating a task", "I'll create", "I will create",
            ],
            pass_threshold=0.8,
        ),

        # ------------------------------------------------------------------
        # 6. Clear item with goal match — should link and present
        # ------------------------------------------------------------------
        EvalScenario(
            id="clear_item_goal_match",
            name="Clear item matching a goal",
            description="Agent receives a clear task that aligns with Goal 3 (Developer Experience).",
            system_prompt="",
            user_message=(
                "Process this backlog item:\n\n"
                "```\n- Define developer portal requirements for API docs and test credentials\n```"
            ),
            criteria=[
                GradingCriterion(
                    "links_to_goal",
                    "Agent identifies this aligns with Goal 3 (Improve Merchant Onboarding & Developer Experience)",
                ),
                GradingCriterion(
                    "suggests_category",
                    "Agent suggests a category (e.g., technical, strategy, or discovery)",
                ),
                GradingCriterion(
                    "presents_for_review",
                    "Agent presents the item for user review before creating",
                ),
            ],
            fail_if_present=["task created", "I've created"],
            pass_threshold=0.8,
        ),

        # ------------------------------------------------------------------
        # 7. Thought partner — agent must challenge, not just execute
        # ------------------------------------------------------------------
        EvalScenario(
            id="thought_partner",
            name="Thought partner — challenge strategic assumption",
            description="Agent should push back on a casual strategic proposal rather than immediately executing.",
            system_prompt="",
            user_message=(
                "I'm thinking of building a CSV export feature for Q2. "
                "Seems like an easy win — users have asked for it a few times. "
                "Can you help me get this into the backlog?"
            ),
            criteria=[
                GradingCriterion(
                    "challenges_assumption",
                    "Agent questions or challenges the framing of this as an 'easy win' — "
                    "surfaces potential hidden complexity, scope questions, or trade-offs",
                ),
                GradingCriterion(
                    "names_trade_offs",
                    "Agent names at least one concrete risk, edge case, or alternative consideration "
                    "(e.g. data volume, privacy, format support, opportunity cost)",
                ),
                GradingCriterion(
                    "does_not_just_execute",
                    "Agent does NOT immediately create a task or proceed to backlog entry "
                    "without first engaging with the strategic question",
                ),
            ],
            fail_if_present=[
                "task created", "I've created", "I created", "I've added",
                "adding to tasks", "created the task", "I'll create", "I will create",
            ],
            pass_threshold=0.7,
        ),

        # ------------------------------------------------------------------
        # 8. Domain learning capture — agent must write to correct files
        # ------------------------------------------------------------------
        EvalScenario(
            id="domain_learning_capture",
            name="Domain learning — capture analysis into knowledge folder",
            description="After completing analysis, agent should write learnings to the right domain files.",
            system_prompt="",
            user_message=(
                "I just finished a deep dive on our checkout flow. Here's what I found:\n\n"
                "- 40% of users drop off at the address form step (confirmed in analytics)\n"
                "- There's no inline validation — users only see errors on submit\n"
                "- This pattern appears on both mobile and web\n\n"
                "Can you capture these learnings?"
            ),
            criteria=[
                GradingCriterion(
                    "creates_domain_folder",
                    "Agent describes creating or updating a domain-specific folder under knowledge/ "
                    "(e.g. knowledge/checkout-flow/ or similar)",
                ),
                GradingCriterion(
                    "classifies_correctly",
                    "Agent puts the confirmed drop-off stat in knowledge.md (fact) and the "
                    "mobile/web pattern in hypotheses.md (not yet confirmed 3 times, not rules.md)",
                ),
                GradingCriterion(
                    "updates_index",
                    "Agent mentions updating knowledge/INDEX.md to record the new domain folder",
                ),
            ],
            fail_if_present=[],
            pass_threshold=0.7,
            requires_knowledge_context=True,
        ),

        # ------------------------------------------------------------------
        # 9. System review — agent must promote confirmed hypotheses
        # ------------------------------------------------------------------
        EvalScenario(
            id="system_review",
            name="System review — promote confirmed hypotheses to rules",
            description="Agent runs a system review and promotes a hypothesis confirmed 3+ times.",
            system_prompt="",
            user_message=(
                "Can you run a system review on my checkout-flow domain?\n\n"
                "Current state:\n\n"
                "**hypotheses.md**\n"
                "- [3 confirmations] Address form is the primary drop-off point "
                "— confirmed in Jun analytics, Jul user interviews, Aug heatmaps\n"
                "- [1 confirmation] Mobile users bounce faster than web users "
                "— seen in Aug analytics only\n\n"
                "**rules.md**\n"
                "(empty)\n"
            ),
            criteria=[
                GradingCriterion(
                    "promotes_confirmed_hypothesis",
                    "Agent moves the 3-confirmation hypothesis (address form drop-off) to rules.md",
                ),
                GradingCriterion(
                    "keeps_unconfirmed",
                    "Agent leaves the 1-confirmation hypothesis in hypotheses.md — does NOT promote it",
                ),
                GradingCriterion(
                    "reports_changes",
                    "Agent clearly summarises what was promoted, what was kept, and why",
                ),
            ],
            fail_if_present=[],
            pass_threshold=0.8,
            requires_knowledge_context=True,
        ),

        # ------------------------------------------------------------------
        # 10. Decision journal — agent must log with required sections
        # ------------------------------------------------------------------
        EvalScenario(
            id="decision_journal",
            name="Decision journal — log a technical decision",
            description="Agent documents a decision in knowledge/decisions/ with the correct format.",
            system_prompt="",
            user_message=(
                "I just decided to use REST instead of GraphQL for our new data API. "
                "The team knows REST well, GraphQL has a steeper learning curve, "
                "and we don't have complex client-driven query needs right now. "
                "Can you log this decision?"
            ),
            criteria=[
                GradingCriterion(
                    "names_correct_location",
                    "Agent says it will create a file in knowledge/decisions/ "
                    "with a YYYY-MM-DD-{topic}.md filename",
                ),
                GradingCriterion(
                    "includes_required_sections",
                    "Agent's proposed file includes: Decision, Context, Alternatives considered, "
                    "Reasoning, and Trade-offs accepted",
                ),
                GradingCriterion(
                    "includes_supersedes_field",
                    "Agent includes a Supersedes field (even if N/A or empty)",
                ),
            ],
            fail_if_present=[],
            pass_threshold=0.8,
            requires_knowledge_context=True,
        ),
    ]
