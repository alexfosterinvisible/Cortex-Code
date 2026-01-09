"""Unit tests for cxc/integrations/github.py

<R7> GitHub Operations Tests

Tests cover:
- get_github_env: Environment setup with GitHub token
- get_repo_url: Getting repository URL from git remote
- extract_repo_path: Extracting owner/repo from URL
- fetch_issue: Fetching GitHub issue data
- make_issue_comment: Posting comments to issues
- mark_issue_in_progress: Adding labels and assignees
- fetch_open_issues: Fetching list of open issues
- fetch_issue_comments: Fetching comments for an issue
- find_keyword_from_comment: Finding keywords in comments
- approve_pr: Approving a pull request
- close_issue: Closing an issue
"""

import json
import os
import pytest
from unittest.mock import MagicMock, patch


# ----- Test get_github_env -----

class TestGetGithubEnv:
    """Tests for get_github_env function."""

    def test_get_github_env_with_pat(self, monkeypatch):
        """<R7.1> Returns env dict with GH_TOKEN when PAT is set."""
        monkeypatch.setenv("GITHUB_PAT", "ghp_test_token")
        monkeypatch.setenv("PATH", "/usr/bin")
        
        from cxc.integrations.github import get_github_env
        result = get_github_env()
        
        assert result is not None
        assert result["GH_TOKEN"] == "ghp_test_token"
        assert "PATH" in result

    def test_get_github_env_without_pat(self, monkeypatch):
        """<R7.1> Returns None when no PAT is set."""
        monkeypatch.delenv("GITHUB_PAT", raising=False)
        
        from cxc.integrations.github import get_github_env
        result = get_github_env()
        
        assert result is None


# ----- Test get_repo_url -----

class TestGetRepoUrl:
    """Tests for get_repo_url function."""

    def test_get_repo_url_success(self):
        """<R7.2> Returns remote URL."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="https://github.com/test-org/test-repo.git\n",
                stderr="",
            )
            
            from cxc.integrations.github import get_repo_url
            result = get_repo_url()
            
            assert result == "https://github.com/test-org/test-repo.git"

    def test_get_repo_url_no_remote(self):
        """<R7.2> Raises ValueError when no remote."""
        import subprocess
        
        with patch("cxc.integrations.github.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git", stderr="error")
            
            from cxc.integrations.github import get_repo_url
            
            # The function uses check=True, so it raises CalledProcessError which is caught
            with pytest.raises(ValueError):
                get_repo_url()

    def test_get_repo_url_git_not_found(self):
        """<R7.2> Raises ValueError when git not installed."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("git not found")
            
            from cxc.integrations.github import get_repo_url
            
            with pytest.raises(ValueError) as exc_info:
                get_repo_url()
            
            assert "git command not found" in str(exc_info.value)


# ----- Test extract_repo_path -----

class TestExtractRepoPath:
    """Tests for extract_repo_path function."""

    def test_extract_repo_path_https(self):
        """<R7.3> Extracts owner/repo from HTTPS URL."""
        from cxc.integrations.github import extract_repo_path
        
        result = extract_repo_path("https://github.com/test-org/test-repo")
        
        assert result == "test-org/test-repo"

    def test_extract_repo_path_with_git_suffix(self):
        """<R7.3> Handles .git suffix."""
        from cxc.integrations.github import extract_repo_path
        
        result = extract_repo_path("https://github.com/test-org/test-repo.git")
        
        assert result == "test-org/test-repo"


# ----- Test fetch_issue -----

class TestFetchIssue:
    """Tests for fetch_issue function."""

    def test_fetch_issue_success(self, monkeypatch):
        """<R7.4> Returns GitHubIssue model."""
        monkeypatch.delenv("GITHUB_PAT", raising=False)
        
        issue_data = {
            "number": 42,
            "title": "Test Issue",
            "body": "Test body",
            "state": "open",
            "author": {"login": "testuser"},
            "assignees": [],
            "labels": [],
            "milestone": None,
            "comments": [],
            "createdAt": "2025-01-01T00:00:00Z",
            "updatedAt": "2025-01-01T00:00:00Z",
            "closedAt": None,
            "url": "https://github.com/test-org/test-repo/issues/42",
        }
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps(issue_data),
                stderr="",
            )
            
            from cxc.integrations.github import fetch_issue
            result = fetch_issue("42", "test-org/test-repo")
            
            assert result.number == 42
            assert result.title == "Test Issue"
            assert result.state == "open"

    def test_fetch_issue_not_found(self, monkeypatch):
        """<R7.4> Exits on issue not found."""
        monkeypatch.delenv("GITHUB_PAT", raising=False)
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="Could not resolve to an Issue",
            )
            
            from cxc.integrations.github import fetch_issue
            
            with pytest.raises(SystemExit):
                fetch_issue("999", "test-org/test-repo")

    def test_fetch_issue_gh_not_installed(self, monkeypatch):
        """<R7.4> Exits when gh CLI not installed."""
        monkeypatch.delenv("GITHUB_PAT", raising=False)
        
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("gh not found")
            
            from cxc.integrations.github import fetch_issue
            
            with pytest.raises(SystemExit):
                fetch_issue("42", "test-org/test-repo")


# ----- Test make_issue_comment -----

class TestMakeIssueComment:
    """Tests for make_issue_comment function."""

    def test_make_issue_comment_adds_bot_identifier(self, monkeypatch):
        """<R7.5> Prepends CXC_BOT_IDENTIFIER."""
        monkeypatch.delenv("GITHUB_PAT", raising=False)
        
        with patch("subprocess.run") as mock_run, \
             patch("cxc.integrations.github.get_repo_url") as mock_url, \
             patch("cxc.integrations.github.extract_repo_path") as mock_path:
            mock_url.return_value = "https://github.com/test-org/test-repo.git"
            mock_path.return_value = "test-org/test-repo"
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            from cxc.integrations.github import make_issue_comment
            make_issue_comment("42", "Test comment")
            
            # Check the comment includes the bot identifier
            call_args = mock_run.call_args[0][0]
            body_idx = call_args.index("--body") + 1
            assert "[CXC-AGENTS]" in call_args[body_idx]

    def test_make_issue_comment_preserves_existing_identifier(self, monkeypatch):
        """<R7.5> Doesn't double-add identifier."""
        monkeypatch.delenv("GITHUB_PAT", raising=False)
        
        with patch("subprocess.run") as mock_run, \
             patch("cxc.integrations.github.get_repo_url") as mock_url, \
             patch("cxc.integrations.github.extract_repo_path") as mock_path:
            mock_url.return_value = "https://github.com/test-org/test-repo.git"
            mock_path.return_value = "test-org/test-repo"
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            from cxc.integrations.github import make_issue_comment, CXC_BOT_IDENTIFIER
            make_issue_comment("42", f"{CXC_BOT_IDENTIFIER} Already has identifier")
            
            call_args = mock_run.call_args[0][0]
            body_idx = call_args.index("--body") + 1
            # Should only have one occurrence
            assert call_args[body_idx].count("[CXC-AGENTS]") == 1

    def test_make_issue_comment_failure_blocking(self, monkeypatch):
        """<R7.5> Raises on comment failure when blocking=True."""
        monkeypatch.delenv("GITHUB_PAT", raising=False)
        
        with patch("subprocess.run") as mock_run, \
             patch("cxc.integrations.github.get_repo_url") as mock_url, \
             patch("cxc.integrations.github.extract_repo_path") as mock_path:
            mock_url.return_value = "https://github.com/test-org/test-repo.git"
            mock_path.return_value = "test-org/test-repo"
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="Failed to post comment",
            )
            
            from cxc.integrations.github import make_issue_comment
            
            # Blocking=True should raise error on failure
            with pytest.raises(RuntimeError):
                make_issue_comment("42", "Test comment", blocking=True)
    
    def test_make_issue_comment_failure_async_no_raise(self, monkeypatch):
        """<R7.5b> Fire-and-forget mode doesn't raise on failure."""
        monkeypatch.delenv("GITHUB_PAT", raising=False)
        
        with patch("subprocess.run") as mock_run, \
             patch("cxc.integrations.github.get_repo_url") as mock_url, \
             patch("cxc.integrations.github.extract_repo_path") as mock_path, \
             patch("threading.Thread") as mock_thread:
            mock_url.return_value = "https://github.com/test-org/test-repo.git"
            mock_path.return_value = "test-org/test-repo"
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="Failed to post comment",
            )
            mock_thread_instance = MagicMock()
            mock_thread.return_value = mock_thread_instance
            
            from cxc.integrations.github import make_issue_comment
            
            # Default (blocking=False) should not raise, uses thread
            make_issue_comment("42", "Test comment")
            mock_thread.assert_called_once()  # Thread was created
            mock_thread_instance.start.assert_called_once()


# ----- Test mark_issue_in_progress -----

class TestMarkIssueInProgress:
    """Tests for mark_issue_in_progress function."""

    def test_mark_issue_in_progress_adds_label(self, monkeypatch):
        """<R7.6> Adds in_progress label."""
        monkeypatch.delenv("GITHUB_PAT", raising=False)
        
        with patch("subprocess.run") as mock_run, \
             patch("cxc.integrations.github.get_repo_url") as mock_url, \
             patch("cxc.integrations.github.extract_repo_path") as mock_path:
            mock_url.return_value = "https://github.com/test-org/test-repo.git"
            mock_path.return_value = "test-org/test-repo"
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            from cxc.integrations.github import mark_issue_in_progress
            mark_issue_in_progress("42")
            
            # Should have called for label and assignee
            assert mock_run.call_count >= 2

    def test_mark_issue_in_progress_label_missing(self, monkeypatch):
        """<R7.6> Continues when label doesn't exist."""
        monkeypatch.delenv("GITHUB_PAT", raising=False)
        
        with patch("subprocess.run") as mock_run, \
             patch("cxc.integrations.github.get_repo_url") as mock_url, \
             patch("cxc.integrations.github.extract_repo_path") as mock_path:
            mock_url.return_value = "https://github.com/test-org/test-repo.git"
            mock_path.return_value = "test-org/test-repo"
            # First call (add label) fails, second (assign) succeeds
            mock_run.side_effect = [
                MagicMock(returncode=1, stdout="", stderr="label not found"),
                MagicMock(returncode=0, stdout="", stderr=""),
            ]
            
            from cxc.integrations.github import mark_issue_in_progress
            # Should not raise
            mark_issue_in_progress("42")


# ----- Test fetch_open_issues -----

class TestFetchOpenIssues:
    """Tests for fetch_open_issues function."""

    def test_fetch_open_issues_success(self, monkeypatch):
        """<R7.7> Returns list of issues."""
        monkeypatch.delenv("GITHUB_PAT", raising=False)
        
        issues_data = [
            {
                "number": 1,
                "title": "Issue 1",
                "body": "Body 1",
                "labels": [],
                "createdAt": "2025-01-01T00:00:00Z",
                "updatedAt": "2025-01-01T00:00:00Z",
            },
            {
                "number": 2,
                "title": "Issue 2",
                "body": "Body 2",
                "labels": [],
                "createdAt": "2025-01-02T00:00:00Z",
                "updatedAt": "2025-01-02T00:00:00Z",
            },
        ]
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps(issues_data),
                stderr="",
            )
            
            from cxc.integrations.github import fetch_open_issues
            result = fetch_open_issues("test-org/test-repo")
            
            assert len(result) == 2
            assert result[0].number == 1
            assert result[1].number == 2

    def test_fetch_open_issues_empty(self, monkeypatch):
        """<R7.7> Returns empty list when no issues."""
        monkeypatch.delenv("GITHUB_PAT", raising=False)
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="[]",
                stderr="",
            )
            
            from cxc.integrations.github import fetch_open_issues
            result = fetch_open_issues("test-org/test-repo")
            
            assert result == []

    def test_fetch_open_issues_failure(self, monkeypatch):
        """<R7.7> Returns empty list on failure."""
        import subprocess
        monkeypatch.delenv("GITHUB_PAT", raising=False)
        
        with patch("cxc.integrations.github.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "gh", stderr="error")
            
            from cxc.integrations.github import fetch_open_issues
            result = fetch_open_issues("test-org/test-repo")
            
            assert result == []


# ----- Test fetch_issue_comments -----

class TestFetchIssueComments:
    """Tests for fetch_issue_comments function."""

    def test_fetch_issue_comments_success(self, monkeypatch):
        """<R7.8> Returns sorted comments."""
        monkeypatch.delenv("GITHUB_PAT", raising=False)
        
        comments_data = {
            "comments": [
                {"body": "Comment 2", "createdAt": "2025-01-02T00:00:00Z"},
                {"body": "Comment 1", "createdAt": "2025-01-01T00:00:00Z"},
            ]
        }
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps(comments_data),
                stderr="",
            )
            
            from cxc.integrations.github import fetch_issue_comments
            result = fetch_issue_comments("test-org/test-repo", 42)
            
            assert len(result) == 2
            # Should be sorted by createdAt
            assert result[0]["createdAt"] < result[1]["createdAt"]

    def test_fetch_issue_comments_empty(self, monkeypatch):
        """<R7.8> Returns empty list when no comments."""
        monkeypatch.delenv("GITHUB_PAT", raising=False)
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='{"comments": []}',
                stderr="",
            )
            
            from cxc.integrations.github import fetch_issue_comments
            result = fetch_issue_comments("test-org/test-repo", 42)
            
            assert result == []


# ----- Test find_keyword_from_comment -----

class TestFindKeywordFromComment:
    """Tests for find_keyword_from_comment function."""

    def test_find_keyword_from_comment_found(self):
        """<R7.9> Finds keyword in comments."""
        from cxc.integrations.github import find_keyword_from_comment
        from cxc.core.data_types import GitHubIssue, GitHubComment
        from datetime import datetime
        
        issue = MagicMock(spec=GitHubIssue)
        issue.comments = [
            MagicMock(
                spec=GitHubComment,
                body="This is a test comment",
                created_at=datetime(2025, 1, 1),
            ),
            MagicMock(
                spec=GitHubComment,
                body="This contains KEYWORD here",
                created_at=datetime(2025, 1, 2),
            ),
        ]
        
        result = find_keyword_from_comment("KEYWORD", issue)
        
        assert result is not None
        assert "KEYWORD" in result.body

    def test_find_keyword_from_comment_not_found(self):
        """<R7.9> Returns None when keyword not found."""
        from cxc.integrations.github import find_keyword_from_comment
        
        issue = MagicMock()
        issue.comments = [
            MagicMock(body="No match here", created_at="2025-01-01"),
        ]
        
        result = find_keyword_from_comment("MISSING", issue)
        
        assert result is None

    def test_find_keyword_skips_bot_comments(self):
        """<R7.9> Ignores CXC bot comments."""
        from cxc.integrations.github import find_keyword_from_comment, CXC_BOT_IDENTIFIER
        from datetime import datetime
        
        issue = MagicMock()
        issue.comments = [
            MagicMock(
                body=f"{CXC_BOT_IDENTIFIER} KEYWORD in bot comment",
                created_at=datetime(2025, 1, 2),
            ),
            MagicMock(
                body="Human comment without keyword",
                created_at=datetime(2025, 1, 1),
            ),
        ]
        
        result = find_keyword_from_comment("KEYWORD", issue)
        
        # Should not find the bot comment
        assert result is None


# ----- Test approve_pr -----

class TestApprovePr:
    """Tests for approve_pr function."""

    def test_approve_pr_success(self, monkeypatch):
        """<R7.10> Approves PR successfully."""
        monkeypatch.delenv("GITHUB_PAT", raising=False)
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            from cxc.integrations.github import approve_pr
            success, error = approve_pr("42", "test-org/test-repo")
            
            assert success is True
            assert error is None

    def test_approve_pr_failure(self, monkeypatch):
        """<R7.10> Returns error on failure."""
        monkeypatch.delenv("GITHUB_PAT", raising=False)
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="cannot approve own PR",
            )
            
            from cxc.integrations.github import approve_pr
            success, error = approve_pr("42", "test-org/test-repo")
            
            assert success is False
            assert "cannot approve" in error


# ----- Test close_issue -----

class TestCloseIssue:
    """Tests for close_issue function."""

    def test_close_issue_success(self, monkeypatch):
        """<R7.11> Closes issue successfully."""
        monkeypatch.delenv("GITHUB_PAT", raising=False)
        
        with patch("subprocess.run") as mock_run, \
             patch("cxc.integrations.github.get_repo_url") as mock_url, \
             patch("cxc.integrations.github.extract_repo_path") as mock_path:
            mock_url.return_value = "https://github.com/test-org/test-repo.git"
            mock_path.return_value = "test-org/test-repo"
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            from cxc.integrations.github import close_issue
            success, error = close_issue("42")
            
            assert success is True
            assert error is None

    def test_close_issue_with_repo_path(self, monkeypatch):
        """<R7.11> Uses provided repo_path."""
        monkeypatch.delenv("GITHUB_PAT", raising=False)
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            from cxc.integrations.github import close_issue
            success, error = close_issue("42", "custom-org/custom-repo")
            
            assert success is True
            # Verify repo path was used
            call_args = mock_run.call_args[0][0]
            assert "custom-org/custom-repo" in call_args

    def test_close_issue_failure(self, monkeypatch):
        """<R7.11> Returns error on failure."""
        monkeypatch.delenv("GITHUB_PAT", raising=False)
        
        with patch("subprocess.run") as mock_run, \
             patch("cxc.integrations.github.get_repo_url") as mock_url, \
             patch("cxc.integrations.github.extract_repo_path") as mock_path:
            mock_url.return_value = "https://github.com/test-org/test-repo.git"
            mock_path.return_value = "test-org/test-repo"
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="issue not found",
            )
            
            from cxc.integrations.github import close_issue
            success, error = close_issue("999")
            
            assert success is False
            assert "issue not found" in error
