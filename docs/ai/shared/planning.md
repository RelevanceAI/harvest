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

Plans are stored in the `.claude/plans/` directory with timestamped files organized by branch name.

See [`.claude/plans/README.md`](../../.claude/plans/README.md) for:
- Directory structure and naming conventions
- Three-phase workflow (research → plan → implementation)
- Versioning strategy (timestamps for iterations)
- How to discover and reference plans
- Integration with GitHub PRs

This infrastructure enables:
- **Agent self-awareness**: Timestamps help track "which iteration?" across sessions
- **Clear approval gates**: Plans reviewed before implementation
- **Feedback loops**: Completed plans stay in git history for reference
