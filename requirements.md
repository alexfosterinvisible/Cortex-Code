Terminal And GitHub Logging Requirements

Scope: console output, live Claude Code streaming, and GitHub comment logging.

1) Phase Titles
- All "=== ISOLATED ... PHASE ===" banners render as rich titles, not panels.
- Phase titles are bold red text.

2) Live Claude Code Streaming
- On each Claude Code subprocess, print: "Claude model: <model> | Prompt: <prompt>" in orange.
- Live assistant messages are plain console prints (no panels).
- Live result messages are rich panels (green border).
- Live assistant messages are truncated to 1000 characters and suffixed with "...(truncated)".
- The "[assistant]" prefix is orange; the rest of the line follows normal coloring.

3) Artifact Printing
- Rich markdown artifacts (plans, reports, etc.) render in terminal as full markdown.
- The same markdown is posted to GitHub via issue comments.

4) GitHub Comment Logging
- When a comment is posted:
  - If the comment body length is >500 chars, render it as a rich markdown panel.
  - If <=500 chars, render inline as a single line.
- Print a debug line showing comment length and whether it was panel or inline.

5) Console Color Rules
- Message types are colorized by content:
  - "[assistant]" prefix is orange.
  - "[result]" is green.
  - GitHub interactions are blue.
  - Warnings/errors follow standard yellow/red rules.
- Low-signal operational lines (e.g., "Using ...", "Allocated ports ...") are dimmed.

6) Opt-Out
- When NO_COLOR is set, all ANSI color output is disabled.
