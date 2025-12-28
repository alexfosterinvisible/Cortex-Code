#!/usr/bin/env python3
"""
Setup ADW in a target project directory.

Run from the target project directory:
    python /path/to/adw-framework/setup_adw_example.py

What it does:
    1. Creates/updates pyproject.toml with adw-framework dependency
    2. Creates .adw.yaml config (prompts for project_id if needed)
    3. Copies required env vars from source .env (ANTHROPIC_API_KEY, GITHUB_PAT, CLAUDE_CODE_PATH)
    3b. Copies ADW command templates to .claude/commands/ (required for Claude CLI)
    4. Runs uv sync
    5. Verifies setup with adw --help
"""
import os
import re
import subprocess
import sys
from pathlib import Path

# ----- CONFIG -----
ADW_FRAMEWORK_DIR = Path(__file__).parent.resolve()
REQUIRED_ENV_KEYS = ["ANTHROPIC_API_KEY", "GITHUB_PAT", "CLAUDE_CODE_PATH"]
OPTIONAL_ENV_KEYS = ["CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR"]


# ----- HELPERS -----
def _run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run command, print output."""
    print(f"  → {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, capture_output=False)


def _read_env_file(path: Path) -> dict[str, str]:
    """Parse .env file into dict."""
    env = {}
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip()
    return env


def _get_git_remote_url(target_dir: Path) -> str | None:
    """Get git remote origin URL."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=target_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def _extract_project_id(url: str) -> str | None:
    """Extract org/repo from git URL."""
    # https://github.com/org/repo.git or git@github.com:org/repo.git
    match = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$", url)
    if match:
        return match.group(1)
    return None


def _get_gh_token() -> str | None:
    """Get GitHub token from gh CLI."""
    try:
        result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


# ----- MAIN STEPS -----
def step1_pyproject(target_dir: Path) -> None:
    """Create or update pyproject.toml."""
    print("\n[1/5] Setting up pyproject.toml...")
    pyproject = target_dir / "pyproject.toml"
    
    if not pyproject.exists():
        # Create minimal pyproject.toml
        project_name = target_dir.name.replace("-", "_").replace(" ", "_")
        content = f'''[project]
name = "{project_name}"
version = "0.1.0"
description = ""
requires-python = ">=3.11"
dependencies = []
'''
        pyproject.write_text(content)
        print(f"  Created {pyproject}")
    
    # Add adw-framework dependency via uv
    _run(["uv", "add", str(ADW_FRAMEWORK_DIR)], check=False)


def step2_adw_yaml(target_dir: Path) -> None:
    """Create .adw.yaml config."""
    print("\n[2/5] Creating .adw.yaml...")
    adw_yaml = target_dir / ".adw.yaml"
    
    if adw_yaml.exists():
        print(f"  {adw_yaml} already exists, skipping")
        return
    
    # Try to detect project_id from git
    project_id = None
    git_url = _get_git_remote_url(target_dir)
    if git_url:
        project_id = _extract_project_id(git_url)
        if project_id:
            print(f"  Detected project_id from git: {project_id}")
    
    if not project_id:
        project_id = input("  Enter project_id (org/repo): ").strip()
        if not project_id:
            project_id = f"org/{target_dir.name}"
            print(f"  Using default: {project_id}")
    
    content = f'''# .adw.yaml - ADW Framework Configuration

# REQUIRED: Used for artifact namespacing (matches GitHub repo)
project_id: "{project_id}"

# REQUIRED: Where ADW stores state, logs, worktrees
artifacts_dir: "./artifacts"

# Port ranges for isolated worktrees (15 concurrent agents max)
ports:
  backend_start: 9100
  backend_count: 15
  frontend_start: 9200
  frontend_count: 15

# Claude command paths (framework commands + your overrides)
commands:
  - "${{ADW_FRAMEWORK}}/commands"
  - ".claude/commands"

# App-specific settings (customize for your project)
app:
  test_command: "uv run pytest"
'''
    adw_yaml.write_text(content)
    print(f"  Created {adw_yaml}")


def step3_env(target_dir: Path) -> None:
    """Copy required env vars to target .env."""
    print("\n[3/5] Setting up .env...")
    target_env = target_dir / ".env"
    
    # Find source .env (try common locations)
    source_env_paths = [
        ADW_FRAMEWORK_DIR / ".env",
        Path.home() / ".env",
        Path.home() / "code4b" / "wf-kiss1" / ".env",
    ]
    
    source_env = {}
    for p in source_env_paths:
        if p.exists():
            source_env = _read_env_file(p)
            if any(k in source_env for k in REQUIRED_ENV_KEYS):
                print(f"  Found source .env: {p}")
                break
    
    # Read existing target env
    target_env_data = _read_env_file(target_env) if target_env.exists() else {}
    
    # Try to get GITHUB_PAT from gh CLI if not in source
    if "GITHUB_PAT" not in source_env or source_env.get("GITHUB_PAT", "").startswith("ghp_xxxxx"):
        gh_token = _get_gh_token()
        if gh_token:
            source_env["GITHUB_PAT"] = gh_token
            print("  Got GITHUB_PAT from `gh auth token`")
    
    # Find claude CLI path
    if "CLAUDE_CODE_PATH" not in source_env or "xxxxx" in source_env.get("CLAUDE_CODE_PATH", ""):
        claude_paths = [
            Path.home() / ".claude" / "local" / "claude",
            Path("/usr/local/bin/claude"),
        ]
        for cp in claude_paths:
            if cp.exists():
                source_env["CLAUDE_CODE_PATH"] = str(cp)
                print(f"  Found claude CLI: {cp}")
                break
    
    # Detect GITHUB_REPO_URL from git
    git_url = _get_git_remote_url(target_dir)
    if git_url:
        source_env["GITHUB_REPO_URL"] = git_url
    
    # Merge: copy required keys from source, keep existing target values
    lines = ["# ADW Framework Environment Variables\n"]
    
    for key in REQUIRED_ENV_KEYS + OPTIONAL_ENV_KEYS + ["GITHUB_REPO_URL"]:
        value = target_env_data.get(key) or source_env.get(key)
        if value and "xxxxx" not in value:
            lines.append(f"{key}={value}\n")
        elif key in REQUIRED_ENV_KEYS:
            print(f"  ⚠️  Missing required: {key}")
            lines.append(f"# {key}=  # TODO: fill in\n")
    
    target_env.write_text("".join(lines))
    print(f"  Created {target_env}")


def step3b_commands(target_dir: Path) -> None:
    """Copy ADW command templates to .claude/commands/."""
    print("\n[3b/6] Copying ADW commands to .claude/commands/...")

    commands_src = ADW_FRAMEWORK_DIR / "commands"
    commands_dst = target_dir / ".claude" / "commands"

    if not commands_src.exists():
        print(f"  ⚠️  ADW commands not found at {commands_src}")
        return

    commands_dst.mkdir(parents=True, exist_ok=True)

    copied = 0
    # Copy root-level commands
    for md_file in commands_src.glob("*.md"):
        dst_file = commands_dst / md_file.name
        if not dst_file.exists():
            dst_file.write_text(md_file.read_text())
            copied += 1

    # Copy examples/ subdirectory (contains /test, /test_e2e, etc.)
    examples_src = commands_src / "examples"
    if examples_src.exists():
        for md_file in examples_src.glob("*.md"):
            dst_file = commands_dst / md_file.name
            if not dst_file.exists():
                dst_file.write_text(md_file.read_text())
                copied += 1
        # Also copy e2e/ subdirectory if it exists
        e2e_src = examples_src / "e2e"
        if e2e_src.exists():
            e2e_dst = commands_dst / "e2e"
            e2e_dst.mkdir(parents=True, exist_ok=True)
            for md_file in e2e_src.glob("*.md"):
                dst_file = e2e_dst / md_file.name
                if not dst_file.exists():
                    dst_file.write_text(md_file.read_text())
                    copied += 1

    print(f"  Copied {copied} command templates to {commands_dst}")
    print(f"  Total commands available: {len(list(commands_dst.glob('*.md')))}")


def step4_sync(target_dir: Path) -> None:
    """Run uv sync."""
    print("\n[4/6] Running uv sync...")
    _run(["uv", "sync"], check=False)


def step5_verify(target_dir: Path) -> None:
    """Verify ADW CLI works."""
    print("\n[5/6] Verifying setup...")
    result = subprocess.run(
        ["uv", "run", "adw", "--help"],
        cwd=target_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and "AI Developer Workflow" in result.stdout:
        print("  ✓ ADW CLI works!")
    else:
        print("  ✗ ADW CLI failed")
        print(result.stderr or result.stdout)
        return
    
    # Quick config check
    result = subprocess.run(
        ["uv", "run", "python", "-c", 
         "from adw.config import ADWConfig; c = ADWConfig.load(); print(f'  ✓ project_id: {c.project_id}')"],
        cwd=target_dir,
        capture_output=True,
        text=True,
    )
    print(result.stdout.strip() if result.returncode == 0 else f"  ✗ Config error: {result.stderr}")


def main():
    target_dir = Path.cwd()
    print(f"Setting up ADW in: {target_dir}")
    print(f"ADW framework at: {ADW_FRAMEWORK_DIR}")
    
    step1_pyproject(target_dir)
    step2_adw_yaml(target_dir)
    step3_env(target_dir)
    step3b_commands(target_dir)
    step4_sync(target_dir)
    step5_verify(target_dir)
    
    print("\n" + "="*50)
    print("Setup complete! Try:")
    print("  uv run adw --help")
    print("  uv run adw plan <issue-number>")


if __name__ == "__main__":
    main()

