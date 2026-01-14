# Harvest AI Agent Rules - Complete Plan for Adversarial Review

## Context

This is a restructure of AI agent rules for the Harvest project (Ramp Inspect-inspired background coding agent). The rules govern behavior across 3 contexts:

1. Local development (human + Claude with OpenCode)
2. Autonomous Modal sandbox agent (Slack-triggered, high autonomy)
3. Shared rules (applied to both)

## Architecture

The Harvest system follows Ramp Inspect's philosophy:

- Slack classifier picks repo + intent from user message
- If unclear → quick-reply agent asks for clarification in Slack
- Once clear → Modal sandbox spins up with full autonomy
- Agent researches, plans, codes, tests, commits, pushes, creates PR
- Session shuts down (work persists in GitHub)

## Complete Ruleset Summary

### 1. SHARED RULES (All Contexts)

**Git Workflow** (`docs/ai/shared/git-workflow.md`):
- Safe-Carry-Forward pattern: snapshot commits instead of stash
- Before sync: `git add -A && git commit -m "wip: snapshot before sync"`
- Rebase autonomously on owned branches
- Checkpoint pattern for risky operations (creates backup branch with timestamp)
- Squash WIP snapshots before final push: `git reset --soft origin/<branch>`
- High-autonomy problem solving with validation loop (3 attempts max)
- Panic Button: when to stop (test failures after 3 attempts, unrecoverable file loss, forced updates on shared branches, unfamiliar errors)

**Code Comments** (`docs/ai/shared/code-comments.md`):
- Explain WHY, not WHAT/HOW
- CRITICAL: NEVER remove existing comments unless explicitly asked
- Focus on intent, constraints, trade-offs, surprising behavior
- Don't narrate code or explain basic language features
- Preserve all comments exactly as they are

**Planning** (`docs/ai/shared/planning.md`):
- Think before code for non-trivial changes
- Research → Draft plan → Validate with Gemini → Implement → Audit
- Gemini adversarial review for architectural decisions, multi-file changes, uncertain approaches
- Act on feedback: BLOCKER (fix first), SHOULD (balance), CONSIDER (optional)
- Audit against project conventions before committing

### 2. LOCAL DEVELOPMENT (`docs/ai/local-development.md`)

**MCP Tools**: github, linear, chrome, gemini

**Workflow**: Research → Plan → Code → Commit → Push → PR

**Key differences from autonomous**:
- Human judgment available (can reason about ambiguity)
- Can iterate thoughtfully (no time pressure)
- Can ask for help directly
- Same git/planning rules, but with human flexibility

**Scenarios documented**:
- Lint/test failure (debug carefully, don't retry blindly)
- Merge conflict (checkpoint, resolve carefully, test thoroughly)
- Uncertain about approach (use Gemini)

### 3. AUTONOMOUS AGENT (`docs/ai/autonomous-agent.md`)

**Operating Environment**: Modal sandbox, full dev environment, per-user session

**Core Principles**:
- Execute, don't ask
- Fail forward (diagnose and fix autonomously)
- Complete the loop (end-to-end: research → code → test → commit → push → PR)
- Work in public (post Slack updates at milestones)

**Task Lifecycle**:
1. Session startup (Slack → classifier → sandbox)
2. Research & plan (read codebase, draft plan, optional Gemini review)
3. Implementation (code autonomously, follow conventions, commit frequently, test continuously)
4. Validation (full test suite, verify success criteria, self-review code)
5. Completion (squash commits, push, create PR, post to Slack)

**Problem Solving**: Same validation loop with 3-attempt max, then Panic Button

**Panic Button Criteria**:
- Test failures after 3 attempts
- Unrecoverable file loss
- Forced update on shared branches
- Unfamiliar error patterns
- Branch ownership verification failure

## Key Innovations

1. **Safe-Carry-Forward**: Snapshot commits are permanent, survive session resets, serve as black box recorder
2. **Checkpoint Pattern**: Backup branch before risky ops, provides undo button, enables aggressive autonomous attempts
3. **Panic Button**: Clear escalation criteria, prevents infinite retry loops, enables high autonomy with safety guardrails
4. **Shared Rules**: Same patterns across local dev and autonomous (local has human flexibility)
5. **Adversarial Review with Gemini**: Plan validation before implementation, structured BLOCKER/SHOULD/CONSIDER categorization

## File Structure

```
docs/ai/
├── .claude/claude.md (index + MCP tools index)
├── local-development.md (you + Claude)
├── autonomous-agent.md (Modal sandbox agent)
└── shared/
    ├── git-workflow.md
    ├── code-comments.md
    └── planning.md
```

**Deleted obsolete files**:
- straya.md (chat personality rules, deferred)
- harvest-mode.md (consolidated into autonomous-agent.md)
- comments.md (moved to shared/)
- git.md (moved to shared/git-workflow.md)

## Design Questions for Adversarial Review

1. **Checkpoint Complexity**: Is the checkpoint pattern with timestamps too complex? Should it be simpler for local dev?

2. **3-Attempt Limit**: Is 3 attempts the right threshold? Could be 2 (aggressive) or 4 (lenient).

3. **Panic Button Criteria**: Are all 5 criteria necessary? Any missing?

4. **Phase 2 Deferral**: Memory MCP deferred to Phase 2. Is this the right call for MVP, or should we include it now?

5. **Classifier Logic**: Not documented in rules (no spec for how to classify messages). Should this be in docs/architecture/?

6. **Session Handoff**: When Slack classifier picks repo, should context be passed via:
   - Initial prompt text to Modal?
   - Session state in API?
   - Both?

7. **Gemini Quota**: Rules suggest using Gemini "sparingly" for deep review. Is default quick review (gemini_chat) sufficient?

8. **Commit Message Format**: Rules show examples but no strict format. Should we formalize (e.g., conventional commits)?

9. **Testing Mandate**: Rules say "test before committing" but no detail on test coverage % or which tests to run. Should this be specified?

10. **Error Logging**: Rules don't mention error logging to persistent memory. Should we capture error patterns for future sessions?

## Assumptions About Harvest

1. All repos have standard node/npm setup (implied by `npm test` in examples)
2. Slack classifier exists and will be built separately (not documented in rules)
3. Modal snapshots/image builds handled separately (mentioned in README, not in agent rules)
4. Durable Objects or equivalent session storage handled by API layer
5. GitHub authentication via user tokens (not bot account)

## Risk Assessment

**LOW RISK**:
- Git workflow is proven (similar to Ramp, well-tested pattern)
- Code comment policy is conservative (doesn't change existing code, only adds)
- Planning with Gemini is optional (can work without it)

**MEDIUM RISK**:
- Autonomous agent with 3-attempt limit could get stuck in retry loops if Panic Button criteria are missed
- Checkpoint branches could accumulate if agent crashes without cleanup
- "Rebase autonomously on owned branches" assumes ownership checks are reliable (script provided but untested)

**UNKNOWN/DEFERRED**:
- Classifier accuracy (will users send clear enough messages?)
- Session lifecycle timing (how long is acceptable?)
- Memory persistence across sessions (Phase 2, but important for learning)
- Error handling in Modal sandbox (what happens when bash commands fail?)

## Strengths

1. **Clear context switching**: Rules explicitly say "load local-development.md OR autonomous-agent.md"
2. **Safety nets**: Snapshots, checkpoints, Panic Button prevent catastrophic failure
3. **Shared foundation**: Same git/comment/planning rules reduce cognitive load
4. **Practical examples**: Code snippets for every major pattern
5. **Transparency**: "Why" is explained for most rules

## Weaknesses / Questions

1. **Implicit classifier logic**: How does classifier decide repo when message is ambiguous? (e.g., "fix the bug" could mean frontend, backend, docs)

2. **Commit message consistency**: Examples show different formats:
   - `feat: descriptive message`
   - `fix(canvas): prevent memory leak`
   - `feat: classifier adds intent detection`
   Should be standardized?

3. **Test suite assumptions**: Rules assume `npm test` works everywhere. What if repo uses different test runner (jest, vitest, mocha)?

4. **Ownership check script**: The bash script for branch ownership verification is complex. Tested? Reliable?

5. **Checkpoint cleanup**: What if Modal crashes with checkpoint branches left behind? Manual cleanup needed?

6. **Squash timing**: Rule says "squash before final push" but what if agent makes multiple commits (e.g., one feature commit + one test fix)? Should each get its own squash or all into one?

7. **Gemini MCP availability**: Rules reference Gemini as optional ("if available") but provide no fallback. What if Gemini API is down?

8. **Code review in vacuum**: Autonomous agent "reviews own code" but lacks human perspective. Could catch syntax errors but not architectural issues.

## Recommendations for Adversarial Review

### Key Questions for Reviewer

1. **Panic Button**: Are all 5 criteria sufficient? Missing "permission denied", "disk full", "network error"?

2. **Classifier Ambiguity**: How will quick-reply agent know which clarification questions to ask?

3. **Phase 2 Memory**: Should persistent learning be in Phase 1 instead?

4. **Checkpoint Cleanup**: Should be automatic (session termination) or manual (user)?

5. **Fallback Strategy**: What if Gemini is unavailable? Default to heuristics?

### Before Implementation

Get Gemini feedback on:
- Classifier ambiguity resolution
- Panic Button criteria (complete?)
- Phase 2 memory strategy (essential now?)

### Before Deployment

Add documentation for:
- `docs/architecture/classifier.md` (how intent extraction works)
- `docs/architecture/session-lifecycle.md` (sandbox startup/shutdown/handoff)
- Standardized commit message format
- Test runner flexibility (not just npm test)

### Risk Mitigation

- Add checkpoint cleanup as part of session termination
- Add fallback if Gemini unavailable
- Document test runner flexibility
- Consider memory persistence in Phase 1

---

**Status**: Submitted for adversarial review with Gemini  
**Awaiting**: BLOCKER, SHOULD, CONSIDER categorized feedback  
**Next**: Address concerns, finalize, commit to repo
