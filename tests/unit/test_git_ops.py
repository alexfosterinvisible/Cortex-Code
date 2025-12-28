"""Unit tests for adw/integrations/git_ops.py - <R6> Git Operations Tests

Tests git operations with mocked subprocess:
- Branch operations (get, create, push)
- Commit operations
- PR operations (check, create, approve, merge)
- Git finalization workflow
"""

import pytest
import json
import logging
from unittest.mock import patch, MagicMock, call
from typing import List


# ----- Helper to create subprocess mock results -----

def make_result(returncode: int = 0, stdout: str = "", stderr: str = "") -> MagicMock:
    """Create a mock subprocess.run result."""
    result = MagicMock()
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = stderr
    return result


class TestGetCurrentBranch:
    """Tests for get_current_branch function."""
    
    def test_get_current_branch_returns_name(self):
        """<R6.1> Returns current branch name."""
        from adw.integrations.git_ops import get_current_branch
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = make_result(stdout="feature-branch\n")
            
            result = get_current_branch()
            
            assert result == "feature-branch"
            mock_run.assert_called_once()
            assert "rev-parse" in mock_run.call_args[0][0]
    
    def test_get_current_branch_with_cwd(self):
        """<R6.1b> Passes cwd to subprocess."""
        from adw.integrations.git_ops import get_current_branch
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = make_result(stdout="main\n")
            
            result = get_current_branch(cwd="/some/path")
            
            assert mock_run.call_args.kwargs["cwd"] == "/some/path"
    
    def test_get_current_branch_strips_whitespace(self):
        """<R6.1c> Strips whitespace from output."""
        from adw.integrations.git_ops import get_current_branch
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = make_result(stdout="  main  \n\n")
            
            result = get_current_branch()
            
            assert result == "main"


class TestPushBranch:
    """Tests for push_branch function."""
    
    def test_push_branch_success(self):
        """<R6.2> Returns (True, None) on success."""
        from adw.integrations.git_ops import push_branch
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = make_result(returncode=0)
            
            success, error = push_branch("feature-branch")
            
            assert success is True
            assert error is None
            assert "push" in mock_run.call_args[0][0]
            assert "feature-branch" in mock_run.call_args[0][0]
    
    def test_push_branch_failure(self):
        """<R6.2b> Returns (False, error) on failure."""
        from adw.integrations.git_ops import push_branch
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = make_result(returncode=1, stderr="rejected: non-fast-forward")
            
            success, error = push_branch("feature-branch")
            
            assert success is False
            assert "rejected" in error
    
    def test_push_branch_with_cwd(self):
        """<R6.2c> Passes cwd to subprocess."""
        from adw.integrations.git_ops import push_branch
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = make_result(returncode=0)
            
            push_branch("feature-branch", cwd="/worktree/path")
            
            assert mock_run.call_args.kwargs["cwd"] == "/worktree/path"


class TestCreateBranch:
    """Tests for create_branch function."""
    
    def test_create_branch_new(self):
        """<R6.3> Creates new branch successfully."""
        from adw.integrations.git_ops import create_branch
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = make_result(returncode=0)
            
            success, error = create_branch("new-feature")
            
            assert success is True
            assert error is None
            assert "checkout" in mock_run.call_args[0][0]
            assert "-b" in mock_run.call_args[0][0]
            assert "new-feature" in mock_run.call_args[0][0]
    
    def test_create_branch_exists_checkout(self):
        """<R6.3b> Checks out existing branch if create fails."""
        from adw.integrations.git_ops import create_branch
        
        with patch("subprocess.run") as mock_run:
            # First call fails with "already exists"
            # Second call succeeds (checkout)
            mock_run.side_effect = [
                make_result(returncode=1, stderr="fatal: A branch named 'existing' already exists"),
                make_result(returncode=0),
            ]
            
            success, error = create_branch("existing")
            
            assert success is True
            assert error is None
            assert mock_run.call_count == 2
    
    def test_create_branch_exists_checkout_fails(self):
        """<R6.3c> Returns error if checkout of existing branch fails."""
        from adw.integrations.git_ops import create_branch
        
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                make_result(returncode=1, stderr="fatal: A branch named 'existing' already exists"),
                make_result(returncode=1, stderr="error: pathspec 'existing' did not match"),
            ]
            
            success, error = create_branch("existing")
            
            assert success is False
            assert "pathspec" in error
    
    def test_create_branch_other_error(self):
        """<R6.3d> Returns error for non-exists failures."""
        from adw.integrations.git_ops import create_branch
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = make_result(returncode=1, stderr="fatal: not a git repository")
            
            success, error = create_branch("new-feature")
            
            assert success is False
            assert "not a git repository" in error


class TestCommitChanges:
    """Tests for commit_changes function."""
    
    def test_commit_changes_no_changes(self):
        """<R6.4> Returns success with no changes to commit."""
        from adw.integrations.git_ops import commit_changes
        
        with patch("subprocess.run") as mock_run:
            # git status --porcelain returns empty
            mock_run.return_value = make_result(stdout="")
            
            success, error = commit_changes("Test commit")
            
            assert success is True
            assert error is None
            # Only status check, no add/commit
            assert mock_run.call_count == 1
    
    def test_commit_changes_with_changes(self):
        """<R6.4b> Stages and commits when there are changes."""
        from adw.integrations.git_ops import commit_changes
        
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                make_result(stdout=" M file.txt\n"),  # status shows changes
                make_result(returncode=0),  # git add
                make_result(returncode=0),  # git commit
            ]
            
            success, error = commit_changes("Test commit")
            
            assert success is True
            assert error is None
            assert mock_run.call_count == 3
            
            # Verify git add -A was called
            add_call = mock_run.call_args_list[1]
            assert "add" in add_call[0][0]
            assert "-A" in add_call[0][0]
            
            # Verify git commit -m was called
            commit_call = mock_run.call_args_list[2]
            assert "commit" in commit_call[0][0]
            assert "Test commit" in commit_call[0][0]
    
    def test_commit_changes_add_fails(self):
        """<R6.4c> Returns error if git add fails."""
        from adw.integrations.git_ops import commit_changes
        
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                make_result(stdout=" M file.txt\n"),
                make_result(returncode=1, stderr="error: unable to index file"),
            ]
            
            success, error = commit_changes("Test commit")
            
            assert success is False
            assert "unable to index" in error
    
    def test_commit_changes_commit_fails(self):
        """<R6.4d> Returns error if git commit fails."""
        from adw.integrations.git_ops import commit_changes
        
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                make_result(stdout=" M file.txt\n"),
                make_result(returncode=0),  # add succeeds
                make_result(returncode=1, stderr="error: empty commit message"),
            ]
            
            success, error = commit_changes("")
            
            assert success is False
            assert "empty commit" in error


class TestCheckPrExists:
    """Tests for check_pr_exists function."""
    
    def test_check_pr_exists_no_repo(self):
        """<R6.5> Returns None if repo URL can't be determined."""
        from adw.integrations.git_ops import check_pr_exists
        
        with patch("adw.integrations.git_ops.get_repo_url") as mock_get_url:
            mock_get_url.side_effect = ValueError("No remote")
            
            result = check_pr_exists("feature-branch")
            
            assert result is None


class TestGetPrNumberForBranch:
    """Tests for get_pr_number_for_branch function."""
    
    def test_get_pr_number_for_branch_exists(self):
        """<R6.6> Returns PR number when PR exists."""
        from adw.integrations.git_ops import get_pr_number_for_branch
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = make_result(
                returncode=0,
                stdout='{"number": 42}'
            )
            
            result = get_pr_number_for_branch("feature-branch")
            
            assert result == "42"
    
    def test_get_pr_number_for_branch_not_exists(self):
        """<R6.6b> Returns None when no PR exists."""
        from adw.integrations.git_ops import get_pr_number_for_branch
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = make_result(
                returncode=1,
                stderr="no pull requests found"
            )
            
            result = get_pr_number_for_branch("feature-branch")
            
            assert result is None
    
    def test_get_pr_number_for_branch_invalid_json(self):
        """<R6.6c> Returns None for invalid JSON response."""
        from adw.integrations.git_ops import get_pr_number_for_branch
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = make_result(
                returncode=0,
                stdout="not json"
            )
            
            result = get_pr_number_for_branch("feature-branch")
            
            assert result is None


class TestUpdatePrBody:
    """Tests for update_pr_body function."""
    
    def test_update_pr_body_success(self):
        """<R6.7> Updates PR body successfully."""
        from adw.integrations.git_ops import update_pr_body
        
        logger = MagicMock()
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = make_result(returncode=0)
            
            success, error = update_pr_body("42", "New body content", logger)
            
            assert success is True
            assert error is None
            logger.info.assert_called()
    
    def test_update_pr_body_failure(self):
        """<R6.7b> Returns error on failure."""
        from adw.integrations.git_ops import update_pr_body
        
        logger = MagicMock()
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = make_result(returncode=1, stderr="PR not found")
            
            success, error = update_pr_body("999", "New body", logger)
            
            assert success is False
            assert "PR not found" in error
            logger.error.assert_called()
    
    def test_update_pr_body_extracts_number_from_url(self):
        """<R6.7c> Extracts PR number from URL."""
        from adw.integrations.git_ops import update_pr_body
        
        logger = MagicMock()
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = make_result(returncode=0)
            
            update_pr_body("https://github.com/org/repo/pull/123", "Body", logger)
            
            # Verify the command uses "123" not the full URL
            cmd = mock_run.call_args[0][0]
            assert "123" in cmd


class TestGetPrNumber:
    """Tests for get_pr_number function."""
    
    def test_get_pr_number_exists(self):
        """<R6.8> Returns PR number when exists."""
        from adw.integrations.git_ops import get_pr_number
        
        with patch("adw.integrations.git_ops.get_repo_url") as mock_url:
            mock_url.return_value = "https://github.com/test/repo.git"
            
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = make_result(
                    returncode=0,
                    stdout='[{"number": 99}]'
                )
                
                result = get_pr_number("feature-branch")
                
                assert result == "99"
    
    def test_get_pr_number_not_exists(self):
        """<R6.8b> Returns None when no PR."""
        from adw.integrations.git_ops import get_pr_number
        
        with patch("adw.integrations.git_ops.get_repo_url") as mock_url:
            mock_url.return_value = "https://github.com/test/repo.git"
            
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = make_result(
                    returncode=0,
                    stdout='[]'
                )
                
                result = get_pr_number("feature-branch")
                
                assert result is None
    
    def test_get_pr_number_repo_error(self):
        """<R6.8c> Returns None if can't get repo info."""
        from adw.integrations.git_ops import get_pr_number
        
        with patch("adw.integrations.git_ops.get_repo_url") as mock_url:
            mock_url.side_effect = Exception("No remote")
            
            result = get_pr_number("feature-branch")
            
            assert result is None


class TestApprovePr:
    """Tests for approve_pr function."""
    
    def test_approve_pr_success(self):
        """<R6.9> Approves PR successfully."""
        from adw.integrations.git_ops import approve_pr
        
        logger = MagicMock()
        
        with patch("adw.integrations.git_ops.get_repo_url") as mock_url:
            mock_url.return_value = "https://github.com/test/repo.git"
            
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = make_result(returncode=0)
                
                success, error = approve_pr("42", logger)
                
                assert success is True
                assert error is None
                logger.info.assert_called_with("Approved PR #42")
    
    def test_approve_pr_failure(self):
        """<R6.9b> Returns error on approval failure."""
        from adw.integrations.git_ops import approve_pr
        
        logger = MagicMock()
        
        with patch("adw.integrations.git_ops.get_repo_url") as mock_url:
            mock_url.return_value = "https://github.com/test/repo.git"
            
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = make_result(returncode=1, stderr="Not authorized")
                
                success, error = approve_pr("42", logger)
                
                assert success is False
                assert "Not authorized" in error
    
    def test_approve_pr_repo_error(self):
        """<R6.9c> Returns error if can't get repo info."""
        from adw.integrations.git_ops import approve_pr
        
        logger = MagicMock()
        
        with patch("adw.integrations.git_ops.get_repo_url") as mock_url:
            mock_url.side_effect = Exception("No remote configured")
            
            success, error = approve_pr("42", logger)
            
            assert success is False
            assert "Failed to get repo info" in error


class TestMergePr:
    """Tests for merge_pr function."""
    
    def test_merge_pr_success(self):
        """<R6.10> Merges PR successfully."""
        from adw.integrations.git_ops import merge_pr
        
        logger = MagicMock()
        
        with patch("adw.integrations.git_ops.get_repo_url") as mock_url:
            mock_url.return_value = "https://github.com/test/repo.git"
            
            with patch("subprocess.run") as mock_run:
                # First call: check mergeable
                # Second call: merge
                mock_run.side_effect = [
                    make_result(returncode=0, stdout='{"mergeable": "MERGEABLE", "mergeStateStatus": "CLEAN"}'),
                    make_result(returncode=0),
                ]
                
                success, error = merge_pr("42", logger)
                
                assert success is True
                assert error is None
                logger.info.assert_called()
    
    def test_merge_pr_not_mergeable(self):
        """<R6.10b> Returns error for unmergeable PR."""
        from adw.integrations.git_ops import merge_pr
        
        logger = MagicMock()
        
        with patch("adw.integrations.git_ops.get_repo_url") as mock_url:
            mock_url.return_value = "https://github.com/test/repo.git"
            
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = make_result(
                    returncode=0,
                    stdout='{"mergeable": "CONFLICTING", "mergeStateStatus": "DIRTY"}'
                )
                
                success, error = merge_pr("42", logger)
                
                assert success is False
                assert "not mergeable" in error
    
    def test_merge_pr_squash_method(self):
        """<R6.10c> Uses squash merge method by default."""
        from adw.integrations.git_ops import merge_pr
        
        logger = MagicMock()
        
        with patch("adw.integrations.git_ops.get_repo_url") as mock_url:
            mock_url.return_value = "https://github.com/test/repo.git"
            
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = [
                    make_result(returncode=0, stdout='{"mergeable": "MERGEABLE"}'),
                    make_result(returncode=0),
                ]
                
                merge_pr("42", logger)
                
                # Check the merge command includes --squash
                merge_call = mock_run.call_args_list[1]
                assert "--squash" in merge_call[0][0]
    
    def test_merge_pr_rebase_method(self):
        """<R6.10d> Supports rebase merge method."""
        from adw.integrations.git_ops import merge_pr
        
        logger = MagicMock()
        
        with patch("adw.integrations.git_ops.get_repo_url") as mock_url:
            mock_url.return_value = "https://github.com/test/repo.git"
            
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = [
                    make_result(returncode=0, stdout='{"mergeable": "MERGEABLE"}'),
                    make_result(returncode=0),
                ]
                
                merge_pr("42", logger, merge_method="rebase")
                
                merge_call = mock_run.call_args_list[1]
                assert "--rebase" in merge_call[0][0]
    
    def test_merge_pr_check_fails(self):
        """<R6.10e> Returns error if PR status check fails."""
        from adw.integrations.git_ops import merge_pr
        
        logger = MagicMock()
        
        with patch("adw.integrations.git_ops.get_repo_url") as mock_url:
            mock_url.return_value = "https://github.com/test/repo.git"
            
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = make_result(returncode=1, stderr="PR not found")
                
                success, error = merge_pr("999", logger)
                
                assert success is False
                assert "Failed to check PR status" in error
    
    def test_merge_pr_merge_fails(self):
        """<R6.10f> Returns error if merge command fails."""
        from adw.integrations.git_ops import merge_pr
        
        logger = MagicMock()
        
        with patch("adw.integrations.git_ops.get_repo_url") as mock_url:
            mock_url.return_value = "https://github.com/test/repo.git"
            
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = [
                    make_result(returncode=0, stdout='{"mergeable": "MERGEABLE"}'),
                    make_result(returncode=1, stderr="Merge failed"),
                ]
                
                success, error = merge_pr("42", logger)
                
                assert success is False
                assert "Merge failed" in error


class TestFinalizeGitOperations:
    """Tests for finalize_git_operations function."""
    
    def test_finalize_with_branch_in_state(self):
        """<R6.11> Uses branch from state."""
        from adw.integrations.git_ops import finalize_git_operations
        
        # Create mock state
        state = MagicMock()
        state.get.side_effect = lambda key, default=None: {
            "branch_name": "feature-branch",
            "issue_number": "42",
            "adw_id": "test1234",
        }.get(key, default)
        
        logger = MagicMock()
        
        with patch("adw.integrations.git_ops.push_branch") as mock_push:
            mock_push.return_value = (True, None)
            
            with patch("adw.integrations.git_ops.check_pr_exists") as mock_pr:
                mock_pr.return_value = "https://github.com/org/repo/pull/1"
                
                with patch("adw.integrations.git_ops.make_issue_comment"):
                    finalize_git_operations(state, logger)
        
        mock_push.assert_called_once_with("feature-branch", cwd=None)
    
    def test_finalize_no_branch_uses_current(self):
        """<R6.11b> Falls back to current branch if not in state."""
        from adw.integrations.git_ops import finalize_git_operations
        
        state = MagicMock()
        state.get.return_value = None  # No branch in state
        
        logger = MagicMock()
        
        with patch("adw.integrations.git_ops.get_current_branch") as mock_current:
            mock_current.return_value = "current-feature"
            
            with patch("adw.integrations.git_ops.push_branch") as mock_push:
                mock_push.return_value = (True, None)
                
                with patch("adw.integrations.git_ops.check_pr_exists") as mock_pr:
                    # Return existing PR to avoid the complex create_pull_request path
                    mock_pr.return_value = "https://github.com/org/repo/pull/1"
                    
                    with patch("adw.integrations.git_ops.make_issue_comment"):
                        finalize_git_operations(state, logger)
        
        # Should warn about using current branch
        logger.warning.assert_called()
        # Should use the current branch for push
        mock_push.assert_called_once_with("current-feature", cwd=None)
    
    def test_finalize_main_branch_skips(self):
        """<R6.11c> Skips operations if on main branch with no state."""
        from adw.integrations.git_ops import finalize_git_operations
        
        state = MagicMock()
        state.get.return_value = None
        
        logger = MagicMock()
        
        with patch("adw.integrations.git_ops.get_current_branch") as mock_current:
            mock_current.return_value = "main"
            
            with patch("adw.integrations.git_ops.push_branch") as mock_push:
                finalize_git_operations(state, logger)
        
        # Should not push
        mock_push.assert_not_called()
        logger.error.assert_called()
    
    def test_finalize_push_fails(self):
        """<R6.11d> Logs error and returns if push fails."""
        from adw.integrations.git_ops import finalize_git_operations
        
        state = MagicMock()
        state.get.side_effect = lambda key, default=None: {
            "branch_name": "feature-branch",
        }.get(key, default)
        
        logger = MagicMock()
        
        with patch("adw.integrations.git_ops.push_branch") as mock_push:
            mock_push.return_value = (False, "Push rejected")
            
            with patch("adw.integrations.git_ops.check_pr_exists") as mock_pr:
                finalize_git_operations(state, logger)
        
        logger.error.assert_called()
        mock_pr.assert_not_called()  # Should not check PR after push failure
    
    def test_finalize_existing_pr_posts_link(self):
        """<R6.11e> Posts existing PR link to issue."""
        from adw.integrations.git_ops import finalize_git_operations
        
        state = MagicMock()
        state.get.side_effect = lambda key, default=None: {
            "branch_name": "feature-branch",
            "issue_number": "42",
            "adw_id": "test1234",
        }.get(key, default)
        
        logger = MagicMock()
        
        with patch("adw.integrations.git_ops.push_branch") as mock_push:
            mock_push.return_value = (True, None)
            
            with patch("adw.integrations.git_ops.check_pr_exists") as mock_pr:
                mock_pr.return_value = "https://github.com/org/repo/pull/99"
                
                with patch("adw.integrations.git_ops.make_issue_comment") as mock_comment:
                    finalize_git_operations(state, logger)
        
        mock_comment.assert_called_once()
        assert "pull/99" in mock_comment.call_args[0][1]
    
    def test_finalize_with_cwd(self):
        """<R6.11f> Passes cwd to operations."""
        from adw.integrations.git_ops import finalize_git_operations
        
        state = MagicMock()
        state.get.side_effect = lambda key, default=None: {
            "branch_name": "feature-branch",
            "issue_number": "42",
            "adw_id": "test1234",
        }.get(key, default)
        
        logger = MagicMock()
        
        with patch("adw.integrations.git_ops.push_branch") as mock_push:
            mock_push.return_value = (True, None)
            
            with patch("adw.integrations.git_ops.check_pr_exists") as mock_pr:
                mock_pr.return_value = "https://github.com/org/repo/pull/1"
                
                with patch("adw.integrations.git_ops.make_issue_comment"):
                    finalize_git_operations(state, logger, cwd="/worktree/path")
        
        mock_push.assert_called_once_with("feature-branch", cwd="/worktree/path")

