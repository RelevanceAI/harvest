# Adversarial Review of Harvest AI Agent Ruleset

**Date**: 2026-01-14  
**Status**: In Progress (submitted to Gemini for review)  
**Context**: Complete restructure of AI agent rules for Ramp Inspect-inspired architecture

---

## Submission Summary

**What**: Restructured rules for Harvest background coding agent  
**Scope**: 3 contexts (local dev, autonomous Modal agent, shared rules)  
**Key Innovation**: Safe-Carry-Forward git workflow, checkpoint pattern, Panic Button escalation  
**MCP Integration**: github, linear, chrome, gemini (local dev); same + full bash/git (Modal)

---

## Complete Ruleset (Submitted to Gemini)

See embedded plan below or read:
- `docs/ai/shared/git-workflow.md` — Safe-Carry-Forward pattern
- `docs/ai/shared/code-comments.md` — WHY over WHAT/HOW
- `docs/ai/shared/planning.md` — Research before code, Gemini validation
- `docs/ai/local-development.md` — You + Claude rules
- `docs/ai/autonomous-agent.md` — Modal sandbox agent rules
- `.claude/claude.md` — Index + quick reference

---

## Critical Design Questions Submitted

1. **Checkpoint Complexity**: Is timestamp-based checkpoint branch pattern appropriate for both local and autonomous contexts?

2. **3-Attempt Limit**: Right threshold? (Could be 2 aggressive, 4 lenient)

3. **Panic Button Criteria**: All 5 necessary? Any missing edge cases?

4. **Phase 2 Deferral**: Memory MCP deferred to Phase 2. Correct for MVP?

5. **Classifier Logic**: Should intent/repo classification rules be in docs/architecture/ or rules?

6. **Session Context Handoff**: Pass context via initial prompt, session state, or both?

7. **Gemini Fallback**: Rules say "if available" but no fallback. What if API is down?

8. **Commit Message Format**: Standardize on conventional commits or keep flexible?

9. **Test Flexibility**: Rules assume `npm test` everywhere. Document test runner flexibility?

10. **Error Pattern Capture**: Should errors be logged to persistent memory for future learning?

---

## Key Innovations Analyzed

### 1. Safe-Carry-Forward Snapshots
- **Principle**: Snapshot commits instead of `git stash`
- **Why**: Permanent (survive resets), trackable, serve as black box recorder
- **Risk**: Could accumulate many WIP commits if not squashed consistently
- **Mitigation**: Explicit "squash before push" rule, automated in git workflow

### 2. Checkpoint Pattern with Timestamps
- **Principle**: Backup branch before risky ops (e.g., `checkpoint-feat-xyz-1704123456`)
- **Why**: Provides undo button, enables aggressive autonomous attempts
- **Risk**: Branches could accumulate if agent crashes, or user forgets to clean up
- **Mitigation**: Clear retention policy documented, should be part of session termination cleanup

### 3. Panic Button (Clear Escalation Criteria)
- **Principle**: 5 explicit criteria for when to stop and ask for help
- **Why**: Prevents infinite retry loops, enables high autonomy with safety guardrails
- **Risk**: Criteria might be incomplete (what about "permission denied"? "out of disk space"?)
- **Mitigation**: Document edge cases, allow agent to escalate for "unfamiliar error patterns"

### 4. Shared Rules Across Contexts
- **Principle**: Same git/comment/planning rules for local dev and autonomous
- **Why**: Reduces cognitive load, consistent patterns
- **Risk**: Local dev might benefit from simpler checkpoint approach (not all risky ops need backup)
- **Mitigation**: Could have "local dev" variant of rules, but MVP simplicity wins

### 5. Adversarial Review with Gemini
- **Principle**: Plan validation before implementation for non-trivial changes
- **Why**: Catches architectural issues, missing edge cases, trade-offs
- **Risk**: Gemini might be unavailable, hallucinate concerns, or miss real issues
- **Mitigation**: Make it optional, provide structured BLOCKER/SHOULD/CONSIDER categorization

---

## Risk Assessment

### LOW RISK
- **Git workflow**: Proven pattern (similar to Ramp), well-tested conceptually
- **Code comment policy**: Conservative (doesn't change existing code)
- **Planning with Gemini**: Optional, can work without it

### MEDIUM RISK
- **Autonomous 3-attempt limit**: Could get stuck if criteria are incomplete
- **Checkpoint cleanup**: Could accumulate branches if session crashes
- **Branch ownership verification**: Complex bash script, untested in practice

### UNKNOWN/DEFERRED
- **Classifier accuracy**: Will quick-reply agent ask right clarification questions?
- **Session lifecycle timing**: How long is acceptable for startup/shutdown?
- **Memory persistence**: Phase 2 feature, but important for long-term learning
- **Error handling in sandbox**: What happens with bash command failures?

---

## Strengths

1. ✅ **Clear context switching**: Rules say "load X.md OR Y.md"
2. ✅ **Safety nets**: Snapshots, checkpoints, Panic Button prevent catastrophic failure
3. ✅ **Shared foundation**: Same patterns reduce cognitive load
4. ✅ **Practical examples**: Code snippets for every pattern
5. ✅ **Transparency**: Most rules explain "why"
6. ✅ **Ramp-inspired**: Built on proven architecture, not from scratch

---

## Weaknesses / Questions from Plan

1. **Classifier logic**: Implicit. How does it decide repo when ambiguous?
2. **Commit message format**: Inconsistent examples. Should standardize?
3. **Test runner assumptions**: Assumes `npm test`. What about jest/vitest/mocha?
4. **Ownership check script**: Complex. Tested? Reliable?
5. **Checkpoint cleanup**: Part of session termination? Or manual?
6. **Squash scope**: Single squash for all WIP, or per-logical-feature?
7. **Gemini MCP**: What's the fallback if unavailable?
8. **Code review limitation**: Agent reviews own code but lacks human perspective

---

## Pending Gemini Feedback

Awaiting adversarial review on:

### BLOCKER Concerns (Must Fix)
- [ ] Any architectural flaws?
- [ ] Missing escalation criteria?
- [ ] Unsafe git operations?
- [ ] Data loss scenarios?

### SHOULD Concerns (Should Address)
- [ ] Classifier ambiguity handling?
- [ ] Commit message standardization?
- [ ] Test runner flexibility?
- [ ] Error pattern capture for learning?

### CONSIDER Concerns (Optional)
- [ ] Simplify checkpoint pattern?
- [ ] Add memory persistence in Phase 1?
- [ ] Formal conventional commits format?
- [ ] Pre-commit hooks for code quality?

---

## Next Steps (After Gemini Review)

1. **Address BLOCKER concerns** immediately
2. **Incorporate SHOULD concerns** if feasible
3. **Document CONSIDER concerns** for Phase 2
4. **Add architecture docs** for classifier, session lifecycle
5. **Commit rules to repo**
6. **Share findings with team**

---

## Submission Details

**Plan Document**: See below (full text)

**Gemini System Prompt**: 
```
You are an adversarial code reviewer. Analyze this complete ruleset for AI agents
in the Harvest background coding system. Identify concerns and categorize as:

- BLOCKER: Must fix (security, data loss, breaking changes, fundamental flaws)
- SHOULD: Should address (edge cases, error handling, consistency, maintainability)
- CONSIDER: Nice to have (optimizations, minor improvements, Phase 2 features)

For each concern, explain WHY it matters and suggest a fix. Be specific and actionable.
Focus on the ruleset as a system, not individual files.
```

---

## Full Plan Submitted to Gemini

[See docs/ai/ADVERSARIAL_REVIEW_PLAN.md for complete plan text]

---

**Status**: ⏳ Awaiting Gemini feedback...
