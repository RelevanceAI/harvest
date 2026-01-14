# GEMINI ADVERSARIAL REVIEW - Four SHOULD Fixes

**Context**: We identified 7 SHOULDs in the Harvest AI Rules audit. Relevance AI integration solved 3 of them. This document submits the 4 remaining fixes for rigorous adversarial review.

---

## SHOULD #1: Panic Button Criteria (COMPLETED FIX)

### Original Issue
Panic Button had only 5 criteria, missing system/environment error cases.

### Fix Applied
**File**: `docs/ai/autonomous-agent.md`

Added 8 additional escalation criteria:
- Permission denied (can't read/write files)
- Out of disk space (no room for writes)
- Network timeout (can't sync with remote)
- Memory exhaustion (OOM, resource limits)
- Corrupted git repository (can't read objects)
- Authentication failure (expired tokens, invalid creds)
- Module/dependency resolution (missing packages, conflicts)
- Database/service connectivity (can't reach external services)

Added detailed examples for each Panic Button scenario showing what to report to Slack:
- What failed
- What was attempted
- Checkpoint branch (if applicable)
- Context and suggested next steps

**Why this matters**: Comprehensive escalation criteria prevent infinite retry loops on unrecoverable system errors. Agents know when to stop and escalate.

---

## SHOULD #5: Checkpoint Cleanup Policy (COMPLETED FIX)

### Original Issue
No policy for checkpoint cleanup. Branches could accumulate unbounded.

### Fix Applied
**File**: `docs/ai/autonomous-agent.md` Session Termination section

Added cleanup mandate:
1. **On success**: Delete all checkpoint branches (`git branch -D checkpoint-*`)
2. **On failure**: Keep checkpoint for human recovery
3. **Auto-expiry**: 7-day retention, then auto-cleanup
4. **Manual cleanup**: User can delete earlier

Added specific bash commands for cleanup and verification.

**Why this matters**: Prevents repository clutter from accumulating checkpoints. Clear lifecycle for temporary branches. Human safety net (keep checkpoint if failed).

---

## SHOULD #6: Gemini/LLM Fallback Strategy (COMPLETED FIX)

### Original Issue
Rules reference Gemini as "if available" but no fallback when unavailable.

### Fix Applied
**File**: `docs/ai/shared/planning.md`

Added fallback section with **heuristic self-review checklist**:
- Specific file paths documented?
- Success criteria clear?
- Assumptions listed?
- Obvious security issues?
- Any breaking changes?
- Edge cases considered?
- Error handling planned?
- Performance impact?
- Dependencies clear?

**Escalation logic**:
- All items checked → proceed with confidence
- 2+ items uncertain → escalate to human review
- For autonomous agents: escalate to Panic Button rather than guessing

**Why this matters**: Enables planning validation without Gemini. Agents can self-review using heuristics. Prevents planning paralysis.

---

## SHOULD #7: Squash Scope Clarity (COMPLETED FIX)

### Original Issue
Ambiguous: should agent squash all commits into one, or keep logical commits separate?

### Fix Applied
**File**: `docs/ai/shared/git-workflow.md`

Clear rule:
- **Squash ONLY WIP snapshots** (temporary, black box recorder commits)
- **Keep logical commits separate** (feat, test, docs, refactor)

Added detailed examples:
- What gets squashed (wip: snapshots)
- What stays separate (independent logical units)
- Two methods (interactive rebase vs reset-soft)
- Before/after examples showing clean history

**Why this matters**: Clean git history for human review. Each logical change has own commit. Easy to review, easy to revert. Follows team conventions.

---

## Adversarial Review Requested

Please analyze these 4 fixes for:

### BLOCKERs (Must Fix)
- Are any of these fixes incomplete or unsafe?
- Missing critical error scenarios?
- Conflicts with other rules?
- Security issues?
- Data loss risks?

### SHOULDs (Should Address)
- Edge cases not covered?
- Error handling gaps?
- Unclear wording/instructions?
- Examples that could be clearer?
- Interactions with other parts of system?

### CONSIDERs (Nice to Have)
- Could wording be improved?
- Additional examples helpful?
- Related guidance missing?
- Phase 2 improvements noted?

---

## How These Fixes Integrate

| Fix | Purpose | Dependencies | Impact |
|-----|---------|--------------|--------|
| Panic Button | Clear escalation | Autonomous agent rules | Prevents infinite loops |
| Checkpoint cleanup | Repository hygiene | Safe-Carry-Forward pattern | Prevents clutter |
| Gemini fallback | Planning validation | Non-trivial change detection | Enables offline planning |
| Squash scope | Clean history | Git workflow | Team code review |

---

## Files Modified

1. **docs/ai/autonomous-agent.md**
   - Expanded Panic Button (lines 170-220)
   - Session Termination with cleanup (lines 197-235)

2. **docs/ai/shared/planning.md**
   - Added Gemini fallback section (after line 35)
   - Heuristic checklist for self-review

3. **docs/ai/shared/git-workflow.md**
   - Rewrote Squash section (lines 105-150)
   - Clear before/after examples
   - Two different squash methods

---

## Testing These Fixes

### Panic Button Testing
- Agent encounters permission denied → escalates correctly
- Agent tries test 3 times → escalates correctly
- Agent recovers from known errors → no escalation
- Slack message format is clear → human understands situation

### Checkpoint Cleanup Testing
- Successful task → checkpoints deleted
- Failed task → checkpoint kept for recovery
- 7-day auto-expiry works → old checkpoints removed

### Fallback Testing
- Gemini available → uses Gemini review
- Gemini unavailable → uses heuristic checklist
- Agent can proceed without Gemini → planning not blocked

### Squash Scope Testing
- Agent makes WIP commits → only WIP squashed
- Agent makes logical commits (feat, test) → kept separate
- Final history is clean → one commit per logical unit

---

## Open Questions for Review

1. **Panic Button timing**: Is 3 attempts the right threshold? (Could be 2, 4, or dynamic?)
2. **Checkpoint auto-expiry**: Is 7 days right? (Could be 3, 14, or indefinite with manual cleanup?)
3. **Fallback checklist completeness**: Are all items necessary? Missing any?
4. **Squash methods**: Is reset-soft preferred over interactive rebase? Both documented?

---

## Confidence Assessment

**Panic Button fix**: HIGH confidence (comprehensive, clear, actionable)
**Checkpoint cleanup**: HIGH confidence (clear policy, examples provided)
**Gemini fallback**: MEDIUM confidence (heuristics are guidelines, not foolproof)
**Squash scope**: HIGH confidence (clear rule with examples)

---

## Ready for Review

All 4 fixes are implemented and ready for adversarial analysis. Please identify:
- Any BLOCKERs that must be fixed
- SHOULDs that should be addressed  
- CONSIDERs for improvement
- Any unintended consequences or conflicts

Thank you for the rigorous review!
