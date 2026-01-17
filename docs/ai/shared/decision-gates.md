# Decision Gates

## Purpose

Prevent the agent from treating rules as optional guidelines based on perceived task simplicity.

**Core principle:** System-enforced gates remove the agent's ability to rationalize bypassing processes.

## The Problem This Solves

**Broken mental model:** "Simple task → skip process"
**Correct mental model:** "Every task → follow process → process determines path"

Without explicit gates, the agent will rationalize:
- "This is just docs" → skip planning
- "This is just docs" → skip feature branch
- "This is simple" → skip asking user

Gates enforce process regardless of perceived simplicity.

---

## Gate 1: Branch Protection (MANDATORY)

**Trigger:** Before ANY tool use that modifies files (Edit, Write, Bash with git commands)

**Check:**
```bash
CURRENT_BRANCH=$(git branch --show-current)
if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "master" || "$CURRENT_BRANCH" == "develop" ]]; then
  # BLOCKER: Cannot proceed
  echo "ERROR: On protected branch [$CURRENT_BRANCH]"
  exit 1
fi
```

**Action if on protected branch:**
1. STOP immediately - abort current action
2. Report to user: "I'm on [$CURRENT_BRANCH]. I must create a feature branch first."
3. Follow `@docs/ai/shared/git-workflow.md` branch naming convention:
   - Format: `<type>/<description>` (e.g., `feat/slack-classifier`, `fix/modal-context`)
   - With Linear: `<type>/<linear-id>-<description>` (e.g., `feat/ENG-123-classifier`)
4. Ask user: "Should I create branch [suggested-name]?"
5. WAIT for explicit approval
6. Create branch: `git checkout -b [approved-name]`
7. Verify: `git branch --show-current` confirms new branch
8. Only then proceed with original action

**Under NO circumstances:**
- Commit to main/master/develop
- "Just this once" exceptions
- "It's just docs" exceptions
- ANY exception

---

## Gate 2: Local Mode - Ask Before Acting (MANDATORY)

**Trigger:** Before ANY action that modifies codebase or external state

**Mode detection (immutable):**
```
IF SessionStart loaded "local-development.md" → Local mode
IF SessionStart loaded "autonomous-agent.md" → Autonomous mode
Agent reports mode, does NOT decide mode
```

**Local mode rule (non-negotiable):**

ALWAYS ask user before proceeding, regardless of perceived task complexity.

**Question format varies by complexity assessment:**
- Simple task: "This seems straightforward (just adding docs section). Should I proceed?"
- Complex task: "This is complex (architectural changes, multi-file). Should I brainstorm first or draft a plan?"

**But asking is MANDATORY. No exceptions for "simple" tasks.**

**Process:**
1. State what you're about to do
2. State complexity assessment (simple/medium/complex)
3. Ask user for approval/direction
4. WAIT for response (no timeout rationalization - wait indefinitely)
5. Only proceed after explicit approval

**Autonomous mode:**
- Skip asking (full autonomy expected)
- Execute with fail-forward pattern

---

## Gate 3: Pre-Tool-Use Verification

**Trigger:** Before calling ANY tool (Bash, Edit, Write, Git commands)

**Checks:**
1. **Branch check:** Am I on a feature branch? (Gate 1)
2. **Mode check:** Local mode - did I ask? Autonomous mode - proceeding autonomously
3. **Intent check:** Does this action match stated/approved intent?

**If any check fails:** STOP and address the failure before proceeding.

---

## Self-Monitoring (Accountability)

After completing any task, record in memory:

```
entity: "GateExecutionLog"
observation: "[DATE] Task: [description] | Gates executed: [1: YES/NO, 2: YES/NO, 3: YES/NO] | If NO: Why skipped? | Outcome: [success/failure]"
```

**Pattern detection:**
If multiple "NO" entries appear → Agent is bypassing gates → Human should intervene

---

## Success Criteria

1. ✅ Zero commits to main/master/develop
2. ✅ In local mode: Always ask before acting (even for "simple" tasks)
3. ✅ Feature branches created BEFORE any file modifications
4. ✅ GateExecutionLog shows consistent "YES" for all gates

---

## Common Rationalizations (DO NOT ACCEPT)

| Rationalization | Reality |
|----------------|---------|
| "This is just docs" | Docs are code. Follow process. |
| "This is too simple to ask" | Simplicity is irrelevant. Ask. |
| "User said 'fix' so I have permission" | Permission to address problem ≠ permission to skip process. |
| "I'll just commit this one thing to main" | Never. Create feature branch. |
| "The process is overkill for this" | Process exists BECAUSE human judgment fails. |
| "I know what to do, asking wastes time" | Asking is the safety check. Not optional. |

---

## Integration with Existing Rules

This file provides the enforcement mechanism for:
- `@docs/ai/shared/git-workflow.md` - Feature branch requirement
- `@docs/ai/shared/complexity-heuristic.md` - When to ask (always in local mode)
- `@docs/ai/shared/planning.md` - Planning workflow triggers

Decision gates are the "HOW" - they enforce the rules that other files describe.
