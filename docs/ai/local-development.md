# Local Development Rules

You are working on the Harvest codebase locally with Claude (OpenCode).

## MCP Tools Available

- **github**: GitHub API for PRs, issues, checks
- **linear**: Linear issue tracking and project management
- **chrome**: Browser automation for testing UI changes
- **gemini**: Plan review and adversarial analysis

## Core Rules

Follow these shared rules as your foundation:

- `@docs/ai/shared/git-workflow.md` — Safe-Carry-Forward sync pattern, checkpoint branches, squashing
- `@docs/ai/shared/code-comments.md` — WHY over WHAT/HOW, preserve existing comments
- `@docs/ai/shared/planning.md` — Research before coding, use Gemini for adversarial review

## Workflow

### 1. Before You Start

- **Read the existing code**: Understand patterns, naming conventions, test style
- **Check project rules**: Review `docs/ai/` and `docs/architecture/` for guidance
- **Plan for non-trivial work**: Research the problem, draft a plan, validate with Gemini if uncertain

### 2. While You Code

- **Commit frequently**: Use Safe-Carry-Forward snapshots (`git commit -m "wip: snapshot before sync"`)
- **Test before committing**: Verify changes work (except WIP snapshots)
- **Preserve existing comments**: Only update if your change makes them incorrect
- **Follow project conventions**: Match existing code style, patterns, test approach

### 3. Before You Push

- **Squash WIP snapshots**: `git reset --soft origin/<branch>` then commit with clean message
- **Verify your work**: `git log origin/<branch>..HEAD --oneline` — check for unexpected commits
- **Run tests**: Ensure nothing broke
- **Review your own code**: Spot-check for issues, typos, edge cases

### 4. After You Push

- **Create a PR**: Use clear title and description
- **Link to Linear**: Reference any issue numbers
- **Be ready to iterate**: Address review feedback promptly

## Git Workflow (Local-Specific)

### Safe-Carry-Forward Pattern

Before syncing with remote:

```bash
# Snapshot all work
git add -A && git commit -m "wip: snapshot before sync" --no-verify

# Fetch latest
git fetch origin

# Rebase if you own the branch (safe on feature branches you created)
git rebase origin/<branch>

# Resolve conflicts if any, then test
npm test

# Squash WIP snapshots
git reset --soft origin/<branch>
git commit -m "feat: your clean message"

# Verify before push
git log origin/<branch>..HEAD --oneline

# Push
git push origin <branch>
```

### Checkpoint Pattern (For Risky Operations)

Before complex rebase or conflict resolution:

```bash
CURRENT=$(git branch --show-current)
git checkout -b "checkpoint-$CURRENT-$(date +%s)"
git checkout "$CURRENT"

# Now attempt the risky operation (e.g., rebase, conflict resolution)

# If successful: delete checkpoint
git branch -D checkpoint-*

# If failed after 3 attempts: keep checkpoint, report to team
```

See `@docs/ai/shared/git-workflow.md` for full details on when/how to use checkpoints.

## Planning Workflow

For non-trivial changes:

1. **Research** the problem space (read existing code, understand dependencies)
2. **Draft a plan** with file paths, specific changes, assumptions
3. **Get adversarial feedback** (use Gemini if available)
4. **Address blockers** before coding
5. **Implement with confidence**

Example Gemini call:

```
gemini_chat(
  message="Plan: I want to add a classifier layer to the Slack bot...
[describe your approach with specific file paths and changes]",
  system_prompt="You are an adversarial code reviewer. Identify BLOCKER, SHOULD, and CONSIDER concerns..."
)
```

See `@docs/ai/shared/planning.md` for full guidance.

## Key Differences from Autonomous Agent

You have **human judgment** available — use it:

- Ask yourself: "Does this make sense? Would I review this favorably?"
- Iterate on code if tests fail (don't just retry blindly)
- Think about edge cases and maintainability
- Commit to Linear or Slack if you hit snags

The rules are the same as the autonomous agent, but you can reason about ambiguity and adjust on the fly.

## Common Scenarios

### Lint or Test Failure

1. Parse the error
2. Fix the code
3. Re-run
4. If it fails again, debug further (don't just retry blindly)

### Merge Conflict

1. Create a checkpoint branch (if you're unsure about resolution)
2. Resolve conflicts carefully
3. Test thoroughly
4. If tests pass, delete checkpoint and push
5. If tests fail, keep checkpoint and ask for help

### Branch Stale Against Main

```bash
git rebase origin/main
```

This is safe on your own feature branch. If conflicts arise, treat as merge conflict scenario.

### Uncertain About Approach

- **Draft a plan** with specific file paths and changes
- **Ask Gemini** for adversarial review (blockers, edge cases, tradeoffs)
- **Adjust and implement** with confidence

## When to Stop and Ask for Help

- Tests failing after 3-4 tries and you can't figure out why
- Uncertain about architectural approach (use Gemini first)
- Merge conflict is too complex to resolve safely
- Something feels wrong but you can't pinpoint it (ask the team)

Otherwise: **Debug, iterate, fix, and push.**

## Key Principles

- **Think before you code**: Planning saves time
- **Commit frequently**: Snapshots are safety nets
- **Test before pushing**: Confidence matters
- **Audit against conventions**: Match your team's patterns
- **Use your judgment**: You're human, the rules are guidelines
