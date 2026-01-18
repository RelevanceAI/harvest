# Agent Rules

You are working on the Harvest codebase locally with Claude Code.

> **Build-time replacement:** In the Daytona container, this file is replaced with `autonomous-agent.md` content during the Docker build. The repo version (this file) contains local development rules; the container version contains autonomous agent rules.

## Context

**Mode:** Local (human + Claude collaborative development)
**Intent:** Human judgment available, interactive problem-solving, iterative refinement

All shared rules from `@docs/ai/shared/*.md` apply (loaded via `.claude/CLAUDE.md`).

## Development Commands

Harvest uses pnpm for package management and Husky for git hooks. The main executor package is at `packages/daytona-executor/`.

### Initial Setup

```bash
# Clone and install dependencies
git clone https://github.com/RelevanceAI/harvest.git
cd harvest
pnpm install
```

Husky pre-commit hooks are automatically installed via the `prepare` script.

### Common Development Commands

| Command | Action |
|---------|--------|
| `pnpm run validate` | Run all validation scripts |
| `pnpm run test:snapshot` | Test Daytona snapshot image (requires Docker) |

### Daytona Executor Commands

```bash
cd packages/daytona-executor/snapshot

# Build the Docker snapshot image
./build.sh

# Test snapshot image (no API keys required)
./test-snapshot.sh

# Test with Claude Agent SDK (requires CLAUDE_CODE_OAUTH_TOKEN)
./test.sh "your prompt here"
```

### Testing Workflow

**Before committing:**
```bash
# Husky hooks run automatically on `git commit`
# To test hooks manually:
pnpm run validate
```

### Requirements

- Node.js 20+
- pnpm (install via `corepack enable && corepack prepare pnpm@latest --activate`)
- Docker (for Daytona executor development)
- GitHub personal access token (for repository operations)

## MCP Tools Available

- **github**: GitHub API for PRs, issues, checks
- **linear**: Linear issue tracking and project management
- **chrome**: Browser automation for testing UI changes
- **gemini**: Plan review and adversarial analysis

## Workspace Isolation (Git Worktrees)

**Problem:** Multiple Claude instances on the same repo cause conflicts (file changes, git state, test runs).

**Solution:** Use git worktrees to create isolated workspaces for each feature. Use when:

- Starting new feature work (especially if other Claude instances might be running)
- Complex changes that need dedicated workspace
- When you want to preserve main branch state while experimenting

**How to set up:**

Use the `/superpowers:using-git-worktrees` skill, which will:
1. Create isolated workspace at `.worktrees/<branch-name>/`
2. Verify `.worktrees` is in `.gitignore` (already configured for Harvest)
3. Run `pnpm install` and baseline tests
4. Report ready when clean

Cleanup happens via `/superpowers:finishing-a-development-branch` skill

## Workflow

### 1. Before You Make Any Changes

Git hooks prevent commits to main/master/develop automatically.

Follow the planning workflow in `@docs/ai/shared/planning.md`:
1. **Research** - Read existing code, understand patterns, identify constraints
2. **Plan** - Draft plan with file paths, changes, success criteria
3. **Validate** - Use Gemini for adversarial review if complex
4. **Execute** - Implement with confidence

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

## Git Workflow

Follow `@docs/ai/shared/git-workflow.md` for Safe-Carry-Forward sync, checkpoint patterns, and squashing.

### Local Mode Notes

**Checkpoint flexibility:**
- Optional for simple rebases (use judgment based on risk)
- Can pause during conflict resolution to ask for help
- Time available to verify squashed commits before pushing

**Escalation:**
- If checkpoint recovery needed after 3 attempts, ask user for help directly
- Can discuss git strategy before attempting risky operations

## Complexity Evaluation

Follow `@docs/ai/shared/complexity-heuristic.md` to evaluate task complexity and decide when to invoke brainstorming.

### Local Mode Notes

**User override flexibility:**
- Heuristic is a guideline, not a mandate
- Can ask: "This task seems [simple/complex]. Should I brainstorm or proceed to planning?"
- User may override based on their preferences or project context
- Interactive discussion helps calibrate complexity assessment

## Executing Plans

When using the executing-plans skill:

- **You can pause for feedback**: You have human judgment available
- **"Ready for feedback" is optional**: Report progress and wait if you want validation, or continue immediately
- **Use judgment**: If uncertain about next batch, pause and ask. If confident, keep going.

The skill's checkpoints are opportunities to pause, not mandates.

## Planning

Follow `@docs/ai/shared/planning.md` for all planning workflows (research, draft plan, Gemini review, implementation).

**Iterative planning:**
- Can iterate on plans with user before finalizing
- User may provide additional context during planning phase
- Gemini review is recommended but optional (human can review instead)
- Can pause implementation to revise plan if requirements change

You have **human judgment** available — use it:

- Ask yourself: "Does this make sense? Would I review this favorably?"
- Iterate on code if tests fail (don't just retry blindly)
- Think about edge cases and maintainability
- Commit to Linear or Slack if you hit snags

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
