# Harvest

> Did you **Harvest** that? 🌾

Build your AI Workforce with Harvest - the background coding agent that tends to your repositories like farmers tending to crops, cultivating code that grows stronger while you sleep.

Harvest is a background coding agent service built on the architecture that powers [Ramp's Inspect](https://builders.ramp.com/post/why-we-built-our-background-agent), designed specifically for the **Relevance AI** ecosystem.

---

## Status at a Glance

| Component | Status | Documentation |
|-----------|--------|---------------|
| **Modal Sandboxes** | ✅ Ready | [`packages/modal-executor/`](packages/modal-executor/) |
| **Claude CLI Integration** | ✅ Ready | [`docs/ai/`](docs/ai/) |
| **Git Workflow** | ✅ Ready | [`docs/ai/shared/git-workflow.md`](docs/ai/shared/git-workflow.md) |
| **MCP Servers** | ✅ Ready | [MCP table](#mcp-servers) |
| **PTY Interactive Sessions** | 🚧 In Progress | [EXEC_SUMMARY.md](.claude/plans/feat-harvest-pty-interactive-sessions/EXEC_SUMMARY.md) |
| **API Layer** | ⏳ Planned | [`docs/plans/IMPLEMENTATION_PLAN.md`](docs/plans/IMPLEMENTATION_PLAN.md) |
| **Slack/Web Client** | ⏳ Planned | [`docs/plans/IMPLEMENTATION_PLAN.md`](docs/plans/IMPLEMENTATION_PLAN.md) |

---

## Core Capabilities

- **Autonomous Development**: Works continuously across repositories without human intervention
- **Sandbox Orchestration**: Spins up isolated Modal sandboxes for each session
- **Claude Code CLI Integration**: Leverages Anthropic's official Claude CLI with full tool access
- **Multi-Model Strategy**: Primary Claude Sonnet 4.5 + Gemini for plan validation
- **Session Continuity**: SQLite-backed conversation state persists across sandbox restarts
- **Continuous Harvesting**: Generates pull requests, fixes bugs, and improves code while you focus on other work

---

## Proposed Architecture

```mermaid
graph TD
    subgraph "User Interface"
        A0[Relevance Workforce<br/>Chat Interface]
    end

    subgraph "External Triggers"
        A2[Slack Bot]
        A3[GitHub Webhooks]
    end

    subgraph "Relevance Backend"
        B0[Project Keys DB<br/>Encrypted]
        B1[Sync Services<br/>OAuth/Webhooks]
        B2[TriggerRunner]
        B3[ConversationManager]
        B4[BackgroundCoderPresetAgent]
    end

    subgraph "Harvest Runtime TypeScript"
        C1[HarvestRuntime.ts<br/>GetUserProjectKey]
        C2[Spawn Python Subprocess<br/>env: GITHUB_TOKEN<br/>CLAUDE_OAUTH_TOKEN]
    end

    subgraph "harvest-client Python"
        D1[HarvestClient<br/>reads env vars]
        D2[Modal API Call<br/>HTTPS + credentials]
    end

    subgraph "Modal Container HarvestSandbox"
        E0[modal.Secret.from_dict<br/>ENV vars]
        E1[PTY Manager]
        E2[asyncio.Queue]
        E3[Stop Hook Detection]
        E4[Memory Monitor]
    end

    subgraph "Claude Code CLI"
        F1[Interactive Session<br/>CLAUDE_CODE_OAUTH_TOKEN]
        F2[MCP Servers<br/>GITHUB_TOKEN, etc.]
        F3[Tool Execution]
    end

    subgraph "External Services"
        G1[GitHub API]
        G2[Gemini API]
        G3[Linear API]
        G4[Git Operations]
    end

    A0 --> B2
    A2 --> B1
    A3 --> B1
    B1 --> B2
    B2 --> B3
    B3 --> B4
    B4 --> C1
    C1 --> C2
    C2 --> D1
    D1 --> D2
    D2 --> E1
    E1 --> E2
    E2 --> F1
    F1 --> E3
    E3 -.->|<<<CLAUDE_DONE>>>| E2
    E1 --> E4
    F1 --> F2
    F2 --> F3
    F3 --> G1
    F3 --> G2
    F3 --> G3
    F3 --> G4

    F1 -.->|stdout stream| C2
    C2 -.->|yield chunks| B3
    B3 -.->|toolviewer| A0

    B0 ==>|GetUserProjectKey| C1
    C1 ==>|subprocess env vars| C2
    C2 ==>|env vars| D1
    D1 ==>|Modal API HTTPS| D2
    D2 ==>|modal.Secret| E0
    E0 ==>|sandbox env vars| F1
    E0 ==>|sandbox env vars| F2

    style E1 fill:#e1f5ff
    style F1 fill:#fff4e1
    style E3 fill:#ffe1e1
    style B2 fill:#e8f5e9
    style B0 fill:#fff3e0
    style E0 fill:#fff3e0
```

**Current implementation attempt**: See [PTY Interactive Sessions proposal](.claude/plans/feat-harvest-pty-interactive-sessions/EXEC_SUMMARY.md)

### Agent Modes

Harvest uses **shared base + mode-specific extensions** architecture:

**Local Development Mode** (Your machine):
- Interactive brainstorming for complex tasks
- Can pause for human feedback
- Human judgment available

**Autonomous Agent Mode** (Modal sandbox):
- Maximum autonomy, no human in loop
- Execute without asking
- Fail forward pattern (try alternatives when blocked)

Both modes share execution rules (`docs/ai/shared/*.md`) but differ in intent/approach.

---

## MCP Servers

| Server | Package | Required Secret | Permissions | Where to Get |
|--------|---------|-----------------|-------------|--------------|
| **Memory** | `@modelcontextprotocol/server-memory` | None | - | - |
| **Filesystem** | `@modelcontextprotocol/server-filesystem` | None | - | - |
| **Playwright** | `@anthropic-ai/mcp-server-playwright` | None | - | - |
| **DevTools** | `chrome-devtools-mcp` | None | - | - |
| **GitHub** | `@anthropic-ai/mcp-server-github` | `GITHUB_TOKEN` | Contents: R/W, PRs: R/W, Issues: R/W | [github.com/settings/tokens](https://github.com/settings/tokens?type=beta) |
| **Linear** | `@modelcontextprotocol/server-linear` | `LINEAR_API_KEY` | Full access | [linear.app/settings/api](https://linear.app/settings/api) |
| **Gemini** | `@houtini/gemini-mcp` | `GEMINI_API_KEY` | - | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) |
| **Sentry** | `@sentry/mcp-server` | `SENTRY_AUTH_TOKEN` | project:read, event:read, issue:read | [sentry.io/settings/account/api/auth-tokens](https://sentry.io/settings/account/api/auth-tokens/) |

---

## Getting Started

### Quick Setup (One Command)

```bash
git clone https://github.com/RelevanceAI/harvest.git && \
cd harvest && \
bash scripts/setup-git-hooks.sh && \
cd packages/modal-executor && \
uv venv --allow-existing && \
source .venv/bin/activate && \
uv pip install -e ".[dev]" && \
pre-commit install
```

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- Modal account ([modal.com](https://modal.com))
- GitHub account with PAT
- Claude Code CLI ([claude.ai/download](https://claude.ai/download))

### Claude Code Setup

Enable Harvest AI rules and superpowers skills:

```bash
claude plugins add claude-plugins-official https://github.com/anthropics/claude-plugins-official
claude plugins install claude-plugins-official/superpowers
cp .claude/settings.json.template .claude/settings.json
```

Configure MCP servers in `~/.claude/mcp.json` - see [MCP table](#mcp-servers) for API keys and permissions.

### Testing & Code Quality

```bash
# Run tests
cd packages/modal-executor
uv run pytest tests/ -v

# Linting & formatting
uv run ruff check src/ tests/
uv run black src/ tests/
```

---

## Documentation

| Directory | Purpose |
|-----------|---------|
| [`docs/setup/`](docs/setup/) | Setup and configuration guides |
| [`docs/plans/`](docs/plans/) | Implementation plans |
| [`docs/ai/`](docs/ai/) | AI agent rules and workflows |
| [`docs/mcp/`](docs/mcp/) | MCP server documentation |
| [`.claude/`](.claude/) | Project-level AI agent rules |

---

## Contributing

Use Claude, it knows everything it needs to know.

---

## License

[MIT](LICENSE)
