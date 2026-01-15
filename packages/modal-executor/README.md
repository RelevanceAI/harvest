# Modal Executor

Modal Sandbox executor for Harvest AI agent - enables isolated execution of AI-generated code with full development environment.

## Features

- **Sandbox Execution**: Run arbitrary Python code in isolated Modal Sandboxes
- **HarvestSandbox**: Full agent environment with Claude Code CLI, MCP servers, and browser automation
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
    claude_oauth_token="oauth_xxx",
    # Optional
    gemini_api_key="xxx",
    sentry_auth_token="xxx",
)

# Start sandbox with full environment
sandbox = HarvestSandbox(session)
await sandbox.start()

# Send prompt to Claude CLI agent with streaming
async for chunk in sandbox.send_prompt_stream(
    "Fix the failing tests in src/classifier.ts"
):
    print(chunk, end="")

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
| Claude Code CLI | Latest | AI coding agent (official Anthropic tool) |
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
  memory-seed.json    # Initial memory entities
/root/
  .claude/            # Claude Code CLI config
  .mcp-memory/        # Memory volume (persistent per-repo)
/mnt/state/           # Modal Volume (persistent)
  sessions/           # SQLite databases for conversation state
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

## Debugging Claude CLI Regressions

If Claude CLI integration breaks (auth fails, streaming breaks, format changes), use the validation script to diagnose issues:

### 1. Run Validation Script

```bash
export CLAUDE_CODE_OAUTH_TOKEN=<your-token>
python scripts/validate_claude_cli.py
```

This script validates:
- OAuth authentication
- Streaming format
- Exit code handling

### 2. Check Claude CLI Version

```bash
claude --version
```

### 3. Run POC Test

```bash
modal run tests/poc_claude_cli.py
```

### 4. Update ClaudeCliWrapper

If stream format changed, update `src/modal_executor/claude_cli.py::_extract_text()` to handle new event formats.

The validation script is located at `scripts/validate_claude_cli.py` for easy discovery when debugging regressions.

## Configuration Files

Configuration files are baked into the image at `/app/`:

- **AGENTS.md**: Agent instructions (git workflow, panic button, etc.)
- **memory-seed.json**: Initial knowledge graph entities

See `src/modal_executor/config/` for the source files.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | Yes | GitHub PAT for cloning repos |
| `CLAUDE_CODE_OAUTH_TOKEN` | Yes | OAuth token for Claude Code CLI (team subscription) |
| `GEMINI_API_KEY` | No | For Gemini MCP server |
| `SENTRY_AUTH_TOKEN` | No | For Sentry MCP server |
| `LINEAR_API_KEY` | No | For Linear MCP server |

## Architecture

```
Modal App (harvest-agent-executor)
├── Base Image
│   ├── Python 3.11 + Node.js 22 + Volta
│   ├── Playwright + Chromium
│   ├── Claude Code CLI + MCP servers
│   └── Config files (/app/)
├── Per-Session Sandboxes
│   ├── Repository clone (/workspace/)
│   ├── Git credentials + identity
│   ├── Claude CLI with OAuth
│   ├── Session state (SQLite in /mnt/state/sessions/)
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
