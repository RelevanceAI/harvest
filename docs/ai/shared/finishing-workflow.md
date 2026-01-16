# Finishing a Development Branch

Adapted from superpowers:finishing-a-development-branch skill.

## Pre-Check (MANDATORY)

Before presenting completion options:

```bash
# Run full test suite
npm test

# Check exit code
echo $?  # Must be 0
```

**BLOCKER**: Cannot proceed if tests fail. Fix failures first.

## 4 Completion Options

### Option 1: Merge to Base Branch Locally

**When**: Small internal tools, quick fixes not needing review

**Steps**:
1. Merge feature branch to base (e.g., main)
2. Run tests on merged result
3. Push merged base branch
4. Delete feature branch
5. Cleanup worktree (if used)

### Option 2: Push and Create Pull Request

**When**: Standard workflow (most common)

**Steps**:
1. Push feature branch to remote
2. Create PR using Harvest conventions (emojis, dad joke)
3. Reference plan PR number if applicable
4. Preserve branch for review
5. Report PR link to Slack

### Option 3: Keep Branch As-Is

**When**: Work in progress, need to pause

**Steps**:
1. Push current state (optional)
2. Preserve worktree
3. Document status in Slack
4. Agent can resume later

### Option 4: Discard This Work

**When**: Experimental work, dead end, no longer needed

**Steps**:
1. Require typed confirmation: "discard"
2. Delete feature branch
3. Cleanup worktree
4. Report discarded to Slack

**Safety**: Requires explicit confirmation to prevent accidental loss.

## Checkpoint Cleanup Timing

### On Success (Options 1 & 2)

After merge/PR creation confirmed:
```bash
# Delete all checkpoint branches created during session
git branch -D checkpoint-*

# Verify cleanup
git branch | grep checkpoint
# Should return nothing
```

### On Panic

**DO NOT cleanup** - preserve all checkpoint branches for human investigation.

Include checkpoint names in panic report.

### On Keep/Discard (Options 3 & 4)

Option 3: Leave checkpoints (work may resume)
Option 4: Cleanup checkpoints with branch deletion

## Memory Updates

After successful completion:
```
memory_add_observation(
  entity="SuccessfulWorkflows",
  observation="[Context] Task '[description]' → [workflow: brainstorm/skip → plan → execute → finish option] → PR merged/completed [DATE]"
)
```

After failure requiring panic:
```
memory_add_observation(
  entity="FailurePatterns",
  observation="[DATE] PANIC: [what failed] → Checkpoint: [branch name] → [diagnostic info]"
)
```
