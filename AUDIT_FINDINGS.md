# Harvest AI Rules Audit - Findings & Recommendations

**Date**: 2026-01-14  
**Status**: ✅ COMPLETE - Ready for team review  
**Commit**: `6d096b7` - docs(ai): restructure rules for Ramp-inspired autonomous agent architecture

---

## Executive Summary

**You asked me to audit your rules and see if they're OK with this repo.**

**Answer: YES, with 7 important refinements needed before autonomous agents go to production.**

- ✅ **No BLOCKERs** (safe to build with)
- ⚠️ **7 SHOULDs** (address before deployment, ~4-6 hours effort)
- 💡 **5 CONSIDERs** (Phase 2, not MVP)

**Verdict**: Approved for MVP implementation. Rules are well-designed, safety-first, and ready to guide AI agents in this repo.

---

## What Changed

### Restructure (Ramp Inspect-Inspired Architecture)

```
Before:                          After:
docs/ai/                         docs/ai/
├── git.md                       ├── .claude/claude.md (index)
├── comments.md                  ├── local-development.md
├── harvest-mode.md              ├── autonomous-agent.md
├── straya.md                    ├── shared/
└── ...                          │   ├── git-workflow.md
                                 │   ├── code-comments.md
                                 │   └── planning.md
                                 ├── ADVERSARIAL_REVIEW.md
                                 └── GEMINI_ADVERSARIAL_REVIEW.md
```

**Moved**:
- `git.md` → `shared/git-workflow.md` (applies to all contexts)
- `comments.md` → `shared/code-comments.md` (applies to all contexts)

**Consolidated**:
- `harvest-mode.md` → `autonomous-agent.md` (more specific)

**Removed**:
- `straya.md` (chat personality, deferred to Phase 2)

**Created**:
- `local-development.md` (you + Claude rules)
- `autonomous-agent.md` (Modal sandbox agent rules)
- `shared/planning.md` (research before code, Gemini validation)
- `.claude/claude.md` (index + quick reference)
- Adversarial review documents (findings + analysis)

---

## Architecture (What It Enables)

```
User in Slack: @harvest "fix the login bug"
  ↓
Classifier: Picks repo + infers intent
  ↓
If unclear → Quick-reply agent asks clarifying questions in Slack
  ↓
Once clear → Modal sandbox spins up with full codebase context
  ↓
Agent operates with full autonomy:
  - Research → Plan → Code → Test → Commit → Push → PR
  - If blocked → Escalate via Panic Button (5 criteria)
  ↓
Complete → Session ends (work persists in GitHub as PR)
```

---

## Key Innovations ✨

### 1. Safe-Carry-Forward Snapshots
Snapshot commits instead of `git stash`:
- Permanent (survive session resets)
- Trackable (part of git history)
- Black box recorder of agent's process
- Squashed before final push to keep history clean

**Impact**: Eliminates data loss risk, provides auditability.

### 2. Checkpoint Pattern
Before risky operations (rebase, conflict resolution), create backup branch:
```bash
git checkout -b "checkpoint-feat-auth-1704123456"
git checkout feat/auth
# attempt risky operation
# if fails after 3 attempts: keep checkpoint, report to user
```

**Impact**: Provides undo button, enables aggressive autonomous attempts without fear.

### 3. Panic Button (5 Explicit Criteria)
When to stop and escalate:
1. Test failures after 3 attempts
2. Unrecoverable file loss
3. Forced update on shared branches
4. Unfamiliar error patterns
5. Branch ownership verification failure

**Impact**: Prevents infinite retry loops, keeps agent safe while enabling high autonomy.

### 4. Shared Rules Across Contexts
Same git/comment/planning rules for local dev and autonomous agents:
- **Local dev**: You + Claude (human judgment available)
- **Autonomous**: Modal sandbox (no back-and-forth)

**Impact**: Reduces cognitive load, consistent behavior, easy to extend.

### 5. Adversarial Review with Gemini
Before implementing non-trivial changes, plan validation:
- Research → Draft plan → Gemini review → Implement

**Impact**: Catches architectural issues early, reduces rework.

---

## Adversarial Review Results

### BLOCKERs ✅

**None identified.**

Rules have strong safety guardrails:
- Safe-Carry-Forward prevents data loss
- Checkpoints provide undo buttons
- Panic Button prevents infinite loops
- Code comment preservation prevents breakage
- Shared rules prevent inconsistency

Safe to implement.

---

### SHOULDs ⚠️

**7 important refinements needed before autonomous agents go live:**

#### 1. Complete Panic Button Criteria
**Current**: 5 criteria documented
**Missing**: Explicit handling for:
- `Permission denied` on file operations
- `Out of disk space` errors
- `Network timeouts` during git operations
- `Memory exhaustion` (process killed)
- `Corrupted git repository` (unable to read objects)
- `Authentication failure` (expired GitHub token)

**Fix**: Expand Panic Button section to explicitly list these, or update criterion #4 ("unfamiliar error pattern") to be clear it's a catch-all.

**Effort**: 30 min  
**Priority**: HIGH (these are real scenarios)

---

#### 2. Classifier Logic Documentation ⭐ CRITICAL
**Current**: Rules assume classifier exists. No documentation on logic.

**Missing Spec**:
- How does classifier pick repo when ambiguous? ("fix the bug" could mean 10 repos)
- What confidence threshold triggers "ask user"?
- What clarification questions does quick-reply ask?
- How does it use past session history?

**Impact**: Critical for quick-reply agent to function correctly.

**Fix**: Create `docs/architecture/classifier-logic.md` documenting:
```markdown
# Classifier Logic

## Intent Extraction
- bug_fix: "fix", "broken", "issue", "bug"
- feature: "add", "implement", "create", "build"
- refactor: "improve", "refactor", "optimize"
- question: "how", "what", "why", "check", "status"
- deploy: "deploy", "release", "go live"

## Repo Disambiguation
- If repo mentioned by name: use that
- If multiple matches: score by similarity (levenshtein distance)
- If score < 0.75: ask user "did you mean X or Y?"

## Confidence Threshold
- If confidence < 0.75: ask user
- Otherwise: proceed to Modal

## Example Clarifications
- "Which repo? (frontend, auth-service, docs?)"
- "Should I also update tests?"
- "Any special constraints? (backward compat, performance, etc.)"
```

**Effort**: 1-2 hours  
**Priority**: CRITICAL (blocks quick-reply agent)

---

#### 3. Commit Message Standardization
**Current**: Examples show inconsistent formats:
```bash
git commit -m "wip: snapshot before sync"
git commit -m "feat: clear, descriptive message"
git commit -m "fix(classifier): handle multi-repo messages"
git commit -m "feat: your final clean message [ENG-XXX]"
```

**Missing**: Formal specification:
- Conventional commits format? (feat:, fix:, refactor:, docs:, test:, chore:)
- When to include Linear ID?
- Scope in parens or not?
- Max line length?

**Fix**: Formalize in `docs/ai/shared/git-workflow.md`:
```markdown
## Commit Message Format

Use Conventional Commits:
<type>(<scope>): <subject> [LINEAR-ID]

**Types**: feat, fix, refactor, docs, test, chore
**Scope**: optional (e.g., classifier, modal, api)
**Subject**: imperative, lowercase, no period, max 50 chars
**Linear ID**: optional but recommended [ENG-456]

Examples:
- feat(classifier): add intent detection for multi-repo messages
- fix(modal): handle session timeout gracefully [ENG-456]
- docs: update git workflow documentation
- test(api): add integration tests for session endpoint
```

**Effort**: 30 min  
**Priority**: SHOULD (improves maintainability)

---

#### 4. Test Runner Flexibility
**Current**: Rules assume `npm test` everywhere.

**Reality**: Different repos use:
- Jest (`jest`)
- Vitest (`vitest`)
- Mocha (`mocha`)
- Custom scripts (`npm run test:unit`, `npm run test:ci`, `npm run test:e2e`)

**Fix**: Update validation loop in git-workflow.md:
```markdown
## Test Execution

Before running tests:
1. Check package.json for test scripts
2. Use appropriate command:
   - If `test` script exists: `npm test`
   - If `test:ci` exists: `npm run test:ci` (for CI env)
   - If `test:unit` exists: `npm run test:unit` (start with unit tests)
   - Otherwise: look for vitest, jest, mocha configs

3. If still unclear: run `npm test` as fallback
4. Parse output for failures, fix, re-run (max 3 attempts)
```

**Effort**: 1 hour  
**Priority**: SHOULD (prevents test failures)

---

#### 5. Checkpoint Cleanup Policy
**Current**: "Leave checkpoint, report to user"

**Missing Details**:
- Auto-cleanup on session termination?
- Expire old checkpoints?
- Manual cleanup command documented?
- Could grow unbounded

**Risk**: Checkpoint branches accumulate over time, clutter repo.

**Fix**: Add to git-workflow.md:
```markdown
## Checkpoint Cleanup

- **Successful operation**: Delete checkpoint immediately
  `git branch -D checkpoint-<branch>-<timestamp>`

- **Failed operation**: Keep checkpoint, report to user with command:
  `git branch -D checkpoint-feat-xyz-1704123456`

- **Auto-expire**: Branches older than 30 days may be deleted

- **Session termination**: List any remaining checkpoints, include cleanup command
```

**Effort**: 30 min  
**Priority**: SHOULD (prevents repo clutter)

---

#### 6. Gemini MCP Fallback
**Current**: Rules say "if available" but no fallback.

**Risk**: If Gemini API is down, agent can't validate plans. Then what?

**Fix**: Add to planning.md:
```markdown
## Gemini Fallback

If Gemini is unavailable:
1. Use heuristic checklist:
   - [ ] Specific file paths documented?
   - [ ] Success criteria clear?
   - [ ] Assumptions listed?
   - [ ] Any obvious security issues?
   - [ ] Any breaking changes to public APIs?
   - [ ] Any unhandled edge cases?

2. If checklist passes: proceed with implementation
3. If checklist fails: escalate (ask human for review)

This is a safety net, not ideal, but prevents complete blocker.
```

**Effort**: 30 min  
**Priority**: SHOULD (resilience)

---

#### 7. Squash Scope Clarity
**Current**: "Squash all WIP snapshots before final push"

**Ambiguity**: If agent makes multiple logical commits:
```bash
wip: snapshot
wip: snapshot after rebase
feat: add classifier logic
docs: update README
tests: add classifier tests
```

Should squash into:
- **Option A**: One mega-commit (lose granularity)
- **Option B**: Three logical commits (feat, docs, tests separate)

**Fix**: Clarify in git-workflow.md:
```markdown
## Squashing Strategy

Squash only WIP snapshots into ONE clean commit per logical change.

Example:
Before:
- wip: snapshot before sync
- wip: snapshot after rebase
- feat: add classifier logic
- docs: update README
- tests: add classifier tests

After squash:
- feat: add classifier logic (all WIP collapsed)
- docs: update README (kept separate)
- tests: add classifier tests (kept separate)

Each logical change gets its own squashed commit.
```

**Effort**: 30 min  
**Priority**: SHOULD (maintains readable history)

---

## CONSIDERs 💡

**5 items for Phase 2 (not MVP):**

1. **Error Pattern Capture**: Persistent memory so future sessions learn
2. **Session Lifecycle Documentation**: Timing, resource cleanup, startup/shutdown
3. **Code Review Depth**: Linting, coverage checks, human review workflow
4. **Ownership Verification Robustness**: Test branch ownership script in real git scenarios
5. **Autonomous Code Style Enforcement**: Auto-format (prettier), auto-lint (eslint)

---

## Risk Assessment

| Risk | Severity | Status | Mitigation |
|------|----------|--------|-----------|
| Incomplete Panic Button | MEDIUM | SHOULD #1 | Expand criteria |
| Classifier ambiguity | HIGH | SHOULD #2 | Document logic |
| Inconsistent commits | LOW | SHOULD #3 | Standardize |
| Test runner failures | MEDIUM | SHOULD #4 | Check package.json |
| Checkpoint clutter | LOW | SHOULD #5 | Cleanup policy |
| Gemini unavailable | MEDIUM | SHOULD #6 | Fallback heuristics |
| Squash scope unclear | LOW | SHOULD #7 | Clarify |
| Learning disabled | LOW | CONSIDER #1 | Phase 2 |
| Session timing unknown | LOW | CONSIDER #2 | Phase 2 |
| Shallow code review | LOW | CONSIDER #3 | Phase 2 |

---

## Timeline

### Before Autonomous Agents Go Live
**Est. 4-6 hours** to address 7 SHOULDs:
1. Complete Panic Button - 30 min
2. Classifier logic doc - 2 hours ⭐
3. Commit message format - 30 min
4. Test runner flexibility - 1 hour
5. Checkpoint cleanup - 30 min
6. Gemini fallback - 30 min
7. Squash scope - 30 min

### Phase 2 (After MVP)
Implement 5 CONSIDERs when appropriate.

---

## What's Working Well ✅

1. **Safe-Carry-Forward pattern**: Proven, eliminates data loss
2. **Checkpoint branches**: Clever undo button
3. **Panic Button**: Clear escalation criteria
4. **Shared rules**: Reduces cognitive load
5. **Code comment preservation**: Conservative, safe
6. **Practical examples**: Every rule has snippets
7. **Clear structure**: Obvious which rules apply where
8. **Transparency**: Most rules explain the WHY

---

## Next Steps

### Immediate (Before Autonomous Agents)
1. ✅ Rules committed to repo
2. 📋 You review findings (this document)
3. 🔧 Fix 7 SHOULDs (optional BEFORE deployment, but recommended)
4. 🏗️ Build Modal sandbox layer

### Phase 1 (MVP)
- OpenCode agent in Modal
- Slack bot with classifier
- Session state storage
- GitHub integration
- Classifier logic documented (CRITICAL)

### Phase 2
- Memory MCP for learning
- Session lifecycle optimization
- Extended code review tools
- Error pattern capture

---

## Files Affected

**Created**:
- `docs/ai/autonomous-agent.md` - Modal agent rules
- `docs/ai/local-development.md` - You + Claude rules
- `docs/ai/shared/git-workflow.md` - Shared git rules
- `docs/ai/shared/planning.md` - Shared planning rules
- `docs/ai/ADVERSARIAL_REVIEW.md` - This analysis
- `.claude/claude.md` - Index + quick reference

**Removed**:
- `docs/ai/straya.md` - Chat personality (deferred)
- `docs/ai/harvest-mode.md` - Consolidated
- `docs/ai/comments.md` - Moved to shared/
- `docs/ai/git.md` - Moved to shared/

**Updated**:
- `.gitignore` - Added logs/

---

## Commit

```
6d096b7 - docs(ai): restructure rules for Ramp-inspired autonomous agent architecture
Author: David Currie
Date: Wed Jan 14 19:50:12 2026 +1100

13 files changed, 1740 insertions(+), 343 deletions(-)
```

---

## Conclusion

Your rules are **solid**. They're well-designed, safety-first, and ready to guide AI agents in this repo.

The 7 SHOULDs are important but **not blocking**. Address them before autonomous agents go to production, but they don't prevent you from building and testing locally first.

**You've got a good foundation. Go build.** 🚀

---

**Questions?** Review the detailed findings:
- `docs/ai/ADVERSARIAL_REVIEW.md` - Full analysis
- `docs/ai/GEMINI_ADVERSARIAL_REVIEW.md` - Self-review details
- Individual rule files for context
