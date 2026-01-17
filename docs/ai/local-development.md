# Local Development Rules

You are working on the Harvest codebase locally with Claude (OpenCode).

## Context

**Mode:** Local (human + Claude collaborative development)
**Intent:** Human judgment available, interactive problem-solving, iterative refinement

All shared rules from `@docs/ai/shared/*.md` apply (loaded via `.claude/CLAUDE.md`).

## Development Commands

Harvest is a Python project using `uv` for dependency management. The main package is located at `packages/modal-executor/`.

### Initial Setup

```bash
# Navigate to the package directory
cd packages/modal-executor

# Create virtual environment and install dependencies
uv venv --allow-existing
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"

# Install pre-commit hooks (one-time setup)
pre-commit install

# Authenticate with Modal
modal setup

# Create required secrets
modal secret create harvest-github GITHUB_TOKEN=ghp_xxx
```

### Common Development Commands

| Command | Action |
|---------|--------|
| `pytest` | Run all tests (this should be used by default) |
| `pytest -v` | Run tests with verbose output |
| `pytest tests/test_sandbox.py` | Run specific test file |
| `pytest -m "not modal"` | Run tests excluding Modal-dependent tests |
| `pytest --cov` | Run tests with coverage report |
| `pre-commit run --all-files` | Run all pre-commit hooks (linting, formatting, type checking) |
| `ruff check .` | Run linter |
| `ruff check --fix .` | Run linter and auto-fix issues |
| `mypy src/` | Run type checker |
| `modal list` | Verify Modal setup |

### Testing Workflow

**Default test command:**
```bash
pytest
```

**Before committing:**
```bash
# Pre-commit hooks will run automatically on `git commit`
# To test hooks manually:
pre-commit run --all-files
```

**Skipping Modal-dependent tests:**
```bash
# Use this if you don't have Modal credentials configured
pytest -m "not modal"
```

**Running specific tests:**
```bash
# Single test file
pytest tests/test_sandbox.py

# Single test function
pytest tests/test_sandbox.py::test_basic_execution

# All tests in verbose mode
pytest -v
```

### Stopping Development Servers

Modal sandboxes are ephemeral and auto-terminate. For local development:

- **Python processes**: `Ctrl+C` in the terminal
- **Pre-commit hooks**: Run automatically on commit (no server to stop)
- **pytest**: Tests run and exit automatically

### Requirements

- Python 3.11+
- `uv` package manager (install via `pip install uv` or `brew install uv`)
- Modal account (for sandbox execution)
- GitHub personal access token (for repository cloning)

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
3. Run `npm install` and baseline tests
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
