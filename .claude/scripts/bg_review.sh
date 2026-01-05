#!/bin/bash
# bg_review.sh - Run Claude review as background process
# Usage: ./bg_review.sh [spec_file]
#
# WHY: Saves context window by running claude -p directly
# HOW: --dangerously-skip-permissions skips approval prompts,
#      background process doesn't block terminal

set -euo pipefail

OUTDIR="${PWD}/.tmp"
mkdir -p "$OUTDIR"

OUTFILE="${OUTDIR}/review_$(date +%Y%m%d_%H%M%S).json"
CMD_FILE="${PWD}/commands/review.md"

# Check command file exists
if [[ ! -f "$CMD_FILE" ]]; then
    echo "❌ Missing: $CMD_FILE"
    exit 1
fi

echo "🚀 Starting background review..."
echo "📄 Output: $OUTFILE"

nohup claude -p "$(cat "$CMD_FILE")" \
    --dangerously-skip-permissions \
    --output-format json \
    > "$OUTFILE" 2>&1 &

PID=$!
echo "✅ Background PID: $PID"
echo "📊 Monitor: tail -f $OUTFILE"






