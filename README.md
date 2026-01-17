# Harvest

> Did you **Harvest** that? 🌾

Build your AI Workforce with Harvest - the background coding agent that tends to your repositories like farmers tending to crops, cultivating code that grows stronger while you sleep.

Harvest is a background coding agent service built on the architecture that powers [Ramp's Inspect](https://builders.ramp.com/post/why-we-built-our-background-agent), designed specifically for the **Relevance AI** ecosystem.

### Core Capabilities

- **Autonomous Development**: Works continuously across repositories without human intervention
- **Sandbox Orchestration**: Spins up isolated Modal sandboxes for each session
- **Claude Code CLI Integration**: Leverages Anthropic's official Claude CLI with full tool access
- **Multi-Model Strategy**: Primary Claude Sonnet 4.5 + Gemini for plan validation
- **Session Continuity**: SQLite-backed conversation state persists across sandbox restarts
- **Continuous Harvesting**: Generates pull requests, fixes bugs, and improves code while you focus on other work

### Architecture Overview

```
┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│  Slack/Web UI    │────────►│  Harvest API     │────────►│  Modal Sandboxes │
│  Clients         │         │  Orchestrator    │         │  (Isolated Env)  │
└──────────────────┘         └──────────────────┘         └──────────────────┘
         │                            │                            │
         │                            │                            │
         ▼                            ▼                            ▼
┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│  Relevance AI    │         │  Claude Code CLI │────────►│  GitHub          │
│  Workforce Mgmt  │         │  + MCP Servers   │         │  Repositories    │
└──────────────────┘         └──────────────────┘         └──────────────────┘
                                       │
                                       ├── GitHub MCP (PR/Issue mgmt)
                                       ├── Linear MCP (Task tracking)
                                       ├── Gemini MCP (Plan review)
                                       └── Chrome MCP (Browser testing)
```

## Current Status

**Phase 1 - Foundation**: 🟢 **Partially Complete** (Updated: January 2026)

### ✅ Completed (Phase 1.1 + 1.3)

Harvest infrastructure is production-ready:
- ✅ **Modal sandboxes** with full development environment
- ✅ **Claude Code CLI integration** with OAuth + JSON streaming
- ✅ **Session state persistence** (SQLite on Modal volumes)
- ✅ **Conversation continuity** (last 10 messages context)
- ✅ **Git workflow** with Safe-Carry-Forward patterns
- ✅ **Git credential security** (helper-based, no token exposure)
- ✅ **MCP servers** (memory, filesystem, playwright, devtools, github, gemini, sentry, linear)
- ✅ **30-minute cron** for image refresh
- ✅ **Pre-commit hooks** for linting/formatting
- ✅ **1,927 lines** of production code with tests

**Implementation**: `packages/modal-executor/` ([source](packages/modal-executor/))

### 🚧 Current Blocker

**`harvest-client` Package** (Estimated: 2-4 hours)
- Thin Python wrapper around `HarvestSandbox` for external consumption
- Required for integration with Relevance's NodeAPI
- Blocks Phase 2 (API Layer) work

### ❌ Not Started

- Phase 1.2: Session orchestration and lifecycle management
- Phase 2: API Layer (Cloudflare Workers + Durable Objects)
- Phase 3: Client (Slack bot, web dashboard)
- Phase 4: Intelligence (agent tools, metrics)

---

## Critical Technical TODOs

### 🚨 WORKDIR Verification & Guardrails (Modal Sandbox)

**Context**: The autonomous agent relies on `WORKDIR /app/` for `@docs/` reference resolution in baked rule files. If Claude CLI runs from a different directory, all rule references will fail.

**Required Actions**:

1. **Verify Modal WORKDIR Configuration**
   - Confirm Modal respects `WORKDIR /app/` in container definition
   - Test that working directory persists across all execution contexts
   - Document Modal-specific WORKDIR configuration mechanism

2. **Add Defensive Working Directory Enforcement**
   - Add `os.chdir('/app')` at the start of sandbox execution
   - Add explicit working directory check before every Claude CLI invocation
   - Log `os.getcwd()` before CLI calls for debugging

3. **Test Edge Cases**
   - Verify `@docs/` resolution after cloning a repository
   - Test working directory stability during git operations
   - Ensure subprocess calls don't pollute working directory

4. **Add Guardrails**
   ```python
   # Before every Claude CLI invocation
   assert os.getcwd() == '/app/', f"Working directory must be /app/, got {os.getcwd()}"
   ```

**Risk Level**: HIGH - Single point of failure for all rule file resolution

**Related**: See Gemini audit in `feat/autonomous-local-mode-separation` plan (2026-01-17)

---

## Documentation Structure

This repository uses a structured documentation approach:

| Directory | Audience | Purpose |
|-----------|----------|---------|
| `.claude/` | AI Agent (Claude) | Project-level rules loaded into Claude's context |
| `.claude/plans/` | Developers & AI | Planning workflow (Research → Plan → Implementation) |
| `docs/ai/` | AI Agent (Claude) | Context-specific agent rules and workflows |
| `docs/mcp/` | AI Agent (Claude) | Detailed MCP server documentation |
| `docs/plans/` | Developers | Implementation plans and current work |
| `docs/architecture/` | Developers | Technical documentation |

### LLM-Accessible Documentation

**Documentation Index** (`llms.txt`):
- Emerging standard for LLM-accessible documentation
- Categorized index of all markdown documentation
- Enables efficient documentation discovery by LLMs
- Useful for both AI tools and human developers

**Claude Code Configuration** (`.claude/claude.md`):
- Shared base rules for all contexts
- MCP server integration
- Loaded alongside context-specific extensions

### AI Agent Architecture

Harvest uses a **shared base + mode-specific extensions** architecture with complete separation between local and autonomous modes.

#### Local Development Mode

**Entry Point:** `.claude/settings.json` (SessionStart hook)

**Loaded Files:**
1. `.claude/claude.md` (shared base rules)
2. `docs/ai/local-development.md` (local mode extensions)

**Characteristics:**
- Human judgment available
- Interactive brainstorming for complex tasks
- Can pause for feedback
- All shared rules loaded via `@docs/ai/shared/*.md` references

#### Autonomous Agent Mode (Modal Sandbox)

**Entry Point:** Modal sandbox creates settings file programmatically

**Loaded Files:**
1. `/app/claude.md` (shared base, baked into image)
2. `/app/autonomous-agent.md` (autonomous extensions, baked into image)

**Characteristics:**
- Maximum autonomy
- Execute without asking
- Fail forward pattern
- All shared rules loaded via `@docs/ai/shared/*.md` references (resolve from `/app/`)

#### Design Principle: Intent vs Execution

**Local and autonomous modes differ in PURPOSE/INTENT, but share EXECUTION unless intent requires different execution.**

- **Shared rules** (`docs/ai/shared/*.md`) = EXECUTION (how to do things)
- **Mode files** (`local-development.md`, `autonomous-agent.md`) = INTENT differences (why execution differs)
- **Don't duplicate** - reference shared rules, add only intent-specific notes

#### Architecture Rules

1. **NO cross-references** between `local-development.md` and `autonomous-agent.md`
2. **SessionStart hooks** are the ONLY way to load mode-specific files
3. **Shared rules** are loaded via `@` references in mode-specific files
4. **Router patterns** (like "if local/if autonomous") are not used

**Validation:**
```bash
./scripts/validate-mode-separation.sh
```

### For Developers

#### Planning Workflow

Harvest uses a three-phase planning workflow:

**Directory Structure:**
```
.claude/plans/
└── [branch-name]/
    ├── research_YYYY-MM-DD_HHMM.md
    ├── plan_YYYY-MM-DD_HHMM.md
    └── implementation_YYYY-MM-DD_HHMM.md
```

**Phase 1 - Research:**
- Explore the problem space, understand constraints
- Document findings in `research_YYYY-MM-DD_HHMM.md`
- Commit and push

**Phase 2 - Planning:**
- Create detailed implementation plan in `plan_YYYY-MM-DD_HHMM.md`
- Open PR with `[PLAN]` prefix for review
- Iterate on feedback (new timestamped files, don't overwrite)
- Once approved: close PR, proceed to implementation

**Phase 3 - Implementation:**
- Execute approved plan
- Document results in `implementation_YYYY-MM-DD_HHMM.md`
- Create implementation PR referencing plan PR number
- Merge when approved

**Why timestamps:** Agent self-awareness ("which iteration?"), audit trail, easy sorting.

**Detailed guidelines:** See `docs/ai/shared/planning.md` for full process, Gemini review, and hierarchical planning.

#### Implementation Plans

See [`docs/plans/`](docs/plans/) for overall roadmap:
- [`IMPLEMENTATION_PLAN.md`](docs/plans/IMPLEMENTATION_PLAN.md) - Overall phased approach
- [`phase-1.1-modal-sandbox.md`](docs/plans/phase-1.1-modal-sandbox.md) - Modal sandbox implementation

#### Architecture Documentation

See [`docs/architecture/`](docs/architecture/) for technical documentation.

---

## Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- Modal account ([modal.com](https://modal.com))
- GitHub account with PAT
- Claude Code CLI (`brew install claude` or see [claude.ai/download](https://claude.ai/download))

### Development Setup

```bash
# Clone the repository
git clone https://github.com/RelevanceAI/harvest.git
cd harvest

# Setup modal-executor package
cd packages/modal-executor
uv venv --allow-existing
source .venv/bin/activate
uv pip install -e ".[dev]"

# Install pre-commit hooks (catches linting/formatting issues locally)
pre-commit install

# Test hooks on all files
pre-commit run --all-files
```

### Claude Code Configuration (Local Development)

To enable Harvest AI rules and superpowers skills when working locally with Claude Code:

```bash
# 1. Add the Claude plugins marketplace
claude plugins add claude-plugins-official https://github.com/anthropics/claude-plugins-official

# 2. Install superpowers plugin
claude plugins install claude-plugins-official/superpowers

# 3. Copy the template settings file
cp .claude/settings.json.template .claude/settings.json

# This enables:
# - Automatic loading of Harvest rules on session start
# - Superpowers skills (/brainstorming, /finishing-a-development-branch, etc.)
```

**What this does:**
- **SessionStart hook**: Automatically loads `.claude/claude.md` (shared base) and `docs/ai/local-development.md` (local extensions) with project rules and workflow guidance
- **Superpowers plugin**: Enables workflow skills for planning, debugging, and finishing work

**Note**: `.claude/settings.json` is gitignored (local settings only). The template is committed for easy setup.

### Running Tests

```bash
cd packages/modal-executor

# Run unit tests
uv run pytest tests/ -v

# Run integration tests (requires Modal credentials)
uv run pytest tests/ -m modal -v

# Run with coverage
uv run pytest tests/ --cov=modal_executor --cov-report=term-missing
```

### Code Quality

Pre-commit hooks automatically run:
- **Ruff**: Fast Python linter
- **Black**: Code formatter
- **Mypy**: Static type checker (non-blocking)

Manual checks:
```bash
# Linting
uv run ruff check src/ tests/

# Formatting
uv run black src/ tests/

# Type checking
uv run mypy src/ --ignore-missing-imports
```

---

## Roadmap

Based on the [Ramp Inspect architecture](https://builders.ramp.com/post/why-we-built-our-background-agent):

### Phase 1: Foundation (In Progress)
- [x] Planning complete
- [x] **Phase 1.1**: Modal sandbox infrastructure with Claude Code CLI
- [ ] **Phase 1.2**: Session orchestration and lifecycle management
- [ ] **Phase 1.3**: GitHub App integration

### Phase 2: API Layer
- [ ] Cloudflare Workers + Durable Objects
- [ ] REST & WebSocket API
- [ ] Session management endpoints

### Phase 3: Client
- [ ] Slack bot (primary interface)
- [ ] Web dashboard

### Phase 4: Intelligence
- [ ] Core agent tools (test runner, slack updates)
- [ ] Metrics and observability
- [ ] Multi-repo memory

See [`docs/plans/IMPLEMENTATION_PLAN.md`](docs/plans/IMPLEMENTATION_PLAN.md) for the full roadmap.

---

## How It Works

### Sandbox Architecture

Each Harvest session runs in an isolated Modal sandbox with:

**Sandbox Environment**:
```
/workspace/{repo-name}/     # Cloned repository (ephemeral)
/mnt/state/sessions/        # Session state databases (persistent Modal volume)
/root/.git-credentials      # Git authentication (secure permissions)
~/.claude/                  # Claude CLI config
```

**Session Lifecycle**:

1. **Setup Phase** (runs once per session):
   - Configure git identity with "(Harvest)" attribution
   - Setup git credential helper with secure permissions
   - Clone repository using credential helper (no tokens in args)
   - Initialize Claude CLI with OAuth token
   - Seed session state database

2. **Execution Phase** (per user prompt):
   - Load conversation history from SQLite (last 10 messages)
   - Build context-enriched prompt with history
   - Stream Claude CLI output in real-time
   - Track modified files
   - Persist conversation to SQLite

3. **Persistence**:
   - Modal volumes: `/mnt/state/` persists across sandbox restarts
   - Session database: `/mnt/state/sessions/{session-id}.db`
   - Conversation continuity without memory loss

### Session State Management

SQLite-backed state provides:
- **Conversation History**: Last 10 messages for context
- **Modified Files**: Track changes across agent turns
- **Persistence**: Survives sandbox restarts via Modal Volume
- **Isolation**: One database per session

Example:
```python
state = SessionState(session_id="pr-123")
state.add_exchange("Fix the bug", "I fixed it by...")
context = state.build_context_prompt("What did you change?")
# Returns: "Previous conversation:\nuser: Fix the bug\nassistant: I fixed it by...\n\nUser: What did you change?"
```

### Git Workflow

Harvest follows a strict git workflow (see `docs/ai/shared/git-workflow.md`):

- **Never** uses `git pull` or `git stash`
- Uses **Safe-Carry-Forward** pattern with snapshot commits
- Creates **checkpoint branches** before risky operations
- Commits attributed with `Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>`
- Squashes WIP commits before pushing clean history

### Security Model

**Credential Management**:
- Ephemeral secrets via `Modal.Secret.from_dict()`
- No credentials in dataclass repr (all fields have `repr=False`)
- Credential redaction in error logs (regex-based sanitization)
- Git credentials stored with secure permissions (chmod 600)
- Git credential helper configured before cloning (no tokens in process args)

**Isolation**:
- Each session gets isolated Modal sandbox
- No cross-session data leakage
- Sandboxes terminated after session completion

**MCP Servers**:
- **GitHub**: PR creation, issue management, code search
- **Linear**: Issue tracking and progress updates
- **Gemini**: Adversarial plan review and web research
- **Chrome/DevTools**: Browser automation and visual testing

### Adding MCP Servers

**All servers need:**
1. Entry in MCP Tools Index (`.claude/CLAUDE.md`)
2. Configuration in Modal sandbox setup

**Heavy servers (complex workflows) also need:**
3. Dedicated doc file: `docs/mcp/{server-name}.md`

**Decision criteria:**
- **Create separate doc when:** Documentation exceeds ~50 lines, complex workflows, multi-step patterns
- **Keep in quick reference when:** Straightforward usage (1-3 tools), simple one-liners

**Example structure for docs/mcp/{server}.md:**
- When to use
- Common workflows
- Code examples
- Gotchas and limitations

---

## Contributing

Contributions are welcome! Please:

1. Read implementation plans in `docs/plans/`
2. Follow the git workflow in `docs/ai/shared/git-workflow.md`
3. Install pre-commit hooks (`pre-commit install`)
4. Ensure all tests pass before submitting PR
5. Follow code comment policy (`docs/ai/shared/code-comments.md`)

---

## License

[MIT](LICENSE)
