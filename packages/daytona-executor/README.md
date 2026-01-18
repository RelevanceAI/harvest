# Daytona Executor

Pre-built Docker snapshot image for running Harvest agents via Daytona and Claude Agent SDK.

## Overview

This package provides:
- **Dockerfile** for the Harvest agent snapshot image
- **Build script** that copies config files from source of truth locations
- **Test scripts** for validating the image and demonstrating SDK message flow
- **Memory seed** for initializing the MCP memory server knowledge graph

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed diagrams of:
- System overview (Relevance → Daytona → SDK → Claude)
- Message flow sequences
- Session resume and cancellation flows
- SDK message types state diagram

## Quick Start

### Build the Image

```bash
cd packages/daytona-executor/snapshot

# Build the image (copies config files from source of truth)
./build.sh
```

This creates `harvest-daytona-snapshot:latest` with:
- Node.js 20 + npm + pnpm
- Python 3.11 + Git + ripgrep + fd
- Claude Agent SDK (`@anthropic-ai/claude-code`)
- All MCP servers pre-installed globally
- Playwright + Chromium
- Baked configuration files at `/app/`

### Validate the Image

```bash
# Test image contents (no API keys needed)
./test-snapshot.sh
```

Tests:
- System tools (Node, Python, Git, ripgrep, fd)
- Security (running as `harvest` user, not root)
- Claude Agent SDK installed
- MCP servers installed
- Playwright + Chromium available
- Configuration files baked in at `/app/`

### Test the SDK

```bash
# Requires CLAUDE_CODE_OAUTH_TOKEN (set in .env.local or environment)
export CLAUDE_CODE_OAUTH_TOKEN=your_token_here

# Interactive mode - chat with Claude
./test.sh

# Single prompt mode
./test.sh "List files in /app and describe what you see"
```

Streams the full message flow showing:
- `system/init` - Session start, available tools
- `assistant` - Claude's text and tool_use blocks
- `tool_result` - Tool execution results
- `result` - Final status, cost tracking

## How It Works

### Config File Strategy

Configuration files are **not duplicated** in this package. Instead, `build.sh` copies them at build time from their source of truth locations:

| File in Image | Source |
|---------------|--------|
| `/app/claude.md` | `.claude/CLAUDE.md` |
| `/app/autonomous-agent.md` | `docs/ai/autonomous-agent.md` |
| `/app/docs/ai/shared/*` | `docs/ai/shared/*` |
| `/app/docs/mcp/*` | `docs/mcp/*` |
| `/app/memory-seed.json` | `packages/daytona-executor/config/memory-seed.json` |

Only `memory-seed.json` is unique to this package.

### How `relevance-api-node` Uses This

The snapshot image is used by `relevance-api-node` when creating Daytona sandboxes:

```typescript
// In relevance-api-node (NOT in this package):
import { Daytona } from "@daytonaio/sdk";

const daytona = new Daytona({ apiKey: DAYTONA_API_KEY });

// Create sandbox from pre-built snapshot
const sandbox = await daytona.create({
  image: "registry.daytona.io/harvest-daytona-snapshot:latest",
  envVars: {
    CLAUDE_CODE_OAUTH_TOKEN: userOAuthToken,
    GITHUB_TOKEN: userGitHubToken,
    // ... other MCP server tokens
  }
});

// Run SDK code that invokes Claude
const result = await sandbox.process.codeRun(`
  import { query } from "@anthropic-ai/claude-agent-sdk";

  const rules = await readFile('/app/claude.md', 'utf-8');
  const agentRules = await readFile('/app/autonomous-agent.md', 'utf-8');

  const response = query({
    prompt: "${userPrompt}",
    options: {
      systemPrompt: {
        type: "preset",
        preset: "claude_code",
        append: \`\${rules}\\n\\n\${agentRules}\`
      },
      workingDirectory: "/app",
      mcpServers: {
        memory: { command: "mcp-server-memory" },
        github: { command: "mcp-server-github", env: { GITHUB_TOKEN } },
        // ...
      }
    }
  });

  for await (const message of response) {
    console.log(JSON.stringify(message));
  }
`);
```

### MCP Server Lifecycle

MCP servers are npm-installed globally in the image. The SDK's `mcpServers` option spawns them on demand - no manual startup needed.

### Path Resolution

The SDK's `workingDirectory: "/app"` option means that when Claude sees `@docs/ai/shared/foo.md`, it resolves to `/app/docs/ai/shared/foo.md`.

## Environment Variables

### Required for Testing

| Variable | Purpose |
|----------|---------|
| `CLAUDE_CODE_OAUTH_TOKEN` | OAuth token for Claude API (get from Claude.ai settings) |

### Available in Production (set by `relevance-api-node`)

| Variable | Purpose |
|----------|---------|
| `CLAUDE_CODE_OAUTH_TOKEN` | Claude API authentication |
| `GITHUB_TOKEN` | GitHub API for MCP server |
| `LINEAR_API_KEY` | Linear API for MCP server |
| `GEMINI_API_KEY` | Gemini API for MCP server |
| `SENTRY_AUTH_TOKEN` | Sentry API for MCP server |

## Directory Structure

```
packages/daytona-executor/
├── README.md                    # This file
├── ARCHITECTURE.md              # Architecture diagrams
├── .env.example                 # Environment template
├── snapshot/
│   ├── Dockerfile               # Main image definition
│   ├── build.sh                 # Build script (copies config + builds)
│   ├── test-snapshot.sh         # Validates image contents
│   └── test.sh                  # SDK test (interactive + single prompt)
└── config/
    └── memory-seed.json         # Initial MCP memory graph
```

## Memory Seed

The `config/memory-seed.json` file seeds the MCP memory server with initial entities:

- **HarvestSession** - Session context tracking
- **EnvironmentConfig** - Environment knowledge (paths, tools, limitations)
- **GitWorkflow** - Git rules and patterns
- **WorkflowProcedures** - Testing, PRs, deployment
- **ErrorPatterns** - Errors and solutions (grows over time)
- **LearnedPatterns** - Repo-specific conventions (grows over time)

As the agent works, it adds observations to these entities, building persistent knowledge per-repository.

## Future Work

### Scheduler (Not MVP)

A future scheduler will pre-clone repositories every 30 minutes for faster sandbox startup. This will be implemented as a separate Daytona job.

## Related

- [POC Validation](../../trials/daytona-sdk-poc/) - SDK validation code
