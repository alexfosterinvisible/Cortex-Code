"""Unit tests for adw/core/config.py - <R1> Config Loading Tests

Tests ADWConfig class:
- YAML loading and parsing
- Default value handling
- Path resolution
- Port configuration
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestADWConfigLoad:
    """Tests for ADWConfig.load() method."""
    
    def test_load_from_yaml(self, tmp_project_dir: Path):
        """<R1.1> Config loads correctly from .adw.yaml file."""
        from adw.core.config import ADWConfig
        
        # Load config from temp project dir
        config = ADWConfig.load(tmp_project_dir)
        
        assert config.project_id == "test-org/test-repo"
        assert config.project_root == tmp_project_dir
        assert config.artifacts_dir == tmp_project_dir / "artifacts"
    
    def test_load_missing_yaml_uses_defaults(self, tmp_path: Path):
        """<R1.2> Missing .adw.yaml uses default values gracefully."""
        from adw.core.config import ADWConfig
        
        # No .adw.yaml in tmp_path
        config = ADWConfig.load(tmp_path)
        
        assert config.project_id == "unknown-project"
        assert config.project_root == tmp_path
        assert config.artifacts_dir == tmp_path / "artifacts"
    
    def test_project_root_discovery(self, tmp_path: Path):
        """<R1.3> Walks up directory tree to find .adw.yaml."""
        from adw.core.config import ADWConfig
        
        # Create nested structure
        nested_dir = tmp_path / "level1" / "level2" / "level3"
        nested_dir.mkdir(parents=True)
        
        # Put .adw.yaml at root
        (tmp_path / ".adw.yaml").write_text('project_id: "found-it"')
        
        # Mock cwd to be in nested dir
        with patch("pathlib.Path.cwd", return_value=nested_dir):
            config = ADWConfig.load()
        
        assert config.project_id == "found-it"
        assert config.project_root == tmp_path
    
    def test_artifacts_dir_resolution_relative(self, tmp_path: Path):
        """<R1.4> Relative artifacts_dir resolved to absolute path."""
        from adw.core.config import ADWConfig
        
        # Create config with relative path
        (tmp_path / ".adw.yaml").write_text('''
project_id: "test"
artifacts_dir: "./my_artifacts"
''')
        
        config = ADWConfig.load(tmp_path)
        
        assert config.artifacts_dir.is_absolute()
        assert config.artifacts_dir == tmp_path / "my_artifacts"
    
    def test_artifacts_dir_resolution_absolute(self, tmp_path: Path):
        """<R1.4b> Absolute artifacts_dir preserved as-is."""
        from adw.core.config import ADWConfig
        
        abs_path = "/tmp/adw_artifacts"
        (tmp_path / ".adw.yaml").write_text(f'''
project_id: "test"
artifacts_dir: "{abs_path}"
''')
        
        config = ADWConfig.load(tmp_path)
        
        assert str(config.artifacts_dir) == abs_path


class TestADWConfigCommandPaths:
    """Tests for command path expansion."""
    
    def test_command_paths_expansion(self, tmp_path: Path):
        """<R1.5> ${ADW_FRAMEWORK} expansion works in command paths."""
        from adw.core.config import ADWConfig
        
        (tmp_path / ".adw.yaml").write_text('''
project_id: "test"
commands:
  - "${ADW_FRAMEWORK}/commands"
  - "./local_commands"
''')
        
        config = ADWConfig.load(tmp_path)
        
        # First path should be expanded (framework path)
        assert len(config.commands) == 2
        assert "${ADW_FRAMEWORK}" not in str(config.commands[0])
        # Second path should be resolved relative to project root
        assert config.commands[1] == tmp_path / "local_commands"
    
    def test_default_commands_when_none_specified(self, tmp_path: Path):
        """<R1.5b> Default framework commands added when none specified."""
        from adw.core.config import ADWConfig
        
        (tmp_path / ".adw.yaml").write_text('project_id: "test"')
        
        config = ADWConfig.load(tmp_path)
        
        # Should have at least the framework commands
        assert len(config.commands) >= 1
        assert "commands" in str(config.commands[0])


class TestADWConfigPorts:
    """Tests for port configuration."""
    
    def test_port_config_defaults(self, tmp_path: Path):
        """<R1.6> Default port ranges are correct."""
        from adw.core.config import ADWConfig
        
        (tmp_path / ".adw.yaml").write_text('project_id: "test"')
        
        config = ADWConfig.load(tmp_path)
        
        assert config.ports.backend_start == 9100
        assert config.ports.backend_count == 15
        assert config.ports.frontend_start == 9200
        assert config.ports.frontend_count == 15
    
    def test_port_config_custom(self, tmp_path: Path):
        """<R1.6b> Custom port configuration is loaded."""
        from adw.core.config import ADWConfig
        
        (tmp_path / ".adw.yaml").write_text('''
project_id: "test"
ports:
  backend_start: 8100
  backend_count: 10
  frontend_start: 8200
  frontend_count: 10
''')
        
        config = ADWConfig.load(tmp_path)
        
        assert config.ports.backend_start == 8100
        assert config.ports.backend_count == 10
        assert config.ports.frontend_start == 8200
        assert config.ports.frontend_count == 10


class TestADWConfigPaths:
    """Tests for path helper methods."""
    
    def test_get_project_artifacts_dir(self, tmp_project_dir: Path):
        """<R1.7> Returns correct path structure for project artifacts."""
        from adw.core.config import ADWConfig
        
        config = ADWConfig.load(tmp_project_dir)
        
        artifacts_dir = config.get_project_artifacts_dir()
        
        assert artifacts_dir == tmp_project_dir / "artifacts" / "test-org" / "test-repo"
    
    def test_get_agents_dir(self, tmp_project_dir: Path):
        """<R1.8> Returns correct agent directory path for ADW ID."""
        from adw.core.config import ADWConfig
        
        config = ADWConfig.load(tmp_project_dir)
        
        agents_dir = config.get_agents_dir("abc12345")
        
        expected = tmp_project_dir / "artifacts" / "test-org" / "test-repo" / "abc12345"
        assert agents_dir == expected
    
    def test_get_trees_dir(self, tmp_project_dir: Path):
        """<R1.9> Returns correct worktree base path."""
        from adw.core.config import ADWConfig
        
        config = ADWConfig.load(tmp_project_dir)
        
        trees_dir = config.get_trees_dir()
        
        expected = tmp_project_dir / "artifacts" / "test-org" / "test-repo" / "trees"
        assert trees_dir == expected


class TestADWConfigAppConfig:
    """Tests for app-specific configuration."""
    
    def test_app_config_loaded(self, tmp_path: Path):
        """<R1.10> App-specific config is loaded into app_config dict."""
        from adw.core.config import ADWConfig
        
        (tmp_path / ".adw.yaml").write_text('''
project_id: "test"
app:
  backend_dir: "app/server"
  frontend_dir: "app/client"
  test_command: "pytest"
''')
        
        config = ADWConfig.load(tmp_path)
        
        assert config.app_config["backend_dir"] == "app/server"
        assert config.app_config["frontend_dir"] == "app/client"
        assert config.app_config["test_command"] == "pytest"
    
    def test_app_config_empty_default(self, tmp_path: Path):
        """<R1.10b> Missing app config defaults to empty dict."""
        from adw.core.config import ADWConfig
        
        (tmp_path / ".adw.yaml").write_text('project_id: "test"')
        
        config = ADWConfig.load(tmp_path)
        
        assert config.app_config == {}


class TestADWConfigEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_invalid_yaml_uses_defaults(self, tmp_path: Path):
        """<R1.11> Invalid YAML falls back to defaults with warning."""
        from adw.core.config import ADWConfig
        
        (tmp_path / ".adw.yaml").write_text("invalid: yaml: content: [")
        
        # Should not raise, should use defaults
        config = ADWConfig.load(tmp_path)
        
        assert config.project_id == "unknown-project"
    
    def test_partial_yaml_merges_with_defaults(self, tmp_path: Path):
        """<R1.12> Partial YAML merges with defaults."""
        from adw.core.config import ADWConfig
        
        (tmp_path / ".adw.yaml").write_text('project_id: "my-project"')
        
        config = ADWConfig.load(tmp_path)
        
        # Specified value used
        assert config.project_id == "my-project"
        # Default used for unspecified
        assert config.ports.backend_start == 9100

