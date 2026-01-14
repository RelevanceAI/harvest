# Git Workflow (Shared Rules)

This workflow applies to all contexts: local development, autonomous agents, and collaborative work.

## Philosophy

**Never lose work. Commit frequently. Sync safely. Rebase autonomously.**

Snapshots are your black box recorder. Checkpoints are your undo buttons. Squashing maintains team history.

---

## 1. Branch Naming & Ownership

**Format**: `<type>/<description>` (e.g., `feat/slack-classifier`, `fix/modal-context-passing`)

**Fallback with Linear**: `<type>/<linear-id>-<description>` when Linear issue exists (e.g., `feat/ENG-123-classifier`)

**Ownership Principle**:
- You have **full autonomy** on branches you created
- You are a **guest** on shared branches (`main`, `develop`, or branches with other contributors)

---

## 2. Safe-Carry-Forward Sync Pattern

**Never use `git pull` or `git stash`.** Snapshots are permanent; stash can be lost.

### Before Any Sync

```bash
# 1. Snapshot all local changes
git add -A
git commit -m "wip: snapshot before sync" --no-verify

# 2. Fetch latest from remote
git fetch origin
git status
```

### Handle Divergence

**If branch has diverged AND you own it:**
```bash
git rebase origin/<branch>
```

**If branch has diverged AND others have commits:**
- STOP. Notify user. Don't rebase shared branches autonomously.

### Why Commits Over Stash

- Commits are **permanent** (survive session resets, detached HEAD)
- Rebase provides **clearer conflict resolution** than stash pop
- Snapshots serve as **black box recorder** of your process
- No "meaningful vs trivial" decision overhead

### Red Flags During Fetch

- `(forced update)` on `origin` → remote was rebased, reset to remote
- `+` prefix on ref update → history was rewritten
- If detected on shared branches → STOP and investigate

---

## 3. Checkpoint Pattern (Before Risky Operations)

When attempting conflict resolution, complex rebases, or uncertain operations, create a checkpoint first.

### Command Sequence

```bash
CURRENT=$(git branch --show-current)
git checkout -b "checkpoint-$CURRENT-$(date +%s)"
git checkout "$CURRENT"

# Now attempt risky operation
# ... rebase, resolve conflicts, etc. ...

# If successful and tests pass:
git branch -D checkpoint-*

# If failed after 3 attempts:
# Leave checkpoint intact and report to user
```

### Retention Policy

- **Successful operations**: Delete checkpoint immediately
- **Failed operations**: Keep checkpoint, report branch name to user
- **Manual cleanup**: User can `git branch -D checkpoint-*` when satisfied

### Recovery Procedure

If operation failed after 3 attempts:

```bash
git reset --hard checkpoint-<branch>-<timestamp>
```

This restores you to the pre-operation snapshot. No work is lost because the checkpoint captured everything.

---

## 4. Squash Before Final Push

Collapse all WIP snapshots into one clean commit:

```bash
git reset --soft origin/<branch>
git commit -m "feat: clear, descriptive message"
```

This is **non-interactive** (no editor), so it works in sandboxes without Vim/Nano.

### Commit Message Format

- **Why, not WHAT**: The diff shows what changed. Your message explains *why*.
  - Good: `fix(classifier): handle multi-repo messages with confidence scoring`
  - Bad: `fixed bug`, `updated files`, `ENG-123`
- **Include Linear ID if applicable**: `feat(modal): session context passing [ENG-456]`
- **Be concise and clear**: One line summary, then blank line, then details if needed

---

## 5. Verify Before Push

Always check what you're pushing:

```bash
git log origin/<branch>..HEAD --oneline
```

Look for:
- Unexpected merge commits
- More commits than expected
- Commits from other authors

**If something looks wrong: STOP.** Reset to remote and investigate.

```bash
git reset --hard origin/<branch>
```

---

## 6. High-Autonomy Problem Solving

Instead of stopping for errors, use a **Validation Loop**:

| Scenario | Action |
|----------|--------|
| **Lint/Test Failure** | 1. Parse error → 2. Fix code → 3. Re-run. Max 3 attempts. If still failing, report to Panic Button. |
| **Merge Conflict** | 1. Create checkpoint → 2. Resolve conflicts → 3. Run tests → 4. If tests pass: delete checkpoint, continue → 5. If tests fail: retry (max 3 attempts) → 6. If still failing: keep checkpoint, report. |
| **Stale Branch** | Always `git rebase origin/main` into feature branch. Treat conflicts as "Merge Conflict" scenario. |
| **Hooks Blocked** | Never use `--no-verify` for real commits. Only WIP snapshots can bypass hooks. For real commits, fix the root cause. |

---

## 7. Dangerous Operations (Allowed Under Conditions)

You are authorized to perform these **only if safety checks pass**:

| Operation | Condition |
|-----------|-----------|
| `git reset --hard` | Allowed to align with `origin` IF you've committed current work first (snapshot commit) |
| `git push --force-with-lease` | Allowed if you own the branch (see ownership check below) |
| `git clean -fd` | Allowed ONLY for build artifacts or `.gitignore`'d files |
| `git rebase` | Allowed on your own feature branches to keep them clean |
| `git commit --amend` | Approved to fold temporary snapshots into main commits |
| `git reset --soft` | Preferred method for squashing WIP snapshots (non-interactive) |
| `git rebase -i` | Approved for squashing, but prefer `git reset --soft` (no editor) |

### Branch Ownership Check (Automated)

Count unique logical contributors:

```bash
# Get all unique author names
AUTHORS=$(git log --format='%an' | sort -u)
CO_AUTHORS=$(git log --format='%(trailers:key=Co-Authored-By,valueonly)' | \
             sed 's/ <.*//' | sort -u | grep -v '^$')

# Combine and count
ALL_CONTRIBUTORS=$(echo -e "$AUTHORS\n$CO_AUTHORS" | sort -u | grep -v '^$' | wc -l)

# Decision logic
if [ "$ALL_CONTRIBUTORS" -eq "1" ]; then
  echo "✓ Sole contributor (agent only) - force-push allowed"
  git push --force-with-lease
elif [ "$ALL_CONTRIBUTORS" -le "2" ]; then
  echo "✓ Agent + human pair - force-push allowed (co-authored)"
  git push --force-with-lease
else
  echo "✗ Multiple contributors - guest status (push without force)"
  git push
fi
```

---

## 8. The Panic Button (When to Stop)

Even with high autonomy, **STOP and report to user** if:

1. **Test Failure After 3 Attempts**: Validation loop results in persistent test failures
2. **Unrecoverable File Loss**: Accidentally deleted a file that wasn't tracked/committed/snapshotted
3. **Forced Update on Shared Branch**: Detected `(forced update)` on `main`, `develop`, or shared branches
4. **Unfamiliar Error Pattern**: Git operation fails with error not in existing handling logic
5. **Ownership Verification Failure**: Cannot determine branch ownership reliably

When you hit the Panic Button:
- Leave checkpoint branch intact
- Post clear error message to Slack with:
  - What failed and why
  - Checkpoint branch name (if applicable)
  - What human intervention is needed

---

## Summary: Safe-Carry-Forward Flow

```
Local Changes
    ↓
Snapshot: git commit -m "wip: snapshot before sync"
    ↓
Fetch: git fetch origin
    ↓
Check divergence: git status
    ↓
Rebase (if you own): git rebase origin/<branch>
    ↓
Resolve conflicts (with checkpoint if risky)
    ↓
Run tests to validate
    ↓
Squash: git reset --soft origin/<branch> && git commit
    ↓
Verify: git log origin/<branch>..HEAD --oneline
    ↓
Push: git push origin <branch>
    ↓
Complete: No work lost, clean history maintained
```
