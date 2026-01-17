# Agent Core Principles

**Audience:** ALL Harvest AI agents (local and autonomous modes)

Non-negotiable foundational rules.

## Mode Detection

**You do not decide your mode. You report it.**

```
IF SessionStart loaded "local-development.md" → Local mode
IF SessionStart loaded "autonomous-agent.md" → Autonomous mode
```

Never guess. Never switch. The SessionStart hook determines mode.

## Principle 1: Never Commit to Protected Branches

**ALWAYS create a feature branch before ANY work.**

### For Local Development (Human + Claude)

Git hooks enforce this automatically. If you find yourself on main/master/develop:

```bash
git checkout -b <type>/<description>
# Examples: docs/update-readme, feat/add-classifier
```

### For Autonomous Agent (Modal Sandbox)

Before any file modifications:
1. Check: `git branch --show-current`
2. If on main/master/develop: Create feature branch immediately
3. Use naming convention: `<type>/<description>` or `<type>/<linear-id>-<description>`

**No exceptions.**

## Principle 2: Research and Plan Before Changes

See `@docs/ai/shared/planning.md` for the full workflow.

**Key point:** Never skip directly to execution. Always: research → plan → validate → execute.

Exception: If you're executing an approved plan, you're already past planning.

## Principle 3: Safe-Carry-Forward Git Workflow

See `@docs/ai/shared/git-workflow.md` for full details.

**Never** use `git pull` or `git stash`. Use snapshot commits and checkpoint branches.
