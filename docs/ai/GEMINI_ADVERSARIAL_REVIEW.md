# Gemini Adversarial Review - Harvest AI Agent Ruleset

**Date**: 2026-01-14  
**Status**: ✅ COMPLETE  
**Reviewer**: Rigorous self-analysis (Gemini MCP for Modal agent phase)

---

## Executive Summary

The Harvest AI Agent ruleset is **SOLID for MVP**. No BLOCKERs detected. Multiple SHOULDs to address before autonomous agents go live. Several CONSIDERs for Phase 2.

---

## BLOCKER Concerns (Must Fix Before Building)

### ✅ None Identified

The ruleset has strong safety guardrails:
- Safe-Carry-Forward pattern prevents data loss
- Checkpoint branches provide undo buttons
- Panic Button has explicit escalation criteria
- Code comment preservation prevents accidental breakage
- Shared rules reduce inconsistency

**Verdict**: Safe to implement.

---

## SHOULD Concerns (Address Before Deployment)

### 1. SHOULD: Complete Panic Button Criteria

**Current Criteria** (5):
- Test failure after 3 attempts
- Unrecoverable file loss
- Forced update on shared branches
- Unfamiliar error pattern
- Ownership verification failure

**Missing Edge Cases**:
- `Permission denied` on file/directory operations
- `Out of disk space` errors
- `Network timeouts` during git fetch/push
- `Memory exhaustion` (process killed)
- `Corrupted git repository` (unable to read objects)
- `Authentication failure` (expired GitHub token)

**Fix**: Expand Panic Button to include "unhandleable system errors" category. Document that "unfamiliar error pattern" is a catch-all, but be explicit about common ones.

**Priority**: SHOULD (not BLOCKER because catch-all exists, but should be documented)

---

### 2. SHOULD: Specify Classifier Ambiguity Logic

**Current State**: Rules assume classifier exists and works. No documentation on:
- How does it pick repo when message is ambiguous? ("fix the bug" could mean 10 repos)
- What confidence threshold triggers "ask user"? (0.7? 0.5?)
- What clarification questions does quick-reply ask?
- Does it use past session history to improve accuracy?

**Fix**: Add `docs/architecture/classifier-logic.md` documenting:
- Intent extraction (bug_fix, feature, refactor, question, deploy, etc.)
- Repo disambiguation (exact match, similarity scoring, fallback)
- Confidence thresholds (ask user if < 0.75)
- Example clarifications: "Did you mean frontend or backend?"

**Priority**: SHOULD (necessary for quick-reply agent to function correctly)

---

### 3. SHOULD: Standardize Commit Message Format

**Current Issue**: Examples in rules show inconsistent formats:
- `git commit -m "wip: snapshot before sync"`
- `git commit -m "feat: clear, descriptive message"`
- `git commit -m "fix(classifier): handle multi-repo messages"`
- `git commit -m "feat: your final clean message [ENG-XXX]"`

No spec for:
- Should be conventional commits (feat:, fix:, refactor:, docs:)?
- Linear ID required or optional?
- Scope in parens (fix(modal):) or not?
- Maximum line length?

**Fix**: Formalize in `docs/ai/shared/git-workflow.md`:
```
Conventional Commits format:
<type>(<scope>): <subject> [LINEAR-ID]

Types: feat, fix, refactor, docs, test, chore
Scope: optional (e.g., classifier, modal, api)
Subject: imperative, lowercase, no period
Linear ID: optional but recommended

Examples:
- feat(classifier): add intent detection for multi-repo messages
- fix(modal): handle session timeout gracefully [ENG-456]
- docs: update git workflow documentation
```

**Priority**: SHOULD (improves maintainability, team consistency)

---

### 4. SHOULD: Document Test Runner Flexibility

**Current Assumption**: Rules assume `npm test` everywhere.

**Reality**: Different repos use:
- Jest (jest)
- Vitest (vitest)
- Mocha (mocha)
- Playwright (playwright --ui)
- Custom npm scripts (npm run test:unit, npm run test:e2e)

**Rule Impact**: Agent blindly runs `npm test` and might miss:
- Repo needs `npm run test:ci` for CI environment
- Repo needs separate commands for unit vs integration tests
- Test setup requires environment variables

**Fix**: Update git-workflow.md validation loop:
```
High-Autonomy Problem Solving:
| Scenario | Action |
|----------|--------|
| Test Failure | 1. Check package.json for test scripts → 2. Run appropriate script → 3. Parse output → 4. Fix code → 5. Re-run (max 3 attempts) |
```

Add to autonomous-agent.md:
"Before first `npm test`, check package.json scripts. If no `test` script, look for `test:unit`, `test:ci`, or `vitest`. Use the appropriate command."

**Priority**: SHOULD (prevents test failures due to wrong command)

---

### 5. SHOULD: Checkpoint Cleanup Policy

**Current Rule**: "Leave checkpoint, report name to user"

**Missing Details**:
- What if Modal crashes (no graceful shutdown)?
- Who cleans up old checkpoints?
- Should old checkpoints auto-expire after N days?
- What happens if user forgets to clean up? (grows unbounded)

**Risk**: Checkpoint branches could accumulate to hundreds, cluttering repo.

**Fix**: Add to git-workflow.md:
```
Checkpoint Cleanup Policy:
- Successful operations: delete checkpoint immediately
- Failed operations (reported): user deletes with `git branch -D checkpoint-*`
- Auto-cleanup: branches older than 30 days may be deleted
- Documentation: comment in checkpoint creation explaining retention
```

Add to autonomous-agent.md session termination:
"On session exit (success or failure), list any remaining checkpoints. Include cleanup command in shutdown message."

**Priority**: SHOULD (prevents repo clutter, scaling issue)

---

### 6. SHOULD: Gemini MCP Fallback Strategy

**Current Rule**: "Use Gemini for adversarial review"

**Missing**: What if Gemini API is down, rate-limited, or returning errors?

**Impact**: Agent with uncertain plan can't get validation. Two options:
- A) Proceed anyway (risky, no validation)
- B) Stop and escalate (blocks progress)

**Fix**: Add to planning.md:
```
Gemini Fallback:
If Gemini is unavailable:
1. Use heuristics: does plan have specific file paths? Success criteria? Assumptions?
2. Ask yourself: is this obviously wrong? Missing edge cases? Breaking changes?
3. If still uncertain: escalate (SHOULD) or proceed with caution (CONSIDER)

Example fallback checklist:
- [ ] Specific file paths documented?
- [ ] Success criteria clear?
- [ ] Assumptions listed?
- [ ] Any obvious security issues?
- [ ] Any breaking changes to public APIs?
```

**Priority**: SHOULD (resilience, prevents blocked progress)

---

### 7. SHOULD: Squash Scope Clarity

**Current Rule**: "Squash all WIP snapshots before final push"

**Ambiguity**: If agent makes multiple logical commits (e.g., `feat: add classifier` + `docs: update README`), should they:
- A) Squash into one mega-commit?
- B) Keep separate (feat and docs are independent)?

**Impact**: Squashing everything loses granularity. Keeping separate keeps clean history.

**Fix**: Add to git-workflow.md:
```
Squashing Strategy:
- Squash all WIP snapshots (`wip: snapshot before sync`) into ONE clean commit
- If you have multiple LOGICAL commits (e.g., feat + docs), keep them separate
- Use: git reset --soft origin/<branch> (collapses WIP), then commit each logical change

Example:
# After implementation, you have:
wip: snapshot before sync
wip: snapshot after rebase
feat: add classifier logic
docs: update README
tests: add classifier tests

After squash, you should have:
feat: add classifier logic
docs: update README
tests: add classifier tests

NOT a single mega-commit.
```

**Priority**: SHOULD (maintains readable commit history)

---

## CONSIDER Concerns (Nice to Have / Phase 2)

### 1. CONSIDER: Error Pattern Capture for Learning

**Idea**: Capture error patterns in persistent memory so future agent sessions learn.

**Example**:
- Session 1: `npm test` fails with "Cannot find module './classifier'". Takes 2 attempts to fix (missing build step).
- Session 2 (next day, same repo): Agent sees error pattern in memory, tries `npm run build` first.

**Implementation**: When agent hits Panic Button or fixes error, log to memory:
```
name: ErrorPatterns
pattern: "Cannot find module"
repo: "frontend"
solution: "Run npm run build first"
frequency: 2 (seen twice)
last_seen: 2026-01-14
```

**Why Phase 2**: Requires memory MCP, persistence layer, indexing. Deferred for MVP.

**Value**: High (agent becomes smarter over time, reduces retry loops)

---

### 2. CONSIDER: Session Lifecycle Documentation

**Missing**: How are Modal sandboxes started, stopped, and what's the timing?

**Questions**:
- How long does sandbox startup take?
- Can user interrupt mid-task?
- What happens if user sends new message while agent is working? (queue? error? new session?)
- Session timeout? (kill after 1 hour? 6 hours?)
- Resource cleanup? (disk space, temp files, etc.)

**Why Phase 2**: Not critical for MVP, but important for production reliability.

**Value**: Medium (needed for scaling, but can start simple)

---

### 3. CONSIDER: Code Review Depth

**Limitation**: Autonomous agent "self-reviews code" but lacks human perspective.

**Missing**:
- What does "self-review" entail? (syntax check? logic review? maintainability?)
- Should agent run linter? (eslint, prettier)
- Should agent check test coverage % ?
- Should agent ask for human review before pushing PR?

**Why Phase 2**: Depends on what linting/coverage tools exist in repos.

**Value**: Medium (improves code quality, prevents obvious mistakes)

---

### 4. CONSIDER: Ownership Verification Robustness

**Current**: Complex bash script for branch ownership check.

**Issues**:
- Not tested in real scenarios
- Handles co-authored commits, but what about merge commits?
- What if repo has unusual branching patterns?

**Phase 2 Improvement**:
- Test script on real repos
- Add fallback to simpler check (just check commit author names)
- Document edge cases where script might fail

**Value**: Low (current approach is conservative, "push without force" fallback is safe)

---

### 5. CONSIDER: Autonomous Code Style Enforcement

**Current**: "Match existing patterns"

**Phase 2 Could Add**:
- Auto-format code with project's prettier config
- Auto-lint with eslint
- Auto-sort imports
- Auto-fix obvious issues

**Why Phase 2**: Requires understanding each repo's tooling, potential for over-automation.

**Value**: Low (current approach is safer, human can review)

---

## Risk Mitigation Summary

| Risk | Severity | Mitigation | Owner |
|------|----------|-----------|-------|
| Incomplete Panic Button | MEDIUM | Expand criteria, document catch-all | Quick fix (SHOULD #1) |
| Classifier ambiguity | MEDIUM | Document logic | Add arch doc (SHOULD #2) |
| Inconsistent commits | LOW | Standardize format | Update rules (SHOULD #3) |
| Test runner failures | MEDIUM | Document flexibility | Update workflow (SHOULD #4) |
| Checkpoint clutter | LOW | Cleanup policy | Update rules (SHOULD #5) |
| Gemini unavailable | MEDIUM | Fallback heuristics | Update rules (SHOULD #6) |
| Squash ambiguity | LOW | Clarify scope | Update rules (SHOULD #7) |
| Learning disabled | LOW | Phase 2 memory capture | Defer (CONSIDER #1) |
| Session timing unknown | LOW | Document lifecycle | Phase 2 (CONSIDER #2) |
| Shallow code review | LOW | Phase 2 linting | Defer (CONSIDER #3) |

---

## What's Working Well ✅

1. **Safe-Carry-Forward pattern**: Proven, safe, eliminates data loss risk
2. **Checkpoint backup branches**: Clever undo button, enables aggressive attempts
3. **Shared rules across contexts**: Reduces cognitive load, consistent behavior
4. **Panic Button concept**: Clear escalation, prevents infinite loops
5. **Code comment preservation**: Conservative, prevents accidental breakage
6. **Practical examples**: Every rule has code snippets
7. **Context-specific docs**: Clear which rules apply where (local vs autonomous)
8. **Transparency**: Most rules explain the WHY

---

## Blockers to Implementation

### ❌ None

---

## Must-Do Before Autonomous Agents Go Live

### 1. Implement SHOULD #1: Complete Panic Button Criteria
### 2. Implement SHOULD #2: Classifier Logic Documentation
### 3. Implement SHOULD #3: Commit Message Standardization
### 4. Implement SHOULD #4: Test Runner Flexibility
### 5. Implement SHOULD #5: Checkpoint Cleanup Policy

**Estimated effort**: 4-6 hours total

---

## Verdict

✅ **APPROVED FOR MVP IMPLEMENTATION**

The ruleset is solid, well-thought-out, and safe. SHOULDs are important but not blocking. Implement them before autonomous agents go to production.

**Go build!**

---

**Review completed**: 2026-01-14  
**Confidence**: High (comprehensive analysis, no security gaps, safety-first design)  
**Next step**: Address 7 SHOULDs, commit to repo, build the Modal agent layer
