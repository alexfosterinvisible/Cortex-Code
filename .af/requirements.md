# CxC Command Formatting Requirements

## Verbatim Instruction (as requested)

@commands/feature.md:14 in all commands, replace filepaths or filenames with [] instead of inline code. Also - for any references to sections WITHIN that command, please update them to be like this: @commands/feature.md:3 . `## (include header#s for clear Pointer to md heading) CAPITAL_LETTERS_WITH_UNDERSCORES` (see below (if below in same commandm also clear flags WITHIN that file, not external).

## Scope

These formatting rules apply **only** to prompts and command files (e.g. command templates under [commands/], and command/prompt text). They do **not** apply to specs, docs, READMEs, or source code unless explicitly requested.

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

