## Git Workflow

### 1. Branch Naming & Ownership

**Format**: `<type>/<linear-id>-<short-description>` (e.g., `feat/ENG-123-user-auth`)
**Fallback**: `<type>/<short-description>` when no Linear ID exists (e.g., `chore/update-deps`)

**Ownership Principle**: You have full autonomy on branches you created. You are a guest on shared branches (`main`, `develop`, or branches with other contributors).

### 2. The "Safe-Carry-Forward" Sync

**Never use `git pull` or `git stash`.** Use snapshot commits to ensure persistence and trackability. This applies to ALL sync scenarios, including temporary changes.

```bash
# 1. Snapshot all local changes (black box recorder)
git add -A
git commit -m "wip: autopilot snapshot before sync [ENG-XXX]" --no-verify

# 2. Sync with remote
git fetch origin
git checkout <branch>

# 3. Handle divergence autonomously
git status
# If "diverged" AND you created this branch:
git rebase origin/<branch>  # Keep clean linear history

# If "diverged" AND others have commits: STOP and notify user

# 4. Clean-up mandate (before final push)
# Non-interactive squash: collapse all commits into one clean commit
git reset --soft origin/<branch>
git commit -m "feat: your final clean message [ENG-XXX]"

# Autopilot Tip: This instantly collapses all WIP snapshots without needing
# interactive editor (picks/squashes). Avoids Vim/Nano complexity.
```

**Why commits over stash:**
- Commits are permanent (survive session resets, detached HEAD scenarios)
- Rebase provides clearer conflict resolution interface than `stash pop`
- No "meaningful vs trivial" decision overhead
- Snapshots serve as black box recorder of agent's process

**Red flags during fetch:**
- `(forced update)` - remote was rebased, reset to remote
- `+` prefix on ref update - history was rewritten

### 2.1. Safety Branches (The Checkpoint Pattern)

When attempting risky operations (conflict resolution, complex rebases), create a checkpoint branch BEFORE making changes. This provides a safety net without stopping the autonomous workflow.

**When to Create Checkpoints:**
- Before resolving merge/rebase conflicts
- Before attempting a complex interactive rebase
- Before force-pushing to a branch with multiple contributors (if ownership check is ambiguous)

**Command Sequence:**
```bash
CURRENT=$(git branch --show-current)
git checkout -b "checkpoint-$CURRENT-$(date +%s)"
git checkout "$CURRENT"

# Now perform risky operation
# ... attempt resolution, rebase, etc. ...

# If successful and tests pass:
git branch -D "checkpoint-$CURRENT-"*

# If failed after 3 attempts:
# Leave checkpoint branch intact and notify user:
# "Operation failed. Checkpoint branch: checkpoint-feat-auth-1234567890"
```

**Retention Policy:**
- Successful operations: delete checkpoint immediately
- Failed operations: keep checkpoint, report name to user
- Manual cleanup: user can `git branch -D checkpoint-*` when satisfied

**Rationale:**
- Eliminates "fear of destroying state" that causes "ask user" friction
- Enables aggressive autonomous attempts (checkpoint = undo button)
- Time-based suffix prevents name collisions

**Recovery Procedure (The "Undo" Command):**

If the agent detects it is "lost" or operation failed after 3 attempts:

```bash
# Roll back to known good state before risky operation began
git reset --hard checkpoint-<branch>-<timestamp>
```

This is the ultimate "undo" that restores the agent to the checkpoint state. No work is lost because the checkpoint branch captured the pre-operation snapshot.

**Example Recovery Flow**:
1. Agent creates checkpoint: `checkpoint-feat-auth-1704123456`
2. Agent attempts complex rebase, encounters errors
3. After 3 failed attempts, agent executes:
   ```bash
   git reset --hard checkpoint-feat-auth-1704123456
   ```
4. Agent reports to user: "Operation failed. Rolled back to checkpoint: checkpoint-feat-auth-1704123456"

### 3. Before Any Push

**Always verify what you're about to push:**
```bash
git log origin/<branch>..HEAD --oneline
```

Check for:
- Merge commits you didn't intentionally create
- More commits than expected
- Commits from other authors

**If something looks wrong, STOP.** Reset to remote and investigate.

### 4. High-Autonomy Problem Solving

Instead of stopping for errors, enter a **Validation Loop**:

| Scenario | Autopilot Action |
|----------|------------------|
| Lint/Test Failure | 1. Parse error → 2. Fix code → 3. Re-run. (Max 3 attempts). If still failing, trigger Panic Button #1. |
| Merge Conflict | 1. Create checkpoint branch (`conflict-backup/<branch>`) → 2. Attempt resolution of ALL conflicts → 3. Run test suite → 4. If tests pass: delete checkpoint, proceed → 5. If tests fail: retry (max 3 attempts) → 6. If still failing: STOP, report checkpoint branch name. |
| Stale Branch | Always `git rebase origin/main` into feature branch. If conflicts arise, treat as "Merge Conflict" scenario above. |
| Hooks Blocked | Never use `--no-verify` for real commits. Only WIP snapshots (`wip: autopilot snapshot`) can bypass hooks. For real commits, fix the root cause. |

### 5. Dangerous Operations

You are authorized to perform these **only if safety checks pass**:

| Operation | Autopilot Condition |
|-----------|---------------------|
| `git reset --hard` | Allowed to align with `origin` IF you have committed current work first (snapshot commit) |
| `git push --force` | Allowed if branch ownership check passes (≤2 contributors with agent included). Use `--force-with-lease` |
| `git clean -fd` | Allowed ONLY for build artifacts or files in `.gitignore` |
| `git rebase` | Allowed on your own feature branches to keep them clean |
| `git commit --amend` | Approved to fold temporary snapshots into main commits |
| `git reset --soft HEAD~1` | Approved to undo temporary snapshot after successful sync |
| `git reset --soft` | Preferred method for squashing WIP snapshots (non-interactive) |
| `git rebase -i` | Approved for squashing, but prefer `git reset --soft` (no editor needed) |

**How to verify branch ownership (automated):**
```bash
# Autonomous Force-Push Check
# Count unique logical contributors (handles co-authored commits)

# Get all unique author names
AUTHORS=$(git log --format='%an' | sort -u)
CO_AUTHORS=$(git log --format='%(trailers:key=Co-Authored-By,valueonly)' | \
             sed 's/ <.*//' | sort -u | grep -v '^$')

# Combine and count
ALL_CONTRIBUTORS=$(echo -e "$AUTHORS\n$CO_AUTHORS" | sort -u | grep -v '^$' | wc -l)

# Agent identity (matches entrypoint.sh attribution)
AGENT_NAME=$(git config user.name | sed 's/ (Autopilot)//')

# Decision logic
if [ "$ALL_CONTRIBUTORS" -eq "1" ]; then
  # Sole contributor (agent only)
  git push --force-with-lease
elif [ "$ALL_CONTRIBUTORS" -eq "2" ] && echo "$ALL_CONTRIBUTORS" | grep -q "$AGENT_NAME"; then
  # Agent + one human (co-authored pair, still considered sole logical ownership)
  git push --force-with-lease
else
  # Multiple logical contributors - guest status
  git push  # Let it fail naturally if history diverged
fi
```

### 6. The Panic Button (When to Stop)

Even in Autopilot, **STOP and report to the user** if:

1. **Test Failure After 3 Attempts**: Conflict resolution or validation loop results in persistent test failures (max 3 iterations)
2. **Unrecoverable File Loss**: You accidentally deleted a file that wasn't tracked, committed, or snapshotted
3. **Forced Update on Shared Branch**: You detect `(forced update)` on `main`, `develop`, or other shared branches during fetch
4. **Unfamiliar Error Pattern**: Git operation fails with error not covered by existing handling logic (e.g., permission denied, corrupted repo)
5. **Ownership Verification Failure**: Branch ownership check returns ambiguous result (e.g., cannot parse git log output)

### 7. Commit Messages

- **Why, not what**: The diff shows what changed. Your message explains *why*.
  - Good: `fix(canvas): prevent memory leak from undisposed iframes [ENG-456]`
  - Bad: `fixed bug`, `updated files`, `ENG-123`
- **Small, logical commits**: Commit often. Include the Linear ID if one exists.
- **Temporary snapshots**: Use `wip: autopilot snapshot before sync [ENG-XXX]` for sync snapshots. These will be squashed before final push.
- **Test before committing**: Verify changes work before committing (except for temporary snapshot commits).
- **Clean-up before push**: Squash all temporary snapshots using `git reset --soft` to maintain clean history for the team.

### Pull Requests

See `@docs/ai/pull-requests.md` for PR description conventions.
