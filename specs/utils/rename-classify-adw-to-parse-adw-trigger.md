# Chore: Rename classify_cxc → parse_cxc_trigger

## Metadata
issue_number: `N/A`
cxc_id: `N/A`
type: `chore/refactor`

## Problem Statement

The current naming of `classify_cxc` is confusing because:
- `classify_issue` → classifies issues into `/bug`, `/feature`, `/chore` (clear!)
- `classify_cxc` → extracts command+id+model_set from free-form text (confusing!)

The name "classify" implies categorization, but this command actually **parses/extracts** structured data from natural language text.

## Current State

| Component | Location | Purpose |
|-----------|----------|---------|
| `/classify_cxc` | `commands/classify_cxc.md` | Slash command template that parses text |
| `extract_cxc_info()` | `cxc/integrations/workflow_ops.py:61-109` | Python wrapper that calls the command |
| `CxCExtractionResult` | `cxc/core/data_types.py:278-289` | Return type dataclass |

## User Stories / Flows

### Flow 1: GitHub Webhook Trigger (Primary Use)

```
User comments on GitHub issue:
  "cxc_plan_iso" or "run cxc_sdlc_iso model_set heavy"
        ↓
trigger_webhook.py receives webhook
        ↓
Checks if "cxc_" in text
        ↓
extract_cxc_info(comment_body, temp_id)
        ↓
Claude parses text → returns {command, cxc_id?, model_set}
        ↓
Launches workflow subprocess
```

### Flow 2: Resume/Continue Workflows

```
User comments: "cxc_build_iso abc12345"
        ↓
extract_cxc_info detects BOTH:
  - workflow: cxc_build_iso
  - cxc_id: abc12345
        ↓
Loads existing worktree/state
        ↓
Continues from where it left off
```

## Solution Statement

Rename for clarity:

| Current | Proposed |
|---------|----------|
| `/classify_cxc` | `/parse_cxc_trigger` |
| `extract_cxc_info()` | `parse_cxc_trigger_text()` |

## Relevant Files

Files that need modification:

- `commands/classify_cxc.md` → rename to `commands/parse_cxc_trigger.md`
- `cxc/integrations/workflow_ops.py` - rename `extract_cxc_info` function
- `cxc/triggers/trigger_webhook.py` - update import and function call
- `cxc/core/data_types.py` - update `SlashCommand` literal (line 54)
- `commands/_command_index.yaml` - update command entry
- `tests/unit/test_workflow_ops.py` - update test class/function names
- `docs/REFACTOR_REPORT.md` - has old function references (documentation)

## Step by Step Tasks

### Step 1: Rename slash command file
- Rename `commands/classify_cxc.md` → `commands/parse_cxc_trigger.md`
- Update header from "CxC Workflow Extraction" to "Parse CxC Trigger"

### Step 2: Update data_types.py
- Change `/classify_cxc` to `/parse_cxc_trigger` in `SlashCommand` literal

### Step 3: Update workflow_ops.py
- Rename function `extract_cxc_info` → `parse_cxc_trigger_text`
- Update docstring
- Update internal reference to `/classify_cxc` → `/parse_cxc_trigger`

### Step 4: Update trigger_webhook.py
- Update import: `from cxc.integrations.workflow_ops import parse_cxc_trigger_text`
- Update function calls

### Step 5: Update command index
- Update `commands/_command_index.yaml` entry

### Step 6: Update tests
- Rename test class `TestExtractCxcInfo` → `TestParseCxcTriggerText`
- Update test function names

### Step 7: Run validation

## Validation Commands

```bash
# Grep for old names (should return nothing after refactor)
rg "classify_cxc" --type py --type md
rg "extract_cxc_info" --type py

# Run tests
uv run pytest tests/unit/test_workflow_ops.py -v

# Run full test suite
uv run pytest -m unit
```

## Acceptance Criteria

- [ ] No references to `classify_cxc` remain in codebase
- [ ] No references to `extract_cxc_info` remain in codebase  
- [ ] All tests pass
- [ ] Webhook trigger still works (manual test with GitHub comment)

## Notes

- This is a pure rename refactor, no behavior change
- Low risk change
- Improves code clarity for new contributors

