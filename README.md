# Harvest

> Did you **Harvest** that? 🌾

Build your AI Workforce with Harvest - the background coding agent that tends to your repositories like farmers tending to crops, cultivating code that grows stronger while you sleep.

Harvest is a background coding agent service built on the architecture that powers [Ramp's Inspect](https://builders.ramp.com/post/why-we-built-our-background-agent), designed specifically for the **Relevance AI** ecosystem.

### Core Capabilities

- **Autonomous Development**: Works continuously across multiple repositories without human intervention
- **Sandbox Orchestration**: Spins up isolated Modal sandboxes for each task or repository
- **OpenCode Integration**: Leverages the full power of OpenCode agents and multi-model switching
- **Multi-Repo Management**: Seamlessly switches between your entire codebase portfolio
- **Growth Monitoring**: Tracks progress, quality, and deployment readiness
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
│  Relevance AI    │────────►│  OpenCode        │────────►│  GitHub          │
│  Workforce Mgmt  │         │  Server          │         │  Repositories    │
└──────────────────┘         └──────────────────┘         └──────────────────┘
```

---

## Documentation Structure

This repository uses a structured documentation approach:

| Directory | Audience | Purpose |
|-----------|----------|---------|
| `docs/ai/` | AI Agent (OpenCode) | Rules and instructions loaded into the agent's context |
| `docs/plans/` | Developers | Implementation plans and internal roadmap |
| `docs/architecture/` | Developers | Technical documentation explaining how things work |

### For AI Agents

Rules in `docs/ai/` are loaded into the Harvest agent's context via OpenCode's `instructions` config. These define:

- **`git.md`** - Git workflow requirements (Safe-Carry-Forward, checkpoint branches, force-push rules)
- **`memory.md`** - Memory MCP usage patterns (when to query, when to update, maintenance)
- **`harvest-mode.md`** - Autonomous operation rules (execute don't ask, fail forward, complete the loop)

### For Developers

- **Implementation Plans**: See [`docs/plans/`](docs/plans/) for the implementation roadmap
  - [`IMPLEMENTATION_PLAN.md`](docs/plans/IMPLEMENTATION_PLAN.md) - Overall phased approach
  - [`phase-1.1-modal-sandbox.md`](docs/plans/phase-1.1-modal-sandbox.md) - Detailed Modal sandbox infrastructure plan

- **Architecture Docs**: See [`docs/architecture/`](docs/architecture/) for system design documentation

---

## Getting Started

> **Note**: Harvest is currently in development. Setup instructions will be added as implementation progresses.

### Prerequisites

- Node.js 20+
- Modal account ([modal.com](https://modal.com))
- GitHub account with PAT
- OpenCode CLI (`npm install -g opencode`)

### Setup

```bash
# Clone the repository
git clone https://github.com/RelevanceAI/harvest.git
cd harvest

# Install dependencies
npm install

# Run setup wizard (creates Modal secrets)
npm run setup
```

---

## Roadmap

Based on the [Ramp Inspect architecture](https://builders.ramp.com/post/why-we-built-our-background-agent):

### Phase 1: Foundation
- [x] Planning complete
- [ ] Modal sandbox infrastructure
- [ ] GitHub App integration
- [ ] OpenCode server integration

### Phase 2: API Layer
- [ ] Cloudflare Workers + Durable Objects
- [ ] REST & WebSocket API

### Phase 3: Client
- [ ] Slack bot (primary interface)

### Phase 4: Intelligence
- [ ] Core agent tools (test runner, slack updates)
- [ ] Basic metrics tracking

See [`docs/plans/IMPLEMENTATION_PLAN.md`](docs/plans/IMPLEMENTATION_PLAN.md) for the full roadmap.

---

## How It Works

### Sandbox Architecture

Each Harvest session runs in an isolated Modal sandbox with:

- **`/app/`** - Harvest instructions, docs, and configs (baked into image)
- **`/workspace/{repo-name}/`** - Cloned repository (session-scoped)
- **`/root/.mcp-memory/`** - Persistent memory (per-repo Modal volume)

The agent's instructions and rules live in `/app/` and are referenced via absolute paths, keeping the user's repository clean.

### Memory Persistence

Harvest uses per-repository memory that persists across sessions:

- Volume: `harvest-memory-{owner}-{repo}`
- Location: `/root/.mcp-memory/memory.jsonl`
- Seeded with environment knowledge on first use
- Agent learns error patterns and conventions over time

### Git Workflow

Harvest follows a strict git workflow (see [`docs/ai/git.md`](docs/ai/git.md)):

- **Never** uses `git pull` or `git stash`
- Uses **Safe-Carry-Forward** pattern with snapshot commits
- Creates **checkpoint branches** before risky operations
- Commits are attributed with `(Harvest)` suffix

---

## Contributing

Contributions are welcome! Please read the implementation plans in `docs/plans/` to understand the architecture before contributing.

---

## License

[MIT](LICENSE)
