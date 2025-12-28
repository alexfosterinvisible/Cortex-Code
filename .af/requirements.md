# ADW Command Formatting Requirements

## Filepaths and Filenames

Replace filepaths or filenames with `[]` instead of inline code.

**Example:**
- ❌ `specs/` directory
- ✅ [specs/] directory

## Internal Section References

For any references to sections WITHIN that command, use the format:

`## (include header#s for clear Pointer to md heading) CAPITAL_LETTERS_WITH_UNDERSCORES` (see below)

This applies when:
- Referencing a section below in the same command file
- The flag "(see below)" indicates it's within that file, not external

**Example:**
- ❌ Follow the `Instructions` to create the plan
- ✅ Follow the `## INSTRUCTIONS` (see below) to create the plan

