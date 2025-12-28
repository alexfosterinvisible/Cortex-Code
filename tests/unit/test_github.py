"""Unit tests for adw/integrations/github.py - <R7> GitHub Operations Tests

Tests GitHub operations with mocked subprocess calls:
- Environment setup (get_github_env)
- Repository URL extraction
- Issue fetching and manipulation
- Comment posting
- PR operations
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestGetGithubEnv:
    """Tests for get_github_env function."""
    
    def test_get_github_env_with_pat(self, monkeypatch):
        """<R7.1> Returns env dict with GH_TOKEN when GITHUB_PAT is set."""
        from adw.integrations.github import get_github_env
        
        monkeypatch.setenv("GITHUB_PAT", "ghp_test_token")
        monkeypatch.setenv("PATH", "/usr/bin:/bin")
        
        env = get_github_env()
        
        assert env is not None
        assert env["GH_TOKEN"] == "ghp_test_token"
        assert "PATH" in env
    
    def test_get_github_env_without_pat(self, monkeypatch):
        """<R7.2> Returns None when GITHUB_PAT is not set."""
        from adw.integrations.github import get_github_env
        
        monkeypatch.delenv("GITHUB_PAT", raising=False)
        
        env = get_github_env()
        
        assert env is None


class TestGetRepoUrl:
    """Tests for get_repo_url function."""
    
    def test_get_repo_url_success(self):
        """<R7.3> Returns remote URL on success."""
        from adw.integrations.github import get_repo_url
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="https://github.com/test-org/test-repo.git\n",
                stderr="",
            )
            
            url = get_repo_url()
            
            assert url == "https://github.com/test-org/test-repo.git"
            mock_run.assert_called_once()
            assert "git" in mock_run.call_args[0][0]
            assert "remote" in mock_run.call_args[0][0]
    
    def test_get_repo_url_no_remote(self):
        """<R7.4> Raises ValueError when no remote origin exists."""
        from adw.integrations.github import get_repo_url
        import subprocess
        
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=1, cmd=["git", "remote", "get-url", "origin"]
            )
            
            with pytest.raises(ValueError, match="No git remote 'origin' found"):
                get_repo_url()
    
    def test_get_repo_url_git_not_installed(self):
        """<R7.4b> Raises ValueError when git is not installed."""
        from adw.integrations.github import get_repo_url
        
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("git not found")
            
            with pytest.raises(ValueError, match="git command not found"):
                get_repo_url()


class TestExtractRepoPath:
    """Tests for extract_repo_path function."""
    
    def test_extract_repo_path_https(self):
        """<R7.5> Extracts owner/repo from HTTPS URL."""
        from adw.integrations.github import extract_repo_path
        
        url = "https://github.com/owner/repo"
        result = extract_repo_path(url)
        
        assert result == "owner/repo"
    
    def test_extract_repo_path_with_git_suffix(self):
        """<R7.5b> Handles .git suffix correctly."""
        from adw.integrations.github import extract_repo_path
        
        url = "https://github.com/owner/repo.git"
        result = extract_repo_path(url)
        
        assert result == "owner/repo"
    
    def test_extract_repo_path_nested(self):
        """<R7.5c> Handles nested org/repo paths."""
        from adw.integrations.github import extract_repo_path
        
        url = "https://github.com/my-org/my-repo.git"
        result = extract_repo_path(url)
        
        assert result == "my-org/my-repo"


class TestFetchIssue:
    """Tests for fetch_issue function."""
    
    def test_fetch_issue_success(self, sample_github_issue):
        """<R7.6> Returns GitHubIssue model on success."""
        from adw.integrations.github import fetch_issue
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps(sample_github_issue),
                stderr="",
            )
            
            issue = fetch_issue("42", "test-org/test-repo")
            
            assert issue.number == 42
            assert issue.title == "Add new feature"
            assert issue.state == "open"
    
    def test_fetch_issue_not_found(self, capsys):
        """<R7.7> Exits with error when issue not found."""
        from adw.integrations.github import fetch_issue
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="issue not found",
            )
            
            with pytest.raises(SystemExit) as exc_info:
                fetch_issue("9999", "test-org/test-repo")
            
            assert exc_info.value.code == 1
    
    def test_fetch_issue_gh_not_installed(self, capsys):
        """<R7.7b> Exits with helpful message when gh CLI not installed."""
        from adw.integrations.github import fetch_issue
        
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("gh not found")
            
            with pytest.raises(SystemExit) as exc_info:
                fetch_issue("42", "test-org/test-repo")
            
            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "GitHub CLI (gh) is not installed" in captured.err
    
    def test_fetch_issue_uses_github_env(self, sample_github_issue, monkeypatch):
        """<R7.8> Uses GitHub PAT environment when available."""
        from adw.integrations.github import fetch_issue
        
        monkeypatch.setenv("GITHUB_PAT", "ghp_test_token")
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps(sample_github_issue),
                stderr="",
            )
            
            fetch_issue("42", "test-org/test-repo")
            
            # Check that env was passed to subprocess
            call_kwargs = mock_run.call_args[1]
            if call_kwargs.get("env"):
                assert "GH_TOKEN" in call_kwargs["env"]


class TestMakeIssueComment:
    """Tests for make_issue_comment function."""
    
    def test_make_issue_comment_adds_bot_identifier(self):
        """<R7.9> Prepends ADW_BOT_IDENTIFIER to comment."""
        from adw.integrations.github import make_issue_comment, ADW_BOT_IDENTIFIER
        
        with patch("subprocess.run") as mock_run:
            # Mock get_repo_url
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="https://github.com/test-org/test-repo.git\n"),
                MagicMock(returncode=0, stdout="", stderr=""),
            ]
            
            make_issue_comment("42", "Test comment")
            
            # Get the comment body from the second call
            second_call = mock_run.call_args_list[1]
            cmd = second_call[0][0]
            body_idx = cmd.index("--body") + 1
            comment_body = cmd[body_idx]
            
            assert comment_body.startswith(ADW_BOT_IDENTIFIER)
            assert "Test comment" in comment_body
    
    def test_make_issue_comment_preserves_identifier(self):
        """<R7.9b> Preserves existing ADW_BOT_IDENTIFIER."""
        from adw.integrations.github import make_issue_comment, ADW_BOT_IDENTIFIER
        
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="https://github.com/test-org/test-repo.git\n"),
                MagicMock(returncode=0, stdout="", stderr=""),
            ]
            
            comment_with_id = f"{ADW_BOT_IDENTIFIER} Already has identifier"
            make_issue_comment("42", comment_with_id)
            
            second_call = mock_run.call_args_list[1]
            cmd = second_call[0][0]
            body_idx = cmd.index("--body") + 1
            comment_body = cmd[body_idx]
            
            # Should not have double identifier
            assert comment_body.count(ADW_BOT_IDENTIFIER) == 1
    
    def test_make_issue_comment_success(self, capsys):
        """<R7.10> Prints success message on success."""
        from adw.integrations.github import make_issue_comment
        
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="https://github.com/test-org/test-repo.git\n"),
                MagicMock(returncode=0, stdout="", stderr=""),
            ]
            
            make_issue_comment("42", "Test comment")
            
            captured = capsys.readouterr()
            assert "Successfully posted comment" in captured.out
    
    def test_make_issue_comment_failure(self):
        """<R7.10b> Raises RuntimeError on failure."""
        from adw.integrations.github import make_issue_comment
        
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="https://github.com/test-org/test-repo.git\n"),
                MagicMock(returncode=1, stdout="", stderr="Error: permission denied"),
            ]
            
            with pytest.raises(RuntimeError, match="Failed to post comment"):
                make_issue_comment("42", "Test comment")


class TestMarkIssueInProgress:
    """Tests for mark_issue_in_progress function."""
    
    def test_mark_issue_in_progress_adds_label(self, capsys):
        """<R7.11> Attempts to add in_progress label."""
        from adw.integrations.github import mark_issue_in_progress
        
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="https://github.com/test-org/test-repo.git\n"),
                MagicMock(returncode=0, stdout="", stderr=""),  # Add label
                MagicMock(returncode=0, stdout="", stderr=""),  # Add assignee
            ]
            
            mark_issue_in_progress("42")
            
            # Check that edit command was called with --add-label
            calls = mock_run.call_args_list
            label_call = calls[1][0][0]
            assert "--add-label" in label_call
            assert "in_progress" in label_call
    
    def test_mark_issue_in_progress_label_failure(self, capsys):
        """<R7.11b> Continues even if label doesn't exist."""
        from adw.integrations.github import mark_issue_in_progress
        
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="https://github.com/test-org/test-repo.git\n"),
                MagicMock(returncode=1, stdout="", stderr="label not found"),  # Label fails
                MagicMock(returncode=0, stdout="", stderr=""),  # Assignee succeeds
            ]
            
            # Should not raise
            mark_issue_in_progress("42")
            
            captured = capsys.readouterr()
            assert "Could not add 'in_progress' label" in captured.out
    
    def test_mark_issue_in_progress_assigns_self(self, capsys):
        """<R7.11c> Assigns issue to self."""
        from adw.integrations.github import mark_issue_in_progress
        
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="https://github.com/test-org/test-repo.git\n"),
                MagicMock(returncode=0, stdout="", stderr=""),
                MagicMock(returncode=0, stdout="", stderr=""),
            ]
            
            mark_issue_in_progress("42")
            
            # Check that @me was used for assignment
            calls = mock_run.call_args_list
            assignee_call = calls[2][0][0]
            assert "--add-assignee" in assignee_call
            assert "@me" in assignee_call
            
            captured = capsys.readouterr()
            assert "Assigned issue" in captured.out


class TestFetchOpenIssues:
    """Tests for fetch_open_issues function."""
    
    def test_fetch_open_issues_returns_list(self, capsys):
        """<R7.12> Returns list of GitHubIssueListItem."""
        from adw.integrations.github import fetch_open_issues
        
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
            
            issues = fetch_open_issues("test-org/test-repo")
            
            assert len(issues) == 2
            assert issues[0].number == 1
            assert issues[1].number == 2
            
            captured = capsys.readouterr()
            assert "Fetched 2 open issues" in captured.out
    
    def test_fetch_open_issues_empty_list(self, capsys):
        """<R7.12b> Returns empty list when no issues."""
        from adw.integrations.github import fetch_open_issues
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="[]",
                stderr="",
            )
            
            issues = fetch_open_issues("test-org/test-repo")
            
            assert issues == []
    
    def test_fetch_open_issues_error(self, capsys):
        """<R7.12c> Returns empty list on error."""
        from adw.integrations.github import fetch_open_issues
        import subprocess
        
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=1, cmd=["gh"], stderr="error"
            )
            
            issues = fetch_open_issues("test-org/test-repo")
            
            assert issues == []
    
    def test_fetch_open_issues_invalid_json(self, capsys):
        """<R7.12d> Returns empty list on invalid JSON."""
        from adw.integrations.github import fetch_open_issues
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="not valid json",
                stderr="",
            )
            
            issues = fetch_open_issues("test-org/test-repo")
            
            assert issues == []


class TestFetchIssueComments:
    """Tests for fetch_issue_comments function."""
    
    def test_fetch_issue_comments_success(self):
        """<R7.13> Returns sorted list of comments."""
        from adw.integrations.github import fetch_issue_comments
        
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
            
            comments = fetch_issue_comments("test-org/test-repo", 42)
            
            assert len(comments) == 2
            # Should be sorted by createdAt
            assert comments[0]["createdAt"] < comments[1]["createdAt"]
    
    def test_fetch_issue_comments_empty(self):
        """<R7.13b> Returns empty list when no comments."""
        from adw.integrations.github import fetch_issue_comments
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({"comments": []}),
                stderr="",
            )
            
            comments = fetch_issue_comments("test-org/test-repo", 42)
            
            assert comments == []
    
    def test_fetch_issue_comments_error(self):
        """<R7.13c> Returns empty list on error."""
        from adw.integrations.github import fetch_issue_comments
        import subprocess
        
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=1, cmd=["gh"], stderr="error"
            )
            
            comments = fetch_issue_comments("test-org/test-repo", 42)
            
            assert comments == []


class TestFindKeywordFromComment:
    """Tests for find_keyword_from_comment function."""
    
    def test_find_keyword_from_comment_found(self):
        """<R7.14> Returns comment containing keyword."""
        from adw.integrations.github import find_keyword_from_comment
        from adw.core.data_types import GitHubIssue, GitHubComment, GitHubUser
        
        # Create issue with comments
        comments = [
            GitHubComment(
                id="1",
                author=GitHubUser(login="user1"),
                body="First comment",
                createdAt=datetime(2025, 1, 1),
            ),
            GitHubComment(
                id="2",
                author=GitHubUser(login="user2"),
                body="This contains the KEYWORD here",
                createdAt=datetime(2025, 1, 2),
            ),
        ]
        
        issue = GitHubIssue(
            number=42,
            title="Test",
            body="Test body",
            state="open",
            author=GitHubUser(login="author"),
            comments=comments,
            createdAt=datetime(2025, 1, 1),
            updatedAt=datetime(2025, 1, 1),
            url="https://github.com/test/test/issues/42",
        )
        
        result = find_keyword_from_comment("KEYWORD", issue)
        
        assert result is not None
        assert result.id == "2"
        assert "KEYWORD" in result.body
    
    def test_find_keyword_from_comment_not_found(self):
        """<R7.14b> Returns None when keyword not found."""
        from adw.integrations.github import find_keyword_from_comment
        from adw.core.data_types import GitHubIssue, GitHubComment, GitHubUser
        
        comments = [
            GitHubComment(
                id="1",
                author=GitHubUser(login="user1"),
                body="No keyword here",
                createdAt=datetime(2025, 1, 1),
            ),
        ]
        
        issue = GitHubIssue(
            number=42,
            title="Test",
            body="Test body",
            state="open",
            author=GitHubUser(login="author"),
            comments=comments,
            createdAt=datetime(2025, 1, 1),
            updatedAt=datetime(2025, 1, 1),
            url="https://github.com/test/test/issues/42",
        )
        
        result = find_keyword_from_comment("NOTFOUND", issue)
        
        assert result is None
    
    def test_find_keyword_skips_bot_comments(self):
        """<R7.15> Ignores comments from ADW bot."""
        from adw.integrations.github import find_keyword_from_comment, ADW_BOT_IDENTIFIER
        from adw.core.data_types import GitHubIssue, GitHubComment, GitHubUser
        
        comments = [
            GitHubComment(
                id="1",
                author=GitHubUser(login="user1"),
                body="Human comment with KEYWORD",
                createdAt=datetime(2025, 1, 1),
            ),
            GitHubComment(
                id="2",
                author=GitHubUser(login="bot"),
                body=f"{ADW_BOT_IDENTIFIER} Bot comment with KEYWORD",
                createdAt=datetime(2025, 1, 2),  # Newer
            ),
        ]
        
        issue = GitHubIssue(
            number=42,
            title="Test",
            body="Test body",
            state="open",
            author=GitHubUser(login="author"),
            comments=comments,
            createdAt=datetime(2025, 1, 1),
            updatedAt=datetime(2025, 1, 1),
            url="https://github.com/test/test/issues/42",
        )
        
        result = find_keyword_from_comment("KEYWORD", issue)
        
        # Should return human comment, not bot comment (even though bot is newer)
        assert result is not None
        assert result.id == "1"
        assert ADW_BOT_IDENTIFIER not in result.body
    
    def test_find_keyword_returns_latest(self):
        """<R7.15b> Returns latest matching comment."""
        from adw.integrations.github import find_keyword_from_comment
        from adw.core.data_types import GitHubIssue, GitHubComment, GitHubUser
        
        comments = [
            GitHubComment(
                id="1",
                author=GitHubUser(login="user1"),
                body="First KEYWORD",
                createdAt=datetime(2025, 1, 1),
            ),
            GitHubComment(
                id="2",
                author=GitHubUser(login="user2"),
                body="Second KEYWORD",
                createdAt=datetime(2025, 1, 2),  # Newer
            ),
        ]
        
        issue = GitHubIssue(
            number=42,
            title="Test",
            body="Test body",
            state="open",
            author=GitHubUser(login="author"),
            comments=comments,
            createdAt=datetime(2025, 1, 1),
            updatedAt=datetime(2025, 1, 1),
            url="https://github.com/test/test/issues/42",
        )
        
        result = find_keyword_from_comment("KEYWORD", issue)
        
        # Should return the newer comment
        assert result is not None
        assert result.id == "2"


class TestApprovePr:
    """Tests for approve_pr function."""
    
    def test_approve_pr_success(self, capsys):
        """<R7.16> Returns (True, None) on success."""
        from adw.integrations.github import approve_pr
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="",
                stderr="",
            )
            
            success, error = approve_pr("123", "test-org/test-repo")
            
            assert success is True
            assert error is None
            
            captured = capsys.readouterr()
            assert "Successfully approved PR" in captured.out
    
    def test_approve_pr_failure(self):
        """<R7.16b> Returns (False, error) on failure."""
        from adw.integrations.github import approve_pr
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="permission denied",
            )
            
            success, error = approve_pr("123", "test-org/test-repo")
            
            assert success is False
            assert "permission denied" in error
    
    def test_approve_pr_exception(self):
        """<R7.16c> Returns (False, error) on exception."""
        from adw.integrations.github import approve_pr
        
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Network error")
            
            success, error = approve_pr("123", "test-org/test-repo")
            
            assert success is False
            assert "Network error" in error
    
    def test_approve_pr_includes_bot_identifier(self):
        """<R7.16d> Approval comment includes ADW_BOT_IDENTIFIER."""
        from adw.integrations.github import approve_pr, ADW_BOT_IDENTIFIER
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            approve_pr("123", "test-org/test-repo")
            
            cmd = mock_run.call_args[0][0]
            body_idx = cmd.index("--body") + 1
            body = cmd[body_idx]
            
            assert ADW_BOT_IDENTIFIER in body


class TestCloseIssue:
    """Tests for close_issue function."""
    
    def test_close_issue_success(self, capsys):
        """<R7.17> Returns (True, None) on success."""
        from adw.integrations.github import close_issue
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="",
                stderr="",
            )
            
            success, error = close_issue("42", "test-org/test-repo")
            
            assert success is True
            assert error is None
            
            captured = capsys.readouterr()
            assert "Successfully closed issue" in captured.out
    
    def test_close_issue_failure(self):
        """<R7.17b> Returns (False, error) on failure."""
        from adw.integrations.github import close_issue
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="issue already closed",
            )
            
            success, error = close_issue("42", "test-org/test-repo")
            
            assert success is False
            assert "already closed" in error
    
    def test_close_issue_auto_detects_repo(self):
        """<R7.17c> Auto-detects repo_path when not provided."""
        from adw.integrations.github import close_issue
        
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="https://github.com/auto/repo.git\n"),
                MagicMock(returncode=0, stdout="", stderr=""),
            ]
            
            success, error = close_issue("42")  # No repo_path
            
            assert success is True
            
            # Check the close command used detected repo
            close_call = mock_run.call_args_list[1]
            cmd = close_call[0][0]
            assert "-R" in cmd
            repo_idx = cmd.index("-R") + 1
            assert cmd[repo_idx] == "auto/repo"
    
    def test_close_issue_includes_bot_identifier(self):
        """<R7.17d> Close comment includes ADW_BOT_IDENTIFIER."""
        from adw.integrations.github import close_issue, ADW_BOT_IDENTIFIER
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            close_issue("42", "test-org/test-repo")
            
            cmd = mock_run.call_args[0][0]
            comment_idx = cmd.index("--comment") + 1
            comment = cmd[comment_idx]
            
            assert ADW_BOT_IDENTIFIER in comment


class TestBotIdentifier:
    """Tests for ADW_BOT_IDENTIFIER constant."""
    
    def test_bot_identifier_format(self):
        """<R7.18> ADW_BOT_IDENTIFIER has expected format."""
        from adw.integrations.github import ADW_BOT_IDENTIFIER
        
        assert "[ADW" in ADW_BOT_IDENTIFIER
        assert "]" in ADW_BOT_IDENTIFIER

