"""State management for CXC composable architecture.

Provides persistent state management via file storage and
transient state passing between scripts via stdin/stdout.
"""

import json
import os
import sys
import logging
from typing import Dict, Any, Optional
from .data_types import CxcStateData
from .config import CxcConfig


class CxcState:
    """Container for CXC workflow state with file persistence."""

    STATE_FILENAME = "cxc_state.json"

    def __init__(self, cxc_id: str):
        """Initialize CxcState with a required CXC ID.
        
        Args:
            cxc_id: The CXC ID for this state (required)
        """
        if not cxc_id:
            raise ValueError("cxc_id is required for CxcState")
        
        self.cxc_id = cxc_id
        # Start with minimal state
        self.data: Dict[str, Any] = {"cxc_id": self.cxc_id}
        self.logger = logging.getLogger(__name__)
        
        # Load config
        self.config = CxcConfig.load()

    def update(self, **kwargs):
        """Update state with new key-value pairs."""
        # Filter to only our core fields
        core_fields = {"cxc_id", "issue_number", "branch_name", "plan_file", "issue_class", "worktree_path", "backend_port", "frontend_port", "model_set", "all_cxcs"}
        for key, value in kwargs.items():
            if key in core_fields:
                self.data[key] = value

    def get(self, key: str, default=None):
        """Get value from state by key."""
        return self.data.get(key, default)

    def append_cxc_id(self, cxc_id: str):
        """Append an CXC ID to the all_cxcs list if not already present."""
        all_cxcs = self.data.get("all_cxcs", [])
        if cxc_id not in all_cxcs:
            all_cxcs.append(cxc_id)
            self.data["all_cxcs"] = all_cxcs

    def get_working_directory(self) -> str:
        """Get the working directory for this CXC instance.
        
        Returns worktree_path if set (for isolated workflows),
        otherwise returns the main repo path from config.
        """
        worktree_path = self.data.get("worktree_path")
        if worktree_path:
            return worktree_path
        
        # Return main repo path from config
        return str(self.config.project_root)

    def get_state_path(self) -> str:
        """Get path to state file."""
        return str(self.config.get_agents_dir(self.cxc_id) / self.STATE_FILENAME)

    def save(self, workflow_step: Optional[str] = None) -> None:
        """Save state to file in agents/{cxc_id}/cxc_state.json."""
        state_path = self.get_state_path()
        os.makedirs(os.path.dirname(state_path), exist_ok=True)

        # Create CxcStateData for validation
        state_data = CxcStateData(
            cxc_id=self.data.get("cxc_id"),
            issue_number=self.data.get("issue_number"),
            branch_name=self.data.get("branch_name"),
            plan_file=self.data.get("plan_file"),
            issue_class=self.data.get("issue_class"),
            worktree_path=self.data.get("worktree_path"),
            backend_port=self.data.get("backend_port"),
            frontend_port=self.data.get("frontend_port"),
            model_set=self.data.get("model_set", "base"),
            all_cxcs=self.data.get("all_cxcs", []),
        )

        # Save as JSON
        with open(state_path, "w") as f:
            json.dump(state_data.model_dump(), f, indent=2)

        self.logger.info(f"Saved state to {state_path}")
        if workflow_step:
            self.logger.info(f"State updated by: {workflow_step}")

    @classmethod
    def load(
        cls, cxc_id: str, logger: Optional[logging.Logger] = None
    ) -> Optional["CxcState"]:
        """Load state from file if it exists."""
        # Need config to know where to look
        config = CxcConfig.load()
        state_path = config.get_agents_dir(cxc_id) / cls.STATE_FILENAME

        if not state_path.exists():
            return None

        try:
            with open(state_path, "r") as f:
                data = json.load(f)

            # Validate with CxcStateData
            state_data = CxcStateData(**data)

            # Create CxcState instance
            state = cls(state_data.cxc_id)
            state.data = state_data.model_dump()

            if logger:
                logger.info(f"🔍 Found existing state from {state_path}")
                logger.info(f"State: {json.dumps(state_data.model_dump(), indent=2)}")

            return state
        except Exception as e:
            if logger:
                logger.error(f"Failed to load state from {state_path}: {e}")
            return None

    @classmethod
    def from_stdin(cls) -> Optional["CxcState"]:
        """Read state from stdin if available (for piped input).

        Returns None if no piped input is available (stdin is a tty).
        """
        if sys.stdin.isatty():
            return None
        try:
            input_data = sys.stdin.read()
            if not input_data.strip():
                return None
            data = json.loads(input_data)
            cxc_id = data.get("cxc_id")
            if not cxc_id:
                return None  # No valid state without cxc_id
            state = cls(cxc_id)
            state.data = data
            return state
        except (json.JSONDecodeError, EOFError):
            return None

    def to_stdout(self):
        """Write state to stdout as JSON (for piping to next script)."""
        # Only output core fields
        output_data = {
            "cxc_id": self.data.get("cxc_id"),
            "issue_number": self.data.get("issue_number"),
            "branch_name": self.data.get("branch_name"),
            "plan_file": self.data.get("plan_file"),
            "issue_class": self.data.get("issue_class"),
            "worktree_path": self.data.get("worktree_path"),
            "backend_port": self.data.get("backend_port"),
            "frontend_port": self.data.get("frontend_port"),
            "all_cxcs": self.data.get("all_cxcs", []),
        }
        print(json.dumps(output_data, indent=2))
