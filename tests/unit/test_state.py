"""Unit tests for adw/core/state.py - <R2> State Persistence Tests

Tests ADWState class:
- Initialization and validation
- State updates and retrieval
- File persistence (save/load)
- stdin/stdout piping
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
from io import StringIO


class TestADWStateInit:
    """Tests for ADWState initialization."""
    
    def test_init_requires_adw_id(self):
        """<R2.1> ValueError raised if adw_id is empty."""
        from adw.core.state import ADWState
        
        with pytest.raises(ValueError, match="adw_id is required"):
            ADWState("")
        
        with pytest.raises(ValueError, match="adw_id is required"):
            ADWState(None)
    
    def test_init_with_valid_adw_id(self, mock_adw_config):
        """<R2.1b> Valid adw_id creates state successfully."""
        from adw.core.state import ADWState
        
        state = ADWState("test1234")
        
        assert state.adw_id == "test1234"
        assert state.data["adw_id"] == "test1234"


class TestADWStateUpdate:
    """Tests for ADWState.update() method."""
    
    def test_update_filters_core_fields(self, mock_adw_config):
        """<R2.2> Only core fields are persisted in state."""
        from adw.core.state import ADWState
        
        state = ADWState("test1234")
        
        # Try to update with core and non-core fields
        state.update(
            issue_number="42",
            branch_name="feature-branch",
            random_field="should-be-ignored",
            another_random="also-ignored",
        )
        
        # Core fields should be present
        assert state.data.get("issue_number") == "42"
        assert state.data.get("branch_name") == "feature-branch"
        
        # Non-core fields should be filtered out
        assert "random_field" not in state.data
        assert "another_random" not in state.data
    
    def test_update_all_core_fields(self, mock_adw_config):
        """<R2.2b> All core fields can be updated."""
        from adw.core.state import ADWState
        
        state = ADWState("test1234")
        
        state.update(
            issue_number="42",
            branch_name="feature-branch",
            plan_file="specs/plan.md",
            issue_class="/feature",
            worktree_path="/path/to/worktree",
            backend_port=9100,
            frontend_port=9200,
            model_set="heavy",
            all_adws=["adw_plan_iso"],
        )
        
        assert state.data["issue_number"] == "42"
        assert state.data["branch_name"] == "feature-branch"
        assert state.data["plan_file"] == "specs/plan.md"
        assert state.data["issue_class"] == "/feature"
        assert state.data["worktree_path"] == "/path/to/worktree"
        assert state.data["backend_port"] == 9100
        assert state.data["frontend_port"] == 9200
        assert state.data["model_set"] == "heavy"
        assert state.data["all_adws"] == ["adw_plan_iso"]


class TestADWStateGet:
    """Tests for ADWState.get() method."""
    
    def test_get_returns_value(self, mock_adw_config):
        """<R2.3> Returns value for existing key."""
        from adw.core.state import ADWState
        
        state = ADWState("test1234")
        state.update(issue_number="42")
        
        assert state.get("issue_number") == "42"
    
    def test_get_returns_default(self, mock_adw_config):
        """<R2.3b> Returns default value for missing keys."""
        from adw.core.state import ADWState
        
        state = ADWState("test1234")
        
        assert state.get("nonexistent") is None
        assert state.get("nonexistent", "default") == "default"
        assert state.get("nonexistent", 42) == 42


class TestADWStateAppendAdwId:
    """Tests for ADWState.append_adw_id() method."""
    
    def test_append_adw_id_adds_to_list(self, mock_adw_config):
        """<R2.4> Appends ADW ID to all_adws list."""
        from adw.core.state import ADWState
        
        state = ADWState("test1234")
        
        state.append_adw_id("adw_plan_iso")
        state.append_adw_id("adw_build_iso")
        
        assert "adw_plan_iso" in state.data["all_adws"]
        assert "adw_build_iso" in state.data["all_adws"]
    
    def test_append_adw_id_deduplicates(self, mock_adw_config):
        """<R2.4b> Duplicate ADW IDs are not added."""
        from adw.core.state import ADWState
        
        state = ADWState("test1234")
        
        state.append_adw_id("adw_plan_iso")
        state.append_adw_id("adw_plan_iso")
        state.append_adw_id("adw_plan_iso")
        
        assert state.data["all_adws"].count("adw_plan_iso") == 1


class TestADWStateWorkingDirectory:
    """Tests for ADWState.get_working_directory() method."""
    
    def test_get_working_directory_prefers_worktree(self, mock_adw_config):
        """<R2.5> Returns worktree_path if set."""
        from adw.core.state import ADWState
        
        state = ADWState("test1234")
        state.update(worktree_path="/path/to/worktree")
        
        assert state.get_working_directory() == "/path/to/worktree"
    
    def test_get_working_directory_falls_back_to_project_root(self, mock_adw_config):
        """<R2.5b> Returns project root if worktree_path not set."""
        from adw.core.state import ADWState
        
        state = ADWState("test1234")
        
        working_dir = state.get_working_directory()
        
        # Should be project root from config
        assert working_dir == str(mock_adw_config.project_root)


class TestADWStateStatePath:
    """Tests for ADWState.get_state_path() method."""
    
    def test_get_state_path_uses_config(self, mock_adw_config):
        """<R2.6> State path matches config structure."""
        from adw.core.state import ADWState
        
        state = ADWState("test1234")
        
        state_path = state.get_state_path()
        
        expected = str(mock_adw_config.get_agents_dir("test1234") / "adw_state.json")
        assert state_path == expected


class TestADWStateSave:
    """Tests for ADWState.save() method."""
    
    def test_save_creates_directory(self, mock_adw_config, tmp_path):
        """<R2.7> Parent directories created when saving."""
        from adw.core.state import ADWState
        
        # Update config to use tmp_path
        mock_adw_config.artifacts_dir = tmp_path / "artifacts"
        
        state = ADWState("test1234")
        state.update(issue_number="42")
        
        # Save should create directories
        state.save("test")
        
        state_path = Path(state.get_state_path())
        assert state_path.exists()
        assert state_path.parent.exists()
    
    def test_save_validates_with_pydantic(self, mock_adw_config, tmp_path):
        """<R2.8> ADWStateData validation runs on save."""
        from adw.core.state import ADWState
        
        mock_adw_config.artifacts_dir = tmp_path / "artifacts"
        
        state = ADWState("test1234")
        state.update(
            issue_number="42",
            model_set="base",
        )
        
        # Should not raise - valid data
        state.save("test")
        
        # Verify saved JSON is valid
        state_path = Path(state.get_state_path())
        saved_data = json.loads(state_path.read_text())
        
        assert saved_data["adw_id"] == "test1234"
        assert saved_data["issue_number"] == "42"
        assert saved_data["model_set"] == "base"
    
    def test_save_with_workflow_step(self, mock_adw_config, tmp_path, caplog):
        """<R2.8b> Workflow step logged when provided."""
        import logging
        from adw.core.state import ADWState
        
        mock_adw_config.artifacts_dir = tmp_path / "artifacts"
        caplog.set_level(logging.INFO)
        
        state = ADWState("test1234")
        state.save("adw_plan_iso")
        
        # Should log the workflow step
        assert any("adw_plan_iso" in record.message for record in caplog.records)


class TestADWStateLoad:
    """Tests for ADWState.load() class method."""
    
    def test_load_returns_none_if_missing(self, mock_adw_config):
        """<R2.9> None returned for nonexistent state file."""
        from adw.core.state import ADWState
        
        result = ADWState.load("nonexistent-id")
        
        assert result is None
    
    def test_load_parses_valid_json(self, mock_adw_config, tmp_path):
        """<R2.10> Valid JSON state file parsed correctly."""
        from adw.core.state import ADWState
        
        mock_adw_config.artifacts_dir = tmp_path / "artifacts"
        
        # Create a valid state file
        state_dir = tmp_path / "artifacts" / "test-org" / "test-repo" / "test1234"
        state_dir.mkdir(parents=True)
        
        state_data = {
            "adw_id": "test1234",
            "issue_number": "42",
            "branch_name": "feature-branch",
            "plan_file": "specs/plan.md",
            "issue_class": "/feature",
            "worktree_path": None,
            "backend_port": 9100,
            "frontend_port": 9200,
            "model_set": "base",
            "all_adws": ["adw_plan_iso"],
        }
        
        (state_dir / "adw_state.json").write_text(json.dumps(state_data))
        
        # Load the state
        loaded = ADWState.load("test1234")
        
        assert loaded is not None
        assert loaded.adw_id == "test1234"
        assert loaded.get("issue_number") == "42"
        assert loaded.get("branch_name") == "feature-branch"
        assert loaded.get("all_adws") == ["adw_plan_iso"]
    
    def test_load_with_logger(self, mock_adw_config, tmp_path, caplog):
        """<R2.10b> Logger receives info when loading state."""
        import logging
        from adw.core.state import ADWState
        
        mock_adw_config.artifacts_dir = tmp_path / "artifacts"
        caplog.set_level(logging.INFO)
        
        # Create state file
        state_dir = tmp_path / "artifacts" / "test-org" / "test-repo" / "test1234"
        state_dir.mkdir(parents=True)
        (state_dir / "adw_state.json").write_text(json.dumps({
            "adw_id": "test1234",
            "all_adws": [],
        }))
        
        logger = logging.getLogger("test")
        loaded = ADWState.load("test1234", logger)
        
        assert loaded is not None


class TestADWStateFromStdin:
    """Tests for ADWState.from_stdin() class method."""
    
    def test_from_stdin_returns_none_for_tty(self, mock_adw_config):
        """<R2.11> Returns None when stdin is a tty."""
        from adw.core.state import ADWState
        
        with patch.object(sys.stdin, "isatty", return_value=True):
            result = ADWState.from_stdin()
        
        assert result is None
    
    def test_from_stdin_parses_json(self, mock_adw_config):
        """<R2.11b> Parses JSON from stdin when piped."""
        from adw.core.state import ADWState
        
        state_json = json.dumps({
            "adw_id": "piped123",
            "issue_number": "99",
        })
        
        with patch.object(sys.stdin, "isatty", return_value=False):
            with patch.object(sys.stdin, "read", return_value=state_json):
                result = ADWState.from_stdin()
        
        assert result is not None
        assert result.adw_id == "piped123"
        assert result.get("issue_number") == "99"
    
    def test_from_stdin_returns_none_for_empty(self, mock_adw_config):
        """<R2.11c> Returns None for empty stdin."""
        from adw.core.state import ADWState
        
        with patch.object(sys.stdin, "isatty", return_value=False):
            with patch.object(sys.stdin, "read", return_value=""):
                result = ADWState.from_stdin()
        
        assert result is None
    
    def test_from_stdin_returns_none_for_invalid_json(self, mock_adw_config):
        """<R2.11d> Returns None for invalid JSON."""
        from adw.core.state import ADWState
        
        with patch.object(sys.stdin, "isatty", return_value=False):
            with patch.object(sys.stdin, "read", return_value="not valid json"):
                result = ADWState.from_stdin()
        
        assert result is None
    
    def test_from_stdin_returns_none_without_adw_id(self, mock_adw_config):
        """<R2.11e> Returns None if JSON lacks adw_id."""
        from adw.core.state import ADWState
        
        state_json = json.dumps({"issue_number": "99"})
        
        with patch.object(sys.stdin, "isatty", return_value=False):
            with patch.object(sys.stdin, "read", return_value=state_json):
                result = ADWState.from_stdin()
        
        assert result is None


class TestADWStateToStdout:
    """Tests for ADWState.to_stdout() method."""
    
    def test_to_stdout_outputs_json(self, mock_adw_config, capsys):
        """<R2.12> JSON output is valid and complete."""
        from adw.core.state import ADWState
        
        state = ADWState("test1234")
        state.update(
            issue_number="42",
            branch_name="feature-branch",
            plan_file="specs/plan.md",
            backend_port=9100,
            frontend_port=9200,
        )
        
        state.to_stdout()
        
        captured = capsys.readouterr()
        output_data = json.loads(captured.out)
        
        assert output_data["adw_id"] == "test1234"
        assert output_data["issue_number"] == "42"
        assert output_data["branch_name"] == "feature-branch"
        assert output_data["plan_file"] == "specs/plan.md"
        assert output_data["backend_port"] == 9100
        assert output_data["frontend_port"] == 9200
    
    def test_to_stdout_includes_all_adws(self, mock_adw_config, capsys):
        """<R2.12b> all_adws list included in output."""
        from adw.core.state import ADWState
        
        state = ADWState("test1234")
        state.append_adw_id("adw_plan_iso")
        state.append_adw_id("adw_build_iso")
        
        state.to_stdout()
        
        captured = capsys.readouterr()
        output_data = json.loads(captured.out)
        
        assert "adw_plan_iso" in output_data["all_adws"]
        assert "adw_build_iso" in output_data["all_adws"]

