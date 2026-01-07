"""
Feature flags for CXC Framework.

⏳ ISSUE_SOURCE: Control where issues come from
⏳ ISOLATION: Control workflow isolation strategy  
⏳ STATE_BACKEND: Control state persistence
☑️ GITHUB_COMMENTS: Already implemented via CXC_DISABLE_GITHUB_COMMENTS
⏳ ARTIFACTS_BACKEND: Control artifact storage

Usage:
    from cxc.core.features import Features
    
    features = Features.load()
    if features.github_comments:
        make_issue_comment(...)
"""

import os
from dataclasses import dataclass, field
from typing import Literal, Optional, Dict, Any
from pathlib import Path


# Type aliases for feature options
IssueSource = Literal["github", "local_json", "sqlite", "yaml"]
IsolationStrategy = Literal["worktree", "branch_only", "docker", "none"]
AgentBackend = Literal["claude_code", "anthropic_api", "openai"]
StateBackend = Literal["json_file", "sqlite", "yaml"]
ArtifactsBackend = Literal["local", "r2", "s3"]


@dataclass
class GitHubFeatures:
    """GitHub integration feature flags."""
    comments: bool = True
    create_prs: bool = True
    auto_merge: bool = False  # ZTE only


@dataclass
class ArtifactsFeatures:
    """Artifact storage feature flags."""
    backend: ArtifactsBackend = "local"
    screenshots: bool = True


@dataclass 
class Features:
    """
    Feature flags for CXC Framework.
    
    Load from .cxc.yaml or environment variables.
    Environment variables take precedence.
    """
    # Core feature flags
    issue_source: IssueSource = "github"
    isolation: IsolationStrategy = "worktree"
    agent_backend: AgentBackend = "claude_code"
    state_backend: StateBackend = "json_file"
    
    # Nested feature groups
    github: GitHubFeatures = field(default_factory=GitHubFeatures)
    artifacts: ArtifactsFeatures = field(default_factory=ArtifactsFeatures)
    
    # === Convenience properties for backward compatibility ===
    
    @property
    def github_comments(self) -> bool:
        """Check if GitHub comments are enabled (respects CXC_DISABLE_GITHUB_COMMENTS)."""
        env_disabled = os.getenv("CXC_DISABLE_GITHUB_COMMENTS", "").strip().lower()
        if env_disabled in ("1", "true", "yes"):
            return False
        return self.github.comments
    
    @property
    def use_worktrees(self) -> bool:
        """Check if worktree isolation is enabled."""
        return self.isolation == "worktree"
    
    @property
    def use_local_issues(self) -> bool:
        """Check if using local issue source (not GitHub)."""
        return self.issue_source in ("local_json", "sqlite", "yaml")
    
    # === Loading ===
    
    @classmethod
    def load(cls, config_data: Optional[Dict[str, Any]] = None) -> "Features":
        """
        Load features from config dict (typically from .cxc.yaml).
        
        Environment variables override config values.
        """
        features_data = (config_data or {}).get("features", {})
        
        # Parse nested github features
        github_data = features_data.get("github", {})
        github_features = GitHubFeatures(
            comments=github_data.get("comments", True),
            create_prs=github_data.get("create_prs", True),
            auto_merge=github_data.get("auto_merge", False),
        )
        
        # Parse nested artifacts features
        artifacts_data = features_data.get("artifacts", {})
        artifacts_features = ArtifactsFeatures(
            backend=artifacts_data.get("backend", "local"),
            screenshots=artifacts_data.get("screenshots", True),
        )
        
        # Build main features
        instance = cls(
            issue_source=features_data.get("issue_source", "github"),
            isolation=features_data.get("isolation", "worktree"),
            agent_backend=features_data.get("agent_backend", "claude_code"),
            state_backend=features_data.get("state_backend", "json_file"),
            github=github_features,
            artifacts=artifacts_features,
        )
        
        # Apply environment variable overrides
        instance._apply_env_overrides()
        
        return instance
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to feature flags."""
        # CXC_ISSUE_SOURCE
        if env_val := os.getenv("CXC_ISSUE_SOURCE"):
            if env_val in ("github", "local_json", "sqlite", "yaml"):
                self.issue_source = env_val  # type: ignore
        
        # CXC_ISOLATION
        if env_val := os.getenv("CXC_ISOLATION"):
            if env_val in ("worktree", "branch_only", "docker", "none"):
                self.isolation = env_val  # type: ignore
        
        # CXC_STATE_BACKEND
        if env_val := os.getenv("CXC_STATE_BACKEND"):
            if env_val in ("json_file", "sqlite", "yaml"):
                self.state_backend = env_val  # type: ignore


# === ISSUE SOURCE ADAPTERS ===
# These will be implemented as the feature flags are used

@dataclass
class LocalIssue:
    """Local issue representation (matches GitHubIssue interface)."""
    number: int
    title: str
    body: str
    state: str = "open"
    labels: list = field(default_factory=list)


class IssueSourceAdapter:
    """Base class for issue source adapters."""
    
    def fetch_issue(self, issue_id: str) -> LocalIssue:
        raise NotImplementedError
    
    def list_issues(self, state: str = "open") -> list[LocalIssue]:
        raise NotImplementedError
    
    def create_issue(self, title: str, body: str) -> LocalIssue:
        raise NotImplementedError
    
    def update_issue(self, issue_id: str, **kwargs) -> LocalIssue:
        raise NotImplementedError


class LocalJsonIssueSource(IssueSourceAdapter):
    """
    Local JSON file-based issue source.
    
    File format (issues_db.json):
    {
        "issues": [
            {"number": 1, "title": "...", "body": "...", "state": "open"},
            ...
        ],
        "next_number": 2
    }
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        from cxc.core.config import CxcConfig
        config = CxcConfig.load()
        self.db_path = db_path or (config.artifacts_dir / "issues_db.json")
        self._ensure_db()
    
    def _ensure_db(self) -> None:
        """Create DB file if it doesn't exist."""
        if not self.db_path.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._write_db({"issues": [], "next_number": 1})
    
    def _read_db(self) -> dict:
        import json
        with open(self.db_path) as f:
            return json.load(f)
    
    def _write_db(self, data: dict) -> None:
        import json
        with open(self.db_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Wrote issues DB to: {self.db_path.absolute()}")
    
    def fetch_issue(self, issue_id: str) -> LocalIssue:
        db = self._read_db()
        issue_num = int(issue_id)
        for issue in db["issues"]:
            if issue["number"] == issue_num:
                return LocalIssue(**issue)
        raise ValueError(f"Issue #{issue_id} not found in local DB")
    
    def list_issues(self, state: str = "open") -> list[LocalIssue]:
        db = self._read_db()
        return [
            LocalIssue(**issue) 
            for issue in db["issues"] 
            if issue.get("state", "open") == state
        ]
    
    def create_issue(self, title: str, body: str) -> LocalIssue:
        db = self._read_db()
        issue = {
            "number": db["next_number"],
            "title": title,
            "body": body,
            "state": "open",
            "labels": [],
        }
        db["issues"].append(issue)
        db["next_number"] += 1
        self._write_db(db)
        return LocalIssue(**issue)
    
    def update_issue(self, issue_id: str, **kwargs) -> LocalIssue:
        db = self._read_db()
        issue_num = int(issue_id)
        for i, issue in enumerate(db["issues"]):
            if issue["number"] == issue_num:
                issue.update(kwargs)
                db["issues"][i] = issue
                self._write_db(db)
                return LocalIssue(**issue)
        raise ValueError(f"Issue #{issue_id} not found in local DB")


def get_issue_source(features: Optional[Features] = None) -> IssueSourceAdapter:
    """Factory function to get the configured issue source adapter."""
    features = features or Features.load()
    
    if features.issue_source == "local_json":
        return LocalJsonIssueSource()
    elif features.issue_source == "sqlite":
        raise NotImplementedError("SQLite issue source not yet implemented")
    elif features.issue_source == "yaml":
        raise NotImplementedError("YAML issue source not yet implemented")
    else:
        # GitHub is default - but that uses gh CLI directly, not this adapter
        raise ValueError("GitHub issue source uses integrations/github.py directly")


# === Quick test ===
if __name__ == "__main__":
    # Test loading features
    features = Features.load()
    print(f"Issue Source: {features.issue_source}")
    print(f"Isolation: {features.isolation}")
    print(f"GitHub Comments: {features.github_comments}")
    print(f"Use Worktrees: {features.use_worktrees}")
    
    # Test local JSON issue source
    print("\n--- Testing LocalJsonIssueSource ---")
    source = LocalJsonIssueSource()
    
    # Create a test issue
    issue = source.create_issue(
        title="Test Feature Flag Issue",
        body="This is a test issue created via local JSON source"
    )
    print(f"Created issue #{issue.number}: {issue.title}")
    
    # Fetch it back
    fetched = source.fetch_issue(str(issue.number))
    print(f"Fetched issue #{fetched.number}: {fetched.title}")
    
    # List all
    all_issues = source.list_issues()
    print(f"Total open issues: {len(all_issues)}")

