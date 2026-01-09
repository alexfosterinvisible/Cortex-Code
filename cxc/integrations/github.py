#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
GitHub Operations Module - Cortex Code (CXC)

This module contains all GitHub-related operations including:
- Issue fetching and manipulation
- Comment posting
- Repository path extraction
- Issue status management
"""

import subprocess
import sys
import os
import json
import threading
from typing import Dict, List, Optional
from cxc.core.data_types import GitHubIssue, GitHubIssueListItem, GitHubComment

# Bot identifier to prevent webhook loops and filter bot comments
CXC_BOT_IDENTIFIER = "[CXC-AGENTS]"

def github_comments_disabled() -> bool:
    """Return True when GitHub issue comments should be skipped."""
    flag = os.getenv("CXC_DISABLE_GITHUB_COMMENTS", "").strip().lower()
    return flag in {"1", "true", "yes", "y", "on"}


def get_github_env() -> Optional[dict]:
    """Get environment with GitHub token set up. Returns None if no GITHUB_PAT.
    
    Subprocess env behavior:
    - env=None → Inherits parent's environment (default)
    - env={} → Empty environment (no variables)
    - env=custom_dict → Only uses specified variables
    
    So this will work with gh authentication:
    # These are equivalent:
    result = subprocess.run(cmd, capture_output=True, text=True)
    result = subprocess.run(cmd, capture_output=True, text=True, env=None)
    
    But this will NOT work (no PATH, no auth):
    result = subprocess.run(cmd, capture_output=True, text=True, env={})
    """
    github_pat = os.getenv("GITHUB_PAT")
    if not github_pat:
        return None
    
    # Only create minimal env with GitHub token
    env = {
        "GH_TOKEN": github_pat,
        "PATH": os.environ.get("PATH", ""),
    }
    return env


def get_repo_url() -> str:
    """Get GitHub repository URL from git remote."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        raise ValueError(
            "No git remote 'origin' found. Please ensure you're in a git repository with a remote."
        )
    except FileNotFoundError:
        raise ValueError("git command not found. Please ensure git is installed.")


def extract_repo_path(github_url: str) -> str:
    """Extract owner/repo from GitHub URL."""
    # Handle both https://github.com/owner/repo and https://github.com/owner/repo.git
    return github_url.replace("https://github.com/", "").replace(".git", "")


def fetch_issue(issue_number: str, repo_path: str) -> GitHubIssue:
    """Fetch GitHub issue using gh CLI and return typed model."""
    # Use JSON output for structured data
    cmd = [
        "gh",
        "issue",
        "view",
        issue_number,
        "-R",
        repo_path,
        "--json",
        "number,title,body,state,author,assignees,labels,milestone,comments,createdAt,updatedAt,closedAt,url",
    ]

    # Set up environment with GitHub token if available
    env = get_github_env()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)

        if result.returncode == 0:
            # Parse JSON response into Pydantic model
            issue_data = json.loads(result.stdout)
            issue = GitHubIssue(**issue_data)

            return issue
        else:
            print(result.stderr, file=sys.stderr)
            sys.exit(result.returncode)
    except FileNotFoundError:
        print("Error: GitHub CLI (gh) is not installed.", file=sys.stderr)
        print("\nTo install gh:", file=sys.stderr)
        print("  - macOS: brew install gh", file=sys.stderr)
        print(
            "  - Linux: See https://github.com/cli/cli#installation",
            file=sys.stderr,
        )
        print(
            "  - Windows: See https://github.com/cli/cli#installation", file=sys.stderr
        )
        print("\nAfter installation, authenticate with: gh auth login", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing issue data: {e}", file=sys.stderr)
        sys.exit(1)


def _make_issue_comment_sync(issue_id: str, comment: str, repo_path: str, env: Optional[dict]) -> bool:
    """Internal sync implementation for posting a comment. Returns success status."""
    # Build command
    cmd = [
        "gh",
        "issue",
        "comment",
        issue_id,
        "-R",
        repo_path,
        "--body",
        comment,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)

        if result.returncode == 0:
            from cxc.core.utils import colorize_console_message, print_markdown
            print(colorize_console_message(f"Successfully posted comment to issue #{issue_id}"))
            cleaned = comment.strip()
            comment_len = len(cleaned)
            if comment_len > 500:
                print(colorize_console_message(f"Comment length: {comment_len} (panel)"))
                print_markdown(cleaned, title="GitHub comment", border_style="blue")
            else:
                print(colorize_console_message(f"Comment length: {comment_len} (inline)"))
                print(colorize_console_message(f"Comment body: {cleaned}"))
            return True
        else:
            print(f"Error posting comment: {result.stderr}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"Error posting comment: {e}", file=sys.stderr)
        return False


def make_issue_comment(issue_id: str, comment: str, blocking: bool = False) -> None:
    """Post a comment to a GitHub issue using gh CLI.
    
    By default runs as fire-and-forget (non-blocking) to speed up workflows.
    Set blocking=True if you need to wait for confirmation.
    
    Args:
        issue_id: GitHub issue number
        comment: Comment body
        blocking: If True, wait for comment to post; if False, fire-and-forget
    """
    if github_comments_disabled():
        print(f"Skipping GitHub comment for issue #{issue_id} (CXC_DISABLE_GITHUB_COMMENTS=1)")
        return

    # Get repo information from git remote
    github_repo_url = get_repo_url()
    repo_path = extract_repo_path(github_repo_url)

    # Ensure comment has CXC_BOT_IDENTIFIER to prevent webhook loops
    if not comment.startswith(CXC_BOT_IDENTIFIER):
        comment = f"{CXC_BOT_IDENTIFIER} {comment}"

    # Set up environment with GitHub token if available
    env = get_github_env()

    if blocking:
        # Synchronous - wait for result
        success = _make_issue_comment_sync(issue_id, comment, repo_path, env)
        if not success:
            raise RuntimeError(f"Failed to post comment to issue #{issue_id}")
    else:
        # Fire-and-forget - run in background thread
        thread = threading.Thread(
            target=_make_issue_comment_sync,
            args=(issue_id, comment, repo_path, env),
            daemon=True  # Don't prevent program exit
        )
        thread.start()
        from cxc.core.utils import colorize_console_message
        print(colorize_console_message(f"Posting comment to issue #{issue_id} (async)..."))


def mark_issue_in_progress(issue_id: str) -> None:
    """Mark issue as in progress by adding label and comment."""
    # Get repo information from git remote
    github_repo_url = get_repo_url()
    repo_path = extract_repo_path(github_repo_url)

    # Add "in_progress" label
    cmd = [
        "gh",
        "issue",
        "edit",
        issue_id,
        "-R",
        repo_path,
        "--add-label",
        "in_progress",
    ]

    # Set up environment with GitHub token if available
    env = get_github_env()

    # Try to add label (may fail if label doesn't exist)
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        print(f"Note: Could not add 'in_progress' label: {result.stderr}")

    # Post comment indicating work has started
    # make_issue_comment(issue_id, "🚧 CXC is working on this issue...")

    # Assign to self (optional)
    cmd = [
        "gh",
        "issue",
        "edit",
        issue_id,
        "-R",
        repo_path,
        "--add-assignee",
        "@me",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode == 0:
        print(f"Assigned issue #{issue_id} to self")


def fetch_open_issues(repo_path: str) -> List[GitHubIssueListItem]:
    """Fetch all open issues from the GitHub repository."""
    try:
        cmd = [
            "gh",
            "issue",
            "list",
            "--repo",
            repo_path,
            "--state",
            "open",
            "--json",
            "number,title,body,labels,createdAt,updatedAt",
            "--limit",
            "1000",
        ]

        # Set up environment with GitHub token if available
        env = get_github_env()

        # DEBUG level - not printing command
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, env=env
        )

        issues_data = json.loads(result.stdout)
        issues = [GitHubIssueListItem(**issue_data) for issue_data in issues_data]
        print(f"Fetched {len(issues)} open issues")
        return issues

    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to fetch issues: {e.stderr}", file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse issues JSON: {e}", file=sys.stderr)
        return []


def fetch_issue_comments(repo_path: str, issue_number: int) -> List[Dict]:
    """Fetch all comments for a specific issue."""
    try:
        cmd = [
            "gh",
            "issue",
            "view",
            str(issue_number),
            "--repo",
            repo_path,
            "--json",
            "comments",
        ]

        # Set up environment with GitHub token if available
        env = get_github_env()

        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, env=env
        )
        data = json.loads(result.stdout)
        comments = data.get("comments", [])

        # Sort comments by creation time
        comments.sort(key=lambda c: c.get("createdAt", ""))

        # DEBUG level - not printing
        return comments

    except subprocess.CalledProcessError as e:
        print(
            f"ERROR: Failed to fetch comments for issue #{issue_number}: {e.stderr}",
            file=sys.stderr,
        )
        return []
    except json.JSONDecodeError as e:
        print(
            f"ERROR: Failed to parse comments JSON for issue #{issue_number}: {e}",
            file=sys.stderr,
        )
        return []


def find_keyword_from_comment(keyword: str, issue: GitHubIssue) -> Optional[GitHubComment]:
    """Find the latest comment containing a specific keyword.

    Args:
        keyword: The keyword to search for in comments
        issue: The GitHub issue containing comments

    Returns:
        The latest GitHubComment containing the keyword, or None if not found
    """
    # Sort comments by created_at date (newest first)
    sorted_comments = sorted(issue.comments, key=lambda c: c.created_at, reverse=True)

    # Search through sorted comments (newest first)
    for comment in sorted_comments:
        # Skip CXC bot comments to prevent loops
        if CXC_BOT_IDENTIFIER in comment.body:
            continue

        if keyword in comment.body:
            return comment

    return None


def update_comment(comment_id: int, new_body: str, repo_path: Optional[str] = None) -> tuple[bool, Optional[str]]:
    """Update an existing GitHub issue comment using gh API.
    
    Args:
        comment_id: The comment ID to update
        new_body: New content for the comment
        repo_path: Repository path (org/repo). If None, will be detected from git remote.
        
    Returns:
        Tuple of (success, error_message)
    """
    if github_comments_disabled():
        print(f"Skipping GitHub comment update for comment #{comment_id} (CXC_DISABLE_GITHUB_COMMENTS=1)")
        return True, None
    
    if repo_path is None:
        github_repo_url = get_repo_url()
        repo_path = extract_repo_path(github_repo_url)
    
    # Ensure comment has CXC_BOT_IDENTIFIER to prevent webhook loops
    if not new_body.startswith(CXC_BOT_IDENTIFIER):
        new_body = f"{CXC_BOT_IDENTIFIER} {new_body}"
    
    # Use gh api to PATCH the comment
    cmd = [
        "gh", "api", "-X", "PATCH",
        f"/repos/{repo_path}/issues/comments/{comment_id}",
        "-f", f"body={new_body}"
    ]
    
    env = get_github_env()
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if result.returncode == 0:
            from cxc.core.utils import colorize_console_message
            print(colorize_console_message(f"Successfully updated comment #{comment_id}"))
            return True, None
        else:
            return False, result.stderr
    except Exception as e:
        return False, str(e)


def find_comment_id_by_pattern(issue_number: str, pattern: str, repo_path: Optional[str] = None) -> Optional[int]:
    """Find a comment ID by searching for a pattern in the comment body.
    
    Args:
        issue_number: GitHub issue number
        pattern: Pattern to search for (e.g., "[CXC-AGENTS] abc12345_plan")
        repo_path: Repository path (org/repo). If None, will be detected from git remote.
        
    Returns:
        Comment ID if found, None otherwise
    """
    if repo_path is None:
        github_repo_url = get_repo_url()
        repo_path = extract_repo_path(github_repo_url)
    
    # Use gh api to list comments and filter by pattern
    cmd = [
        "gh", "api",
        f"/repos/{repo_path}/issues/{issue_number}/comments",
        "--jq", f'.[] | select(.body | contains("{pattern}")) | .id'
    ]
    
    env = get_github_env()
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if result.returncode == 0 and result.stdout.strip():
            # Return the first (most recent) matching comment ID
            comment_ids = result.stdout.strip().split('\n')
            if comment_ids:
                return int(comment_ids[-1])  # Get the last (most recent) match
        return None
    except Exception:
        return None


def make_issue_comment_and_get_id(issue_id: str, comment: str) -> Optional[int]:
    """Post a comment to a GitHub issue and return the comment ID.
    
    Args:
        issue_id: GitHub issue number
        comment: Comment body
        
    Returns:
        Comment ID if successful, None if failed
    """
    if github_comments_disabled():
        print(f"Skipping GitHub comment for issue #{issue_id} (CXC_DISABLE_GITHUB_COMMENTS=1)")
        return None

    github_repo_url = get_repo_url()
    repo_path = extract_repo_path(github_repo_url)

    # Ensure comment has CXC_BOT_IDENTIFIER to prevent webhook loops
    if not comment.startswith(CXC_BOT_IDENTIFIER):
        comment = f"{CXC_BOT_IDENTIFIER} {comment}"

    # Use gh api to create comment and get the ID back
    cmd = [
        "gh", "api", "-X", "POST",
        f"/repos/{repo_path}/issues/{issue_id}/comments",
        "-f", f"body={comment}",
        "--jq", ".id"
    ]

    env = get_github_env()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if result.returncode == 0:
            from cxc.core.utils import colorize_console_message
            comment_id = int(result.stdout.strip())
            print(colorize_console_message(f"Successfully posted comment #{comment_id} to issue #{issue_id}"))
            return comment_id
        else:
            print(f"Error posting comment: {result.stderr}", file=sys.stderr)
            return None
    except Exception as e:
        print(f"Error posting comment: {e}", file=sys.stderr)
        return None


def approve_pr(pr_number: str, repo_path: str) -> tuple[bool, Optional[str]]:
    """Approve a pull request using gh CLI.

    Args:
        pr_number: The PR number to approve
        repo_path: Repository path (org/repo)

    Returns:
        Tuple of (success, error_message)
    """
    cmd = [
        "gh", "pr", "review", pr_number,
        "-R", repo_path,
        "--approve",
        "--body", f"{CXC_BOT_IDENTIFIER} ✅ Approved by CXC Ship workflow"
    ]

    env = get_github_env()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if result.returncode == 0:
            print(f"Successfully approved PR #{pr_number}")
            return True, None
        else:
            return False, result.stderr
    except Exception as e:
        return False, str(e)


def close_issue(issue_number: str, repo_path: Optional[str] = None) -> tuple[bool, Optional[str]]:
    """Close a GitHub issue using gh CLI.

    Args:
        issue_number: The issue number to close
        repo_path: Repository path (org/repo). If None, will be detected from git remote.

    Returns:
        Tuple of (success, error_message)
    """
    if repo_path is None:
        github_repo_url = get_repo_url()
        repo_path = extract_repo_path(github_repo_url)

    cmd = [
        "gh", "issue", "close", issue_number,
        "-R", repo_path,
        "--comment", f"{CXC_BOT_IDENTIFIER} 🎉 Closed by CXC Ship workflow - code shipped to production!"
    ]

    env = get_github_env()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if result.returncode == 0:
            print(f"Successfully closed issue #{issue_number}")
            return True, None
        else:
            return False, result.stderr
    except Exception as e:
        return False, str(e)
