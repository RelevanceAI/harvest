# Systematic Debugging & Failure Escalation

## Decision Tree

```
Error occurs
  ↓
Classify error type
  ↓
┌──────────────────┬──────────────────┬──────────────────┐
│ SIMPLE           │ COMPLEX          │ SYSTEM           │
│ (lint, syntax,   │ (logic bugs,     │ (permissions,    │
│  obvious)        │  integration)    │  disk, network)  │
└──────────────────┴──────────────────┴──────────────────┘
         ↓                  ↓                  ↓
   Fail Forward      Systematic          Panic Button
   (max 3 retries)   Debugging           (immediate)
         ↓                  ↓                  ↓
   Still failing?    3 fixes failed?
         ↓                  ↓
   → Systematic      → Panic Button
     Debugging
```

## Loop Detection (Circuit Breaker)

**Problem**: Agent can get stuck retrying same failed approach repeatedly.

**Solution**: Simple state-aware detection (start basic, iterate based on learnings).

**Gemini Validation**: RECOMMENDED approach - pragmatic starting point with viable iteration path.

### Simple Loop Detection (v1)

Before each debugging attempt:

```bash
# 1. Check if code changed since last attempt
CHANGED_FILES=$(git diff --name-only HEAD | wc -l)

# 2. Record attempt
memory_add_observation(
  entity="SessionProgress",
  observation="Attempt ${N}: ${action} (files changed: ${CHANGED_FILES}) → ${result}"
)

# 3. Check for loop (last 3 attempts)
recent_attempts = memory_query("SessionProgress last 3 attempts")

if (CHANGED_FILES == 0 && action == recent[-1].action) {
  # LOOP DETECTED: No code changes, trying same thing
  trigger_circuit_breaker()
}
```

### Circuit Breaker Actions

When loop detected:
1. **STOP** - Don't retry immediately
2. **Ask user**: "I've tried this approach 2-3x without code changes. Do you have a suggestion for a different direction?"
3. **OR** Enter plan mode for structured reset
4. **Clear** SessionProgress after human input (fresh start)

### What This Catches ✅

Obvious loops:
```
Attempt 1: npm test → FAIL (syntax error)
Attempt 2: npm test (no code changes) → FAIL (same error)
Attempt 3: npm test (no code changes) → LOOP DETECTED ✋
```

### Known Limitations (v1) ⚠️

Will NOT detect:

❌ **Environment changes** (HIGHEST PRIORITY if this fails):
```
rm -rf node_modules && npm install
git diff: 0 files (node_modules gitignored)
→ False positive: blocks retry
```

❌ **Same-file different-line changes**:
```
Fix line 45 → still fails
Fix line 46 (same file) → git diff shows change ✓
(Actually works correctly - git diff detects change)
```

❌ **Semantic loops** (fixing symptoms not root cause):
```
Agent makes code changes each time
But error remains the same
→ False negative: doesn't catch loop
```

❌ **Longer loops** (>3 steps):
```
Agent loops through 6-step cycle
Only checking last 3 attempts
→ Misses loop
```

### Mitigation Strategy

**Primary**: Panic Button backstop (3 retries → escalate)
- Loop detection is ADDITIONAL safety net
- Panic Button catches what loop detection misses
- Human escalation handles edge cases

**Secondary**: Learn from failures
```
memory_add_observation(
  entity="LoopDetectionFailures",
  observation="[DATE] Simple detection failed: [scenario] → Suggests need for [environment tracking/content hashing/etc]"
)
```

Review `LoopDetectionFailures` periodically → add complexity where proven necessary.

### Iteration Path (Based on Gemini Feedback)

**Priority 1 - If false positives occur**: Environment tracking
- Track cache hash (node_modules, dist/)
- Track .env hash
- Include in state comparison

**Priority 2 - If same-file issues**: File content hashing
- Hash file contents, not just names
- Detects line 45 vs line 46 changes

**Priority 3 - If longer loops observed**: Extended window
- Increase from 3 to 5-7 attempts
- Or graph-based cycle detection

**Priority 4 - If semantic loops waste time**: Error message analysis
- Include error message hash in state
- Same error + code changes = potential semantic loop

**Priority 5 - If whitespace causes issues**: AST comparison
- Compare syntax trees, not raw text
- Ignore formatting-only changes

**Decision criteria**: Add feature only when simple version demonstrably fails in practice.

---

## Simple Errors → Fail Forward

**Criteria**: Error is straightforward to fix
- Linting errors (missing semicolon, unused variable)
- Syntax errors (typo, missing bracket)
- Obvious bugs (wrong variable name, off-by-one)
- Import/module resolution (missing import statement)

**Process**:
1. Parse error message
2. Apply fix
3. Re-run verification
4. Max 3 attempts
5. If still failing → Escalate to Systematic Debugging

## Complex Errors → Systematic Debugging

**Criteria**: Error requires investigation
- Logic bugs (wrong output, unexpected behavior)
- Test failures (unclear why test fails)
- Integration issues (component interaction)
- Race conditions or timing issues
- Mysterious failures (no obvious cause)

**4-Phase Process**:

### Phase 1: Root Cause Investigation
- Examine error messages and stack traces thoroughly
- Reproduce consistently (identify exact steps)
- Review recent changes (git diff, git log)
- Add instrumentation at component boundaries
- Trace data flow backward to original source

### Phase 2: Pattern Analysis
- Find similar working code in codebase
- Compare working vs broken (all differences)
- Identify dependencies and assumptions
- Check for recent changes to dependencies

### Phase 3: Hypothesis and Testing
- Form specific hypothesis about root cause
- Test with minimal changes (one variable at a time)
- Verify results before proceeding

### Phase 4: Implementation
- Write failing test that reproduces bug
- Implement single targeted fix (address root cause, not symptom)
- Verify fix works without breaking other tests
- Document root cause and fix in commit message

**Escalation**: If 3 fixes fail → Question the architecture, not just the code. Trigger Panic Button.

## System Errors → Panic Button (Immediate)

**Criteria**: Environmental/infrastructure issues beyond code fixes
- Permission denied on files/directories
- Out of disk space
- Network timeout (git fetch/push)
- Memory exhaustion / OOM
- Corrupted git repository
- Authentication failure (expired tokens)
- Module resolution failure (missing deps, can't install)
- Database/service connectivity

**Process**:
1. **STOP** - Don't retry, don't attempt fixes
2. **Preserve state** - Keep checkpoint branches intact
3. **Gather diagnostics**:
   - Full error message (not truncated)
   - Environment details (disk space, network status)
   - Recent commands executed
   - Checkpoint branch name for recovery
4. **Report to Slack** with structured panic message
5. **Session ends** - Human intervention required

### Panic Report Format

```
❌ [ERROR TYPE] (Panic Button triggered)
Operation: [what was being attempted]
Error: [full error message]

Context:
- Repo: [owner/repo]
- Branch: [current branch]
- Task: [task description]
- Checkpoint: [checkpoint branch name if exists]

Attempts made: [what fixes were tried]
Root cause: [diagnosed cause if known]

Next: [what human needs to do]
```

## Memory Integration

After debugging session:
```
memory_add_observation(
  entity="FailurePatterns",
  observation="[DATE] PANIC/RESOLVED: [error type] → [root cause] → [fix applied] → [outcome]"
)
```

Before debugging similar error:
```
memory_query("Similar errors to [current error]")
→ Check FailurePatterns entity
→ Known root causes for this error type?
→ Successful fixes from past?
```
