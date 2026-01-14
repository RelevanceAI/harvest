# Modal Executor

Modal Sandbox executor for Harvest AI agent - enables isolated execution of AI-generated code with full development environment.

## Features

- **Sandbox Execution**: Run arbitrary Python code in isolated Modal Sandboxes
- **HarvestSandbox**: Full agent environment with OpenCode, MCP servers, and browser automation
- **Multi-Repo Support**: Clone and work with any GitHub repository at `/workspace/{repo-name}`
- **Persistent Memory**: Per-repo knowledge graph that persists across sessions
- **Pre-Built Images**: 30-minute cron job keeps repository images warm with dependencies installed
- **Git Integration**: Safe-Carry-Forward workflow with "(Harvest)" attribution suffix
- **Timeout Enforcement**: Configurable execution timeouts with clean termination

## Installation

```bash
cd packages/modal-executor
uv venv --allow-existing
source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Setup

1. Authenticate with Modal:
   ```bash
   modal setup
   ```

2. Create required secrets:
   ```bash
   modal secret create harvest-github GITHUB_TOKEN=ghp_xxx
   ```

3. Verify setup:
   ```bash
   modal list
   ```

## Usage

### Basic Code Execution

```python
from modal_executor import SandboxExecutor

# Create executor
executor = SandboxExecutor()

# Execute code
result = await executor.execute(
    code='print("Hello from sandbox")',
    timeout_secs=30
)

print(f"Exit code: {result.returncode}")
print(f"Output: {result.stdout}")
```

### Full Agent Session (HarvestSandbox)

```python
from modal_executor import HarvestSandbox, HarvestSession

# Configure session
session = HarvestSession(
    session_id="task-123",
    repo_owner="RelevanceAI",
    repo_name="relevance-chat-app",
    branch="main",
    user_email="dev@example.com",
    user_name="Developer",
    github_token="ghp_xxx",
    anthropic_api_key="sk-ant-xxx",
    # Optional
    gemini_api_key="xxx",
    sentry_auth_token="xxx",
)

# Start sandbox with full environment
sandbox = HarvestSandbox(session)
await sandbox.start()

# Send prompt to OpenCode agent
response = await sandbox.send_prompt(
    "Fix the failing tests in src/classifier.ts"
)
print(response)

# Run commands directly
result = await sandbox.exec("npm", "test")
print(result.stdout)

# Clean up
await sandbox.terminate()
```

### Pre-Build Repository Images

```python
from modal_executor import build_repo_image, refresh_all_images

# Build a specific repo
result = build_repo_image.remote(
    repo_owner="RelevanceAI",
    repo_name="relevance-chat-app",
    branch="main"
)
print(f"Build success: {result['success']}")

# Refresh all registered repos (runs every 30 min automatically)
refresh_all_images.remote()
```

## Environment

The sandbox includes:

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11 | Base runtime |
| Node.js | 22 | JavaScript/TypeScript execution |
| Volta | Latest | Node version management |
| pnpm | Latest | Monorepo package management |
| Playwright | Latest | Browser automation (Chromium) |
| OpenCode | Latest | AI coding agent |
| GitHub CLI | Latest | Repository operations |

### MCP Servers

**Always Available:**
- `memory` - Persistent knowledge graph at `/root/.mcp-memory/`
- `filesystem` - File operations in `/workspace`
- `playwright` - Browser automation
- `devtools` - Chrome DevTools Protocol

**Conditionally Available (require API keys):**
- `github` - Repository operations
- `gemini` - Plan review and web research
- `sentry` - Error tracking
- `linear` - Issue tracking (via mcp-remote)

## Directory Structure

```
/workspace/           # Repository root
  {repo-name}/        # Cloned repository
/app/                 # Harvest config (read-only)
  AGENTS.md           # Agent instructions
  opencode.json       # OpenCode configuration
  memory-seed.json    # Initial memory entities
/root/
  .config/opencode/   # OpenCode config
  .mcp-memory/        # Memory volume (persistent per-repo)
```

## Development

```bash
# Run tests (mocked, no Modal required)
pytest

# Run integration tests (requires Modal credentials)
pytest -m modal

# Deploy to Modal
modal deploy src/modal_executor/app.py
```

## Configuration Files

Configuration files are baked into the image at `/app/`:

- **opencode.json**: MCP server configuration
- **AGENTS.md**: Agent instructions (git workflow, panic button, etc.)
- **memory-seed.json**: Initial knowledge graph entities

See `src/modal_executor/config/` for the source files.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | Yes | GitHub PAT for cloning repos |
| `ANTHROPIC_API_KEY` | Yes | For OpenCode agent |
| `GEMINI_API_KEY` | No | For Gemini MCP server |
| `SENTRY_AUTH_TOKEN` | No | For Sentry MCP server |
| `LINEAR_API_KEY` | No | For Linear MCP server |

## Architecture

```
Modal App (harvest-agent-executor)
├── Base Image
│   ├── Python 3.11 + Node.js 22 + Volta
│   ├── Playwright + Chromium
│   ├── OpenCode + MCP servers
│   └── Config files (/app/)
├── Per-Session Sandboxes
│   ├── Repository clone (/workspace/)
│   ├── Git credentials + identity
│   ├── OpenCode server (:8080)
│   └── Memory volume mount
├── Per-Repo Memory Volumes
│   └── harvest-memory-{owner}-{repo}
└── Cron Job (30 min)
    └── Refresh repo images with latest deps
```

## Git Workflow

The agent follows Safe-Carry-Forward rules:

1. **Never `git pull` or `git stash`** - commits are permanent
2. **Snapshot before sync**: `git commit -m "wip: snapshot" --no-verify`
3. **Fetch then rebase**: `git fetch origin && git rebase origin/branch`
4. **Checkpoint before risky ops**: Create branch for recovery

Git commits include "(Harvest)" suffix for attribution:
```
Author: Developer (Harvest) <dev@example.com>
```

## Related Documentation

- [Phase 1.1 Plan](../../docs/plans/phase-1.1-modal-sandbox.md) - Detailed architecture
- [Git Workflow Rules](../../docs/ai/shared/git-workflow.md) - Safe-Carry-Forward pattern
- [Autonomous Agent Rules](../../docs/ai/autonomous-agent.md) - Agent behavior
- [Memory MCP](../../docs/mcp/memory.md) - Knowledge graph usage
