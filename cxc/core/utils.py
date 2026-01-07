"""Utility functions for CXC system."""

import json
import logging
import os
import re
import sys
import time
import threading
import uuid
from typing import Any, TypeVar, Type, Union, Dict, Optional

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.theme import Theme
from rich.text import Text

T = TypeVar('T')

# ----- Rich Console for Terminal Output -----

# ----- Console Styling (ANSI) -----

_COLOR_RESET = "\x1b[0m"
_COLOR_DIM = "\x1b[2m"
_COLOR_BLUE = "\x1b[34m"
_COLOR_CYAN = "\x1b[36m"
_COLOR_GREEN = "\x1b[32m"
_COLOR_YELLOW = "\x1b[33m"
_COLOR_MAGENTA = "\x1b[35m"
_COLOR_RED = "\x1b[31m"
_COLOR_ORANGE = "\x1b[38;5;208m"

_HIGHLIGHT_RULES = [
    (re.compile(r"^Claude model:", re.IGNORECASE), _COLOR_YELLOW),
    (re.compile(r"\[assistant\]", re.IGNORECASE), _COLOR_CYAN),
    (re.compile(r"\[result\]", re.IGNORECASE), _COLOR_GREEN),
    (re.compile(r"\bcomment to issue\b", re.IGNORECASE), _COLOR_BLUE),
    (re.compile(r"\bissue #\d+\b", re.IGNORECASE), _COLOR_BLUE),
    (re.compile(r"\bgithub\b", re.IGNORECASE), _COLOR_BLUE),
]

_DIM_RULES = [
    re.compile(r"^Using\b"),
    re.compile(r"^Found existing state\b"),
    re.compile(r"^State:\s*$"),
    re.compile(r"^Log file:\s"),
    re.compile(r"^Running:\s"),
    re.compile(r"^Allocated ports\b"),
    re.compile(r"^Creating worktree\b"),
    re.compile(r"^Created worktree\b"),
    re.compile(r"^Created \.ports\.env\b"),
    re.compile(r"^Setting up\b"),
    re.compile(r"^Working directory:\s"),
]


def _supports_color(stream: Any) -> bool:
    if os.getenv("NO_COLOR"):
        return False
    return hasattr(stream, "isatty") and stream.isatty()


def _apply_console_style(message: str, level: int = logging.INFO) -> str:
    if not _supports_color(sys.stdout):
        return message

    style = ""
    if level >= logging.ERROR:
        style = _COLOR_RED
    elif level >= logging.WARNING:
        style = _COLOR_YELLOW
    else:
        for pattern, color in _HIGHLIGHT_RULES:
            if pattern.search(message):
                style = color
                break
        if not style and any(rule.search(message) for rule in _DIM_RULES):
            style = _COLOR_DIM

    if not style:
        return message
    return f"{style}{message}{_COLOR_RESET}"


def colorize_console_message(message: str) -> str:
    """Apply console styling rules to a plain message."""
    return _apply_console_style(message, logging.INFO)


def colorize_assistant_prefix(message: str) -> str:
    """Color only the [assistant] prefix in a message."""
    if not _supports_color(sys.stdout):
        return message
    if "[assistant]" not in message:
        return message
    return message.replace(
        "[assistant]",
        f"{_COLOR_ORANGE}[assistant]{_COLOR_RESET}",
        1,
    )


def truncate_text(text: str, max_len: int, suffix: str = "...(truncated)") -> str:
    """Trim text to max_len characters with a suffix when truncated."""
    cleaned = text.strip()
    if len(cleaned) <= max_len:
        return cleaned
    return f"{cleaned[:max_len].rstrip()}{suffix}"


class _ColorizingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        return _apply_console_style(message, record.levelno)

# Custom theme for CXC markdown output
CXC_THEME = Theme({
    "markdown.h1": "bold cyan",
    "markdown.h2": "bold blue",
    "markdown.h3": "bold magenta",
    "markdown.code": "green on black",
    "markdown.item.bullet": "yellow",
})

_console = Console(theme=CXC_THEME, force_terminal=True)


# ----- Ephemeral Wait Timer -----

class WaitTimer:
    """Ephemeral timer that shows elapsed seconds while waiting, clears on output."""
    
    _instance: Optional["WaitTimer"] = None
    
    def __init__(self):
        self._start_time = time.time()
        self._live: Optional[Live] = None
        self._running = False
        self._lock = threading.Lock()
    
    @classmethod
    def get(cls) -> "WaitTimer":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _render(self) -> Text:
        elapsed = int(time.time() - self._start_time)
        return Text(f"  ⏱ {elapsed}s waiting...", style="dim")
    
    def start(self) -> None:
        """Start the live timer display."""
        with self._lock:
            if self._running:
                return
            self._start_time = time.time()
            self._running = True
            try:
                self._live = Live(
                    self._render(),
                    console=_console,
                    refresh_per_second=1,
                    transient=True,  # Clears when stopped
                )
                self._live.start()
                # Start background update thread
                threading.Thread(target=self._update_loop, daemon=True).start()
            except Exception:
                self._running = False
    
    def _update_loop(self) -> None:
        """Background thread to update the timer display."""
        while self._running and self._live:
            try:
                time.sleep(1)
                if self._running and self._live:
                    self._live.update(self._render())
            except Exception:
                break
    
    def stop(self) -> None:
        """Stop and clear the timer (call before printing)."""
        with self._lock:
            self._running = False
            if self._live:
                try:
                    self._live.stop()
                except Exception:
                    pass
                self._live = None
    
    def reset(self) -> None:
        """Stop current timer and start fresh."""
        self.stop()
        self.start()


def wait_timer_start() -> None:
    """Start the global wait timer."""
    WaitTimer.get().start()


def wait_timer_stop() -> None:
    """Stop the global wait timer (call before printing)."""
    WaitTimer.get().stop()


def make_cxc_id() -> str:
    """Generate a short 8-character UUID for CXC tracking."""
    return str(uuid.uuid4())[:8]


def setup_logger(cxc_id: str, trigger_type: str = "cxc_plan_build") -> logging.Logger:
    """Set up logger that writes to both console and file using cxc_id.
    
    Args:
        cxc_id: The CXC workflow ID
        trigger_type: Type of trigger (cxc_plan_build, trigger_webhook, etc.)
    
    Returns:
        Configured logger instance
    """
    # Import here to avoid circular imports
    from .config import CxcConfig
    
    # Create log directory using config
    config = CxcConfig.load()
    log_dir = config.get_agents_dir(cxc_id) / trigger_type
    os.makedirs(log_dir, exist_ok=True)
    
    # Log file path: {artifacts_dir}/{project_id}/{cxc_id}/{trigger_type}/execution.log
    log_file = str(log_dir / "execution.log")
    
    # Create logger with unique name using cxc_id
    logger = logging.getLogger(f"cxc_{cxc_id}")
    logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # File handler - captures everything
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler - INFO and above
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Format with timestamp for file
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Simpler format for console (similar to current print statements)
    console_formatter = _ColorizingFormatter('%(message)s')
    
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Log initial setup message
    logger.info(f"CXC Logger initialized - ID: {cxc_id}")
    logger.debug(f"Log file: {log_file}")
    
    return logger


def get_logger(cxc_id: str) -> logging.Logger:
    """Get existing logger by CXC ID.
    
    Args:
        cxc_id: The CXC workflow ID
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"cxc_{cxc_id}")


def parse_json(text: str, target_type: Type[T] = None) -> Union[T, Any]:
    """Parse JSON that may be wrapped in markdown code blocks.
    
    Handles various formats:
    - Raw JSON
    - JSON wrapped in ```json ... ```
    - JSON wrapped in ``` ... ```
    - JSON with extra whitespace or newlines
    
    Args:
        text: String containing JSON, possibly wrapped in markdown
        target_type: Optional type to validate/parse the result into (e.g., List[TestResult])
        
    Returns:
        Parsed JSON object, optionally validated as target_type
        
    Raises:
        ValueError: If JSON cannot be parsed from the text
    """
    # Try to extract JSON from markdown code blocks
    # Pattern matches ```json\n...\n``` or ```\n...\n```
    code_block_pattern = r'```(?:json)?\s*\n(.*?)\n```'
    match = re.search(code_block_pattern, text, re.DOTALL)
    
    if match:
        json_str = match.group(1).strip()
    else:
        # No code block found, try to parse the entire text
        json_str = text.strip()
    
    # Try to find JSON array or object boundaries if not already clean
    if not (json_str.startswith('[') or json_str.startswith('{')):
        # Look for JSON array
        array_start = json_str.find('[')
        array_end = json_str.rfind(']')
        
        # Look for JSON object
        obj_start = json_str.find('{')
        obj_end = json_str.rfind('}')
        
        # Determine which comes first and extract accordingly
        if array_start != -1 and (obj_start == -1 or array_start < obj_start):
            if array_end != -1:
                json_str = json_str[array_start:array_end + 1]
        elif obj_start != -1:
            if obj_end != -1:
                json_str = json_str[obj_start:obj_end + 1]
    
    try:
        result = json.loads(json_str)
        
        # If target_type is provided and has from_dict/parse_obj/model_validate methods (Pydantic)
        if target_type and hasattr(target_type, '__origin__'):
            # Handle List[SomeType] case
            if target_type.__origin__ is list:
                item_type = target_type.__args__[0]
                # Try Pydantic v2 first, then v1
                if hasattr(item_type, 'model_validate'):
                    result = [item_type.model_validate(item) for item in result]
                elif hasattr(item_type, 'parse_obj'):
                    result = [item_type.parse_obj(item) for item in result]
        elif target_type:
            # Handle single Pydantic model
            if hasattr(target_type, 'model_validate'):
                result = target_type.model_validate(result)
            elif hasattr(target_type, 'parse_obj'):
                result = target_type.parse_obj(result)
            
        return result
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON: {e}. Text was: {json_str}")


def check_env_vars(logger: Optional[logging.Logger] = None) -> None:
    """Check that all required environment variables are set.
    
    Args:
        logger: Optional logger instance for error reporting
        
    Raises:
        SystemExit: If required environment variables are missing
    """
    required_vars = [
        "ANTHROPIC_API_KEY",
        "CLAUDE_CODE_PATH",
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        error_msg = "Error: Missing required environment variables:"
        if logger:
            logger.error(error_msg)
            for var in missing_vars:
                logger.error(f"  - {var}")
        else:
            print(error_msg, file=sys.stderr)
            for var in missing_vars:
                print(f"  - {var}", file=sys.stderr)
        sys.exit(1)


def get_safe_subprocess_env() -> Dict[str, str]:
    """Get filtered environment variables safe for subprocess execution.
    
    Returns only the environment variables needed for CXC workflows based on
    .env.sample configuration. This prevents accidental exposure of sensitive
    credentials to subprocesses.
    
    Returns:
        Dictionary containing only required environment variables
    """
    safe_env_vars = {
        # Anthropic Configuration (required)
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        
        # GitHub Configuration (optional)
        # GITHUB_PAT is optional - if not set, will use default gh auth
        "GITHUB_PAT": os.getenv("GITHUB_PAT"),
        
        # Claude Code Configuration
        "CLAUDE_CODE_PATH": os.getenv("CLAUDE_CODE_PATH", "claude"),
        "CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR": os.getenv(
            "CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR", "true"
        ),
        
        # Agent Cloud Sandbox Environment (optional)
        "E2B_API_KEY": os.getenv("E2B_API_KEY"),
        
        # Cloudflare tunnel token (optional)
        "CLOUDFLARED_TUNNEL_TOKEN": os.getenv("CLOUDFLARED_TUNNEL_TOKEN"),
        
        # Essential system environment variables
        "HOME": os.getenv("HOME"),
        "USER": os.getenv("USER"),
        "PATH": os.getenv("PATH"),
        "SHELL": os.getenv("SHELL"),
        "TERM": os.getenv("TERM"),
        "LANG": os.getenv("LANG"),
        "LC_ALL": os.getenv("LC_ALL"),
        
        # Python-specific variables that subprocesses might need
        "PYTHONPATH": os.getenv("PYTHONPATH"),
        "PYTHONUNBUFFERED": "1",  # Useful for subprocess output
        
        # Working directory tracking
        "PWD": os.getcwd(),
    }
    
    # Add GH_TOKEN as alias for GITHUB_PAT if it exists
    github_pat = os.getenv("GITHUB_PAT")
    if github_pat:
        safe_env_vars["GH_TOKEN"] = github_pat
    
    # Filter out None values
    return {k: v for k, v in safe_env_vars.items() if v is not None}


# ----- Rich Markdown Terminal Printing -----

def print_markdown(
    content: str,
    title: Optional[str] = None,
    border_style: str = "cyan",
    file_path: Optional[str] = None,
) -> None:
    """Print markdown content with rich formatting to terminal.
    
    Args:
        content: Markdown content to print
        title: Optional title for panel header
        border_style: Rich style for panel border (default: cyan)
        file_path: Optional file path to show in subtitle
    """
    if not content or not content.strip():
        return
    
    md = Markdown(content)
    
    # Build subtitle if file_path provided
    subtitle = f"📄 {file_path}" if file_path else None
    
    if title:
        panel = Panel(
            md,
            title=title,
            subtitle=subtitle,
            border_style=border_style,
            expand=False,
            padding=(1, 2),
        )
        _console.print(panel)
    else:
        _console.print(md)
    
    # Add spacing after
    _console.print()


def print_phase_title(title: str) -> None:
    """Print a phase title in red without a panel."""
    if not title or not title.strip():
        return
    _console.print()
    _console.print(Text(title.strip(), style="bold red"))


def print_artifact(
    title: str,
    content: str,
    file_path: Optional[str] = None,
    border_style: str = "cyan",
) -> None:
    """Print an artifact (plan, report, etc.) with rich markdown formatting.
    
    Convenience wrapper around print_markdown specifically for artifacts.
    
    Args:
        title: Artifact title (e.g., "📋 Implementation Plan")
        content: The artifact markdown content
        file_path: Optional path to the artifact file
        border_style: Rich style for panel border
    """
    print_markdown(content, title=title, border_style=border_style, file_path=file_path)


def print_state_json(
    state_data: dict,
    title: str = "📋 State",
) -> None:
    """Print workflow state as formatted JSON to terminal.
    
    Args:
        state_data: The state dictionary to print
        title: Title for the panel
    """
    state_json = json.dumps(state_data, indent=2, default=str)
    
    # Wrap JSON in code block for markdown rendering
    md_content = f"```json\n{state_json}\n```"
    print_markdown(md_content, title=title, border_style="blue")


def print_agent_log(cxc_id: str, agent_name: str, tail_lines: int = 30) -> None:
    """Print the last N lines of an agent's JSONL log file.
    
    Extracts and displays assistant messages and results from the log.
    
    Args:
        cxc_id: The CXC workflow ID
        agent_name: Name of the agent (e.g., "classify_and_branch")
        tail_lines: Number of JSONL entries to read from end (default 30)
    """
    from .config import CxcConfig
    
    config = CxcConfig.load()
    log_file = config.get_agents_dir(cxc_id) / agent_name / "raw_output.jsonl"
    
    if not log_file.exists():
        print(f"{_COLOR_RED}Agent log not found: {log_file}{_COLOR_RESET}")
        return
    
    print(f"\n{_COLOR_CYAN}═══ Agent Log: {agent_name} ({log_file}) ═══{_COLOR_RESET}\n")
    
    try:
        with open(log_file, "r") as f:
            lines = f.readlines()
        
        # Take last N lines
        recent_lines = lines[-tail_lines:] if len(lines) > tail_lines else lines
        
        for line in recent_lines:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                msg_type = data.get("type", "")
                
                if msg_type == "assistant":
                    # Extract text from assistant message
                    content = data.get("message", {}).get("content", [])
                    if isinstance(content, list):
                        text = "".join(
                            part.get("text", "") for part in content if isinstance(part, dict)
                        )
                        if text.strip():
                            print(f"{_COLOR_BLUE}[assistant]{_COLOR_RESET} {truncate_text(text, 1000)}")
                
                elif msg_type == "result":
                    result_text = data.get("result", "")
                    is_error = data.get("is_error", False)
                    subtype = data.get("subtype", "")
                    
                    # Show empty result explicitly
                    if not result_text:
                        result_text = "(empty)"
                    
                    if is_error:
                        print(f"{_COLOR_RED}[result:error]{_COLOR_RESET} {result_text}")
                    elif subtype:
                        print(f"{_COLOR_YELLOW}[result:{subtype}]{_COLOR_RESET} {result_text}")
                    else:
                        print(f"{_COLOR_GREEN}[result]{_COLOR_RESET} {result_text}")
                
                elif msg_type == "error":
                    error_text = data.get("error", {}).get("message", str(data))
                    print(f"{_COLOR_RED}[error]{_COLOR_RESET} {error_text}")
                
                elif msg_type == "system":
                    system_text = data.get("message", "") or data.get("system", "")
                    if system_text:
                        print(f"{_COLOR_MAGENTA}[system]{_COLOR_RESET} {system_text}")
                
                elif msg_type == "user":
                    # Show user/prompt message
                    content = data.get("message", {}).get("content", "")
                    if isinstance(content, str) and content:
                        # Show first 300 chars of prompt
                        print(f"{_COLOR_DIM}[user/prompt]{_COLOR_RESET} {content[:300]}...")
                    
            except json.JSONDecodeError:
                # Print raw line if not valid JSON
                print(f"{_COLOR_DIM}{line[:200]}{_COLOR_RESET}")
        
        print(f"\n{_COLOR_CYAN}═══ End Agent Log ═══{_COLOR_RESET}\n")
        
    except Exception as e:
        print(f"{_COLOR_RED}Failed to read agent log: {e}{_COLOR_RESET}")
