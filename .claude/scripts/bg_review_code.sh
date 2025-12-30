#!/bin/bash
# bg_review_code.sh - Run Claude code review as background process
# Usage: ./bg_review_code.sh [spec_file]
#
# WHY: Saves context window by running claude -p directly
# HOW: --dangerously-skip-permissions skips approval prompts

set -euo pipefail

OUTDIR="${PWD}/.tmp"
mkdir -p "$OUTDIR"

OUTFILE="${OUTDIR}/review_$(date +%Y%m%d_%H%M%S).json"
CMD_FILE="${PWD}/commands/review_code.md"
SPEC_FILE="${1:-}"

# Check command file exists
if [[ ! -f "$CMD_FILE" ]]; then
    echo "❌ Missing: $CMD_FILE"
    exit 1
fi

echo "🚀 Starting background code review..."
echo "📄 Output: $OUTFILE"
echo "📋 Command: $CMD_FILE"
[[ -n "$SPEC_FILE" ]] && echo "📝 Spec: $SPEC_FILE"

# Build prompt with optional spec file
PROMPT="$(cat "$CMD_FILE")"
[[ -n "$SPEC_FILE" ]] && PROMPT="$PROMPT

spec_file: $SPEC_FILE"

nohup claude -p "$PROMPT" \
    --dangerously-skip-permissions \
    --output-format json \
    > "$OUTFILE" 2>&1 &

PID=$!
echo "✅ Background PID: $PID"
echo "📊 Monitor: tail -f $OUTFILE"
echo ""
echo "🛑 Kill if needed: kill $PID"


