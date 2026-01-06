# ADW Reference UI – Requirements

> Single-page HTML reference and management UI for ADW Framework.
> File: `apps/ui/index.html`

---

## R1: Design System (Invisible Technologies Theme)

### R1.1: Colors ☑️✅
- White: `#ffffff`
- Carbon Black: `#0f0f0f`
- Primary brand: `#dcf58f` (lime green with 050-950 palette)
- Borders/dividers: zinc-200
- Text: zinc color palette (50-950)

### R1.2: Typography ☑️✅
- Headlines/Body: Inter (system font fallback)
- Buttons/Callouts: Roboto Mono
- Normal weight for most text, bold for h3/h4

### R1.3: Border Radius ☑️✅
- Buttons: `rounded` (0.25rem)
- Containers: `rounded-md` (0.375rem) / `rounded-lg` (0.5rem)

### R1.4: Shadows ☑️✅
- Restricted - only hover states and select instances

---

## R2: Navigation & Layout

### R2.1: Header ☑️✅
- Fixed logo with "ADW" icon badge
- Tab navigation (horizontal, scrollable on mobile)

### R2.2: Tabs ☑️✅
- **Management tabs**: Issues, Pull Requests, Active Workflows
- **Reference tabs**: Prompts, Workflows, CLI, Data Types, Config

### R2.3: Responsive Design ☑️✅
- Breakpoints: 1200px, 1024px, 768px, 480px
- Tabs: horizontal scroll with hidden scrollbar on mobile
- Cards: single column on mobile
- Tables: horizontal scroll wrapper
- Modals: 95% width on mobile

---

## R3: Issues Tab

### R3.1: Stats Dashboard ☑️✅
- Open, In Progress, Closed, Total counts
- Grid adapts from 4-col → 2-col on mobile

### R3.2: Issue List ☑️✅
- Card-based list with selection state
- Search input with icon
- Filter tabs: All / Open / In Progress / Closed

### R3.3: Issue CRUD ☑️✅
- **Create**: Modal with title, description, type, labels
- **Read**: Detail panel with full info
- **Update**: Edit modal with title, description, status
- **Delete**: Confirmation dialog

### R3.4: Issue Type (ADW Classification) ☑️✅
- Types match ADW slash commands: `/feature`, `/bug`, `/chore`
- Type selector shows ADW command mapping

### R3.5: Labels Display ☑️✅
- Minimal #tag style (no pills, no colors)
- Dimmed text (zinc-400) to show less importance
- Small font (0.6875rem)
- Prefix with `#` character

### R3.6: Comments ☑️✅
- Comment list with author and timestamp
- ADW Bot comments styled differently (lime border)
- Add comment textarea + submit button

### R3.7: Workflow Triggers ☑️✅
- Quick buttons: Plan, Full SDLC, Patch
- Trigger modal with:
  - Workflow type selector (plan, build, test, sdlc, zte)
  - Model set selector (base/heavy)
  - Options (skip-e2e checkbox)

---

## R4: Pull Requests Tab

### R4.1: PR List ☑️✅
- Card-based list with status badges (Open/Merged/Closed)
- Branch name, change stats (+/-), file count, timestamp
- Filter tabs: All / Open / Merged / Closed

### R4.2: PR Detail ☑️✅
- Linked issue with clickable navigation
- ADW metadata (ADW ID, plan file path)
- Change summary (+additions -deletions in N files)
- Actions: Merge, Request Changes, Close

---

## R5: Active Workflows Tab

### R5.1: Stats Dashboard ☑️✅
- Running, Completed Today, Failed counts

### R5.2: Workflow List ☑️✅
- Card-based with status indicator (running animation)
- Shows: ADW ID, workflow type, issue #, phase progress

### R5.3: Workflow Detail ☑️✅
- Phase timeline with visual progress dots
- Worktree path display
- Port allocation (backend/frontend)
- Actions: View Logs, Cancel Workflow

### R5.4: Phase Timeline with Iterations ☑️✅
- Each phase shows status (pending/running/completed/failed)
- **Test phase**: Shows iterations with pass/fail/resolved counts
- **Review phase**: Shows iterations with blocker/tech_debt/skippable counts

---

## R6: Test & Review Iteration Documentation

### R6.1: Test Phase Iterations ☑️✅
- MAX_TEST_RETRY_ATTEMPTS = 4 (unit tests)
- MAX_E2E_TEST_RETRY_ATTEMPTS = 2 (browser tests)
- SERIAL processing: fix each failure → re-run all → repeat
- Stop conditions: all pass, max attempts, no fixes made

### R6.2: Review Phase Iterations ☑️✅
- MAX_REVIEW_RETRY_ATTEMPTS = 3
- SERIAL processing: fix blockers only → re-review → repeat
- Only `blocker` severity auto-fixed

### R6.3: Severity Rubric ☑️✅
| Severity | Auto-Fixed? | Criteria |
|----------|-------------|----------|
| blocker | ✓ Yes | Breaks core func, security, explicit req not met |
| tech_debt | ✗ No | Works but suboptimal, fix eventually |
| skippable | ✗ No | Nice-to-have, style preference |

### R6.4: Visual Documentation ☑️✅
- SDLC flow diagram with iteration counts (×4, ×3)
- Iteration legend explaining serial processing
- Pseudocode blocks showing algorithm
- Examples table with real scenarios

---

## R7: Prompts Tab (Reference)

### R7.1: SDLC Flow Diagram ☑️✅
- Visual pipeline: Plan → Build → Test → Review → Document → Ship
- Iteration badges on Test (×4) and Review (×3)
- Hover tooltips explaining iterations

### R7.2: Collapsible Prompt Sections ☑️✅
- Grouped by phase: Classification, Planning, Building, Testing, Review, Documentation, Git
- Each command shows: name, description, arguments, example usage

### R7.3: Prompt Content Boxes ☑️✅
- White background box for dropdown content
- Visual separation from surrounding UI

---

## R8: Workflows Tab (Reference)

### R8.1: Individual Workflow Cards ☑️✅
- Icon, name, subtitle
- Description with iteration info
- CLI command example

### R8.2: Composite Workflows Table ☑️✅
- Lists all workflow combinations
- Highlights: sdlc_iso (full), sdlc_zte_iso (auto-merge)

### R8.3: Model Selection Table ☑️✅
- Heavy (Opus): /implement, /document, /feature, /bug, /chore, /patch
- Base (Sonnet): Everything else

---

## R9: CLI Tab (Reference) ☑️✅

- Installation command
- Core commands table with descriptions
- Badge indicators for phase/dangerous commands

---

## R10: Data Types Tab (Reference) ☑️✅

- Cards for each major data type
- YAML-like schema display
- Links to related types

---

## R11: Config Tab (Reference) ☑️✅

- `.adw.yaml` structure with comments
- `.env` requirements
- Feature flags documentation

---

## R12: Data Persistence

### R12.1: localStorage Backend ☑️✅
- Key: `adw_framework_data`
- Stores: issues, prs, workflows, next_issue counter

### R12.2: Sample Data ☑️✅
- Pre-populated with realistic example data
- Includes workflows with iteration states

---

## R13: UI Components

### R13.1: Status Badges ☑️✅
- open (green), closed (purple), merged (blue)
- running (lime, animated pulse), pending (amber), failed (red)

### R13.2: Modals ☑️✅
- Create Issue, Edit Issue, Trigger Workflow
- Overlay with backdrop blur
- Close on: X button, Escape key, overlay click

### R13.3: Dropdowns ☑️✅
- Action menus (Edit, Close, Delete)
- Close on outside click

### R13.4: Timeline ☑️✅
- Vertical with connecting line
- Phase dots with status colors
- Expandable iteration details

---

## R14: Accessibility & UX

### R14.1: Keyboard ☑️✅
- Escape closes modals
- Tab navigation works

### R14.2: Touch ☑️✅
- Smooth scrolling on mobile (webkit-overflow-scrolling)
- Touch-friendly button sizes

### R14.3: Loading States ⏳
- Skeleton loaders for async operations
- Disabled buttons during actions

---

## Out of Scope ⛔

- ⛔ Backend API integration (localStorage only for now)
- ⛔ Real GitHub OAuth
- ⛔ WebSocket real-time updates
- ⛔ File upload for screenshots
- ⛔ Diff viewer for PRs
- ⛔ Log streaming viewer

