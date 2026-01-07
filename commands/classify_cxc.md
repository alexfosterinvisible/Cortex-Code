# CxC Workflow Extraction

Extract CxC workflow information from the text below and return a JSON response.

## INSTRUCTIONS

- Look for CxC workflow commands in the text (e.g., `/cxc_plan_iso`, `/cxc_build_iso`, `/cxc_test_iso`, `/cxc_review_iso`, `/cxc_document_iso`, `/cxc_patch_iso`, `/cxc_plan_build_iso`, `/cxc_plan_build_test_iso`, `/cxc_plan_build_test_review_iso`, `/cxc_sdlc_iso`, `/cxc_sdlc_ZTE_iso`)
- Also recognize commands without the `_iso` suffix and automatically add it (e.g., `/cxc_plan` → `/cxc_plan_iso`)
- Also recognize variations like `cxc_plan_build`, `cxc plan build`, `/cxc plan then build`, etc. and map to the correct command
- Look for CxC IDs (8-character alphanumeric strings, often after "cxc_id:" or "CxC ID:" or similar)
- Look for model set specification: "model_set base" or "model_set heavy" (case insensitive)
  - Default to "base" if no model_set is specified
  - Also recognize variations like "model set: heavy", "modelset heavy", etc.
- Return a JSON object with the extracted information
- If no CxC workflow is found, return empty JSON: `{}`
- IMPORTANT: DO NOT RUN the `cxc_sdlc_ZTE_iso` workflows unless `ZTE` is EXPLICITLY uppercased. This is a dangerous workflow and it needs to be absolutely clear when we're running it. If zte is not capitalized, then run the non zte version `/cxc_sdlc_iso`.

## VALID_CxC_COMMANDS

- `/cxc_plan_iso` - Planning only
- `/cxc_build_iso` - Building only (requires cxc_id)
- `/cxc_test_iso` - Testing only (requires cxc_id)
- `/cxc_review_iso` - Review only (requires cxc_id)
- `/cxc_document_iso` - Documentation only (requires cxc_id)
- `/cxc_ship_iso` - Ship/approve and merge PR (requires cxc_id)
- `/cxc_patch_iso` - Direct patch from issue
- `/cxc_plan_build_iso` - Plan + Build
- `/cxc_plan_build_test_iso` - Plan + Build + Test
- `/cxc_plan_build_review_iso` - Plan + Build + Review (skips test)
- `/cxc_plan_build_document_iso` - Plan + Build + Document (skips test and review)
- `/cxc_plan_build_test_review_iso` - Plan + Build + Test + Review
- `/cxc_sdlc_iso` - Complete SDLC: Plan + Build + Test + Review + Document
- `/cxc_sdlc_zte_iso` - Zero Touch Execution: Complete SDLC + auto-merge to production. Note: as per instructions, 'ZTE' must be capitalized. Do not run this if 'zte' is not capitalized.

## RESPONSE_FORMAT

Respond ONLY with a JSON object in this format:
```json
{
  "cxc_slash_command": "/cxc_plan",
  "cxc_id": "abc12345",
  "model_set": "base"
}
```

Fields:
- `cxc_slash_command`: The CxC command found (include the slash)
- `cxc_id`: The 8-character CxC ID if found
- `model_set`: The model set to use ("base" or "heavy"), defaults to "base" if not specified

If only some fields are found, include only those fields.
If nothing is found, return: `{}`
IMPORTANT: Always include `model_set` with value "base" if no model_set is explicitly mentioned in the text.

## TEXT_TO_ANALYZE

$ARGUMENTS