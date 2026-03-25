"""Tests for RuleLoader."""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from agents.core.rule_loader import RuleLoader, EXCERPT_MAX_CHARS


@pytest.fixture
def loader(tmp_path):
    # Create minimal rule file structure
    common = tmp_path / "common"
    common.mkdir()
    (common / "depth-levels.md").write_text("# Depth Levels\n" + "x" * 3000)
    (common / "overconfidence-prevention.md").write_text("# Overconfidence\ncontent here")
    (common / "question-format-guide.md").write_text("# Questions\nformat here")

    security = tmp_path / "extensions" / "security" / "baseline"
    security.mkdir(parents=True)
    (security / "security-baseline.md").write_text("# Security Baseline\n" + "s" * 5000)

    return RuleLoader(base_path=tmp_path)


def test_load_for_agent_returns_string(loader):
    result = loader.load_for_agent("classifier")
    assert isinstance(result, str)
    assert "AI-DLC Rules Context" in result


def test_universal_rules_always_included(loader):
    result = loader.load_for_agent("classifier")
    assert "Depth Levels" in result


def test_depth_levels_excerpt_truncated(loader):
    result = loader.load_for_agent("classifier")
    # depth-levels is 3000+ chars but excerpt caps at EXCERPT_MAX_CHARS
    assert len(result) < 10_000


def test_security_agent_gets_full_rules(loader):
    result = loader.load_for_agent("security")
    assert "Security Baseline" in result
    # Full file (5000+ chars of 's') should be present
    assert "s" * 100 in result


def test_missing_file_logs_warning_and_continues(loader, capsys):
    result = loader.load_for_agent("unknown_agent_type")
    # Should not raise, should return at least universal rules
    assert isinstance(result, str)


def test_sections_separated_correctly(loader):
    result = loader.load_for_agent("reproduction")
    assert "---" in result
