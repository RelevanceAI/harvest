# Problem-Solving Principles

## Don't Hack - Find the Proper Solution

When you hit a problem, your first instinct should NOT be to patch or bypass. Follow this order:

1. **Check for official APIs** - Most libraries export configuration/customization functions
   - Search library documentation for configuration options
   - Examine public API exports and method signatures
   - Check for environment variables or config files
   - Read official documentation for extension patterns

2. **Search for existing solutions** - GitHub issues, Stack Overflow, docs
   - Check the project's issue tracker for similar problems
   - Look for official guidance in documentation
   - Search for established patterns in the community
   - Review changelog for relevant changes

3. **Only if no official way exists** - Consider alternatives, wrappers, or different approaches
   - Evaluate alternative libraries that provide the functionality
   - Consider wrapper patterns that don't modify external code
   - Rethink the approach if monkey-patching feels necessary
   - Discuss with the team before proceeding

**NEVER do these without exhausting the above:**
- ❌ Patch dependency source files directly
- ❌ Use dependency patching tools as first resort
- ❌ Bypass linters/hooks with skip flags (except WIP snapshots - see git-workflow.md)
- ❌ Disable type checking or suppress errors
- ❌ Modify vendored dependencies
- ❌ Hack around errors instead of fixing root cause

**Red flag:** If you're thinking "let me patch this..." or "I'll bypass this..." → STOP and find the proper solution.

## Examples

### ❌ Bad: Patching a Library

```bash
# Modifying dependency source files directly
vim .venv/lib/python3.12/site-packages/some_lib/module.py
# or editing node_modules/some-lib/dist/index.js
# then using a patching tool to persist changes
```

**Why it's bad:**
- Breaks when dependencies reinstall
- Hard to maintain and track
- Unclear to other developers
- May conflict with library updates
- Not reproducible across environments

### ✅ Good: Using Official APIs

```python
# Check the library's documentation for configuration
from some_lib import configure

# Use the official configuration API
configure(
    custom_behavior=True,
    option='value'
)
```

### ❌ Bad: Suppressing Type/Lint Errors

```python
# type: ignore
result = unsafe_operation()

# Or in other languages:
# @ts-ignore, #[allow(clippy::all)], //nolint, etc.
```

**Why it's bad:**
- Hides real type/safety issues
- Makes refactoring dangerous
- Loses tooling support
- Technical debt accumulates

### ✅ Good: Fixing the Root Cause

```python
# Properly type the operation
result: ExpectedType = safe_operation()

# Or if types are genuinely wrong, contribute fixes upstream
# Or create proper type stubs/declarations
```

### ❌ Bad: Skipping Linters/Hooks

```bash
git commit --no-verify -m "quick fix"  # DON'T do this

# Exception: WIP snapshots are allowed --no-verify (see git-workflow.md)
git commit -m "wip: snapshot before sync" --no-verify  # OK for WIP only

# Or: pytest -x --no-cov
# Or: eslint --no-inline-config
```

**Why it's bad:**
- Bypasses quality checks for final commits
- Can break CI if merged
- Creates technical debt
- Defeats the purpose of automation
- (Exception: WIP snapshots are temporary and get squashed)

### ✅ Good: Fixing the Issue

```bash
# Fix the linting error
ruff check --fix .
# Or: npm run lint -- --fix
# Or: go fmt ./...

# Or if the check is genuinely wrong, update the configuration
# Edit .pre-commit-config.yaml, .eslintrc, pyproject.toml, etc.
```

## When Workarounds Are Acceptable

There are rare cases where workarounds are necessary:

1. **Third-party library has confirmed bug** - Use workaround temporarily
   - ONLY if bug is confirmed by maintainer in public issue tracker
   - OR documented in project's official known issues/changelog
   - Document with comment linking to upstream issue URL
   - Add TODO with issue number to remove when fixed
   - Consider contributing a fix upstream

2. **Blocking external dependency** - Temporary measure while waiting for maintainer
   - Document the reason clearly
   - Create tracking issue to remove the hack
   - Consider forking and fixing properly

3. **Legacy code migration** - Temporary bridges during refactoring
   - Clear migration plan documented
   - Tracked in project management system
   - Time-boxed removal date

**Even in these cases:**
- Document WHY the workaround exists
- Link to relevant issues/tickets
- Add TODO with removal plan
- Make it obvious this is temporary

## When to Ask for Help

Before spending excessive time searching for solutions, ask a human if:

- **After 3-4 different approaches fail** - You've tried official APIs, searched issues, and attempted alternatives
- **Documentation is unclear or contradictory** - The library docs don't clearly explain how to solve your problem
- **Architectural decision required** - Multiple valid approaches exist with different tradeoffs
- **Security or safety implications** - The change could affect authentication, data integrity, or user safety
- **Legacy code with unclear intent** - Code patterns don't match modern best practices and purpose is unclear

**Better to ask early than waste time on the wrong approach.**

In local mode: Ask the user directly via chat.
In autonomous mode: Create a Linear issue or Slack message with context.

## Problem-Solving Checklist

Before implementing a solution, ask yourself:

- [ ] Did I check the official documentation?
- [ ] Did I search for existing solutions (GitHub issues, Stack Overflow)?
- [ ] Did I explore the library's exported APIs?
- [ ] Is there a configuration option I'm missing?
- [ ] Am I trying to use the library in an unsupported way?
- [ ] Could a different approach avoid this problem entirely?
- [ ] If this is a workaround, is it documented with clear rationale?

## Integration with Other Rules

This problem-solving approach integrates with:

- **Planning** (`@docs/ai/shared/planning.md`): Research phase should identify proper solutions
- **Debugging** (`@docs/ai/shared/debugging.md`): Systematic debugging finds root causes, not symptoms
- **Code Comments** (`@docs/ai/shared/code-comments.md`): Document WHY when workarounds are genuinely needed

## Red Flags That Should Trigger Research

If you find yourself:
- Looking up how to patch dependency directories
- Searching for dependency patching tool tutorials
- Adding error suppression comments
- Using skip/bypass flags for quality tools
- Modifying vendored dependencies
- Copying code from dependencies into your project
- Writing wrappers to bypass safety checks

**STOP.** Go back to step 1: Check for official APIs.

## The Right Mindset

**Good:** "This library must have a way to configure this behavior. Let me find it."

**Bad:** "I'll just patch this file quickly."

**Good:** "This error indicates a real problem. Let me understand what's wrong."

**Bad:** "I'll just suppress this error to make it compile."

**Good:** "The pre-commit hook caught a real issue. Let me fix it."

**Bad:** "I'll use --no-verify to commit faster."

Proper solutions take slightly more time upfront but save massive time in maintenance, debugging, and onboarding.
