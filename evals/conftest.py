"""
Shared pytest fixtures for SAMS PRODUCT OS evaluation suite.

Provides common fixtures for:
- Temporary test directories with proper structure
- Test data loading (fixtures and expected outputs)
- Task file creation helpers
"""

import json
import os
import sys
from pathlib import Path
from typing import Generator

import pytest
import yaml

# Add parent directory to path so we can import from tools/mcp-servers/task-manager
# tests/ -> evals/ -> project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "tools" / "mcp-servers" / "task-manager"))


# ============================================================================
# Path Fixtures
# ============================================================================


@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the fixtures directory path."""
    return PROJECT_ROOT / "evals" / "fixtures"


@pytest.fixture
def expected_dir() -> Path:
    """Return the expected outputs directory path."""
    return PROJECT_ROOT / "evals" / "expected" / "outputs"


# ============================================================================
# Temporary Directory Fixtures
# ============================================================================


@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Create a temporary project directory with proper structure.

    Includes:
    - tasks/ directory
    - knowledge/ subdirectories
    - config.yaml with test configuration
    - Empty BACKLOG.md
    """
    # Create directory structure
    (tmp_path / "tasks").mkdir()
    (tmp_path / "knowledge" / "initiatives").mkdir(parents=True)
    (tmp_path / "knowledge" / "references").mkdir(parents=True)
    (tmp_path / "knowledge" / "notes").mkdir(parents=True)

    # Create default config.yaml
    config = {
        "categories": [
            "technical", "outreach", "research", "writing",
            "admin", "strategy", "stakeholder", "discovery"
        ],
        "priorities": ["P0", "P1", "P2", "P3"],
        "statuses": {"n": "not_started", "s": "started", "b": "blocked", "d": "done"},
        "deduplication": {
            "similarity_threshold": 0.6,
            "check_categories": True,
            "check_keywords": True,
        },
        "priority_caps": {"P0": 3, "P1": 7, "P2": 15, "P3": 999},
        "task_aging": {"prune_completed_after": 90, "flag_stale_after": 14},
        "category_keywords": {
            "technical": ["code", "api", "database", "deploy", "fix", "bug", "implement", "develop", "debug", "server"],
            "outreach": ["email", "contact", "reach", "meeting", "call", "follow", "introduce", "connect"],
            "research": ["research", "study", "learn", "investigate", "analyze", "explore", "understand", "evaluate"],
            "writing": ["write", "draft", "document", "blog", "article", "report", "proposal", "outline"],
            "admin": ["schedule", "organize", "expense", "invoice", "calendar", "filing", "review"],
            "strategy": ["roadmap", "vision", "okr", "prioritize", "strategy", "planning", "north star", "metric", "goal"],
            "stakeholder": ["executive", "leadership", "alignment", "present", "stakeholder", "update", "buy-in", "communicate"],
            "discovery": ["interview", "user research", "customer", "pain point", "problem", "discovery", "validate", "persona"],
        },
    }

    with open(tmp_path / "config.yaml", "w") as f:
        yaml.dump(config, f)

    # Create empty BACKLOG.md
    (tmp_path / "BACKLOG.md").touch()

    yield tmp_path


# ============================================================================
# Test Data Loading Fixtures
# ============================================================================


@pytest.fixture
def load_fixture_file(fixtures_dir: Path):
    """
    Factory fixture to load fixture files.

    Usage:
        def test_something(load_fixture_file):
            content = load_fixture_file("test-backlogs/basic.md")
    """
    def _load_fixture(relative_path: str) -> str:
        filepath = fixtures_dir / relative_path
        if not filepath.exists():
            raise FileNotFoundError(f"Fixture file not found: {filepath}")
        return filepath.read_text()

    return _load_fixture


@pytest.fixture
def load_expected_output(expected_dir: Path):
    """
    Factory fixture to load expected output JSON files.

    Usage:
        def test_something(load_expected_output):
            expected = load_expected_output("basic.json")
    """
    def _load_expected(filename: str) -> dict:
        filepath = expected_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Expected output file not found: {filepath}")
        with open(filepath) as f:
            return json.load(f)

    return _load_expected


# ============================================================================
# Pytest Configuration
# ============================================================================


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "llm: marks tests that require LLM API calls (need ANTHROPIC_API_KEY)"
    )


# ============================================================================
# LLM Eval Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def anthropic_client():
    """Session-scoped Anthropic client. Loads from .env, skips if no API key."""
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set in .env or environment — skipping LLM evals")

    import anthropic

    return anthropic.Anthropic(api_key=api_key)


@pytest.fixture(scope="session")
def llm_model() -> str:
    """Model used for the agent under test. Override with LLM_EVAL_MODEL env var."""
    return os.environ.get("LLM_EVAL_MODEL", "claude-sonnet-4-20250514")


@pytest.fixture(scope="session")
def judge_model() -> str:
    """Model used for the judge. Override with LLM_JUDGE_MODEL env var."""
    return os.environ.get("LLM_JUDGE_MODEL", "claude-haiku-4-5-20251001")


@pytest.fixture(scope="session")
def agents_md_content() -> str:
    """Load AGENTS.md content for LLM evals."""
    path = PROJECT_ROOT / "AGENTS.md"
    if not path.exists():
        pytest.skip("AGENTS.md not found")
    return path.read_text()


@pytest.fixture(scope="session")
def skill_md_content() -> str:
    """Load process-backlog SKILL.md content for LLM evals."""
    path = PROJECT_ROOT / ".claude" / "skills" / "process-backlog" / "SKILL.md"
    if not path.exists():
        pytest.skip("process-backlog SKILL.md not found")
    return path.read_text()


@pytest.fixture(scope="session")
def goals_md_content() -> str:
    """Load GOALS.md content for LLM evals."""
    path = PROJECT_ROOT / "GOALS.md"
    if not path.exists():
        pytest.skip("GOALS.md not found")
    return path.read_text()
