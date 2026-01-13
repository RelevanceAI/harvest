# Harvest

> Did you **Harvest** that? 🌾

Build your AI Workforce with Harvest - the background coding agent that tends to your repositories like farmers tending to crops, cultivating code that grows stronger while you sleep.

Harvest is a background coding agent service built on the architecture that powers [Ramp's Inspect](https://builders.ramp.com/post/why-we-built-our-background-agent), designed specifically for the **Relevance AI** ecosystem.

### Core Capabilities

- **🔄 Autonomous Development**: Works continuously across multiple repositories without human intervention
- **📦 Sandbox Orchestration**: Spins up isolated Modal sandboxes for each task or repository
- **🤖 OpenCode Integration**: Leverages the full power of OpenCode agents and multi-model switching
- **🌾 Multi-Repo Management**: Seamlessly switches between your entire codebase portfolio
- **📊 Growth Monitoring**: Tracks progress, quality, and deployment readiness
- **🔄 Continuous Harvesting**: Generates pull requests, fixes bugs, and improves code while you focus on other work

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

## 🎯 Our Roadmap (Inspired by Ramp)

Based on the [Ramp Inspect architecture](https://builders.ramp.com/post/why-we-built-our-background-agent)
