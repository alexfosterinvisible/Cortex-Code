"""Unit tests for cxc/integrations/git_ops.py

<R6> Git Operations Tests

Tests cover:
- get_current_branch: Getting current git branch
- push_branch: Pushing branch to remote
- create_branch: Creating and checking out branches
- commit_changes: Staging and committing changes
- get_pr_number: Getting PR number for branch
- get_pr_number_for_branch: Getting PR number via gh pr view
- update_pr_body: Updating PR body
- approve_pr: Approving a PR
- merge_pr: Merging a PR
- check_pr_exists: Checking if PR exists
- finalize_git_operations: Standard git finalization
"""

import json
import pytest
from unittest.mock import MagicMock, patch


# ----- Test get_current_branch -----

class TestGetCurrentBranch:
    """Tests for get_current_branch function."""

    def test_get_current_branch_success(self):
        """<R6.1> Returns current branch name."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="feature-branch\n",
                stderr="",
            )
            
            from cxc.integrations.git_ops import get_current_branch
            result = get_current_branch()
            
            assert result == "feature-branch"

    def test_get_current_branch_with_cwd(self):
        """<R6.1> Passes cwd to subprocess."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="main\n",
                stderr="",
            )
            
            from cxc.integrations.git_ops import get_current_branch
            result = get_current_branch(cwd="/test/path")
            
            mock_run.assert_called_once()
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["cwd"] == "/test/path"

    def test_get_current_branch_strips_whitespace(self):
        """<R6.1> Strips whitespace from branch name."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="  main  \n",
                stderr="",
            )
            
            from cxc.integrations.git_ops import get_current_branch
            result = get_current_branch()
            
            assert result == "main"


# ----- Test push_branch -----

class TestPushBranch:
    """Tests for push_branch function."""

    def test_push_branch_success(self):
        """<R6.2> Returns (True, None) on success."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            from cxc.integrations.git_ops import push_branch
            success, error = push_branch("feature-branch")
            
            assert success is True
            assert error is None

    def test_push_branch_failure(self):
        """<R6.2> Returns (False, error) on failure."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="error: failed to push",
            )
            
            from cxc.integrations.git_ops import push_branch
            success, error = push_branch("feature-branch")
            
            assert success is False
            assert "failed to push" in error

    def test_push_branch_with_cwd(self):
        """<R6.2> Passes cwd to subprocess."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            from cxc.integrations.git_ops import push_branch
            push_branch("feature-branch", cwd="/test/path")
            
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["cwd"] == "/test/path"


# ----- Test create_branch -----

class TestCreateBranch:
    """Tests for create_branch function."""

    def test_create_branch_new(self):
        """<R6.3> Creates new branch successfully."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            from cxc.integrations.git_ops import create_branch
            success, error = create_branch("new-branch")
            
            assert success is True
            assert error is None

    def test_create_branch_exists_checkout(self):
        """<R6.3> Checks out existing branch."""
        with patch("subprocess.run") as mock_run:
            # First call fails (branch exists), second succeeds (checkout)
            mock_run.side_effect = [
                MagicMock(returncode=1, stdout="", stderr="already exists"),
                MagicMock(returncode=0, stdout="", stderr=""),
            ]
            
            from cxc.integrations.git_ops import create_branch
            success, error = create_branch("existing-branch")
            
            assert success is True
            assert error is None

    def test_create_branch_failure(self):
        """<R6.3> Returns error on failure."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="fatal: not a git repository",
            )
            
            from cxc.integrations.git_ops import create_branch
            success, error = create_branch("new-branch")
            
            assert success is False
            assert "not a git repository" in error


# ----- Test commit_changes -----

class TestCommitChanges:
    """Tests for commit_changes function."""

    def test_commit_changes_no_changes(self):
        """<R6.4> Returns success with no changes to commit."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            from cxc.integrations.git_ops import commit_changes
            success, error = commit_changes("Test commit")
            
            assert success is True
            assert error is None

    def test_commit_changes_with_changes(self):
        """<R6.4> Stages and commits changes."""
        with patch("subprocess.run") as mock_run:
            # status shows changes, add succeeds, commit succeeds
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="M file.py\n", stderr=""),
                MagicMock(returncode=0, stdout="", stderr=""),  # git add
                MagicMock(returncode=0, stdout="", stderr=""),  # git commit
            ]
            
            from cxc.integrations.git_ops import commit_changes
            success, error = commit_changes("Test commit")
            
            assert success is True
            assert error is None
            assert mock_run.call_count == 3

    def test_commit_changes_add_failure(self):
        """<R6.4> Returns error when git add fails."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="M file.py\n", stderr=""),
                MagicMock(returncode=1, stdout="", stderr="error: pathspec"),
            ]
            
            from cxc.integrations.git_ops import commit_changes
            success, error = commit_changes("Test commit")
            
            assert success is False
            assert "pathspec" in error

    def test_commit_changes_commit_failure(self):
        """<R6.4> Returns error when git commit fails."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="M file.py\n", stderr=""),
                MagicMock(returncode=0, stdout="", stderr=""),  # git add
                MagicMock(returncode=1, stdout="", stderr="error: commit failed"),
            ]
            
            from cxc.integrations.git_ops import commit_changes
            success, error = commit_changes("Test commit")
            
            assert success is False
            assert "commit failed" in error


# ----- Test get_pr_number -----

class TestGetPrNumber:
    """Tests for get_pr_number function."""

    def test_get_pr_number_exists(self):
        """<R6.5> Returns PR number when exists."""
        with patch("subprocess.run") as mock_run, \
             patch("cxc.integrations.git_ops.get_repo_url") as mock_url, \
             patch("cxc.integrations.git_ops.extract_repo_path") as mock_path:
            mock_url.return_value = "https://github.com/test-org/test-repo.git"
            mock_path.return_value = "test-org/test-repo"
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='[{"number": 42}]',
                stderr="",
            )
            
            from cxc.integrations.git_ops import get_pr_number
            result = get_pr_number("feature-branch")
            
            assert result == "42"

    def test_get_pr_number_not_found(self):
        """<R6.5> Returns None when no PR exists."""
        with patch("subprocess.run") as mock_run, \
             patch("cxc.integrations.git_ops.get_repo_url") as mock_url, \
             patch("cxc.integrations.git_ops.extract_repo_path") as mock_path:
            mock_url.return_value = "https://github.com/test-org/test-repo.git"
            mock_path.return_value = "test-org/test-repo"
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='[]',
                stderr="",
            )
            
            from cxc.integrations.git_ops import get_pr_number
            result = get_pr_number("feature-branch")
            
            assert result is None

    def test_get_pr_number_repo_error(self):
        """<R6.5> Returns None when repo info fails."""
        with patch("cxc.integrations.git_ops.get_repo_url") as mock_url:
            mock_url.side_effect = ValueError("No remote")
            
            from cxc.integrations.git_ops import get_pr_number
            result = get_pr_number("feature-branch")
            
            assert result is None


# ----- Test get_pr_number_for_branch -----

class TestGetPrNumberForBranch:
    """Tests for get_pr_number_for_branch function."""

    def test_get_pr_number_for_branch_exists(self):
        """<R6.6> Returns PR number when exists."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='{"number": 123}',
                stderr="",
            )
            
            from cxc.integrations.git_ops import get_pr_number_for_branch
            result = get_pr_number_for_branch("feature-branch")
            
            assert result == "123"

    def test_get_pr_number_for_branch_not_found(self):
        """<R6.6> Returns None when no PR exists."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="no pull requests",
            )
            
            from cxc.integrations.git_ops import get_pr_number_for_branch
            result = get_pr_number_for_branch("feature-branch")
            
            assert result is None


# ----- Test update_pr_body -----

class TestUpdatePrBody:
    """Tests for update_pr_body function."""

    def test_update_pr_body_success(self):
        """<R6.7> Updates PR body successfully."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            from cxc.integrations.git_ops import update_pr_body
            
            logger = MagicMock()
            success, error = update_pr_body("42", "New body content", logger)
            
            assert success is True
            assert error is None
            logger.info.assert_called()

    def test_update_pr_body_from_url(self):
        """<R6.7> Extracts PR number from URL."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            from cxc.integrations.git_ops import update_pr_body
            
            logger = MagicMock()
            update_pr_body("https://github.com/org/repo/pull/42", "New body", logger)
            
            # Verify the command used "42" not the full URL
            call_args = mock_run.call_args[0][0]
            assert "42" in call_args

    def test_update_pr_body_failure(self):
        """<R6.7> Returns error on failure."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="could not update PR",
            )
            
            from cxc.integrations.git_ops import update_pr_body
            
            logger = MagicMock()
            success, error = update_pr_body("42", "New body", logger)
            
            assert success is False
            assert "could not update" in error


# ----- Test approve_pr -----

class TestApprovePr:
    """Tests for approve_pr function."""

    def test_approve_pr_success(self):
        """<R6.8> Approves PR successfully."""
        with patch("subprocess.run") as mock_run, \
             patch("cxc.integrations.git_ops.get_repo_url") as mock_url, \
             patch("cxc.integrations.git_ops.extract_repo_path") as mock_path:
            mock_url.return_value = "https://github.com/test-org/test-repo.git"
            mock_path.return_value = "test-org/test-repo"
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            from cxc.integrations.git_ops import approve_pr
            
            logger = MagicMock()
            success, error = approve_pr("42", logger)
            
            assert success is True
            assert error is None
            logger.info.assert_called()

    def test_approve_pr_failure(self):
        """<R6.8> Returns error on failure."""
        with patch("subprocess.run") as mock_run, \
             patch("cxc.integrations.git_ops.get_repo_url") as mock_url, \
             patch("cxc.integrations.git_ops.extract_repo_path") as mock_path:
            mock_url.return_value = "https://github.com/test-org/test-repo.git"
            mock_path.return_value = "test-org/test-repo"
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="cannot approve own PR",
            )
            
            from cxc.integrations.git_ops import approve_pr
            
            logger = MagicMock()
            success, error = approve_pr("42", logger)
            
            assert success is False
            assert "cannot approve" in error

    def test_approve_pr_repo_error(self):
        """<R6.8> Returns error when repo info fails."""
        with patch("cxc.integrations.git_ops.get_repo_url") as mock_url:
            mock_url.side_effect = ValueError("No remote")
            
            from cxc.integrations.git_ops import approve_pr
            
            logger = MagicMock()
            success, error = approve_pr("42", logger)
            
            assert success is False
            assert "Failed to get repo info" in error


# ----- Test merge_pr -----

class TestMergePr:
    """Tests for merge_pr function."""

    def test_merge_pr_success(self):
        """<R6.9> Merges PR successfully."""
        with patch("subprocess.run") as mock_run, \
             patch("cxc.integrations.git_ops.get_repo_url") as mock_url, \
             patch("cxc.integrations.git_ops.extract_repo_path") as mock_path:
            mock_url.return_value = "https://github.com/test-org/test-repo.git"
            mock_path.return_value = "test-org/test-repo"
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout='{"mergeable": "MERGEABLE"}', stderr=""),
                MagicMock(returncode=0, stdout="", stderr=""),
            ]
            
            from cxc.integrations.git_ops import merge_pr
            
            logger = MagicMock()
            success, error = merge_pr("42", logger)
            
            assert success is True
            assert error is None

    def test_merge_pr_not_mergeable(self):
        """<R6.9> Returns error for unmergeable PR."""
        with patch("subprocess.run") as mock_run, \
             patch("cxc.integrations.git_ops.get_repo_url") as mock_url, \
             patch("cxc.integrations.git_ops.extract_repo_path") as mock_path:
            mock_url.return_value = "https://github.com/test-org/test-repo.git"
            mock_path.return_value = "test-org/test-repo"
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='{"mergeable": "CONFLICTING", "mergeStateStatus": "BLOCKED"}',
                stderr="",
            )
            
            from cxc.integrations.git_ops import merge_pr
            
            logger = MagicMock()
            success, error = merge_pr("42", logger)
            
            assert success is False
            assert "not mergeable" in error

    def test_merge_pr_squash_method(self):
        """<R6.9> Uses squash merge by default."""
        with patch("subprocess.run") as mock_run, \
             patch("cxc.integrations.git_ops.get_repo_url") as mock_url, \
             patch("cxc.integrations.git_ops.extract_repo_path") as mock_path:
            mock_url.return_value = "https://github.com/test-org/test-repo.git"
            mock_path.return_value = "test-org/test-repo"
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout='{"mergeable": "MERGEABLE"}', stderr=""),
                MagicMock(returncode=0, stdout="", stderr=""),
            ]
            
            from cxc.integrations.git_ops import merge_pr
            
            logger = MagicMock()
            merge_pr("42", logger)
            
            # Check the merge command includes --squash
            merge_call = mock_run.call_args_list[1]
            assert "--squash" in merge_call[0][0]

    def test_merge_pr_rebase_method(self):
        """<R6.9> Supports rebase merge method."""
        with patch("subprocess.run") as mock_run, \
             patch("cxc.integrations.git_ops.get_repo_url") as mock_url, \
             patch("cxc.integrations.git_ops.extract_repo_path") as mock_path:
            mock_url.return_value = "https://github.com/test-org/test-repo.git"
            mock_path.return_value = "test-org/test-repo"
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout='{"mergeable": "MERGEABLE"}', stderr=""),
                MagicMock(returncode=0, stdout="", stderr=""),
            ]
            
            from cxc.integrations.git_ops import merge_pr
            
            logger = MagicMock()
            merge_pr("42", logger, merge_method="rebase")
            
            merge_call = mock_run.call_args_list[1]
            assert "--rebase" in merge_call[0][0]


# ----- Test check_pr_exists -----

class TestCheckPrExists:
    """Tests for check_pr_exists function."""

    def test_check_pr_exists_returns_none_on_error(self):
        """<R6.10> Returns None when repo info fails."""
        with patch("cxc.integrations.git_ops.get_repo_url") as mock_url:
            mock_url.side_effect = ValueError("No remote")
            
            from cxc.integrations.git_ops import check_pr_exists
            result = check_pr_exists("feature-branch")
            
            assert result is None


# ----- Test finalize_git_operations -----

class TestFinalizeGitOperations:
    """Tests for finalize_git_operations function."""

    def test_finalize_git_operations_pushes_and_creates_pr(self):
        """<R6.11> Pushes branch and creates PR."""
        from cxc.integrations import git_ops
        from cxc.integrations import github as github_module
        from cxc.integrations import workflow_ops as workflow_ops_module
        
        # Need to patch make_issue_comment on git_ops since it's imported there
        with patch.object(git_ops, "push_branch") as mock_push, \
             patch.object(git_ops, "check_pr_exists") as mock_check_pr, \
             patch.object(git_ops, "get_repo_url") as mock_url, \
             patch.object(git_ops, "extract_repo_path") as mock_path, \
             patch.object(git_ops, "make_issue_comment") as mock_comment, \
             patch.object(github_module, "fetch_issue") as mock_fetch, \
             patch.object(workflow_ops_module, "create_pull_request") as mock_create_pr:
            mock_push.return_value = (True, None)
            mock_check_pr.return_value = None  # No existing PR
            mock_url.return_value = "https://github.com/test-org/test-repo.git"
            mock_path.return_value = "test-org/test-repo"
            mock_fetch.return_value = MagicMock()
            mock_create_pr.return_value = ("https://github.com/org/repo/pull/42", None)
            
            state = MagicMock()
            state.get.side_effect = lambda k: {
                "branch_name": "feature-branch",
                "issue_number": "42",
                "cxc_id": "test1234",
            }.get(k)
            
            logger = MagicMock()
            git_ops.finalize_git_operations(state, logger)
            
            mock_push.assert_called_once()
            logger.info.assert_called()

    def test_finalize_git_operations_no_branch(self):
        """<R6.11> Uses current branch if none in state."""
        with patch("cxc.integrations.git_ops.get_current_branch") as mock_branch, \
             patch("cxc.integrations.git_ops.push_branch") as mock_push, \
             patch("cxc.integrations.git_ops.check_pr_exists") as mock_check_pr:
            mock_branch.return_value = "feature-from-git"
            mock_push.return_value = (True, None)
            mock_check_pr.return_value = "https://github.com/org/repo/pull/42"
            
            from cxc.integrations.git_ops import finalize_git_operations
            
            state = MagicMock()
            state.get.return_value = None  # No branch_name in state
            
            logger = MagicMock()
            finalize_git_operations(state, logger)
            
            mock_branch.assert_called_once()
            logger.warning.assert_called()  # Should warn about missing branch

    def test_finalize_git_operations_push_failure(self):
        """<R6.11> Logs error on push failure."""
        with patch("cxc.integrations.git_ops.push_branch") as mock_push:
            mock_push.return_value = (False, "push failed")
            
            from cxc.integrations.git_ops import finalize_git_operations
            
            state = MagicMock()
            state.get.side_effect = lambda k: {
                "branch_name": "feature-branch",
            }.get(k)
            
            logger = MagicMock()
            finalize_git_operations(state, logger)
            
            logger.error.assert_called()
