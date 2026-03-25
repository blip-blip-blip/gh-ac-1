"""Tests for GitHubClient."""

import pytest
from unittest.mock import MagicMock, patch

from agents.core.github_client import GitHubClient, _parse_linked_issue


@pytest.fixture
def client():
    return GitHubClient(token="test-token", repo="owner/repo")


def mock_response(status_code: int, json_data=None, text: str = ""):
    r = MagicMock()
    r.status_code = status_code
    r.json.return_value = json_data or {}
    r.text = text
    r.content = b"content" if json_data else b""
    r.headers = {}
    return r


# ------------------------------------------------------------------
# _parse_linked_issue
# ------------------------------------------------------------------

@pytest.mark.parametrize("body,expected", [
    ("Fixes #42", 42),
    ("Closes #100", 100),
    ("Resolves #7", 7),
    ("fixes #99 and some text", 99),
    ("No issue reference here", None),
    ("", None),
])
def test_parse_linked_issue(body, expected):
    assert _parse_linked_issue(body) == expected


# ------------------------------------------------------------------
# post_comment
# ------------------------------------------------------------------

def test_post_comment_success(client):
    with patch.object(client._session, "request",
                      return_value=mock_response(201, {"id": 1})):
        assert client.post_comment(1, "hello") is True


def test_post_comment_failure_returns_false(client):
    with patch.object(client._session, "request",
                      return_value=mock_response(422, text="error")):
        assert client.post_comment(1, "hello") is False


# ------------------------------------------------------------------
# apply_labels
# ------------------------------------------------------------------

def test_apply_labels_success(client):
    with patch.object(client._session, "request",
                      return_value=mock_response(200, [{"name": "bug"}])):
        assert client.apply_labels(1, ["bug"]) is True


# ------------------------------------------------------------------
# create_branch
# ------------------------------------------------------------------

def test_create_branch_success(client):
    ref_response = mock_response(200, {"object": {"sha": "abc123"}})
    create_response = mock_response(201, {"ref": "refs/heads/fix/test-pr-1"})
    with patch.object(client._session, "request",
                      side_effect=[ref_response, create_response]):
        assert client.create_branch("fix/test-pr-1", "main") is True


def test_create_branch_fails_if_ref_not_found(client):
    with patch.object(client._session, "request",
                      return_value=mock_response(404, text="not found")):
        assert client.create_branch("fix/test-pr-1", "nonexistent") is False


# ------------------------------------------------------------------
# Retry behaviour
# ------------------------------------------------------------------

def test_retries_on_server_error(client):
    fail = mock_response(500, text="server error")
    success = mock_response(201, {"id": 1})
    with patch.object(client._session, "request", side_effect=[fail, fail, success]):
        with patch("agents.core.github_client.time.sleep"):
            assert client.post_comment(1, "hello") is True


def test_returns_none_after_max_retries(client):
    fail = mock_response(500, text="server error")
    with patch.object(client._session, "request", side_effect=[fail, fail, fail]):
        with patch("agents.core.github_client.time.sleep"):
            assert client.post_comment(1, "hello") is False
