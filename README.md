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

**Phase 1.1 - Modal Sandbox Infrastructure** ✅

Harvest currently provides:
- ✅ Modal sandboxes with Claude Code CLI integration
- ✅ Session state persistence (SQLite on Modal volumes)
- ✅ Git credential management with security hardening
- ✅ MCP server support (GitHub, Linear, Gemini, Chrome)
- ✅ Pre-commit hooks for local linting/formatting

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

### For AI Agents

**Project Rules** (`.claude/CLAUDE.md`):
- Context detection (local dev vs autonomous agent)
- MCP tools index
- Quick reference for shared rules

**Shared Rules** (`docs/ai/shared/`):
- `git-workflow.md` - Safe-Carry-Forward sync, checkpoints, squashing
- `code-comments.md` - Explain WHY not WHAT; preserve existing comments
- `planning.md` - Research before coding, use Gemini for adversarial review

**Context-Specific Rules** (`docs/ai/`):
- `local-development.md` - Rules for local Claude CLI usage
- `autonomous-agent.md` - Rules for background agent in Modal sandbox

**MCP Server Guides** (`docs/mcp/`):
- `gemini.md` - Plan review and web research workflows
- `github.md` - PR/issue management patterns
- `linear.md` - Task tracking integration
- `chrome.md` - Browser automation for testing

### For Developers

- **Planning Workflow**: See [`.claude/plans/README.md`](.claude/plans/README.md)
  - Three-phase workflow: Research → Plan → Implementation
  - Plans organized by branch in `.claude/plans/[branch-name]/`
  - Timestamped files for versioning and audit trail
  - Plans submitted as PRs with `[PLAN]` prefix for review

- **Implementation Plans**: See [`docs/plans/`](docs/plans/)
  - [`IMPLEMENTATION_PLAN.md`](docs/plans/IMPLEMENTATION_PLAN.md) - Overall phased approach
  - [`phase-1.1-modal-sandbox.md`](docs/plans/phase-1.1-modal-sandbox.md) - Modal sandbox implementation

- **Architecture Docs**: See [`docs/architecture/`](docs/architecture/)

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
