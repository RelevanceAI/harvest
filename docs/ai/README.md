# Harvest AI Agent Rules

## Architecture

Harvest uses a **shared base + mode-specific extensions** architecture with complete separation between local and autonomous modes:

### Local Development Mode

**Entry Point:** `.claude/settings.json` (SessionStart hook)

**Loaded Files:**
1. `.claude/claude.md` (shared base rules)
2. `docs/ai/local-development.md` (local mode extensions)

**Characteristics:**
- Human judgment available
- Interactive brainstorming for complex tasks
- Can pause for feedback
- All shared rules loaded via `@docs/ai/shared/*.md` references

### Autonomous Agent Mode (Modal Sandbox)

**Entry Point:** Modal sandbox `sandbox.py::_create_user_settings()`

**Loaded Files:**
1. `/app/claude.md` (shared base, baked into image)
2. `/app/autonomous-agent.md` (autonomous extensions, baked into image)

**Working Directory:** Claude CLI executes from the repo directory, but @ references in baked files resolve relative to the file location (`/app/`)

**Characteristics:**
- Maximum autonomy
- Execute without asking
- Fail forward pattern
- All shared rules loaded via `@docs/ai/shared/*.md` references (resolve from `/app/`)

## Shared Rules

Both modes reference these shared rules via @ references:

- `git-workflow.md` - Safe-Carry-Forward sync, checkpoints, squashing
- `code-comments.md` - WHY over WHAT, preserve existing comments
- `planning.md` - Research before coding, Gemini review, hierarchical planning
- `documentation.md` - Update docs with changes
- `complexity-heuristic.md` - When to brainstorm
- `verification.md` - Smart verification patterns
- `debugging.md` - Systematic debugging with escalation
- `finishing-workflow.md` - 4-option completion framework

## Rules

1. **NO cross-references** between `local-development.md` and `autonomous-agent.md`
2. **SessionStart hooks** are the ONLY way to load mode-specific files
3. **Shared rules** are loaded via `@` references in mode-specific files
4. **Router patterns** (like the old approach with "if local/if autonomous") are not used

## File Organization

```
.claude/
  claude.md                    # Shared base (all modes)
  settings.json               # Local SessionStart hooks (gitignored)
  settings.json.template      # Template for local setup

docs/ai/
  local-development.md        # Local mode extensions
  autonomous-agent.md         # Autonomous mode extensions
  shared/                     # Shared rules (@ referenced)
    git-workflow.md
    code-comments.md
    planning.md
    documentation.md
    complexity-heuristic.md
    verification.md
    debugging.md
    finishing-workflow.md

Modal Image (/app/):
  claude.md                   # Baked from .claude/claude.md
  autonomous-agent.md         # Baked from docs/ai/autonomous-agent.md
  docs/ai/shared/             # Baked, @ references resolve here
  docs/mcp/                   # Baked, @ references resolve here
```

## Validation

Run the validation script to check mode separation:

```bash
./scripts/validate-mode-separation.sh
```

## Historical Context

**Pre-2026-01-17:** Used a router pattern in CLAUDE.md with "if local load X, if autonomous load Y" instructions and repo-specific override mechanisms. This created confusion about which files were loaded when.

**Current (2026-01-17+):** Clean separation with shared base + mode extensions. SessionStart hooks directly load the appropriate files. No cross-references, no overrides, predictable behavior.

**Archived Files:**
- None (AGENTS.md was removed completely, not archived)
