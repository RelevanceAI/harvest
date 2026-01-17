# Problem-Solving Principles

## Don't Hack - Find the Proper Solution

When you hit a problem, your first instinct should NOT be to patch or bypass. Follow this order:

1. **Check for official APIs** - Most libraries export configuration/customization functions
   - Example: `grep "export" node_modules/@package/dist/index.js`
   - Check TypeScript definitions for available options
   - Read official documentation for configuration patterns

2. **Search for existing solutions** - GitHub issues, Stack Overflow, docs
   - Check the project's issue tracker for similar problems
   - Look for official guidance in documentation
   - Search for established patterns in the community

3. **Only if no official way exists** - Consider alternatives, wrappers, or different approaches
   - Evaluate alternative libraries that provide the functionality
   - Consider wrapper patterns that don't modify external code
   - Rethink the approach if monkey-patching feels necessary

**NEVER do these without exhausting the above:**
- ❌ Patch `node_modules/` files
- ❌ Use `patch-package` as first resort
- ❌ Bypass hooks with `--no-verify`
- ❌ Disable errors with `@ts-ignore` or `any`
- ❌ Modify vendored dependencies directly
- ❌ Hack around type errors instead of fixing root cause

**Red flag:** If you're thinking "let me patch this..." or "I'll bypass this..." → STOP and find the proper solution.

## Examples

### ❌ Bad: Patching a Library

```bash
# Modifying node_modules directly
vim node_modules/some-lib/dist/index.js
# then using patch-package
```

**Why it's bad:**
- Breaks on `npm install`
- Hard to maintain
- Unclear to other developers
- May conflict with library updates

### ✅ Good: Using Official APIs

```typescript
// Check the library's exports
import { configure } from 'some-lib';

// Use the official configuration API
configure({
  customBehavior: true,
  option: 'value'
});
```

### ❌ Bad: Bypassing Type Errors

```typescript
// @ts-ignore
const result = unsafeOperation();
```

**Why it's bad:**
- Hides real type issues
- Makes refactoring dangerous
- No IDE support

### ✅ Good: Fixing the Root Cause

```typescript
// Properly type the operation
const result: ExpectedType = safeOperation();

// Or if types are genuinely wrong, contribute to DefinitelyTyped
// Or create proper type declarations
```

### ❌ Bad: Skipping Git Hooks

```bash
git commit --no-verify -m "quick fix"
```

**Why it's bad:**
- Bypasses linting and tests
- Can break CI
- Creates technical debt

### ✅ Good: Fixing the Issue

```bash
# Fix the linting error
npm run lint -- --fix

# Or if the hook is genuinely wrong, update the hook configuration
# Edit .pre-commit-config.yaml or .husky/ scripts
```

## When Workarounds Are Acceptable

There are rare cases where workarounds are necessary:

1. **Third-party library has confirmed bug** - Use workaround temporarily
   - Document with comment linking to upstream issue
   - Add TODO to remove when fixed
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
- Looking up how to patch `node_modules`
- Searching for `patch-package` tutorials
- Adding `@ts-ignore` comments
- Using `--no-verify` flags
- Modifying vendored dependencies
- Copying code from `node_modules` into your project
- Writing wrappers to bypass type checking

**STOP.** Go back to step 1: Check for official APIs.

## The Right Mindset

**Good:** "This library must have a way to configure this behavior. Let me find it."

**Bad:** "I'll just patch this file quickly."

**Good:** "This type error indicates a real problem. Let me understand what's wrong."

**Bad:** "I'll just use `any` to make it compile."

**Good:** "The pre-commit hook caught a real issue. Let me fix it."

**Bad:** "I'll use `--no-verify` to commit faster."

Proper solutions take slightly more time upfront but save massive time in maintenance, debugging, and onboarding.
