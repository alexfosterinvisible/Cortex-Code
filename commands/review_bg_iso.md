# Review Background (Isolated)

Runs the review command as a background process using `claude -p --dangerously-skip-permissions`.

## Usage

```bash
./.claude/scripts/bg_review.sh
```

## Why

- Saves context window by running claude -p directly (not through Cursor)
- `--dangerously-skip-permissions` skips approval prompts
- Background process doesn't block terminal
- Output captured to [.tmp/review_*.json]

## Execute

Run the script now:

```bash
./.claude/scripts/bg_review.sh
```

