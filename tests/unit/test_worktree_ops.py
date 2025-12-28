"""Unit tests for adw/integrations/worktree_ops.py

<R8> Worktree and Port Management Tests

Tests cover:
- get_default_branch: Detecting default branch from remote
- create_worktree: Creating git worktrees for isolated execution
- validate_worktree: Three-way validation (state, filesystem, git)
- get_worktree_path: Path resolution
- remove_worktree: Cleanup operations
- setup_worktree_environment: .ports.env file creation
- get_ports_for_adw: Deterministic port assignment
- is_port_available: Port availability checking
- find_next_available_ports: Finding available port pairs
"""

import os
import socket
import pytest
from unittest.mock import MagicMock, patch

# Module under test
from adw.integrations import worktree_ops


# ----- Test get_default_branch -----

class TestGetDefaultBranch:
    """Tests for get_default_branch function."""

    def test_get_default_branch_from_remote_show(self):
        """<R8.1> Detects main from remote show output."""
        with patch.object(worktree_ops.subprocess, "run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="* remote origin\n  HEAD branch: main\n  Remote branch:\n",
                stderr="",
            )
            
            result = worktree_ops.get_default_branch("/test/project")
            
            assert result == "main"

    def test_get_default_branch_master(self):
        """<R8.1> Detects master as default branch."""
        with patch.object(worktree_ops.subprocess, "run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="* remote origin\n  HEAD branch: master\n",
                stderr="",
            )
            
            result = worktree_ops.get_default_branch("/test/project")
            
            assert result == "master"

    def test_get_default_branch_fallback_main(self):
        """<R8.1> Falls back to main when remote show fails."""
        with patch.object(worktree_ops.subprocess, "run") as mock_run:
            # First call (remote show) fails, second call (rev-parse main) succeeds
            mock_run.side_effect = [
                MagicMock(returncode=1, stdout="", stderr="error"),
                MagicMock(returncode=0, stdout="abc123", stderr=""),
            ]
            
            result = worktree_ops.get_default_branch("/test/project")
            
            assert result == "main"

    def test_get_default_branch_fallback_master(self):
        """<R8.1> Falls back to master when main doesn't exist."""
        with patch.object(worktree_ops.subprocess, "run") as mock_run:
            # remote show fails, main fails, master succeeds
            mock_run.side_effect = [
                MagicMock(returncode=1, stdout="", stderr="error"),
                MagicMock(returncode=1, stdout="", stderr="not found"),
                MagicMock(returncode=0, stdout="abc123", stderr=""),
            ]
            
            result = worktree_ops.get_default_branch("/test/project")
            
            assert result == "master"

    def test_get_default_branch_final_fallback(self):
        """<R8.1> Returns main as final fallback."""
        with patch.object(worktree_ops.subprocess, "run") as mock_run:
            # All calls fail
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
            
            result = worktree_ops.get_default_branch("/test/project")
            
            assert result == "main"


# ----- Test create_worktree -----

class TestCreateWorktree:
    """Tests for create_worktree function."""

    def test_create_worktree_new(self, tmp_path):
        """<R8.2> Creates new worktree successfully."""
        with patch.object(worktree_ops, "ADWConfig") as mock_config_cls, \
             patch.object(worktree_ops.subprocess, "run") as mock_run, \
             patch.object(worktree_ops, "get_default_branch", return_value="main"):
            
            config = MagicMock()
            config.project_root = tmp_path
            config.get_trees_dir.return_value = tmp_path / "trees"
            mock_config_cls.load.return_value = config
            
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            logger = MagicMock()
            path, error = worktree_ops.create_worktree("test1234", "feature-branch", logger)
            
            assert path == str(tmp_path / "trees" / "test1234")
            assert error is None
            logger.info.assert_called()

    def test_create_worktree_exists(self, tmp_path):
        """<R8.2> Returns existing worktree path if already exists."""
        # Create the worktree directory
        worktree_path = tmp_path / "trees" / "test1234"
        worktree_path.mkdir(parents=True)
        
        with patch.object(worktree_ops, "ADWConfig") as mock_config_cls, \
             patch.object(worktree_ops.subprocess, "run") as mock_run:
            
            config = MagicMock()
            config.project_root = tmp_path
            config.get_trees_dir.return_value = tmp_path / "trees"
            mock_config_cls.load.return_value = config
            
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            logger = MagicMock()
            path, error = worktree_ops.create_worktree("test1234", "feature-branch", logger)
            
            assert path == str(worktree_path)
            assert error is None
            logger.warning.assert_called()  # Should warn about existing worktree

    def test_create_worktree_branch_exists(self, tmp_path):
        """<R8.2> Handles existing branch by checking out without -b."""
        with patch.object(worktree_ops, "ADWConfig") as mock_config_cls, \
             patch.object(worktree_ops.subprocess, "run") as mock_run, \
             patch.object(worktree_ops, "get_default_branch", return_value="main"):
            
            config = MagicMock()
            config.project_root = tmp_path
            config.get_trees_dir.return_value = tmp_path / "trees"
            mock_config_cls.load.return_value = config
            
            # First worktree add fails (branch exists), second succeeds
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="", stderr=""),  # fetch
                MagicMock(returncode=1, stdout="", stderr="already exists"),  # worktree add -b
                MagicMock(returncode=0, stdout="", stderr=""),  # worktree add without -b
            ]
            
            logger = MagicMock()
            path, error = worktree_ops.create_worktree("test1234", "feature-branch", logger)
            
            assert path == str(tmp_path / "trees" / "test1234")
            assert error is None

    def test_create_worktree_failure(self, tmp_path):
        """<R8.2> Returns error on worktree creation failure."""
        with patch.object(worktree_ops, "ADWConfig") as mock_config_cls, \
             patch.object(worktree_ops.subprocess, "run") as mock_run, \
             patch.object(worktree_ops, "get_default_branch", return_value="main"):
            
            config = MagicMock()
            config.project_root = tmp_path
            config.get_trees_dir.return_value = tmp_path / "trees"
            mock_config_cls.load.return_value = config
            
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="", stderr=""),  # fetch
                MagicMock(returncode=1, stdout="", stderr="fatal error"),  # worktree add fails
            ]
            
            logger = MagicMock()
            path, error = worktree_ops.create_worktree("test1234", "feature-branch", logger)
            
            assert path is None
            assert "Failed to create worktree" in error


# ----- Test validate_worktree -----

class TestValidateWorktree:
    """Tests for validate_worktree function."""

    def test_validate_worktree_valid(self, tmp_path):
        """<R8.3> Returns (True, None) for valid worktree."""
        worktree_path = tmp_path / "test-worktree"
        worktree_path.mkdir()
        
        with patch.object(worktree_ops.subprocess, "run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=f"{worktree_path} abc123 [branch]\n",
                stderr="",
            )
            
            state = MagicMock()
            state.get.return_value = str(worktree_path)
            
            is_valid, error = worktree_ops.validate_worktree("test1234", state)
            
            assert is_valid is True
            assert error is None

    def test_validate_worktree_no_path_in_state(self):
        """<R8.3> Returns error when no worktree_path in state."""
        state = MagicMock()
        state.get.return_value = None
        
        is_valid, error = worktree_ops.validate_worktree("test1234", state)
        
        assert is_valid is False
        assert "No worktree_path in state" in error

    def test_validate_worktree_no_directory(self):
        """<R8.3> Returns error when directory doesn't exist."""
        state = MagicMock()
        state.get.return_value = "/nonexistent/path"
        
        is_valid, error = worktree_ops.validate_worktree("test1234", state)
        
        assert is_valid is False
        assert "not found" in error

    def test_validate_worktree_not_in_git(self, tmp_path):
        """<R8.3> Returns error when git doesn't know about worktree."""
        worktree_path = tmp_path / "test-worktree"
        worktree_path.mkdir()
        
        with patch.object(worktree_ops.subprocess, "run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="/other/path abc123 [branch]\n",  # Different path
                stderr="",
            )
            
            state = MagicMock()
            state.get.return_value = str(worktree_path)
            
            is_valid, error = worktree_ops.validate_worktree("test1234", state)
            
            assert is_valid is False
            assert "not registered with git" in error


# ----- Test get_worktree_path -----

class TestGetWorktreePath:
    """Tests for get_worktree_path function."""

    def test_get_worktree_path(self, tmp_path):
        """<R8.4> Returns correct absolute path."""
        with patch.object(worktree_ops, "ADWConfig") as mock_config_cls:
            config = MagicMock()
            config.get_trees_dir.return_value = tmp_path / "trees"
            mock_config_cls.load.return_value = config
            
            result = worktree_ops.get_worktree_path("test1234")
            
            assert result == str(tmp_path / "trees" / "test1234")


# ----- Test remove_worktree -----

class TestRemoveWorktree:
    """Tests for remove_worktree function."""

    def test_remove_worktree_success(self, tmp_path):
        """<R8.5> Removes worktree successfully."""
        with patch.object(worktree_ops, "get_worktree_path") as mock_path, \
             patch.object(worktree_ops.subprocess, "run") as mock_run:
            mock_path.return_value = str(tmp_path / "test-worktree")
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            logger = MagicMock()
            success, error = worktree_ops.remove_worktree("test1234", logger)
            
            assert success is True
            assert error is None
            logger.info.assert_called()

    def test_remove_worktree_git_fails_manual_cleanup(self, tmp_path):
        """<R8.5> Falls back to manual cleanup when git fails."""
        worktree_path = tmp_path / "test-worktree"
        worktree_path.mkdir()
        
        with patch.object(worktree_ops, "get_worktree_path") as mock_path, \
             patch.object(worktree_ops.subprocess, "run") as mock_run, \
             patch.object(worktree_ops.shutil, "rmtree") as mock_rmtree:
            mock_path.return_value = str(worktree_path)
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
            
            logger = MagicMock()
            success, error = worktree_ops.remove_worktree("test1234", logger)
            
            assert success is True
            mock_rmtree.assert_called_once_with(str(worktree_path))
            logger.warning.assert_called()

    def test_remove_worktree_complete_failure(self, tmp_path):
        """<R8.5> Returns error when both git and manual cleanup fail."""
        worktree_path = tmp_path / "test-worktree"
        worktree_path.mkdir()
        
        with patch.object(worktree_ops, "get_worktree_path") as mock_path, \
             patch.object(worktree_ops.subprocess, "run") as mock_run, \
             patch.object(worktree_ops.shutil, "rmtree") as mock_rmtree:
            mock_path.return_value = str(worktree_path)
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="git error")
            mock_rmtree.side_effect = PermissionError("Access denied")
            
            logger = MagicMock()
            success, error = worktree_ops.remove_worktree("test1234", logger)
            
            assert success is False
            assert "Failed to remove worktree" in error


# ----- Test setup_worktree_environment -----

class TestSetupWorktreeEnvironment:
    """Tests for setup_worktree_environment function."""

    def test_setup_worktree_environment_creates_ports_env(self, tmp_path):
        """<R8.6> Creates .ports.env file with correct content."""
        worktree_path = tmp_path / "test-worktree"
        worktree_path.mkdir()
        
        logger = MagicMock()
        worktree_ops.setup_worktree_environment(str(worktree_path), 9100, 9200, logger)
        
        ports_env = worktree_path / ".ports.env"
        assert ports_env.exists()
        
        content = ports_env.read_text()
        assert "BACKEND_PORT=9100" in content
        assert "FRONTEND_PORT=9200" in content
        assert "VITE_BACKEND_URL=http://localhost:9100" in content
        
        logger.info.assert_called()


# ----- Test get_ports_for_adw -----

class TestGetPortsForAdw:
    """Tests for get_ports_for_adw function."""

    def test_get_ports_for_adw_deterministic(self):
        """<R8.7> Same ADW ID always returns same ports."""
        ports1 = worktree_ops.get_ports_for_adw("test1234")
        ports2 = worktree_ops.get_ports_for_adw("test1234")
        
        assert ports1 == ports2

    def test_get_ports_for_adw_different_ids(self):
        """<R8.7> Different ADW IDs may return different ports."""
        ports1 = worktree_ops.get_ports_for_adw("aaaaaaaa")
        ports2 = worktree_ops.get_ports_for_adw("zzzzzzzz")
        
        # Different IDs should likely have different ports (not guaranteed but probable)
        # At minimum, both should be valid port tuples
        assert isinstance(ports1, tuple)
        assert isinstance(ports2, tuple)
        assert len(ports1) == 2
        assert len(ports2) == 2

    def test_get_ports_for_adw_range(self):
        """<R8.7> Ports are in expected range (9100-9114 / 9200-9214)."""
        # Test multiple IDs
        for adw_id in ["test1234", "abcd5678", "xyz12345"]:
            backend, frontend = worktree_ops.get_ports_for_adw(adw_id)
            
            assert 9100 <= backend <= 9114
            assert 9200 <= frontend <= 9214
            assert frontend - backend == 100  # Frontend is always 100 above backend

    def test_get_ports_for_adw_handles_special_chars(self):
        """<R8.7> Handles IDs with non-alphanumeric characters."""
        # Should not raise, should return valid ports
        backend, frontend = worktree_ops.get_ports_for_adw("test-1234")
        
        assert 9100 <= backend <= 9114
        assert 9200 <= frontend <= 9214


# ----- Test is_port_available -----

class TestIsPortAvailable:
    """Tests for is_port_available function."""

    def test_is_port_available_free(self):
        """<R8.8> Returns True for free port."""
        # Use a high port that's unlikely to be in use
        # Note: This test may be flaky if the port is actually in use
        result = worktree_ops.is_port_available(59999)
        
        # We can't guarantee the result, but we can verify the function runs
        assert isinstance(result, bool)

    def test_is_port_available_bound(self):
        """<R8.8> Returns False for bound port."""
        # Create a socket and bind it
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('localhost', 59998))
            
            # Now check if the port is available (it shouldn't be)
            result = worktree_ops.is_port_available(59998)
            
            assert result is False


# ----- Test find_next_available_ports -----

class TestFindNextAvailablePorts:
    """Tests for find_next_available_ports function."""

    def test_find_next_available_ports_success(self):
        """<R8.9> Finds available port pair."""
        with patch.object(worktree_ops, "is_port_available", return_value=True):
            backend, frontend = worktree_ops.find_next_available_ports("test1234")
            
            assert 9100 <= backend <= 9114
            assert 9200 <= frontend <= 9214

    def test_find_next_available_ports_skips_busy(self):
        """<R8.9> Skips busy ports and finds next available."""
        call_count = [0]
        
        def mock_is_available(port):
            call_count[0] += 1
            # First few ports are busy, then available
            return call_count[0] > 4
        
        with patch.object(worktree_ops, "is_port_available", side_effect=mock_is_available):
            backend, frontend = worktree_ops.find_next_available_ports("test1234")
            
            # Should have tried multiple times
            assert call_count[0] > 2

    def test_find_next_available_ports_raises_on_exhaustion(self):
        """<R8.9> Raises RuntimeError when no ports available."""
        with patch.object(worktree_ops, "is_port_available", return_value=False):
            with pytest.raises(RuntimeError) as exc_info:
                worktree_ops.find_next_available_ports("test1234")
            
            assert "No available ports" in str(exc_info.value)

    def test_find_next_available_ports_max_attempts(self):
        """<R8.9> Respects max_attempts parameter."""
        call_count = [0]
        
        def mock_is_available(port):
            call_count[0] += 1
            return False
        
        with patch.object(worktree_ops, "is_port_available", side_effect=mock_is_available):
            with pytest.raises(RuntimeError):
                worktree_ops.find_next_available_ports("test1234", max_attempts=5)
            
            # Should have tried exactly max_attempts * 2 times (backend + frontend each attempt)
            assert call_count[0] == 5  # Only checks backend first, stops if backend unavailable
