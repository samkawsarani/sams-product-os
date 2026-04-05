"""
Agent Behavioral Requirement Tests

Tests that the agent follows behavioral requirements from AGENTS.md and workflows:
- Present findings for user review before creating anything
- Wait for user confirmation before creating tasks/initiatives
- Link tasks to goals from GOALS.md
- Ask for clarification on ambiguous items
- Follow interaction style guidelines

These tests validate behavioral contracts, not just function outputs.

Run with: pytest evals/test_agent_behavior.py -v
"""

import re
from pathlib import Path
from typing import Optional

import pytest

PROJECT_ROOT = Path(__file__).parent.parent


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def agents_md() -> str:
    """Load AGENTS.md content."""
    agents_file = PROJECT_ROOT / "AGENTS.md"
    if not agents_file.exists():
        pytest.skip("AGENTS.md not found")
    return agents_file.read_text()


@pytest.fixture
def process_backlog_workflow() -> str:
    """Load process-backlog skill content."""
    skill_file = PROJECT_ROOT / ".claude" / "skills" / "process-backlog" / "SKILL.md"
    if not skill_file.exists():
        pytest.skip("process-backlog SKILL.md not found")
    return skill_file.read_text()


@pytest.fixture
def goals_md() -> str:
    """Load GOALS.md content."""
    goals_file = PROJECT_ROOT / "GOALS.md"
    if not goals_file.exists():
        pytest.skip("GOALS.md not found")
    return goals_file.read_text()


@pytest.fixture
def sample_goals() -> list[dict]:
    """Sample goals for testing goal alignment."""
    return [
        {
            "name": "Improve Developer Experience",
            "description": "Reduce friction in daily dev workflows",
            "keywords": ["developer", "dx", "tooling", "automation"],
        },
        {
            "name": "Launch Mobile App",
            "description": "Ship iOS and Android apps by Q2",
            "keywords": ["mobile", "ios", "android", "app"],
        },
        {
            "name": "Reduce Churn",
            "description": "Decrease customer churn rate by 20%",
            "keywords": ["churn", "retention", "customer", "engagement"],
        },
    ]


# ============================================================================
# Workflow Compliance Tests
# ============================================================================


class TestWorkflowCompliance:
    """Test that workflow files contain required behavioral instructions."""

    def test_process_backlog_requires_user_review(self, process_backlog_workflow: str):
        """Workflow must instruct agent to present findings before creating."""
        review_patterns = [
            r"present.*findings.*review",
            r"present.*for.*user.*review",
            r"before.*creating",
            r"never.*auto.?create",
        ]

        content_lower = process_backlog_workflow.lower()
        has_review_requirement = any(
            re.search(pattern, content_lower) for pattern in review_patterns
        )

        assert has_review_requirement, (
            "Workflow must instruct agent to present findings for user review before creating"
        )

    def test_process_backlog_requires_confirmation(self, process_backlog_workflow: str):
        """Workflow must require user confirmation before creating items."""
        confirmation_patterns = [
            r"wait.*for.*user.*response",
            r"get.*confirmation",
            r"ask.*proceed",
            r"wait.*for.*confirmation",
        ]

        content_lower = process_backlog_workflow.lower()
        has_confirmation = any(
            re.search(pattern, content_lower) for pattern in confirmation_patterns
        )

        assert has_confirmation, (
            "Workflow must require user confirmation before creating items"
        )

    def test_process_backlog_requires_goal_linking(self, process_backlog_workflow: str):
        """Workflow must instruct linking tasks to goals."""
        goal_patterns = [
            r"link.*to.*goal",
            r"goal.*from.*goals\.md",
            r"reference.*goal",
            r"relevant.*goal",
        ]

        content_lower = process_backlog_workflow.lower()
        has_goal_linking = any(
            re.search(pattern, content_lower) for pattern in goal_patterns
        )

        assert has_goal_linking, (
            "Workflow must instruct agent to link tasks to goals from GOALS.md"
        )

    def test_process_backlog_requires_ambiguity_resolution(self, process_backlog_workflow: str):
        """Workflow must instruct resolving ambiguous items."""
        ambiguity_patterns = [
            r"resolve.*ambigu",
            r"clarif",
            r"vague.*item",
            r"ask.*clarification",
        ]

        content_lower = process_backlog_workflow.lower()
        has_ambiguity_handling = any(
            re.search(pattern, content_lower) for pattern in ambiguity_patterns
        )

        assert has_ambiguity_handling, (
            "Workflow must instruct agent to resolve ambiguous items"
        )

    def test_process_backlog_enforces_priority_caps(self, process_backlog_workflow: str):
        """Workflow must mention priority cap enforcement."""
        priority_patterns = [
            r"priority.*cap",
            r"enforce.*priority",
            r"check.*cap",
            r"p0.*max",
        ]

        content_lower = process_backlog_workflow.lower()
        has_priority_enforcement = any(
            re.search(pattern, content_lower) for pattern in priority_patterns
        )

        assert has_priority_enforcement, (
            "Workflow must instruct agent to enforce priority caps"
        )


class TestAgentsMdCompliance:
    """Test that AGENTS.md contains required behavioral guidelines."""

    def test_agents_md_has_core_rules(self, agents_md: str):
        """AGENTS.md must define core behavioral rules."""
        assert "core rules" in agents_md.lower(), (
            "AGENTS.md must have Core Rules section"
        )

    def test_agents_md_requires_clarification(self, agents_md: str):
        """AGENTS.md must instruct asking for clarification."""
        clarification_patterns = [
            r"ask.*clarification",
            r"stop.*and.*ask",
            r"lacks.*context.*ask",
        ]

        content_lower = agents_md.lower()
        has_clarification = any(
            re.search(pattern, content_lower) for pattern in clarification_patterns
        )

        assert has_clarification, (
            "AGENTS.md must instruct agent to ask for clarification when needed"
        )

    def test_agents_md_references_goals(self, agents_md: str):
        """AGENTS.md must reference GOALS.md for alignment."""
        assert "goals.md" in agents_md.lower(), (
            "AGENTS.md must reference GOALS.md for task alignment"
        )

    def test_agents_md_defines_priority_system(self, tasks_agents_md: str):
        """tasks/AGENTS.md must define the priority system (moved from root in progressive disclosure refactor)."""
        priority_patterns = [
            r"p0.*p1.*p2.*p3",
            r"priorities.*p0",
            r"p0.*max.*3",
        ]

        content_lower = tasks_agents_md.lower()
        has_priority_system = any(
            re.search(pattern, content_lower) for pattern in priority_patterns
        )

        assert has_priority_system, (
            "tasks/AGENTS.md must define the priority system (P0-P3)"
        )


# ============================================================================
# Goal Alignment Tests
# ============================================================================


class TestGoalAlignment:
    """Test goal alignment requirements for tasks."""

    def test_task_should_reference_goal(self, sample_goals: list[dict]):
        """Tasks should be linkable to at least one goal."""
        # Tasks that clearly align with goals (using explicit keywords)
        aligned_tasks = [
            ("Fix developer tooling automation", "Improve Developer Experience"),
            ("Fix iOS mobile app crash on login", "Launch Mobile App"),
            ("Add customer retention churn dashboard", "Reduce Churn"),
        ]

        for task_title, expected_goal in aligned_tasks:
            matching_goal = find_matching_goal(task_title, sample_goals)
            assert matching_goal is not None, (
                f"Task '{task_title}' should match goal '{expected_goal}'"
            )

    def test_orphan_task_detection(self, sample_goals: list[dict]):
        """Tasks that don't align with any goal should be flagged."""
        orphan_tasks = [
            "Reorganize office supplies",
            "Update personal LinkedIn",
            "Random cleanup task",
        ]

        for task_title in orphan_tasks:
            matching_goal = find_matching_goal(task_title, sample_goals)
            # These should NOT match any goal - agent should ask about alignment
            assert matching_goal is None, (
                f"Orphan task '{task_title}' should not match any goal"
            )

    def test_goal_keywords_extraction(self):
        """Goal keywords should be extractable for matching."""
        goal = {
            "name": "Improve Developer Experience",
            "description": "Reduce friction in daily dev workflows by improving tooling",
            "keywords": ["developer", "dx", "tooling"],
        }

        # Extract keywords from goal
        all_keywords = set(goal.get("keywords", []))
        all_keywords.update(goal["name"].lower().split())
        all_keywords.update(goal["description"].lower().split())

        assert "developer" in all_keywords
        assert "tooling" in all_keywords
        assert "friction" in all_keywords


# ============================================================================
# Confirmation Before Action Tests
# ============================================================================


class TestConfirmationBeforeAction:
    """Test scenarios where confirmation is required before action."""

    def test_bulk_creation_requires_confirmation(self):
        """Creating multiple items at once should require confirmation."""
        backlog_items = [
            {"title": "Task 1", "type": "task"},
            {"title": "Task 2", "type": "task"},
            {"title": "Initiative 1", "type": "initiative"},
        ]

        # More than 1 item = requires confirmation
        requires_confirmation = len(backlog_items) > 1
        assert requires_confirmation, "Creating multiple items should require confirmation"

    def test_priority_change_requires_confirmation(self):
        """Changing task priority should be confirmed."""
        scenarios = [
            {"from": "P3", "to": "P0", "requires_confirmation": True},
            {"from": "P2", "to": "P1", "requires_confirmation": True},
            {"from": "P1", "to": "P2", "requires_confirmation": False},  # Downgrade ok
        ]

        for scenario in scenarios:
            # Upgrading priority (lower number = higher priority) needs confirmation
            from_num = int(scenario["from"][1])
            to_num = int(scenario["to"][1])
            is_upgrade = to_num < from_num

            assert is_upgrade == scenario["requires_confirmation"], (
                f"Priority change {scenario['from']} -> {scenario['to']} "
                f"confirmation expected: {scenario['requires_confirmation']}"
            )

    def test_near_cap_requires_warning(self):
        """Creating task when near priority cap should warn user."""
        caps = {"P0": 3, "P1": 7, "P2": 15, "P3": 999}

        scenarios = [
            {"priority": "P0", "current_count": 2, "should_warn": True},
            {"priority": "P0", "current_count": 3, "should_warn": True},  # At cap
            {"priority": "P1", "current_count": 5, "should_warn": False},
            {"priority": "P1", "current_count": 6, "should_warn": True},
        ]

        for scenario in scenarios:
            priority = scenario["priority"]
            count = scenario["current_count"]
            cap = caps[priority]

            # Warn if within 1 of cap or at/over cap
            should_warn = count >= cap - 1

            assert should_warn == scenario["should_warn"], (
                f"Priority {priority} with {count}/{cap} tasks: "
                f"warn expected={scenario['should_warn']}, got={should_warn}"
            )


# ============================================================================
# Helper Functions
# ============================================================================


def find_matching_goal(task_title: str, goals: list[dict]) -> Optional[dict]:
    """
    Find a goal that matches the given task title.
    Returns the matching goal or None.
    """
    task_words = set(task_title.lower().split())

    best_match = None
    best_score = 0

    for goal in goals:
        # Get all keywords for this goal
        goal_keywords = set(k.lower() for k in goal.get("keywords", []))
        goal_keywords.update(goal["name"].lower().split())
        goal_keywords.update(goal.get("description", "").lower().split())

        # Remove common words
        stop_words = {"the", "a", "an", "to", "for", "by", "in", "on", "and", "or"}
        goal_keywords -= stop_words
        task_words_clean = task_words - stop_words

        # Calculate overlap
        overlap = len(goal_keywords & task_words_clean)

        if overlap > best_score:
            best_score = overlap
            best_match = goal

    # Require at least 2 matching keywords
    if best_score >= 2:
        return best_match

    return None


# ============================================================================
# Progressive Disclosure — Fixtures
# ============================================================================


@pytest.fixture
def knowledge_agents_md() -> str:
    """Load knowledge/AGENTS.md content."""
    f = PROJECT_ROOT / "knowledge" / "AGENTS.md"
    if not f.exists():
        pytest.skip("knowledge/AGENTS.md not found")
    return f.read_text()


@pytest.fixture
def tasks_agents_md() -> str:
    """Load tasks/AGENTS.md content."""
    f = PROJECT_ROOT / "tasks" / "AGENTS.md"
    if not f.exists():
        pytest.skip("tasks/AGENTS.md not found")
    return f.read_text()


# ============================================================================
# Progressive Disclosure — Structural Instruction Tests
# ============================================================================


class TestProgressiveDisclosureInstructions:
    """
    Verify that behavioral instructions are present in the correct AGENTS.md files
    after the progressive disclosure refactor.

    These are prerequisite checks — if an instruction isn't in the file,
    the agent can't follow it.
    """

    def test_knowledge_agents_md_has_three_file_pattern(self, knowledge_agents_md: str):
        """Domain learning folders must define the 3-file pattern."""
        for filename in ("knowledge.md", "hypotheses.md", "rules.md"):
            assert filename in knowledge_agents_md, (
                f"knowledge/AGENTS.md must define the '{filename}' file in the domain learning pattern"
            )

    def test_knowledge_agents_md_has_hypothesis_promotion(self, knowledge_agents_md: str):
        """Hypothesis promotion rule (3 confirmations) must be present."""
        content_lower = knowledge_agents_md.lower()
        has_count = "3" in knowledge_agents_md or "three" in content_lower
        has_promotion = "promot" in content_lower
        assert has_count and has_promotion, (
            "knowledge/AGENTS.md must describe hypothesis promotion after 3 confirmations"
        )

    def test_knowledge_agents_md_has_system_review_protocol(self, knowledge_agents_md: str):
        """System review protocol must be in knowledge/AGENTS.md, not root."""
        assert "## System Review Protocol" in knowledge_agents_md, (
            "knowledge/AGENTS.md must contain the ## System Review Protocol section"
        )

    def test_knowledge_agents_md_has_decision_journal(self, knowledge_agents_md: str):
        """Decision journal instructions must be in knowledge/AGENTS.md."""
        assert "## Decision Journal" in knowledge_agents_md, (
            "knowledge/AGENTS.md must contain the ## Decision Journal section"
        )

    @pytest.mark.parametrize("section", [
        "## Decision:",
        "## Context:",
        "## Reasoning:",
        "## Trade-offs accepted:",
    ])
    def test_knowledge_agents_md_decision_format_has_required_sections(
        self, knowledge_agents_md: str, section: str
    ):
        """Decision file format must include all required sections."""
        assert section in knowledge_agents_md, (
            f"knowledge/AGENTS.md decision journal format must include '{section}'"
        )

    def test_tasks_agents_md_has_priority_caps(self, tasks_agents_md: str):
        """Priority caps enforcement must be in tasks/AGENTS.md."""
        assert "## Priority Caps" in tasks_agents_md, (
            "tasks/AGENTS.md must contain the ## Priority Caps section"
        )

    def test_tasks_agents_md_has_archiving_rule(self, tasks_agents_md: str):
        """Archiving rule (move done tasks to _archived/) must be in tasks/AGENTS.md."""
        assert "_archived" in tasks_agents_md, (
            "tasks/AGENTS.md must reference _archived/ for completed task archival"
        )

    def test_root_agents_md_has_search_protocol(self, agents_md: str):
        """Root AGENTS.md must define the QMD+Grep search protocol."""
        assert "## Search Protocol" in agents_md, (
            "Root AGENTS.md must contain ## Search Protocol section"
        )
        assert "QMD" in agents_md, "Search Protocol must mention QMD"
        assert "Grep" in agents_md, "Search Protocol must mention Grep"

    def test_root_agents_md_has_thought_partner_rule(self, agents_md: str):
        """Root AGENTS.md must contain the thought partner / challenge rule."""
        assert "Challenge" in agents_md, (
            "Root AGENTS.md Core Rules must include the 'Challenge my thinking' rule"
        )

    @pytest.mark.parametrize("moved_section", [
        "## Knowledge Architecture",
        "## Task System",
        "## Decision Journal",
    ])
    def test_root_agents_md_not_has_moved_sections(self, agents_md: str, moved_section: str):
        """Sections moved to subdirectory AGENTS.md files must not appear in root."""
        assert moved_section not in agents_md, (
            f"'{moved_section}' was moved to a subdirectory AGENTS.md — it must not appear in root AGENTS.md"
        )
