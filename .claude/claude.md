# Harvest AI Agent Rules

You are working on the Harvest codebase. Load the appropriate rules for your context.

## Your Context

**Are you working locally with Claude (terminal)?**
→ Load `@docs/ai/local-development.md`

**Are you running in a Modal sandbox as the Harvest background agent?**
→ Load `@docs/ai/autonomous-agent.md`

---

## Shared Rules (Apply to All Contexts)

All agents follow these core rules:

| Rule | Location | Purpose |
|------|----------|---------|
| **Git Workflow** | `@docs/ai/shared/git-workflow.md` | Safe-Carry-Forward sync, snapshots, checkpoints, squashing |
| **Code Comments** | `@docs/ai/shared/code-comments.md` | Explain WHY not WHAT; preserve existing comments |
| **Planning** | `@docs/ai/shared/planning.md` | Research before coding, use Gemini for adversarial review |

---

## MCP Tools Index

Your available MCP tools depend on context:

### Local Development (You + Claude)

| Server | Purpose | When to Use |
|--------|---------|-------------|
| **github** | GitHub API (PRs, issues) | Creating PRs, managing issues, checking CI |
| **linear** | Linear issue tracking | Linking to issues, updating progress |
| **chrome** | Browser automation | Testing UI changes, visual verification |
| **gemini** | Plan review & web research | Adversarial review of implementation plans |

**Note**: Memory MCP deferred to Phase 2. Browser/devtools tools (playwright, devtools) available only in later phases.

### Autonomous Agent (Modal Sandbox)

Same MCP tools as local development, plus:
- Full bash/git/filesystem access within sandbox

---

## Planning Workflow

For non-trivial changes (architectural, multi-file, uncertain approach):

### 1. Research
Read existing code, understand patterns, identify constraints

### 2. Draft Plan
- Specific file paths
- Concrete changes
- Assumptions
- Success criteria

### 3. Validate (If Available)
```
gemini_chat(
  message="[YOUR DETAILED PLAN with file paths and assumptions]",
  system_prompt="You are an adversarial code reviewer. Analyze this plan and identify concerns. Categorize as:\n- BLOCKER: Must fix\n- SHOULD: Should address\n- CONSIDER: Optional\n\nFor each concern, explain WHY and suggest a fix."
)
```

### 4. Implement
Address BLOCKER concerns first, then build with confidence

### 5. Audit
Check work against project conventions before committing

See `@docs/ai/shared/planning.md` for full guidance.

---

## Git Rules Quick Reference

**Safe-Carry-Forward Pattern:**
```bash
git add -A && git commit -m "wip: snapshot before sync" --no-verify
git fetch origin
git rebase origin/<branch>  # safe on your branches
npm test
git reset --soft origin/<branch>
git commit -m "feat: clean message"
git push origin <branch>
```

**Checkpoint Pattern (Before Risky Ops):**
```bash
CURRENT=$(git branch --show-current)
git checkout -b "checkpoint-$CURRENT-$(date +%s)"
git checkout "$CURRENT"
# attempt risky operation
# if successful: git branch -D checkpoint-*
# if failed: report checkpoint branch to user
```

See `@docs/ai/shared/git-workflow.md` for full details.

---

## Code Comments: WHY Over WHAT

✅ **Good**: 
```typescript
// Need pixelRatio to convert DOM coords to canvas coords on high-DPI displays
const ratio = window.devicePixelRatio;
```

❌ **Bad**:
```typescript
// Gets the pixel ratio
const ratio = window.devicePixelRatio;
```

**Key rules**:
- NEVER remove existing comments (only update if your change makes them incorrect)
- Explain intent, constraints, trade-offs, surprising behavior
- Don't narrate code or explain basic language features
- Preserve all comments exactly as they are

See `@docs/ai/shared/code-comments.md` for full policy.

---

## Glossary

- **Safe-Carry-Forward**: Sync pattern using snapshots (commits) instead of stash
- **Snapshot**: WIP commit before risky operation (e.g., `wip: snapshot before sync`)
- **Checkpoint**: Backup branch created before risky operation (provides undo button)
- **Squash**: Collapse multiple WIP snapshots into one clean commit (`git reset --soft`)
- **Panic Button**: When to stop and ask for help (test failures, unfamiliar errors, etc.)

---

## Philosophy

**Never lose work. Commit frequently. Sync safely. Complete autonomously.**

Snapshots are your black box recorder. Checkpoints are your undo buttons. Squashing maintains clean history. Panic Button ensures you never get truly stuck.

The rules enable high autonomy while maintaining safety and team sanity.
