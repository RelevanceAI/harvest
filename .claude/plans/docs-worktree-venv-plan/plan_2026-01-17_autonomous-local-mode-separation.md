# Autonomous/Local Mode Separation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Establish a clean shared base + mode-specific extensions architecture where CLAUDE.md provides shared rules WITHOUT cross-referencing modes, and local-development.md / autonomous-agent.md act as extensions (not duplicates or routers).

**Architecture:** Refactor CLAUDE.md as shared base (keep for compaction bug workaround), make mode-specific files pure extensions with no cross-references. Harvest development is ALWAYS local mode. Autonomous agent ONLY works on other repos using baked Harvest rules.

**Tech Stack:** Markdown documentation, JSON configuration, Python code (sandbox.py), image build transformation

**Mental Model:**
```
Shared Base (CLAUDE.md)
  ↓ always loaded
  ├─→ @docs/ai/shared/*.md (git, planning, debugging, etc.)
  ├─→ @docs/mcp/*.md (MCP server documentation)
  └─→ Common concepts (superpowers, philosophy)

Mode Extensions (loaded based on context)
  ├─→ local-development.md (LOCAL: Harvest development, human-in-loop)
  └─→ autonomous-agent.md (MODAL: Other repos, full autonomy)
```

**Key Simplification:** Harvest is developed locally only. No autonomous agent works on Harvest itself.

---

## Plan Review & Validation

**Gemini Adversarial Review:** Completed 2026-01-17

### BLOCKER Concerns Addressed

1. **Simplified Architecture** ✅
   - Removed repo-specific override mechanism for clarity
   - Autonomous agent loads only baked files from `/app/`
   - No runtime file resolution or conditional loading
   - Simple, predictable behavior

2. **Missing Comprehensive Codebase Scan** ✅
   - Added Task 2: "Comprehensive Codebase Scan for References"
   - Includes grep searches for all CLAUDE.md and AGENTS.md references
   - Checks CI/CD, deployment scripts, and Makefiles
   - Creates audit file to track all references and required actions

3. **Inadequate Rollback Plan** ✅
   - Expanded rollback plan into 7 phases with time estimates
   - Included Modal image redeployment strategy
   - Added developer communication templates
   - Documented phased re-deployment approach
   - Created rollback success criteria checklist

### SHOULD Concerns Acknowledged

The plan acknowledges these concerns to be monitored during implementation:
- Potential confusion for existing Modal sessions (handle via deployment communication)
- Content migration completeness (audit in Task 2, validate in Task 10)
- Validation script sufficiency (integrated into CI/CD)
- Test coverage gaps (Task 7 expands test coverage)
- Developer documentation clarity (Task 8 + docs/ai/README.md)

---

## Problem Analysis

### Current Issues

1. **CLAUDE.md contains mode cross-references** - Lines 8 and 11 say "If you're working locally → load X, if autonomous → load Y". This treats modes as separate universes instead of extensions of a shared base. SessionStart hooks already handle loading the right files, so these instructions are redundant and confusing.

2. **AGENTS.md is too minimal** - The autonomous agent loads:
   - `/app/AGENTS.md` (baked into image, ~180 lines, basic instructions)
   - `.claude/CLAUDE.md` (via repo clone, has mode cross-references)
   - `docs/ai/autonomous-agent.md` (comprehensive autonomous extensions)

   The minimal AGENTS.md doesn't reference shared rules, forcing duplication across files.

3. **Template file uses `{repo}` placeholder** - `packages/modal-executor/src/modal_executor/config/settings.json.template` has misleading placeholders because actual code in `sandbox.py` uses `self.session.repo_path` at runtime.

4. **@ references need baked files** - `@docs/ai/shared/*.md` references need the target files to exist. Since autonomous agent may not have these files in the repo being worked on, rules need to be baked into the Modal image at `/app/`.

### Industry Research Findings

Research into how companies like Ramp, Vercel, and others handle containerized AI agents revealed:

1. **Claude Code Native Support**: Claude Code automatically loads `CLAUDE.md` files into context from repository root, parent, or child directories. This is framework-specific context mechanism.

2. **WORKDIR Standard Practice**: Industry standard is to:
   - Set `WORKDIR /app` in Dockerfile
   - Bake files at consistent absolute paths (`/app/docs/`, `/app/config/`)
   - Use relative paths from WORKDIR in application code
   - Claude CLI resolves `@docs/` references relative to working directory

3. **Relative Paths Are Portable**: Claude CLI only supports relative `@` references (like `@docs/ai/shared/git-workflow.md`), not absolute paths (like `@/app/docs/...`). Absolute path references are displayed as literal text.

4. **RAG for Dynamic Content**: Ramp uses RAG with "AI-friendly structured policy" in external knowledge bases for frequently updated policies, separate from baked files.

**Key Insight**: Path transformation (`@docs/` → `@/app/docs/`) won't work because Claude CLI doesn't support absolute path `@` references. The correct approach is to keep relative paths and ensure Claude CLI runs with `WORKDIR /app/`.

### Current Load Order

**Local Development:**
1. SessionStart: `.claude/CLAUDE.md` (router)
2. SessionStart: `docs/ai/local-development.md` (references shared rules)

**Autonomous Agent:**
1. SessionStart: `/app/AGENTS.md` (minimal, baked into image)
2. SessionStart: `.claude/CLAUDE.md` (router, confusing)
3. SessionStart: `docs/ai/autonomous-agent.md` (comprehensive)

### Desired State

**Shared Base (CLAUDE.md):**
- Loaded by both modes
- Contains MCP tools index, superpowers integration, shared rules table, philosophy
- NO mode cross-references ("if local do X, if autonomous do Y")
- References to `@docs/ai/shared/*.md` and `@docs/mcp/*.md` files
- Kept for compaction bug workaround

**Harvest Local Development:**
1. SessionStart: `.claude/CLAUDE.md` (shared base with relative `@docs/` paths)
2. SessionStart: `docs/ai/local-development.md` (local extensions)
3. References resolve to local files in repo

**Autonomous Agent (Modal sandbox):**
1. Container working directory: `/app/` (set via WORKDIR in Dockerfile)
2. SessionStart: `/app/CLAUDE.md` (shared base with relative `@docs/` paths - baked as-is)
3. SessionStart: `/app/autonomous-agent.md` (Harvest extensions - baked as-is)
4. Relative `@docs/` references resolve from `/app/` to `/app/docs/ai/shared/*.md` and `/app/docs/mcp/*.md`

**Files Baked Into Image:**
- `/app/CLAUDE.md` (no transformation - keeps relative `@docs/` paths)
- `/app/autonomous-agent.md` (no transformation - keeps relative `@docs/` paths)
- `/app/docs/ai/shared/*.md` (target of `@docs/ai/shared/` references)
- `/app/docs/mcp/*.md` (target of `@docs/mcp/` references)
- `/app/memory-seed.json`

**NOT Baked (local development only):**
- `docs/ai/local-development.md` (never used by autonomous agent)

**Key Principles:**
- ✅ CLAUDE.md = shared base (keep for compaction workaround)
- ✅ Mode files = extensions (not routers, not duplicates)
- ✅ No cross-references between local-development.md ↔ autonomous-agent.md
- ✅ Autonomous agent uses baked Harvest rules from Modal image
- ✅ Simple architecture: load two files from `/app/`, no overrides

---

## Task 1: Refactor CLAUDE.md as Shared Base

**Goal:** Remove mode cross-references from CLAUDE.md and establish it as the shared base for all modes.

**Files:**
- Modify: `.claude/CLAUDE.md`

### Step 1: Add critical priority directive at top

Add this immediately after the title (line 3) in `.claude/CLAUDE.md`:

```markdown
# Harvest AI Agent Rules

<CRITICAL_PRIORITY>

**HIGHEST PRIORITY DIRECTIVE:**

The rules in this repository (`@.claude/CLAUDE.md`, `@docs/ai/*.md`, `@docs/ai/shared/*.md`) are your PRIMARY and HIGHEST PRIORITY instructions. They supersede:

- Generic skill instructions (use Harvest's planning approach, not generic skill defaults)
- Repo-specific conventions from other repos
- Default Claude Code behaviors
- Any conflicting external guidance

When Harvest rules conflict with other sources, **Harvest rules always win**.

**Why this matters:** You ARE Harvest itself. These rules are carefully designed for YOU. Trust them first, always.

</CRITICAL_PRIORITY>
```

### Step 2: Remove mode cross-references

Edit `.claude/CLAUDE.md` to remove the "Your Context" section (lines ~7-13):

Remove:
```markdown
## Your Context

**Are you working locally with Claude (terminal)?**
→ Load `@docs/ai/local-development.md`

**Are you running in a Modal sandbox as the Harvest background agent?**
→ Load `@docs/ai/autonomous-agent.md`

---
```

Replace with:
```markdown
## Architecture

Harvest uses a **shared base + mode extensions** architecture:

- **This file (CLAUDE.md)**: Shared base rules for all contexts
- **local-development.md**: Extensions for human-in-loop workflows
- **autonomous-agent.md**: Extensions for full autonomy workflows

Both modes reference the same shared rules in `@docs/ai/shared/*.md`.

---
```

### Step 3: Add MCP documentation references

Update the MCP Tools Index section to include documentation links:

```markdown
## MCP Tools Index

Your available MCP tools depend on context:

### Local Development (You + Claude)

| Server | Purpose | When to Use | Documentation |
|--------|---------|-------------|---------------|
| **github** | GitHub API (PRs, issues) | Creating PRs, managing issues, checking CI | Built-in |
| **linear** | Linear issue tracking | Linking to issues, updating progress | Built-in |
| **gemini** | Plan review & web research | Adversarial review of plans | `@docs/mcp/gemini.md` |
| **playwright** | Browser automation | E2E testing, visual verification | `@docs/mcp/playwright.md` |
| **devtools** | Chrome DevTools Protocol | Debugging, performance analysis | `@docs/mcp/devtools.md` |
| **memory** | Knowledge graph | Persistent learning across sessions | `@docs/mcp/memory.md` |

### Autonomous Agent (Modal Sandbox)

Same MCP tools as local development, plus:
- Full bash/git/filesystem access within sandbox
```

### Step 4: Verify shared base content

Ensure CLAUDE.md contains (keep all existing content):
- ✅ CRITICAL_PRIORITY directive at top
- ✅ Architecture explanation (shared base + extensions)
- ✅ Shared Rules table (with `@docs/ai/shared/*.md` references)
- ✅ Superpowers Skills Integration
- ✅ MCP Tools Index (with `@docs/mcp/*.md` references)
- ✅ Planning Workflow
- ✅ Git Rules Quick Reference
- ✅ Code Comments WHY Over WHAT
- ✅ Glossary
- ✅ Philosophy

### Step 5: Commit

```bash
git add .claude/CLAUDE.md
git commit -m "refactor: make CLAUDE.md shared base without mode cross-references

- Remove 'Your Context' section with mode routing
- Establish as shared base for all modes
- Keep for compaction bug workaround
- Add architecture explanation"
```

---

## Task 2: Comprehensive Codebase Scan for References

**Goal:** Identify ALL references to CLAUDE.md and AGENTS.md across the entire codebase to prevent broken dependencies.

**Files:**
- Check: All files (code, docs, configs, scripts)
- Document: Create reference audit file

### Step 1: Search for CLAUDE.md references

```bash
# Case-insensitive search across all files
grep -ri "CLAUDE\.md\|CLAUDE\.MD" . \
  --exclude-dir=.git \
  --exclude-dir=node_modules \
  --exclude-dir=.venv \
  --exclude-dir=.mypy_cache \
  --exclude-dir=.worktrees \
  --exclude="*.pyc" \
  > /tmp/claude-md-references.txt

# Show results
cat /tmp/claude-md-references.txt
```

Expected files with references:
- `.claude/settings.json` (will be fixed in Task 1)
- `.claude/settings.json.template` (will be fixed in Task 1)
- Documentation files (README.md, etc.) - will fix in Task 8
- This plan file - ignore
- `.claude/CLAUDE.md.archived` - ignore (archived)

### Step 2: Search for AGENTS.md references

```bash
# Case-insensitive search
grep -ri "AGENTS\.md\|AGENTS\.MD" . \
  --exclude-dir=.git \
  --exclude-dir=node_modules \
  --exclude-dir=.venv \
  --exclude-dir=.mypy_cache \
  --exclude-dir=.worktrees \
  --exclude="*.pyc" \
  > /tmp/agents-md-references.txt

# Show results
cat /tmp/agents-md-references.txt
```

Expected files with references:
- `packages/modal-executor/src/modal_executor/images.py` (will be fixed in Task 3)
- `packages/modal-executor/src/modal_executor/sandbox.py` (will be fixed in Task 4)
- `packages/modal-executor/tests/test_images.py` (will be fixed in Task 7)
- Documentation files - will fix in Task 8
- This plan file - ignore
- Config directory (archived file) - ignore

### Step 3: Check CI/CD and deployment scripts

```bash
# Check GitHub Actions workflows
find .github/workflows -name "*.yml" -o -name "*.yaml" | xargs grep -l "CLAUDE\|AGENTS" || echo "No matches"

# Check any deployment scripts
find scripts/ -type f | xargs grep -l "CLAUDE\.md\|AGENTS\.md" || echo "No matches"

# Check Makefile/justfile if exists
[ -f Makefile ] && grep -i "CLAUDE\|AGENTS" Makefile || echo "No Makefile"
[ -f justfile ] && grep -i "CLAUDE\|AGENTS" justfile || echo "No justfile"
```

### Step 4: Document all findings

Create `/tmp/reference-audit.md`:

```markdown
# CLAUDE.md and AGENTS.md Reference Audit

Date: 2026-01-17

## CLAUDE.md References

| File | Line | Context | Action Required |
|------|------|---------|----------------|
| .claude/settings.json | 11 | SessionStart hook | Fixed in Task 1 |
| README.md | 190 | Documentation | Fix in Task 8 |
| ... | ... | ... | ... |

## AGENTS.md References

| File | Line | Context | Action Required |
|------|------|---------|----------------|
| images.py | 187 | Image build | Fixed in Task 3 |
| sandbox.py | 566 | SessionStart hook | Fixed in Task 4 |
| ... | ... | ... | ... |

## Unexpected References

[List any files not already tracked in the plan]

## Verification

All references accounted for: ✅/❌
All actions planned: ✅/❌
```

### Step 5: Review and update plan if needed

Review `/tmp/reference-audit.md`:
- If all references are already tracked in this plan → proceed
- If unexpected references found → add tasks to handle them
- If CI/CD scripts need updates → add deployment tasks

### Step 6: Commit audit file

```bash
git add /tmp/reference-audit.md
# Note: This is a temp file for execution tracking, not committed to repo
```

---

## Task 3: Update Harvest SessionStart Hooks (Clean Separation)

**Goal:** Configure Harvest's local development to load shared base + local extensions only. Keep clean mode separation to avoid conflicting instructions.

**Files:**
- Modify: `.claude/settings.json`
- Modify: `.claude/settings.json.template`

### Step 1: Update active settings.json

Edit `.claude/settings.json` to load only shared base + local extensions:

```json
{
  "enabledPlugins": {
    "superpowers@claude-plugins-official": true
  },
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "comment": "Shared base rules (all contexts)",
            "command": "cat \"$CLAUDE_PROJECT_DIR/.claude/CLAUDE.md\""
          },
          {
            "type": "command",
            "comment": "Local development extensions",
            "command": "cat \"$CLAUDE_PROJECT_DIR/docs/ai/local-development.md\""
          }
        ]
      }
    ]
  }
}
```

### Step 2: Update template for documentation

Edit `.claude/settings.json.template` to match:

```json
{
  "enabledPlugins": {
    "superpowers@claude-plugins-official": true
  },
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "comment": "Shared base rules (all contexts)",
            "command": "cat \"$CLAUDE_PROJECT_DIR/.claude/CLAUDE.md\""
          },
          {
            "type": "command",
            "comment": "Local development extensions",
            "command": "cat \"$CLAUDE_PROJECT_DIR/docs/ai/local-development.md\""
          }
        ]
      }
    ]
  }
}
```

**Rationale:** Loading both local and autonomous extensions would create conflicting instructions ("ask for feedback" vs "execute autonomously"). When developing Harvest, explicitly read `autonomous-agent.md` using the Read tool when needed.

### Step 3: Verify hook structure

Run: `cat .claude/settings.json | jq '.hooks.SessionStart[0].hooks | length'`

Expected: `2` (two files loaded: shared base + local extensions)

### Step 4: Commit

```bash
git add .claude/settings.json .claude/settings.json.template
git commit -m "feat: clean mode separation for Harvest local development

- Load CLAUDE.md (shared base) + local-development.md (extensions)
- Avoid loading autonomous-agent.md to prevent conflicting instructions
- Read autonomous rules explicitly when needed via Read tool"
```

---

## Task 4: Bake Harvest Rules into Modal Image with WORKDIR

**Goal:** Bake Harvest rules into Modal image at `/app/` and ensure container sets `WORKDIR /app/` so relative `@docs/` references resolve correctly. This follows industry best practice for containerized AI agents.

**Files:**
- Modify: `packages/modal-executor/src/modal_executor/images.py:187-188`
- Verify: Modal Dockerfile sets `WORKDIR /app`

**Approach:** Keep `@docs/` as relative paths (no transformation). Claude CLI will resolve them from the working directory (`/app/`) to the baked files at `/app/docs/ai/shared/*.md`.

### Step 1: Verify _ROOT_DIR is available

Check if `_ROOT_DIR` is defined in `images.py`. If not, add it:

```python
from pathlib import Path

_ROOT_DIR = Path(__file__).parent.parent.parent.parent.parent  # harvest repo root
_CONFIG_DIR = Path(__file__).parent / "config"
```

### Step 2: Update image build to bake files with relative paths

Edit `packages/modal-executor/src/modal_executor/images.py` around line 187:

Replace:
```python
# -------------------------------------------------------------------------
# Harvest Configuration Files (baked into image)
# -------------------------------------------------------------------------
.add_local_file(str(_CONFIG_DIR / "AGENTS.md"), "/app/AGENTS.md")
.add_local_file(str(_CONFIG_DIR / "memory-seed.json"), "/app/memory-seed.json")
```

With:
```python
# -------------------------------------------------------------------------
# Harvest Configuration Files (baked into image)
# -------------------------------------------------------------------------
# Bake rule files with relative @docs/ paths (no transformation needed)
# Working directory will be /app/, so @docs/ resolves to /app/docs/
# CLAUDE.md: Shared base rules (all contexts)
.add_local_file(
    str(_ROOT_DIR / ".claude" / "CLAUDE.md"),
    "/app/CLAUDE.md"
)
# autonomous-agent.md: Autonomous mode extensions
.add_local_file(
    str(_ROOT_DIR / "docs" / "ai" / "autonomous-agent.md"),
    "/app/autonomous-agent.md"
)

# Bake shared rules (targets of @docs/ai/shared/ references)
.add_local_dir(
    str(_ROOT_DIR / "docs" / "ai" / "shared"),
    "/app/docs/ai/shared"
)

# Bake MCP documentation (targets of @docs/mcp/ references)
.add_local_dir(
    str(_ROOT_DIR / "docs" / "mcp"),
    "/app/docs/mcp"
)

# Memory seed file
.add_local_file(str(_CONFIG_DIR / "memory-seed.json"), "/app/memory-seed.json")

# Note: local-development.md is NOT baked (local mode only, never used by autonomous agent)
```

### Step 3: Verify Modal Dockerfile sets WORKDIR

Check if Modal's base image or your custom Dockerfile sets `WORKDIR /app`:

```bash
# Search for WORKDIR in Modal configuration
grep -r "WORKDIR" packages/modal-executor/ || echo "No WORKDIR found"
```

If not found, you may need to add it to Modal's image configuration. Modal containers typically default to `/root` or project directory. You need to ensure Claude CLI runs from `/app/`.

**Note:** This may require updating `sandbox.py` to `cd /app` before running Claude CLI commands, or configuring Modal to set the working directory.

### Step 4: Run test to verify image config

Run: `uv run pytest packages/modal-executor/tests/test_images.py::TestBaseImage::test_config_files_exist -v`

Expected: Test will need updates in Task 7 to check for new structure

### Step 5: Verify file structure

After building the image, verify the structure:

```bash
# List baked files (this would run in Modal container)
# Expected structure:
# /app/CLAUDE.md
# /app/autonomous-agent.md
# /app/docs/ai/shared/*.md
# /app/docs/mcp/*.md
# /app/memory-seed.json
```

### Step 6: Commit

```bash
git add packages/modal-executor/src/modal_executor/images.py
git commit -m "feat: bake Harvest rules into Modal image at /app/

- Bake CLAUDE.md and autonomous-agent.md with relative @docs/ paths
- Bake docs/ai/shared/ and docs/mcp/ directories
- No path transformation needed - rely on WORKDIR /app/
- Replace minimal AGENTS.md with comprehensive rules
- Follow industry standard for containerized AI agents"
```

---

## Task 5: Update Autonomous SessionStart Hook in sandbox.py

**Goal:** Update runtime hook generation to load rule files from `/app/` and ensure Claude CLI runs with working directory set to `/app/` so relative `@docs/` references resolve correctly.

**Files:**
- Modify: `packages/modal-executor/src/modal_executor/sandbox.py:557-577`

**Context:** The baked files at `/app/CLAUDE.md` and `/app/autonomous-agent.md` use relative `@docs/` paths. Claude CLI must run from `/app/` working directory so these references resolve to `/app/docs/ai/shared/*.md`.

### Step 1: Update _create_user_settings method

Edit `packages/modal-executor/src/modal_executor/sandbox.py` around line 557:

Replace:
```python
async def _create_user_settings(self) -> None:
    """Create ~/.claude/settings.json with permissions, hooks, and plugins."""
    # Build SessionStart hooks with absolute paths
    # Repo is already cloned at this point, so we can reference repo_path
    repo_claude_md = f"{self.session.repo_path}/.claude/CLAUDE.md"
    repo_autonomous_md = f"{self.session.repo_path}/docs/ai/autonomous-agent.md"

    hooks = [
        # Always load Harvest's core agent instructions (baked into image)
        {"type": "command", "command": "cat /app/AGENTS.md"},
        # Load repo's CLAUDE.md if it exists
        {
            "type": "command",
            "command": f"[ -f {repo_claude_md} ] && cat {repo_claude_md} || true",
        },
        # Load repo's autonomous-agent.md if it exists
        {
            "type": "command",
            "command": f"[ -f {repo_autonomous_md} ] && cat {repo_autonomous_md} || true",
        },
    ]
```

With:
```python
async def _create_user_settings(self) -> None:
    """Create ~/.claude/settings.json with permissions, hooks, and plugins.

    SessionStart hooks load (in order):
    1. /app/CLAUDE.md (Harvest shared base rules, baked into image)
    2. /app/autonomous-agent.md (Harvest autonomous extensions, baked into image)

    This follows the shared base + extensions architecture where CLAUDE.md provides
    common rules for all modes, and autonomous-agent.md adds full-autonomy workflows.
    """
    # Build SessionStart hooks with absolute paths to baked files
    hooks = [
        # Load Harvest's shared base rules (baked into image)
        {
            "type": "command",
            "comment": "Load Harvest shared base rules from image",
            "command": "cat /app/CLAUDE.md",
        },
        # Load Harvest's autonomous agent extensions (baked into image)
        {
            "type": "command",
            "comment": "Load Harvest autonomous agent extensions from image",
            "command": "cat /app/autonomous-agent.md",
        },
    ]
```

### Step 2: Ensure working directory is set to /app/

Critical: Claude CLI must run with working directory `/app/` for relative `@docs/` paths to resolve.

Add a check or configuration to ensure the working directory:

```python
# Option 1: Set working directory before running Claude CLI
# In sandbox initialization or execution, add:
os.chdir('/app')

# Option 2: Configure Modal function to start in /app/
# (Check Modal documentation for working directory configuration)
```

**Note:** This may require investigation of where Claude CLI is invoked in the sandbox code. The working directory must be `/app/` for `@docs/` references to resolve to `/app/docs/`.

### Step 3: Verify hook structure

The updated hooks should load exactly 2 files:
1. `/app/CLAUDE.md` (shared base with relative `@docs/` paths)
2. `/app/autonomous-agent.md` (autonomous extensions with relative `@docs/` paths)

When Claude CLI runs from `/app/`, relative `@docs/` references resolve to `/app/docs/ai/shared/*.md` and `/app/docs/mcp/*.md`.

### Step 4: Run sandbox tests

Run: `uv run pytest packages/modal-executor/tests/test_harvest_sandbox.py -v -k user_settings`

Expected: Tests should pass with new hook configuration

### Step 5: Commit

```bash
git add packages/modal-executor/src/modal_executor/sandbox.py
git commit -m "fix: simplify autonomous SessionStart hooks in sandbox

- Load only /app/CLAUDE.md and /app/autonomous-agent.md from image
- Remove repo-specific override mechanism for simplicity
- Ensure working directory set to /app/ for relative path resolution
- Files use relative @docs/ paths that resolve from /app/
- Add clear docstring for hook behavior"
```

---

## Task 6: Update settings.json.template Documentation

**Goal:** Fix the template file to accurately reflect runtime behavior without misleading placeholders.

**Files:**
- Modify: `packages/modal-executor/src/modal_executor/config/settings.json.template`
- Add: Comment explaining this is documentation only

### Step 1: Update template with clear documentation

Edit `packages/modal-executor/src/modal_executor/config/settings.json.template`:

```json
{
  "__comment__": "DOCUMENTATION ONLY - This template shows the structure of settings.json",
  "__comment__": "Actual settings.json is generated at runtime in sandbox.py::_create_user_settings()",
  "__comment__": "All rules are baked into Modal image at /app/",

  "permissions": {
    "allow": ["*"],
    "defaultMode": "bypassPermissions"
  },
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "comment": "Load Harvest shared base rules from image",
            "command": "cat /app/CLAUDE.md"
          },
          {
            "type": "command",
            "comment": "Load Harvest autonomous agent extensions from image",
            "command": "cat /app/autonomous-agent.md"
          }
        ]
      }
    ]
  },
  "enabledPlugins": {
    "superpowers@claude-plugins-official": true
  }
}
```

### Step 2: Add README section explaining template

Create or update comments in `packages/modal-executor/src/modal_executor/config/README.md`:

```markdown
## settings.json.template

**Purpose:** Documentation reference showing the structure of the autonomous agent's Claude CLI settings.

**Important:** This is NOT used at runtime. The actual `settings.json` is generated dynamically in `sandbox.py::_create_user_settings()`.

**Runtime behavior:**
- All Harvest rules are baked into the Modal image at `/app/`
- SessionStart hooks load `/app/CLAUDE.md` and `/app/autonomous-agent.md`
- No repo-specific overrides - simple and predictable

**Why template exists:**
- Shows developers what settings structure looks like
- Documents the SessionStart hook pattern
- Provides reference for debugging
```

### Step 3: Update test to reflect template is documentation

Edit `packages/modal-executor/tests/test_images.py` around line 23:

```python
assert (_CONFIG_DIR / "settings.json.template").exists()
# Template is documentation only - actual settings generated at runtime
```

### Step 4: Commit

```bash
git add packages/modal-executor/src/modal_executor/config/settings.json.template packages/modal-executor/src/modal_executor/config/README.md packages/modal-executor/tests/test_images.py
git commit -m "docs: simplify settings.json.template

- Remove repo-specific override mechanism
- Show only 2 SessionStart hooks (CLAUDE.md + autonomous-agent.md)
- Add comments explaining runtime generation
- Document template purpose in README
- Update test comments"
```

---

## Task 7: Archive AGENTS.md

**Goal:** Preserve the minimal AGENTS.md file for reference but mark it as deprecated.

**Files:**
- Rename: `packages/modal-executor/src/modal_executor/config/AGENTS.md` → `packages/modal-executor/src/modal_executor/config/AGENTS.md.archived`

### Step 1: Rename the file

```bash
git mv packages/modal-executor/src/modal_executor/config/AGENTS.md packages/modal-executor/src/modal_executor/config/AGENTS.md.archived
```

### Step 2: Add deprecation notice

Edit `packages/modal-executor/src/modal_executor/config/AGENTS.md.archived`:

```markdown
# [ARCHIVED] Harvest Agent Instructions

> **ARCHIVED 2026-01-17:** This minimal agent instruction file was replaced by baking `docs/ai/autonomous-agent.md` directly into the Modal image. This file is preserved for historical reference only.
>
> **Why replaced:**
> - AGENTS.md was too minimal (no shared rule references)
> - autonomous-agent.md is comprehensive and includes all shared/* rules
> - Avoids duplication and maintains single source of truth
>
> **New approach:**
> - `/app/autonomous-agent.md` is baked into image from `docs/ai/autonomous-agent.md`
> - Repo can optionally override with `docs/ai/autonomous-agent.md`

[rest of original content]
```

### Step 3: Commit

```bash
git add packages/modal-executor/src/modal_executor/config/AGENTS.md.archived
git commit -m "docs: archive minimal AGENTS.md file

- Replaced with comprehensive autonomous-agent.md
- Minimal version lacked shared rule references
- Preserved for historical reference"
```

---

## Task 8: Update Tests

**Goal:** Update all tests to reflect the new configuration structure.

**Files:**
- Modify: `packages/modal-executor/tests/test_images.py`

### Step 1: Update config files test

Edit `packages/modal-executor/tests/test_images.py` around line 18-24:

Replace:
```python
def test_config_files_exist(self):
    """Test that config files are included in image build."""
    from modal_executor.images import _CONFIG_DIR

    assert _CONFIG_DIR.exists()
    assert (_CONFIG_DIR / "AGENTS.md").exists()
    assert (_CONFIG_DIR / "memory-seed.json").exists()
    # settings.json.template is reference only, not baked into image
    assert (_CONFIG_DIR / "settings.json.template").exists()
```

With:
```python
def test_config_files_exist(self):
    """Test that config files are included in image build."""
    from modal_executor.images import _CONFIG_DIR, _ROOT_DIR

    assert _CONFIG_DIR.exists()
    # autonomous-agent.md is now baked from docs/ai/ instead of config/AGENTS.md
    autonomous_md = _ROOT_DIR / "docs" / "ai" / "autonomous-agent.md"
    assert autonomous_md.exists(), "autonomous-agent.md must exist for image build"
    assert (_CONFIG_DIR / "memory-seed.json").exists()
    # settings.json.template is documentation only, not baked into image
    assert (_CONFIG_DIR / "settings.json.template").exists()
```

### Step 2: Run all image tests

Run: `uv run pytest packages/modal-executor/tests/test_images.py -v`

Expected: All tests pass with new configuration

### Step 3: Commit

```bash
git add packages/modal-executor/tests/test_images.py
git commit -m "test: update image tests for new config structure

- Check autonomous-agent.md from docs/ai/ instead of config/AGENTS.md
- Verify file exists before image build
- Update comments for clarity"
```

---

## Task 9: Update Documentation References

**Goal:** Update all documentation that references CLAUDE.md, AGENTS.md, or the old structure.

**Files:**
- Modify: `README.md`
- Modify: `packages/modal-executor/README.md`
- Modify: `llms.txt` (if needed)

### Step 1: Search for references

Run: `grep -r "AGENTS.md\|CLAUDE.md" --include="*.md" . --exclude-dir=.claude --exclude-dir=.worktrees`

### Step 2: Update README.md

Edit `README.md` around lines mentioning CLAUDE.md:

Replace references to:
```markdown
- **SessionStart hook**: Automatically loads `.claude/CLAUDE.md` and `docs/ai/local-development.md`
```

With:
```markdown
- **SessionStart hook**: Automatically loads `docs/ai/local-development.md` with project rules and workflow guidance
```

### Step 3: Update packages/modal-executor/README.md

Search for references to AGENTS.md and update to autonomous-agent.md:

```markdown
The Modal sandbox loads rules via SessionStart hooks:
1. `/app/CLAUDE.md` (shared base rules, baked into image)
2. `/app/autonomous-agent.md` (autonomous extensions, baked into image)

All rules are baked at build time - no runtime overrides.
```

### Step 4: Verify no broken links

Run: `grep -r "@.*AGENTS.md\|@.*CLAUDE.md" --include="*.md" .`

Expected: No matches except in archived files and this plan

### Step 5: Commit

```bash
git add README.md packages/modal-executor/README.md
git commit -m "docs: update references to new config structure

- Remove references to CLAUDE.md router
- Update AGENTS.md references to autonomous-agent.md
- Clarify SessionStart hook behavior"
```

---

## Task 10: Validate No Cross-References

**Goal:** Verify that mode-specific files don't reference each other, only via SessionStart hooks.

**Files:**
- Check: `docs/ai/local-development.md`
- Check: `docs/ai/autonomous-agent.md`

### Step 1: Search for cross-references

Run: `grep -E "local-development\.md|autonomous-agent\.md" docs/ai/local-development.md docs/ai/autonomous-agent.md`

Expected: No matches (files don't reference each other)

### Step 2: Verify shared rule references work

Run: `grep -E "@docs/ai/shared" docs/ai/local-development.md docs/ai/autonomous-agent.md`

Expected: Both files reference shared rules (this is correct)

### Step 3: Document validation

Create a simple validation script `scripts/validate-mode-separation.sh`:

```bash
#!/bin/bash
# Validate that mode-specific files don't cross-reference each other

echo "Checking for cross-references between mode-specific files..."

# Check if local-development.md references autonomous-agent.md
if grep -q "autonomous-agent\.md" docs/ai/local-development.md; then
  echo "❌ FAIL: local-development.md references autonomous-agent.md"
  exit 1
fi

# Check if autonomous-agent.md references local-development.md
if grep -q "local-development\.md" docs/ai/autonomous-agent.md; then
  echo "❌ FAIL: autonomous-agent.md references local-development.md"
  exit 1
fi

# Check if CLAUDE.md exists in active config (should be archived)
if [ -f .claude/CLAUDE.md ]; then
  echo "❌ FAIL: .claude/CLAUDE.md should be archived"
  exit 1
fi

# Check if AGENTS.md exists in active config (should be archived)
if [ -f packages/modal-executor/src/modal_executor/config/AGENTS.md ]; then
  echo "❌ FAIL: config/AGENTS.md should be archived"
  exit 1
fi

echo "✅ PASS: Mode-specific files are properly separated"
exit 0
```

### Step 4: Make script executable and run

```bash
chmod +x scripts/validate-mode-separation.sh
./scripts/validate-mode-separation.sh
```

Expected: Script passes

### Step 5: Commit

```bash
git add scripts/validate-mode-separation.sh
git commit -m "test: add validation for mode separation

- Verify no cross-references between mode files
- Check router files are archived
- Prevent future regressions"
```

---

## Task 11: Final Verification and Documentation

**Goal:** Run all tests, verify the changes work end-to-end, and document the new structure.

**Files:**
- Modify: `docs/ai/README.md` (or create if doesn't exist)

### Step 1: Run full test suite

```bash
# Run Modal executor tests
cd packages/modal-executor
uv run pytest tests/ -v

# Run validation script
cd ../..
./scripts/validate-mode-separation.sh
```

Expected: All tests pass

### Step 2: Create or update docs/ai/README.md

```markdown
# Harvest AI Agent Rules

## Architecture

Harvest uses a **two-mode architecture** with complete separation:

### Local Development Mode

**Entry Point:** `.claude/settings.json` (SessionStart hook)

**Loaded Files:**
1. `docs/ai/local-development.md` (direct load)

**Characteristics:**
- Human judgment available
- Interactive brainstorming for complex tasks
- Can pause for feedback
- All shared rules loaded via `@docs/ai/shared/*.md` references

### Autonomous Agent Mode (Modal Sandbox)

**Entry Point:** Modal sandbox `sandbox.py::_create_user_settings()`

**Loaded Files:**
1. `/app/CLAUDE.md` (shared base, baked into image)
2. `/app/autonomous-agent.md` (autonomous extensions, baked into image)

**Working Directory:** `/app/` (set via WORKDIR)

**Characteristics:**
- Maximum autonomy
- Execute without asking
- Fail forward pattern
- All shared rules loaded via `@docs/ai/shared/*.md` references (resolve from `/app/`)

## Shared Rules

Both modes reference these shared rules:

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
4. **Router patterns** (like the old CLAUDE.md) are not used

## Validation

Run the validation script to check mode separation:

```bash
./scripts/validate-mode-separation.sh
```

## Historical Files

These files are archived for reference only:

- `.claude/CLAUDE.md.archived` - Old router pattern (deprecated 2026-01-17)
- `packages/modal-executor/src/modal_executor/config/AGENTS.md.archived` - Old minimal instructions (deprecated 2026-01-17)
```

### Step 3: Commit

```bash
git add docs/ai/README.md
git commit -m "docs: add architecture overview for AI agent rules

- Document two-mode architecture
- Explain SessionStart hook patterns
- List shared rules
- Reference validation script
- Note archived files"
```

### Step 4: Verify with fresh session

Test local development:
1. Open new terminal
2. `cd /Users/david.currie/src/harvest`
3. `claude code`
4. Verify only `local-development.md` is loaded (check SessionStart output)

Test Modal sandbox (requires Modal deployment):
1. Deploy updated image
2. Trigger test task
3. Check logs for SessionStart hook output
4. Verify `/app/autonomous-agent.md` is loaded

### Step 5: Final commit and summary

```bash
git add -A
git commit -m "feat: complete autonomous/local mode separation

Summary of changes:
- Removed CLAUDE.md router pattern (archived)
- Removed minimal AGENTS.md (archived)
- Baked comprehensive autonomous-agent.md into Modal image
- Updated SessionStart hooks to load mode-specific files directly
- Fixed settings.json.template documentation
- Added validation script for mode separation
- Updated all documentation and tests

Result:
- No cross-references between mode files
- Clean SessionStart hook patterns
- Autonomous agent has access to all shared rules
- Both modes are self-contained and clear"
```

---

## Success Criteria

1. ✅ No cross-references between `local-development.md` and `autonomous-agent.md`
2. ✅ Mode-specific files loaded ONLY via SessionStart hooks
3. ✅ Autonomous agent has access to all shared rules (via `/app/autonomous-agent.md`)
4. ✅ Template file clearly documented as reference only
5. ✅ Router pattern (CLAUDE.md) removed from active use
6. ✅ Minimal AGENTS.md replaced with comprehensive autonomous-agent.md
7. ✅ All tests pass
8. ✅ Validation script confirms proper separation
9. ✅ Documentation updated across the board

---

## Rollback Plan

**When to roll back:**
- Critical bugs in production autonomous agents
- Modal image build failures
- Widespread confusion among developers
- Unexpected behavioral changes in agents

### Phase 1: Immediate Mitigation (< 5 minutes)

**Goal:** Stop the bleeding - revert to last known good state

#### 1. Identify Last Good Commit

```bash
# Find the commit hash before this change
git log --oneline --grep="autonomous-local-mode-separation" -1
# Note the commit hash BEFORE this change
LAST_GOOD_COMMIT="<hash>"
```

#### 2. Create Rollback Branch

```bash
git checkout -b rollback-mode-separation-$(date +%s)
git revert <commits-from-this-plan>
# OR if multiple commits, use range:
git revert $LAST_GOOD_COMMIT..HEAD
```

#### 3. Redeploy Previous Modal Image (CRITICAL)

```bash
# Option A: Deploy from specific image tag
modal deploy packages/modal-executor/src/modal_executor/app.py \
  --tag previous-stable

# Option B: Rebuild from last good commit
git checkout $LAST_GOOD_COMMIT
modal deploy packages/modal-executor/src/modal_executor/app.py
git checkout rollback-mode-separation-*
```

**Why this is critical:** New Modal sessions will use the old image. Existing sessions continue with whatever image they started with until they expire or are restarted.

### Phase 2: Restore File Structure (< 10 minutes)

**Goal:** Restore the old configuration files

#### 1. Restore CLAUDE.md

```bash
# If archived
git mv .claude/CLAUDE.md.archived .claude/CLAUDE.md

# Restore original settings.json
git checkout $LAST_GOOD_COMMIT -- .claude/settings.json .claude/settings.json.template
```

#### 2. Restore AGENTS.md

```bash
# Restore to config directory
git mv packages/modal-executor/src/modal_executor/config/AGENTS.md.archived \
     packages/modal-executor/src/modal_executor/config/AGENTS.md

# Restore original image build
git checkout $LAST_GOOD_COMMIT -- packages/modal-executor/src/modal_executor/images.py
```

#### 3. Restore Sandbox Hooks

```bash
git checkout $LAST_GOOD_COMMIT -- packages/modal-executor/src/modal_executor/sandbox.py
```

#### 4. Rebuild and Deploy Modal Image

```bash
# Rebuild with old structure
modal deploy packages/modal-executor/src/modal_executor/app.py --force-build

# Verify deployment
modal app list | grep modal-executor
```

### Phase 3: Developer Communication (< 15 minutes)

#### 1. Notify Team

Post to Slack/team channel:
```
🚨 ROLLBACK IN PROGRESS 🚨

We've rolled back the autonomous/local mode separation changes due to [issue].

ACTION REQUIRED for local developers:
1. Pull latest changes: `git pull origin main`
2. Restore old settings: `cp .claude/settings.json.template .claude/settings.json`
3. Restart Claude CLI: `claude code`

Autonomous agents: Will use previous configuration automatically after image redeploy.

ETA for fix: [timeframe]
```

#### 2. Update Documentation

Add temporary banner to README.md:
```markdown
> **TEMPORARY ROLLBACK (2026-01-17):** The mode separation changes have been temporarily rolled back. See Slack for details.
```

### Phase 4: Local Developer Restore (Self-Service)

**Developers running locally should:**

```bash
# Pull rollback changes
git checkout main
git pull origin main

# Restore settings from template
cp .claude/settings.json.template .claude/settings.json

# Restart Claude CLI
# Exit current session with /exit, then:
claude code
```

### Phase 5: Verification (< 30 minutes)

#### 1. Verify Modal Image

```bash
# Check deployed image version
modal app list

# Trigger test session
# [depends on your test harness]
```

#### 2. Verify Local Development

```bash
# Start fresh session
claude code
# Check SessionStart output for CLAUDE.md being loaded
```

#### 3. Check for Stragglers

```bash
# Look for any Modal sessions still running old code
modal app logs modal-executor --tail=100
# Check for version mismatches or unexpected errors
```

### Phase 6: Root Cause Analysis

After rollback is stable:

1. **Gather Data:**
   - Modal logs during failure
   - Developer reports
   - Error messages
   - Behavioral differences

2. **Document Issues:**
   - What broke?
   - Why did it break?
   - What was missed in the plan?

3. **Update Plan:**
   - Add missing test cases
   - Add missing edge case handling
   - Improve deployment strategy

4. **Schedule Re-Attempt:**
   - Fix issues found
   - Add better testing
   - Consider phased rollout (beta users first)

### Phase 7: Phased Re-Deployment (Optional)

If trying again:

1. **Beta Phase:**
   - Deploy to beta Modal environment first
   - Ask 2-3 developers to test locally
   - Run for 24-48 hours

2. **Staged Rollout:**
   - Deploy to 25% of Modal sessions (if possible)
   - Monitor for 24 hours
   - Increase to 50%, then 100%

3. **Local Rollout:**
   - Update template, keep old one as `.old`
   - Announce change with clear migration steps
   - Provide support channel

---

### Rollback Success Criteria

- ✅ Modal image reverted and deployed
- ✅ All Modal sessions using old configuration
- ✅ Local developers notified and able to restore
- ✅ No new errors in Modal logs
- ✅ Team acknowledges rollback and understands actions
- ✅ Root cause documented
- ✅ Plan updated with lessons learned

---

## Implementation Approach: WORKDIR vs Path Transformation

### Original Plan (Discarded)

The initial plan proposed transforming `@docs/` references to `@/app/docs/` (absolute paths) for files baked into the Modal image. This was **rejected** after research and validation.

**Why it won't work:**
- Claude CLI only supports **relative path** `@` references (e.g., `@docs/ai/shared/git-workflow.md`)
- Absolute path `@` references (e.g., `@/app/docs/ai/shared/git-workflow.md`) are displayed as literal text, not resolved to file content
- Security by design: Claude CLI restricts file access to relative paths from the working directory

### Adopted Approach: WORKDIR /app/

Based on industry research (Ramp, Vercel, Docker best practices), we adopted the **WORKDIR approach**:

1. **Keep relative paths**: All `@docs/` references stay as-is in CLAUDE.md and autonomous-agent.md
2. **Bake at standard locations**: Files baked at `/app/CLAUDE.md`, `/app/docs/ai/shared/*.md`, `/app/docs/mcp/*.md`
3. **Set working directory**: Container ensures `WORKDIR /app/` so Claude CLI runs from `/app/`
4. **Resolution**: Relative `@docs/ai/shared/git-workflow.md` resolves to `/app/docs/ai/shared/git-workflow.md`

### Industry Validation

This approach aligns with:
- **Claude Code's native behavior**: Automatically loads `CLAUDE.md` files from repo root/parent/child directories
- **Docker best practices**: Use `WORKDIR` with absolute paths, application uses relative paths
- **Ramp's approach**: RAG for dynamic policies, baked files for static rules
- **Vercel's v0 agent**: Curated directories with code samples in read-only filesystem

**Key Insight**: The solution is environment-based (working directory), not file transformation.

---

## Notes

- This is a documentation and configuration change, no runtime logic changes
- The autonomous agent behavior remains identical, just better organized
- Local development workflow is simplified (one less file to load)
- Future developers will find the structure clearer and easier to understand
- No path transformation needed - rely on containerization best practices
