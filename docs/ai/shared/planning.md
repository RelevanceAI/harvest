# Planning Guidelines

For non-trivial changes: **think before you code**.

## Process

1. **Research**: Understand the problem space, existing code, constraints, and edge cases
2. **Design**: Draft a detailed plan with:
   - Specific file paths
   - Concrete changes
   - Assumptions and dependencies
   - Trade-offs and rationale
3. **Validate**: If Gemini is available, submit for adversarial review (see below)
4. **Implement**: Address BLOCKER concerns first, then build
5. **Audit**: Check your work against project conventions before committing

## What Counts as "Non-Trivial"?

- Architectural changes (new modules, dependency injection patterns, etc.)
- Changes affecting multiple files or subsystems
- Anything that touches security, performance, or data handling
- Uncertain about the right approach

**Small, local changes** (bug fix in one file, simple refactor) don't need adversarial review.

## Adversarial Review with Gemini

Use Gemini for plan validation when non-trivial:

```
gemini_chat(
  message="[YOUR DETAILED PLAN including file paths and assumptions]",
  system_prompt="You are an adversarial code reviewer. Analyze this plan and identify concerns. Categorize each as:\n- BLOCKER: Must fix (security, data loss, breaking changes, fundamental flaws)\n- SHOULD: Should address (edge cases, error handling, maintainability)\n- CONSIDER: Nice to have (minor improvements, performance tweaks)\n\nFor each concern, explain WHY it matters and suggest a fix. Be specific and actionable."
)
```

### Gemini MCP Fallback (If Unavailable)

If Gemini is unavailable (API down, rate-limited, or not configured), use this **heuristic checklist** to self-validate your plan:

**Pre-Implementation Self-Review**:
- [ ] Specific file paths documented? (Not vague like "update code")
- [ ] Success criteria clear? (How will you verify this works?)
- [ ] Assumptions listed? (What are you assuming about existing code?)
- [ ] Obvious security issues? (Validation, auth, data handling)
- [ ] Any breaking changes? (Changes to public APIs, data formats)
- [ ] Edge cases considered? (Empty inputs, errors, race conditions)
- [ ] Error handling planned? (What happens if things fail)
- [ ] Performance impact? (Will this slow things down?)
- [ ] Dependencies clear? (Does this depend on other changes)

If **all items are checked**, proceed with confidence.

If **2+ items are uncertain**, escalate to human review before implementing.

**Note for Autonomous Agent**: Use this checklist if Gemini is unavailable. Don't let it block progress—use your own reasoning. If deeply uncertain, escalate to Panic Button rather than guessing.

### What to Include in Your Plan

✅ **DO include**:
- Specific file paths and their purpose
- Concrete code changes (small snippets, not entire files)
- Assumptions about existing code
- Success criteria (how you'll validate the change)
- Any constraints or limitations

❌ **DON'T include**:
- Entire file contents (unless absolutely necessary)
- Unrelated context or history
- Hypothetical "what-ifs"

### Acting on Feedback

1. **BLOCKER concerns**: Fix these before implementing (they indicate fundamental issues)
2. **SHOULD concerns**: Address if feasible (balance against time/scope)
3. **CONSIDER concerns**: Optional (implement if they add clear value)

## Commit Strategy

- **Small, logical commits**: Commit often, early. Easier to review and revert if needed.
- **Explain WHY in commit messages**: The diff shows WHAT changed. Your message explains WHY.
- **Test before committing**: Verify changes work (except for WIP snapshots)
- **Squash WIP snapshots**: Use `git reset --soft` to collapse temporary snapshots before final push

## Audit Against Project Conventions

Before implementing or committing:

1. Check existing code for patterns (naming, structure, test style)
2. Review relevant project rules (this directory)
3. Look for similar features that set precedent
4. Align your approach with team conventions

**If you discover a convention that conflicts with your plan**: Either adapt your plan or flag it for discussion (create an issue).

## Key Principles

- **Slow down to speed up**: Planning upfront saves debugging later
- **Seek feedback on uncertain parts**: Don't guess at architecture
- **Document your reasoning**: Future maintainers (including you) will appreciate it
- **Keep the team in sync**: Use Linear, PRs, and Slack to communicate progress

## Plan Storage & Organization

Plans are stored in `.claude/plans/` organized by branch name with three phases:

1. **Research** (`research_YYYY-MM-DD_HHMM.md`) - Exploration, understanding, context
2. **Plan** (`plan_YYYY-MM-DD_HHMM.md`) - Detailed proposal (approval gate)
3. **Implementation** (`implementation_YYYY-MM-DD_HHMM.md`) - Execution record, lessons learned

### Directory Structure

```
.claude/plans/
└── [branch-name]/
    ├── research_YYYY-MM-DD_HHMM.md
    ├── plan_YYYY-MM-DD_HHMM.md
    └── implementation_YYYY-MM-DD_HHMM.md
```

**Branch naming:** Replace `/` with `-` (e.g., `feat/auth` → `feat-auth/`)

### Finding Plans

```bash
# See all active work
ls .claude/plans/

# Latest plan for current branch
ls -ltr .claude/plans/[branch-name]/plan_*.md | tail -1
```

### Workflow

**Phase 1 - Research:**
1. Create `.claude/plans/[branch-name]/research_YYYY-MM-DD_HHMM.md`
2. Document findings, constraints, approach options
3. Commit and push

**Phase 2 - Planning:**
1. Create `plan_YYYY-MM-DD_HHMM.md` with detailed implementation
2. Open PR with `[PLAN]` prefix for review
3. If feedback: create new `plan_YYYY-MM-DD_HHMM.md` (don't overwrite)
4. Once approved: close PR, proceed to implementation

**Phase 3 - Implementation:**
1. Execute approved plan
2. Create `implementation_YYYY-MM-DD_HHMM.md` with results
3. Reference plan PR number in implementation PR
4. Merge when approved

**Why timestamps:** Agent self-awareness ("which iteration?"), audit trail, easy sorting

## Hierarchical Planning (New)

### Plan PR Contains High-Level Tasks

Plans created in Session 1 should have **5-10 high-level tasks** (30-60 min each).

**Example Plan PR Structure**:
```markdown
# Implementation Plan: Repository Classifier

## Task 1: Core Classification Logic (45 min)
- Implement classify() function with confidence scoring
- Handle edge cases (empty messages, ambiguous intent)
- Success: Function returns repo name + confidence score

## Task 2: Integration with Slack Bot (30 min)
- Add classifier to message handler
- Route to appropriate repo sandbox
- Success: Messages routed correctly in Slack

## Task 3: Testing & Verification (40 min)
- Unit tests for classifier
- Integration tests with mock Slack messages
- Success: All tests pass, coverage >80%
```

### Agent Breaks Down During Execution

During Session 2, agent dynamically expands each high-level task:

**Task 1 becomes**:
- 1.1: Write failing test for classify() (2 min)
- 1.2: Implement classify() basic logic (5 min)
- 1.3: Verify test passes (1 min)
- 1.4: Write failing test for confidence scoring (2 min)
- 1.5: Implement confidence scoring (4 min)
- 1.6: Verify test passes (1 min)
- 1.7: Write failing test for edge cases (3 min)
- 1.8: Implement edge case handling (5 min)
- 1.9: Verify test passes (1 min)
- 1.10: Run full test suite (2 min)
- 1.11: Commit completed task (1 min)

**Benefits**:
- Plan PR stays readable (not hundreds of tiny tasks)
- Agent has flexibility in execution approach
- Human reviews strategy, not micro-steps
- Scales to large features without context overflow
