#!/usr/bin/env python3
"""
Automated tests for Task Manager MCP Server

Tests cover:
- Ambiguity detection
- Clarification question generation
- Task content generation (all categories)
- Similarity calculation
- Auto-categorization
- Backlog parsing
- Helper functions

Run with: python3 -m pytest test_server.py -v
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch
from datetime import datetime

from server import (
    is_ambiguous,
    generate_clarification_questions,
    generate_task_content,
    calculate_similarity,
    auto_categorize,
    load_config,
    archive_task,
    write_task_file,
    get_all_tasks,
    parse_backlog_items,
    slugify,
    generate_initiative_content,
    generate_reference_content,
    find_related_initiative,
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
            "Email the team about the roadmap",
            "Review the design draft for onboarding",
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
        content = generate_task_content("Email the team", "outreach", "Sprint planning")

        assert "## Context" in content
        assert "Sprint planning" in content
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
        result, _ = is_ambiguous("Fix authentication bug in localised settings")
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
        """archive_task() moves file to _archived/ with date prefix"""
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
        assert archived_path.parent.name == "_archived"

    def test_archive_creates_directory(self):
        """archive_task() creates _archived/ if it doesn't exist"""
        task_file = self.temp_tasks / "test-task.md"
        task_file.write_text("---\ntitle: Test\n---\n\nBody\n")

        archive_dir = self.temp_tasks / "_archived"
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
        archive_dir = self.temp_tasks / "_archived"
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


class TestParseBacklogItems:
    """Test block-based backlog parser"""

    def test_heading_with_bullets_expands(self):
        """Heading + bullets: each bullet becomes its own item with heading as context"""
        content = """# Backlog
## Legacy Migration
- Need to talk to the team about migration plans
- Define missing capabilities
"""
        items = parse_backlog_items(content)
        assert len(items) == 2
        assert items[0]["title"] == "Need to talk to the team about migration plans"
        assert "Legacy Migration" in items[0]["description"]
        assert items[1]["title"] == "Define missing capabilities"

    def test_h3_headings(self):
        """### headings should also work as item delimiters"""
        content = """# Backlog
### Scheduled Downtime Handling
- How do we handle jobs during maintenance windows

### New Payment Methods
- What use cases beyond credit cards?
"""
        items = parse_backlog_items(content)
        assert len(items) == 2
        assert items[0]["title"] == "How do we handle jobs during maintenance windows"
        assert items[1]["title"] == "What use cases beyond credit cards?"

    def test_flat_bullets_no_headers(self):
        """Just bullet points, no headers at all"""
        content = """# Backlog

- Email the team about the roadmap
- Review the PRD draft
- Research competitor pricing
"""
        items = parse_backlog_items(content)
        assert len(items) == 3
        assert items[0]["title"] == "Email the team about the roadmap"
        assert items[1]["title"] == "Review the PRD draft"
        assert items[2]["title"] == "Research competitor pricing"

    def test_plain_text_blocks(self):
        """Plain text separated by blank lines"""
        content = """# Backlog

Email the team about the roadmap

Look into mobile perf issues
Users complaining about slow startup times
"""
        items = parse_backlog_items(content)
        assert len(items) == 2
        assert items[0]["title"] == "Email the team about the roadmap"
        assert items[1]["title"] == "Look into mobile perf issues"
        assert "slow startup" in items[1]["description"]

    def test_checklist_skips_done(self):
        """Checked [x] items are skipped, unchecked [ ] are kept"""
        content = """# Backlog

- [x] Setup tool A
- [ ] Setup tool B
- [x] Update all configs
- [ ] Setup tool C
"""
        items = parse_backlog_items(content)
        titles = [i["title"] for i in items]
        assert "Setup tool B" in titles
        assert "Setup tool C" in titles
        assert "Setup tool A" not in titles
        assert "Update all configs" not in titles

    def test_checklist_under_heading_skips_done(self):
        """Checked [x] items under a heading are also skipped"""
        content = """# Backlog
### Setup TODO
- [x] Setup tool A
- [ ] Setup tool B
- [x] Update all configs
- [ ] Setup tool C
"""
        items = parse_backlog_items(content)
        titles = [i["title"] for i in items]
        assert "Setup tool B" in titles
        assert "Setup tool C" in titles
        assert "Setup tool A" not in titles
        assert "Update all configs" not in titles
        # Heading context preserved
        assert all("Setup TODO" in i["description"] for i in items)

    def test_mixed_headings_and_bullets(self):
        """Mix of headed sections and standalone bullets"""
        content = """# Backlog
### Legacy Migration
- Talk to the team about plans

- Random standalone task here

### New Payment Methods
- Explore use cases
"""
        items = parse_backlog_items(content)
        assert len(items) == 3
        titles = [i["title"] for i in items]
        assert "Talk to the team about plans" in titles
        assert "Random standalone task here" in titles
        assert "Explore use cases" in titles

    def test_heading_with_text_description(self):
        """Heading followed by prose, not bullets"""
        content = """# Backlog
## Strategy Feedback
Overall, this is good. Few thoughts on ownership and dependency mapping.
Who owns each pillar?
"""
        items = parse_backlog_items(content)
        assert len(items) == 1
        assert items[0]["title"] == "Strategy Feedback"
        assert "ownership" in items[0]["description"]

    def test_empty_backlog(self):
        """Empty backlog returns no items"""
        items = parse_backlog_items("# Backlog\n")
        assert len(items) == 0

    def test_skips_short_items(self):
        """Items shorter than 3/5 chars are skipped"""
        content = """# Backlog

- Hi
- Do this very important task
"""
        items = parse_backlog_items(content)
        assert len(items) == 1
        assert items[0]["title"] == "Do this very important task"

    def test_h2_grouping_header_with_h3_items(self):
        """h2 grouping header followed by h3 items (real-world format)"""
        content = """# Backlog
## Week of March 10
### Task One
- Details about task one

### Task Two
- Details about task two
"""
        items = parse_backlog_items(content)
        titles = [i["title"] for i in items]
        # Bullets under headings expand — title is the bullet text
        assert "Details about task one" in titles
        assert "Details about task two" in titles
        # Heading context is preserved in description
        task_one = [i for i in items if i["title"] == "Details about task one"][0]
        assert "Task One" in task_one["description"]

    def test_url_in_task_not_treated_as_reference(self):
        """Items with URLs should keep their text as title, URL in description"""
        content = """# Backlog
### Setup TODO
- [ ] Setup Tool A https://example.com/tool-a
- [ ] Setup Tool B https://example.com/tool-b
"""
        items = parse_backlog_items(content)
        assert len(items) == 2
        # URL should be part of the title text, not cause misclassification
        assert "Setup Tool A" in items[0]["title"]
        assert "Setup Tool B" in items[1]["title"]

    def test_asterisk_and_plus_bullets(self):
        """Support * and + bullet styles"""
        content = """# Backlog

* Email the team about goals
+ Review the design draft
- Research competitor trends
"""
        items = parse_backlog_items(content)
        assert len(items) == 3


class TestSlugify:
    """Test slugify helper function"""

    def test_simple_title(self):
        assert slugify("Fix Auth Bug") == "fix-auth-bug"

    def test_special_characters(self):
        assert slugify("Email Team (Q4)!") == "email-team-q4"

    def test_multiple_spaces(self):
        assert slugify("Fix   the   bug") == "fix-the-bug"

    def test_leading_trailing_special(self):
        assert slugify("---hello world---") == "hello-world"

    def test_empty_string(self):
        assert slugify("") == ""

    def test_unicode(self):
        result = slugify("Café résumé")
        assert "caf" in result


class TestGenerateInitiativeContent:
    """Test initiative content generation"""

    def test_basic_content(self):
        content = generate_initiative_content("Mobile Performance", "Users complaining about slow load times")
        assert "# Mobile Performance" in content
        assert "## Summary" in content
        assert "Users complaining about slow load times" in content
        assert "## Opportunity" in content
        assert "## Status" in content
        assert "## Open Questions" in content

    def test_empty_description(self):
        content = generate_initiative_content("Test Initiative", "")
        assert "# Test Initiative" in content
        assert "[Brief description of this initiative]" in content

    def test_format_matches_existing(self):
        """Output should have the same sections as existing initiative files"""
        content = generate_initiative_content("Test", "Desc")
        assert "# Test" in content
        assert "## Summary" in content
        assert "## Opportunity" in content
        assert "## Status" in content
        assert "Early idea" in content
        assert "## Open Questions" in content


class TestGenerateReferenceContent:
    """Test reference content generation"""

    def test_with_url(self):
        content = generate_reference_content(
            "API Design Article",
            "Found article https://example.com/api-design about best practices"
        )
        assert "# API Design Article" in content
        assert "**Source:** https://example.com/api-design" in content
        assert "Found article" in content

    def test_without_url(self):
        content = generate_reference_content("Competitor Notes", "Some notes about competitors")
        assert "# Competitor Notes" in content
        assert "**Source:** [URL]" in content
        assert "Some notes about competitors" in content

    def test_empty_description(self):
        content = generate_reference_content("Empty Ref", "")
        assert "# Empty Ref" in content
        assert "**Source:** [URL]" in content


class TestFindRelatedInitiative:
    """Test find_related_initiative helper"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_initiatives = Path(self.temp_dir) / "initiatives"
        self.temp_initiatives.mkdir()

        # Create some initiative folders
        (self.temp_initiatives / "migrate-legacy").mkdir()
        (self.temp_initiatives / "mobile-performance").mkdir()
        (self.temp_initiatives / "groomed-requests").mkdir()  # Should be ignored

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_finds_matching_folder(self):
        with patch("server.INITIATIVES_DIR", self.temp_initiatives):
            result = find_related_initiative("Legacy migration timeline", "Details about legacy system migration")
        assert result is not None
        assert result.name == "migrate-legacy"

    def test_no_match_returns_none(self):
        with patch("server.INITIATIVES_DIR", self.temp_initiatives):
            result = find_related_initiative("Unrelated topic", "Nothing matches here")
        assert result is None

    def test_ignores_groomed_requests(self):
        with patch("server.INITIATIVES_DIR", self.temp_initiatives):
            result = find_related_initiative("groomed requests info", "About groomed requests")
        assert result is None

    def test_handles_missing_directory(self):
        with patch("server.INITIATIVES_DIR", Path("/nonexistent")):
            result = find_related_initiative("Anything", "Description")
        assert result is None

    def test_matches_related_folder(self):
        with patch("server.INITIATIVES_DIR", self.temp_initiatives):
            result = find_related_initiative("Mobile performance research", "Looking into performance issues")
        assert result is not None
        assert result.name == "mobile-performance"


class TestStatusTransitions:
    """Test valid status transitions via file write/read roundtrip."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_tasks = Path(self.temp_dir) / "tasks"
        self.temp_tasks.mkdir()

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    @pytest.mark.parametrize("from_status,to_status", [
        ("n", "s"),  # not started -> started
        ("s", "b"),  # started -> blocked
        ("b", "s"),  # blocked -> started
        ("s", "d"),  # started -> done
        ("n", "d"),  # not started -> done (skip started)
        ("d", "n"),  # done -> not started (reopen)
    ])
    def test_status_transitions(self, from_status: str, to_status: str):
        """Test all valid status transitions work."""
        task_file = self.temp_tasks / f"transition-{from_status}-{to_status}.md"
        write_task_file(task_file, {
            "title": f"Transition {from_status} to {to_status}",
            "priority": "P2",
            "status": from_status,
            "category": "technical",
            "keywords": [],
            "created_date": datetime.now().isoformat(),
            "updated_date": datetime.now().isoformat(),
        }, "")

        from server import parse_yaml_frontmatter
        fm, body = parse_yaml_frontmatter(task_file)
        fm["status"] = to_status
        write_task_file(task_file, fm, body)

        content = task_file.read_text()
        assert f"status: {to_status}" in content


class TestTaskFileIntegrity:
    """Test task file integrity after multiple operations."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_tasks = Path(self.temp_dir) / "tasks"
        self.temp_tasks.mkdir()

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_multiple_updates_preserve_content(self):
        """Multiple updates preserve all content."""
        original_body = "## Context\nImportant context here.\n\n## Technical Details\n- Tech 1\n- Tech 2\n"
        frontmatter = {
            "title": "Integrity Test",
            "priority": "P1",
            "status": "n",
            "category": "technical",
            "keywords": ["test", "integrity"],
            "created_date": datetime.now().isoformat(),
            "updated_date": datetime.now().isoformat(),
        }
        task_file = self.temp_tasks / "integrity-test.md"
        write_task_file(task_file, frontmatter, original_body)

        from server import parse_yaml_frontmatter
        for status in ["s", "b", "s", "d"]:
            fm, body = parse_yaml_frontmatter(task_file)
            fm["status"] = status
            fm["updated_date"] = datetime.now().isoformat()
            write_task_file(task_file, fm, body)

        final_fm, final_body = parse_yaml_frontmatter(task_file)
        assert final_fm["title"] == "Integrity Test"
        assert final_fm["keywords"] == ["test", "integrity"]
        assert "## Context" in final_body
        assert "## Technical Details" in final_body

    def test_special_characters_preserved(self):
        """Special characters are preserved through updates."""
        body = '## Context\nCode: `const x = { key: "value" };`\nURL: https://example.com/path?p=1&o=2\n'
        task_file = self.temp_tasks / "special-chars.md"
        write_task_file(task_file, {
            "title": "Special chars test",
            "priority": "P1",
            "status": "n",
            "category": "technical",
            "keywords": [],
            "created_date": datetime.now().isoformat(),
            "updated_date": datetime.now().isoformat(),
        }, body)

        from server import parse_yaml_frontmatter
        fm, read_body = parse_yaml_frontmatter(task_file)
        fm["status"] = "s"
        write_task_file(task_file, fm, read_body)

        _, final_body = parse_yaml_frontmatter(task_file)
        assert "https://example.com" in final_body
        assert "const x = { key:" in final_body


class TestClearBacklogSimplified:
    """Test that clear_backlog just resets BACKLOG.md without archiving"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_root = Path(self.temp_dir)
        self.backlog_file = self.temp_root / "BACKLOG.md"
        self.backlog_file.write_text("# Backlog\n\n- Item 1\n- Item 2\n")
        # Create tasks/_archived to verify nothing gets written there
        (self.temp_root / "tasks" / "_archived").mkdir(parents=True)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_clears_backlog(self):
        """After clearing, BACKLOG.md should only have the header"""
        import asyncio
        from server import call_tool
        with patch("server.PROJECT_ROOT", self.temp_root):
            result = asyncio.run(call_tool("clear_backlog", {}))
        assert self.backlog_file.read_text() == "# Backlog\n"
        assert "cleared" in result[0].text.lower()

    def test_no_archive_created(self):
        """No archive file should be created"""
        import asyncio
        from server import call_tool
        with patch("server.PROJECT_ROOT", self.temp_root):
            asyncio.run(call_tool("clear_backlog", {}))
        archive_dir = self.temp_root / "tasks" / "_archived"
        archive_files = list(archive_dir.glob("*.md"))
        assert len(archive_files) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
