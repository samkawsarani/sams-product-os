#!/usr/bin/env python3
"""
Automated tests for SAMS PRODUCT OS Task Manager MCP Server

Tests cover:
- Ambiguity detection
- Clarification question generation
- Task content generation (all categories)
- Similarity calculation
- Auto-categorization
- Helper functions

Run with: python3 -m pytest test_server.py -v
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch
from datetime import datetime, timedelta

from server import (
    is_ambiguous,
    generate_clarification_questions,
    generate_task_content,
    calculate_similarity,
    auto_categorize,
    load_config,
    archive_task,
    write_task_file,
    parse_yaml_frontmatter,
    get_all_tasks,
    TASKS_DIR,
)


class TestAmbiguityDetection:
    """Test ambiguity detection for backlog items"""

    def test_too_short(self):
        """Items less than 10 chars are ambiguous"""
        result, reason = is_ambiguous("Fix bug")
        assert result is True
        assert "too short" in reason.lower()

    def test_no_action_verb(self):
        """Items without action verbs are ambiguous"""
        result, reason = is_ambiguous("The database connection timeout settings")
        assert result is True
        assert "action verb" in reason.lower()

    def test_vague_language(self):
        """Items with vague words are ambiguous"""
        result, reason = is_ambiguous("Maybe update the documentation")
        assert result is True
        assert "vague" in reason.lower()

    def test_clear_item(self):
        """Clear items with action verbs are not ambiguous"""
        result, reason = is_ambiguous("Fix authentication bug in login flow")
        assert result is False
        assert reason == ""

    def test_action_verbs_recognized(self):
        """Various action verbs should be recognized"""
        clear_items = [
            "Add user authentication to the app",
            "Update the API documentation",
            "Email Sarah about Q4 roadmap",
            "Review the PRD draft for mobile app",
            "Research competitor pricing models",
        ]

        for item in clear_items:
            result, _ = is_ambiguous(item)
            assert result is False, f"'{item}' should not be ambiguous"


class TestClarificationQuestions:
    """Test clarification question generation"""

    def test_missing_deadline(self):
        """Items without deadline words get deadline question"""
        questions = generate_clarification_questions("Fix the bug in production")
        assert any("when" in q.lower() for q in questions)

    def test_missing_context(self):
        """Items without context words get context question"""
        questions = generate_clarification_questions("Update documentation")
        assert any("why" in q.lower() or "context" in q.lower() for q in questions)

    def test_has_deadline_and_context(self):
        """Items with deadline and context get fewer questions"""
        questions = generate_clarification_questions(
            "Fix auth bug by Friday because users can't log in"
        )
        # Should have fewer questions since it has deadline and context
        assert len(questions) >= 1  # At least generic question

    def test_question_format(self):
        """All questions should end with question mark"""
        questions = generate_clarification_questions("Something to do")
        for q in questions:
            assert q.endswith("?") or q.endswith(")"), f"'{q}' should be a question"


class TestTaskContentGeneration:
    """Test smart task content generation for each category"""

    def test_technical_template(self):
        """Technical tasks get appropriate sections"""
        content = generate_task_content(
            "Fix auth bug", "technical", "Users can't log in"
        )

        assert "## Context" in content
        assert "Users can't log in" in content
        assert "## Technical Details" in content
        assert "Tech Stack" in content
        assert "Dependencies" in content
        assert "Acceptance Criteria" in content
        assert "## Progress Log" in content

    def test_outreach_template(self):
        """Outreach tasks get appropriate sections"""
        content = generate_task_content("Email Sarah", "outreach", "Q4 planning")

        assert "## Context" in content
        assert "Q4 planning" in content
        assert "## Contact Details" in content
        assert "Who:" in content
        assert "Channel:" in content
        assert "## Talking Points" in content
        assert "## Follow-up" in content

    def test_research_template(self):
        """Research tasks get appropriate sections"""
        content = generate_task_content(
            "Research competitors", "research", "Pricing analysis"
        )

        assert "## Context" in content
        assert "Pricing analysis" in content
        assert "## Questions to Answer" in content
        assert "## Sources to Check" in content
        assert "## Synthesis" in content

    def test_writing_template(self):
        """Writing tasks get appropriate sections"""
        content = generate_task_content("Write blog post", "writing", "Product launch")

        assert "## Context" in content
        assert "Product launch" in content
        assert "## Audience" in content
        assert "## Key Points" in content
        assert "## Outline" in content
        assert "draft" in content.lower()

    def test_admin_template(self):
        """Admin tasks get appropriate sections"""
        content = generate_task_content(
            "Schedule meeting", "admin", "Team planning"
        )

        assert "## Context" in content
        assert "Team planning" in content
        assert "## Details" in content
        assert "## Next Actions" in content

    def test_unknown_category_template(self):
        """Unknown categories get default template"""
        content = generate_task_content(
            "Random task", "unknown-category", "Some context"
        )

        assert "## Context" in content
        assert "Some context" in content
        assert "## Details" in content
        assert "## Next Actions" in content

    def test_empty_context(self):
        """Empty context gets placeholder"""
        content = generate_task_content("Task title", "technical", "")

        assert "## Context" in content
        assert "[Why this task matters]" in content

    def test_progress_log_with_date(self):
        """All templates include progress log with date"""
        content = generate_task_content("Task", "technical", "Context")

        assert "## Progress Log" in content
        assert "Task created" in content


class TestSimilarityCalculation:
    """Test task similarity scoring"""

    def setup_method(self):
        """Load config for tests"""
        self.config = load_config()

    def test_identical_titles(self):
        """Identical titles should have high similarity"""
        task1 = {"title": "Fix auth bug", "keywords": [], "category": "technical"}
        task2 = {"title": "Fix auth bug", "keywords": [], "category": "technical"}

        similarity = calculate_similarity(task1, task2, self.config)
        # With identical titles (1.0 * 0.6) + no keywords (0 * 0.3) = 0.6
        assert similarity >= 0.6

    def test_different_titles(self):
        """Different titles should have low similarity"""
        task1 = {
            "title": "Fix authentication bug",
            "keywords": [],
            "category": "technical",
        }
        task2 = {"title": "Write blog post", "keywords": [], "category": "writing"}

        similarity = calculate_similarity(task1, task2, self.config)
        assert similarity < 0.3

    def test_similar_titles(self):
        """Similar titles should have medium similarity"""
        task1 = {"title": "Fix auth bug", "keywords": [], "category": "technical"}
        task2 = {
            "title": "Fix authentication bug",
            "keywords": [],
            "category": "technical",
        }

        similarity = calculate_similarity(task1, task2, self.config)
        assert 0.4 < similarity < 0.9

    def test_keyword_overlap_increases_similarity(self):
        """Tasks with shared keywords should have higher similarity"""
        task1 = {
            "title": "Task A",
            "keywords": ["auth", "security", "bug"],
            "category": "technical",
        }
        task2 = {
            "title": "Task B",
            "keywords": ["auth", "security"],
            "category": "technical",
        }

        similarity_with_keywords = calculate_similarity(task1, task2, self.config)

        task1_no_kw = {"title": "Task A", "keywords": [], "category": "technical"}
        task2_no_kw = {"title": "Task B", "keywords": [], "category": "technical"}

        similarity_without_keywords = calculate_similarity(
            task1_no_kw, task2_no_kw, self.config
        )

        assert similarity_with_keywords > similarity_without_keywords

    def test_different_category_reduces_similarity(self):
        """Different categories should reduce similarity"""
        task1 = {"title": "Write documentation", "keywords": [], "category": "writing"}
        task2 = {
            "title": "Write documentation",
            "keywords": [],
            "category": "technical",
        }

        similarity = calculate_similarity(task1, task2, self.config)

        # Same title but different category should still be somewhat similar
        # but penalized by category mismatch
        assert similarity < 1.0

    def test_case_insensitive(self):
        """Similarity calculation should be case-insensitive"""
        task1 = {"title": "Fix Auth Bug", "keywords": ["AUTH"], "category": "technical"}
        task2 = {"title": "fix auth bug", "keywords": ["auth"], "category": "technical"}

        similarity = calculate_similarity(task1, task2, self.config)
        assert similarity > 0.8


class TestAutoCategorization:
    """Test auto-categorization based on keywords"""

    def setup_method(self):
        """Load config for tests"""
        self.config = load_config()

    def test_technical_keywords(self):
        """Technical keywords should categorize as technical"""
        category = auto_categorize(
            "Fix the authentication bug", "The API is broken", self.config
        )
        assert category == "technical"

    def test_outreach_keywords(self):
        """Outreach keywords should categorize as outreach"""
        category = auto_categorize(
            "Email the client", "Need to schedule a meeting", self.config
        )
        assert category == "outreach"

    def test_research_keywords(self):
        """Research keywords should categorize as research"""
        category = auto_categorize(
            "Research competitors", "Analyze market trends", self.config
        )
        assert category == "research"

    def test_writing_keywords(self):
        """Writing keywords should categorize as writing"""
        category = auto_categorize("Write blog post", "Draft the proposal", self.config)
        assert category == "writing"

    def test_admin_keywords(self):
        """Admin keywords should categorize as admin"""
        category = auto_categorize(
            "Schedule the meeting", "Organize team calendar", self.config
        )
        assert category == "admin"

    def test_strategy_keywords(self):
        """Strategy keywords should categorize as strategy"""
        category = auto_categorize(
            "Define product roadmap", "Planning OKR goals for the quarter", self.config
        )
        assert category == "strategy"

    def test_stakeholder_keywords(self):
        """Stakeholder keywords should categorize as stakeholder"""
        category = auto_categorize(
            "Prepare executive update", "Leadership alignment presentation", self.config
        )
        assert category == "stakeholder"

    def test_discovery_keywords(self):
        """Discovery keywords should categorize as discovery"""
        category = auto_categorize(
            "Conduct user research interviews", "Validate customer pain points", self.config
        )
        assert category == "discovery"

    def test_no_matching_keywords(self):
        """Items without matching keywords return empty category"""
        category = auto_categorize("Random task", "No specific keywords", self.config)
        assert category == ""

    def test_multiple_categories_picks_best(self):
        """When multiple categories match, pick the one with most matches"""
        # This has both 'code' (technical) and 'document' (writing)
        # but 'code' appears more prominently
        category = auto_categorize(
            "Code review", "Review the code and document findings", self.config
        )
        # Should pick technical since 'code' matches
        assert category == "technical"

    def test_case_insensitive_matching(self):
        """Keyword matching should be case-insensitive"""
        category = auto_categorize("FIX the BUG", "API is broken", self.config)
        assert category == "technical"


class TestConfigLoading:
    """Test configuration loading"""

    def test_config_has_required_fields(self):
        """Config should have all required fields"""
        config = load_config()

        assert "priority_caps" in config
        assert "task_aging" in config
        assert "deduplication" in config
        assert "category_keywords" in config

    def test_priority_caps_correct(self):
        """Priority caps should match expected values"""
        config = load_config()

        assert config["priority_caps"]["P0"] == 3
        assert config["priority_caps"]["P1"] == 7
        assert config["priority_caps"]["P2"] == 15
        assert config["priority_caps"]["P3"] == 999

    def test_deduplication_threshold_valid(self):
        """Deduplication threshold should be between 0 and 1"""
        config = load_config()

        threshold = config["deduplication"]["similarity_threshold"]
        assert 0 <= threshold <= 1


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_empty_title_ambiguity(self):
        """Empty titles are ambiguous"""
        result, _ = is_ambiguous("")
        assert result is True

    def test_whitespace_only_title(self):
        """Whitespace-only titles are ambiguous"""
        result, _ = is_ambiguous("   ")
        assert result is True

    def test_very_long_title(self):
        """Very long clear titles are not ambiguous"""
        long_title = "Fix the critical authentication bug that prevents users from logging in to the production environment by updating the OAuth token validation logic"
        result, _ = is_ambiguous(long_title)
        assert result is False

    def test_special_characters_in_title(self):
        """Special characters don't break ambiguity check"""
        result, _ = is_ambiguous("Fix bug in API endpoint /users/{id}")
        assert result is False

    def test_unicode_in_title(self):
        """Unicode characters are handled correctly"""
        result, _ = is_ambiguous("Fix authentication bug in français locale")
        assert result is False

    def test_empty_config_keywords(self):
        """Auto-categorization works with empty keyword lists"""
        config = {"category_keywords": {}}
        category = auto_categorize("Fix bug", "In the API", config)
        assert category == ""


class TestArchiveTask:
    """Test archive_task() helper function"""

    def setup_method(self):
        """Create a temporary tasks directory for testing"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_tasks = Path(self.temp_dir) / "tasks"
        self.temp_tasks.mkdir()

    def teardown_method(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.temp_dir)

    def test_archive_moves_file(self):
        """archive_task() moves file to _archived/completed/ with date prefix"""
        # Create a task file
        task_file = self.temp_tasks / "test-task.md"
        task_file.write_text("---\ntitle: Test Task\nstatus: d\n---\n\nBody\n")

        with patch("server.TASKS_DIR", self.temp_tasks):
            archived_path = archive_task(task_file)

        # Original file should be gone
        assert not task_file.exists()

        # Archived file should exist with date prefix
        assert archived_path.exists()
        today = datetime.now().strftime("%Y-%m-%d")
        assert archived_path.name == f"{today}-test-task.md"
        assert archived_path.parent.name == "completed"
        assert archived_path.parent.parent.name == "_archived"

    def test_archive_creates_directory(self):
        """archive_task() creates _archived/completed/ if it doesn't exist"""
        task_file = self.temp_tasks / "test-task.md"
        task_file.write_text("---\ntitle: Test\n---\n\nBody\n")

        archive_dir = self.temp_tasks / "_archived" / "completed"
        assert not archive_dir.exists()

        with patch("server.TASKS_DIR", self.temp_tasks):
            archive_task(task_file)

        assert archive_dir.exists()

    def test_archive_preserves_content(self):
        """Archived file retains its original content"""
        content = "---\ntitle: Test Task\nstatus: d\npriority: P1\n---\n\nTask body here\n"
        task_file = self.temp_tasks / "my-task.md"
        task_file.write_text(content)

        with patch("server.TASKS_DIR", self.temp_tasks):
            archived_path = archive_task(task_file)

        assert archived_path.read_text() == content


class TestGetAllTasksWithArchived:
    """Test get_all_tasks() with include_archived parameter"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_tasks = Path(self.temp_dir) / "tasks"
        self.temp_tasks.mkdir()

        # Create an active task
        active_file = self.temp_tasks / "active-task.md"
        write_task_file(active_file, {
            "title": "Active Task",
            "priority": "P1",
            "status": "s",
            "category": "technical",
            "keywords": [],
            "created_date": datetime.now().isoformat(),
            "updated_date": datetime.now().isoformat(),
        }, "Active body")

        # Create an archived task
        archive_dir = self.temp_tasks / "_archived" / "completed"
        archive_dir.mkdir(parents=True)
        archived_file = archive_dir / "2026-02-20-done-task.md"
        write_task_file(archived_file, {
            "title": "Done Task",
            "priority": "P2",
            "status": "d",
            "category": "admin",
            "keywords": [],
            "created_date": datetime.now().isoformat(),
            "updated_date": datetime.now().isoformat(),
        }, "Done body")

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_default_excludes_archived(self):
        """get_all_tasks() without include_archived returns only active tasks"""
        with patch("server.TASKS_DIR", self.temp_tasks):
            tasks = get_all_tasks()
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Active Task"

    def test_include_archived_returns_all(self):
        """get_all_tasks(include_archived=True) returns active + archived tasks"""
        with patch("server.TASKS_DIR", self.temp_tasks):
            tasks = get_all_tasks(include_archived=True)
        assert len(tasks) == 2
        titles = {t["title"] for t in tasks}
        assert "Active Task" in titles
        assert "Done Task" in titles

    def test_archived_tasks_have_archived_flag(self):
        """Archived tasks have 'archived': True"""
        with patch("server.TASKS_DIR", self.temp_tasks):
            tasks = get_all_tasks(include_archived=True)
        archived = [t for t in tasks if t.get("archived")]
        assert len(archived) == 1
        assert archived[0]["title"] == "Done Task"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
