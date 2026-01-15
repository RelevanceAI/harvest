# Plans Directory

## Overview

Plans are organized by feature branch and tracked through three phases:

1. **Research** (`research_YYYY-MM-DD_HHMM.md`) - Exploration, understanding, context gathering
2. **Plan** (`plan_YYYY-MM-DD_HHMM.md`) - Detailed proposal with step-by-step implementation and success criteria
3. **Implementation** (`implementation_YYYY-MM-DD_HHMM.md`) - Code execution, testing, validation, lessons learned

## Directory Structure

```
.claude/plans/
├── README.md (this file)
└── [branch-name]/
    ├── research_YYYY-MM-DD_HHMM.md
    ├── plan_YYYY-MM-DD_HHMM.md
    ├── plan_YYYY-MM-DD_HHMM_v2.md (if revised after feedback)
    └── implementation_YYYY-MM-DD_HHMM.md
```

### Branch Name → Directory Name

Replace `/` with `-` in branch names:
- Branch: `docs/phase-0-rules-finalization` → Dir: `docs-phase-0-rules-finalization`
- Branch: `feat/modal-sandbox-block-1.1` → Dir: `feat-modal-sandbox-block-1.1`

## Timestamps

Format: `YYYY-MM-DD_HHMM` (sortable, unambiguous)

Example: `plan_2026-01-14_2100.md`

Why timestamps matter:
- Agent can quickly see "which iteration am I on?" across sessions
- Easy to sort: `ls -1 .claude/plans/*/plan_*.md | sort`
- Clear audit trail of planning iterations

## How to Read a Plan

### Research File
- **Purpose**: Understand the problem, explore the solution space
- **Contains**: Context, investigation results, constraints discovered, approach options
- **Audience**: Set context for planning phase

### Plan File
- **Purpose**: Detailed proposal for implementation
- **Contains**: Step-by-step procedures, file locations, success criteria, testing strategy, assumptions
- **Approval Gate**: This file goes to PR review - approval required before implementation
- **Audience**: Reviewers validate approach is sound before execution

### Implementation File
- **Purpose**: Record what was actually built
- **Contains**: Code changes made, test results, deviations from plan, lessons learned
- **Status**: References plan PR number and documents decisions made vs. what was planned
- **Audience**: Feedback loop - future work references these decisions

## Versioning

Each iteration gets its own timestamp. Revisions are simply new files with new timestamps:

```
research_2026-01-14_1400.md
research_2026-01-14_1500.md       (deeper investigation)
plan_2026-01-14_1600.md           (initial plan)
plan_2026-01-14_1700.md           (revised after feedback)
implementation_2026-01-14_1800.md (implements latest plan)
```

Latest version is easiest to find:
```bash
ls -ltr .claude/plans/[branch-name]/plan_*.md | tail -1
```

## Finding Plans

**Active Plans**: See open PRs with `[PLAN]` prefix on GitHub. These are the current work in progress.

**Completed/Archived Plans**: Browse `.claude/plans/` directory structure and git history to see past decisions and lessons learned.

```bash
# Find all plan files
find .claude/plans -name "plan_*.md"

# See plan history for a branch
ls .claude/plans/[branch-name]/

# Review completed plans in git
git log --oneline -- .claude/plans/
```

## Workflow

### Phase 1: Research
1. Create new directory under `.claude/plans/[branch-name]/`
2. Write `research_YYYY-MM-DD_HHMM.md` with findings
3. Commit and push

### Phase 2: Planning
1. Write `plan_YYYY-MM-DD_HHMM.md` with detailed implementation steps
2. Commit and push
3. **Open PR** for review
4. Wait for approval (human ticks checkbox)
5. If feedback: create `plan_YYYY-MM-DD_HHMM_v2.md` and iterate
6. Once approved: close PR (don't merge), proceed to implementation

### Phase 3: Implementation
1. Execute the approved plan
2. Write `implementation_YYYY-MM-DD_HHMM.md` with results
3. Create implementation PR
4. Reference the plan PR number for context
5. Merge when approved
6. Plans remain in git for feedback loop

## Why This Structure Works

1. **Clarity**: Each phase has clear input/output
2. **Approval Gates**: Plans reviewed before expensive implementation work
3. **Feedback Loop**: Plans and implementations stay in git history → future work learns from past decisions
4. **Agent Self-Awareness**: Timestamps help agents track "which iteration?" across sessions
5. **Discoverability**: Easy to find all active work: `ls .claude/plans/`
6. **Auditability**: Git history shows planning evolution

## Examples

### Example 1: Simple Feature
```
feat-add-logging/
├── research_2026-01-15_0900.md
├── plan_2026-01-15_1000.md
└── implementation_2026-01-15_1400.md
```

### Example 2: Complex Feature with Revisions
```
feat-modal-sandbox-block-1.1/
├── research_2026-01-16_0900.md
├── research_2026-01-16_1100.md (deeper investigation)
├── plan_2026-01-16_1300.md
├── plan_2026-01-16_1500.md (revised after feedback)
└── implementation_2026-01-17_0900.md
```

## Tips for Agent Workflow

**When starting a new session**:
```bash
# See all active work
ls .claude/plans/

# See latest plan for current branch
ls -ltr .claude/plans/[branch-name]/plan_*.md | tail -1

# Read the most recent plan
cat .claude/plans/[branch-name]/plan_*.md | tail -1
```

**When iterating on a plan**:
1. Read existing plan file
2. Get feedback from PR review
3. Create new `plan_YYYY-MM-DD_HHMM.md` file with a new timestamp
4. Don't overwrite - keep all versions for audit trail
5. Latest version is found by sorting: `ls -ltr plan_*.md | tail -1`

**When implementing**:
1. Reference the approved plan PR number
2. Document deviations in implementation file
3. Add lessons learned section
4. Link back to plan for context

## Integration with GitHub

Example PR title:
```
[PLAN] Phase 0: Plan Infrastructure Setup
```

Example PR description:
```markdown
## Plan Summary
(Brief 2-3 sentence summary)

## Full Plan
[Read full plan](link to plan file)

## Next Steps
1. Review this plan
2. Approve by ticking checkbox
3. Close PR (don't merge)
4. Implementation begins
```

Implementation PRs reference the plan PR:

```markdown
## Implementation Details

Based on plan: #PR_NUMBER

### Changes Made
(Describe what was implemented)

### Deviations from Plan
(Note any changes from original plan)

### Test Results
(Show test outputs)

### Lessons Learned
(Document insights for future work)
```
