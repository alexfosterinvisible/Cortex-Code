"""Configuration management for ADW Framework."""

import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class PortConfig:
    backend_start: int = 9100
    backend_count: int = 15
    frontend_start: int = 9200
    frontend_count: int = 15

@dataclass
class ADWConfig:
    project_root: Path
    project_id: str
    artifacts_dir: Path
    ports: PortConfig
    commands: List[Path] = field(default_factory=list)
    app_config: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def load(cls, project_root: Optional[Path] = None) -> "ADWConfig":
        """Load configuration from .adw.yaml in project root."""
        if project_root is None:
            # Try to find project root by looking for .adw.yaml or walking up
            current_path = Path.cwd()
            while current_path != current_path.parent:
                if (current_path / ".adw.yaml").exists():
                    project_root = current_path
                    break
                current_path = current_path.parent
            
            if project_root is None:
                # Fallback to CWD if not found, assuming we are in project root
                project_root = Path.cwd()

        config_path = project_root / ".adw.yaml"
        
        # Defaults
        config_data = {
            "project_id": "unknown-project",
            "artifacts_dir": "./artifacts",
            "ports": {},
            "commands": [],
            "app": {}
        }

        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    user_config = yaml.safe_load(f) or {}
                    config_data.update(user_config)
            except Exception as e:
                print(f"Warning: Failed to load .adw.yaml: {e}")

        # Parse ports
        ports_data = config_data.get("ports", {})
        ports_config = PortConfig(
            backend_start=ports_data.get("backend_start", 9100),
            backend_count=ports_data.get("backend_count", 15),
            frontend_start=ports_data.get("frontend_start", 9200),
            frontend_count=ports_data.get("frontend_count", 15),
        )

        # Parse artifacts dir (relative to project root)
        artifacts_path = Path(config_data.get("artifacts_dir", "./artifacts"))
        if not artifacts_path.is_absolute():
            artifacts_path = project_root / artifacts_path

        # Parse commands
        # Allow ${ADW_FRAMEWORK} expansion
        framework_root = Path(__file__).parent.parent
        command_paths = []
        for cmd_path_str in config_data.get("commands", []):
            if "${ADW_FRAMEWORK}" in cmd_path_str:
                cmd_path_str = cmd_path_str.replace("${ADW_FRAMEWORK}", str(framework_root))
            
            path = Path(cmd_path_str)
            if not path.is_absolute():
                path = project_root / path
            command_paths.append(path)
            
        # If no commands specified, add framework commands by default
        if not command_paths:
            command_paths.append(framework_root / "commands")

        return cls(
            project_root=project_root,
            project_id=config_data.get("project_id", "unknown"),
            artifacts_dir=artifacts_path,
            ports=ports_config,
            commands=command_paths,
            app_config=config_data.get("app", {})
        )

    def get_project_artifacts_dir(self) -> Path:
        """Get the artifacts directory for this specific project."""
        # Clean project_id to be path safe if needed, but usually it's used as is or simple path
        # Assuming project_id "org/repo" -> artifacts/org/repo/
        return self.artifacts_dir / self.project_id

    def get_agents_dir(self, adw_id: str) -> Path:
        """Get directory for agent state and logs."""
        return self.get_project_artifacts_dir() / adw_id

    def get_trees_dir(self) -> Path:
        """Get base directory for worktrees."""
        return self.get_project_artifacts_dir() / "trees"

