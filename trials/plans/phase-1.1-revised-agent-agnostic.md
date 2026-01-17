# Phase 1.1 Revised: Agent-Agnostic Modal Sandbox Infrastructure

## Context & Constraints

### Critical Blockers Discovered

1. **OpenCode Blocked**: Anthropic policy prohibits third-party wrappers using OAuth
2. **Claude CLI Blocked**: Direct Anthropic API usage too expensive
3. **Solution Pending**: Investigating wrapper solution in separate thread

### Design Principle

**Build infrastructure INDEPENDENT of agent runtime**. Phase 1.1 focuses on:
- Modal sandbox orchestration
- Session management (Ramp architecture)
- Message queueing
- Persistence layer
- Pluggable agent backend (swap in wrapper when ready)

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────────┐
│  Phase 2 (Future): Cloudflare DO + SQLite Session Management  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Durable Object per Session                              │  │
│  │  ├─ SQLite DB (session state, message queue)            │  │
│  │  ├─ authorship: who sent which prompt                   │  │
│  │  └─ status: running | paused | terminated               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                        │                                        │
│                        ▼                                        │
├────────────────────────────────────────────────────────────────┤
│  Phase 1.1 (This Plan): Modal Sandbox Infrastructure          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Modal Sandbox Instance                                  │  │
│  │  ├─ AgentRuntime (abstraction layer)                     │  │
│  │  │   ├─ execute(prompt) → response                       │  │
│  │  │   └─ Implementation: TBD (wrapper from other thread)  │  │
│  │  ├─ MCP Servers (memory, filesystem, playwright)        │  │
│  │  ├─ Repository clone at /workspace/{repo}               │  │
│  │  └─ Per-repo memory volume at /root/.mcp-memory/        │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

---

## What Changed from Original Phase 1.1 Plan

| Aspect | Original (OpenCode) | Revised (Agnostic) |
|--------|---------------------|-------------------|
| **Agent Runtime** | OpenCode server on :8080 | Abstract `AgentRuntime` interface |
| **Invocation** | HTTP POST to `/api/prompt` | `runtime.execute(prompt)` method |
| **Configuration** | `opencode.json` baked in | Runtime-specific config (pluggable) |
| **Continuity** | Server-based session | Cloudflare DO + SQLite (Phase 2) |
| **Message Queue** | N/A (server handles) | Durable Object queue (Ramp pattern) |
| **Dependencies** | Locked to OpenCode | Swap runtime without infrastructure change |

---

## Phase 1.1 Scope: Modal Sandbox Only

### What We're Building

1. **Base Modal Image** with:
   - Node.js 22, Python 3.11
   - Git, GitHub CLI
   - MCP servers (memory, filesystem, playwright, devtools)
   - Placeholder for agent runtime

2. **Sandbox Manager**:
   - Repository cloning to `/workspace/{repo}`
   - Per-repo memory volume mounting
   - Git configuration with "(Harvest)" suffix
   - Secrets injection (GitHub, optional MCP keys)

3. **Agent Runtime Abstraction**:
   ```python
   class AgentRuntime(ABC):
       @abstractmethod
       async def execute(self, prompt: str, context: dict) -> str:
           """Execute prompt, return response"""
           pass
   ```

4. **Stub Implementation** (for testing):
   ```python
   class StubAgentRuntime(AgentRuntime):
       async def execute(self, prompt: str, context: dict) -> str:
           # Placeholder - replace when wrapper ready
           return f"[STUB] Would execute: {prompt}"
   ```

### What We're NOT Building (Phase 2)

- ❌ Cloudflare Workers API
- ❌ Durable Objects session management
- ❌ Message queue implementation
- ❌ Slack bot integration
- ❌ Multiplayer/authorship tracking

---

## Implementation Blocks

### Block 1.1.1: Abstract Agent Runtime

**File**: `packages/modal-executor/src/modal_executor/agent_runtime.py`

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class AgentRuntime(ABC):
    """
    Abstract interface for AI agent execution.

    Allows swapping between different agent backends (OpenCode, Claude CLI,
    custom wrapper, etc.) without changing Modal infrastructure.
    """

    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the agent runtime.

        Args:
            config: Runtime-specific configuration (API keys, model settings, etc.)
        """
        pass

    @abstractmethod
    async def execute(self, prompt: str, context: Dict[str, Any]) -> str:
        """
        Execute a prompt and return the response.

        Args:
            prompt: User prompt or task description
            context: Session context (repo, branch, memory, etc.)

        Returns:
            Agent response text
        """
        pass

    @abstractmethod
    async def terminate(self) -> None:
        """Clean up resources (stop servers, close connections, etc.)"""
        pass


class StubAgentRuntime(AgentRuntime):
    """Placeholder runtime for testing infrastructure"""

    async def initialize(self, config: Dict[str, Any]) -> None:
        print(f"[STUB] Initialized with config: {config.keys()}")

    async def execute(self, prompt: str, context: Dict[str, Any]) -> str:
        return (
            f"[STUB RESPONSE]\n"
            f"Received prompt: {prompt}\n"
            f"Context: repo={context.get('repo')}, branch={context.get('branch')}\n"
            f"Would execute task here once real agent runtime is plugged in."
        )

    async def terminate(self) -> None:
        print("[STUB] Terminated")
```

**Deliverables**:
- [ ] `AgentRuntime` abstract base class
- [ ] `StubAgentRuntime` for testing
- [ ] Documentation in docstrings about plugging in real implementation

---

### Block 1.1.2: Base Modal Image (Agent-Agnostic)

**File**: `packages/modal-executor/src/modal_executor/images.py`

Update the base image to remove OpenCode-specific components:

```python
base_image = (
    modal.Image.debian_slim(python_version="3.11")
    # System dependencies
    .apt_install([
        "git", "curl", "wget", "jq", "ripgrep",
        "tree", "fd-find", "vim", "less",
        "build-essential",  # For native npm packages
        # Playwright dependencies
        "libnss3", "libnspr4", "libatk1.0-0", "libatk-bridge2.0-0",
        "libcups2", "libdrm2", "libdbus-1-3", "libxkbcommon0",
        "libatspi2.0-0", "libxcomposite1", "libxdamage1",
        "libxfixes3", "libxrandr2", "libgbm1", "libasound2",
    ])
    .run_commands("ln -s $(which fdfind) /usr/local/bin/fd || true")

    # Node.js 22 LTS
    .run_commands([
        "curl -fsSL https://deb.nodesource.com/setup_22.x | bash -",
        "apt-get install -y nodejs",
    ])

    # GitHub CLI
    .run_commands([
        "curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg",
        "chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg",
        "echo 'deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main' | tee /etc/apt/sources.list.d/github-cli.list > /dev/null",
        "apt-get update && apt-get install -y gh",
    ])

    # MCP Servers (agent-agnostic, work with any runtime)
    .run_commands([
        # Core MCP servers
        "npm install -g @modelcontextprotocol/server-memory",
        "npm install -g @modelcontextprotocol/server-filesystem",
        "npm install -g @anthropic-ai/mcp-server-playwright@latest || npm install -g @playwright/mcp@latest",
        "npm install -g chrome-devtools-mcp@latest",
        # Optional MCP servers
        "npm install -g @anthropic-ai/mcp-server-github@latest || true",
    ])

    # Playwright browsers
    .run_commands("npx playwright install chromium")

    # Directory structure
    .run_commands([
        "mkdir -p /workspace",
        "mkdir -p /app/docs/ai",
        "mkdir -p /root/.mcp-memory",
    ])

    # Agent-agnostic instructions
    .add_local_file(
        str(_CONFIG_DIR / "AGENTS.md"),
        "/app/AGENTS.md"
    )
    .add_local_file(
        str(_CONFIG_DIR / "memory-seed.json"),
        "/app/memory-seed.json"
    )
)
```

**Key Changes**:
- ❌ Removed OpenCode installation
- ❌ Removed OpenCode config injection
- ✅ Keep MCP servers (work with any agent)
- ✅ Keep agent instructions (generic behavior rules)

**Deliverables**:
- [ ] Updated base image without agent-specific dependencies
- [ ] MCP servers installed globally
- [ ] Generic agent instructions at `/app/AGENTS.md`

---

### Block 1.1.3: Sandbox Manager with Runtime Abstraction

**File**: `packages/modal-executor/src/modal_executor/sandbox.py`

Update `HarvestSandbox` to use pluggable runtime:

```python
from modal_executor.agent_runtime import AgentRuntime, StubAgentRuntime

class HarvestSandbox:
    """Modal sandbox for Harvest session with pluggable agent runtime"""

    def __init__(
        self,
        session_id: str,
        repo_owner: str,
        repo_name: str,
        agent_runtime: AgentRuntime = None,
    ):
        self.session_id = session_id
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.repo_path = f"/workspace/{repo_name}"

        # Use stub runtime if none provided
        self.agent_runtime = agent_runtime or StubAgentRuntime()

        # Per-repo memory volume
        self.memory_volume = modal.Volume.from_name(
            f"harvest-memory-{repo_owner}-{repo_name}",
            create_if_missing=True
        )

    async def start(
        self,
        github_token: str,
        user_email: str,
        user_name: str,
        branch: str = "main",
        agent_config: dict = None,
    ):
        """Start sandbox with repository and agent runtime"""

        # Build secrets
        secrets = {
            "GITHUB_TOKEN": github_token,
            "GIT_USER_EMAIL": user_email,
            "GIT_USER_NAME": user_name,
        }

        # Create Modal sandbox
        self.sandbox = await modal.Sandbox.create(
            image=base_image,
            timeout=3600,
            secrets=[modal.Secret.from_dict(secrets)],
            volumes={"/root/.mcp-memory": self.memory_volume},
        )

        # Setup sequence
        await self._clone_repo(github_token, branch)
        await self._configure_git(user_email, user_name, github_token)
        await self._seed_memory_if_needed()

        # Initialize agent runtime
        runtime_config = agent_config or {}
        runtime_config.update({
            "session_id": self.session_id,
            "repo_path": self.repo_path,
            "memory_path": "/root/.mcp-memory/memory.jsonl",
        })
        await self.agent_runtime.initialize(runtime_config)

        return self.sandbox

    async def send_prompt(self, prompt: str) -> str:
        """Send prompt to agent runtime"""
        context = {
            "repo": f"{self.repo_owner}/{self.repo_name}",
            "branch": await self._get_current_branch(),
            "session_id": self.session_id,
            "memory_path": "/root/.mcp-memory/memory.jsonl",
        }

        return await self.agent_runtime.execute(prompt, context)

    async def _get_current_branch(self) -> str:
        """Get current git branch"""
        result = await self.sandbox.exec(
            "git", "-C", self.repo_path, "branch", "--show-current"
        )
        return result.stdout.strip()

    # ... existing _clone_repo, _configure_git, etc. methods remain unchanged
```

**Deliverables**:
- [ ] `HarvestSandbox` accepts `AgentRuntime` parameter
- [ ] Uses `StubAgentRuntime` by default
- [ ] Passes context to runtime (repo, branch, memory path)
- [ ] Agent-agnostic sandbox setup (git, memory, volumes)

---

### Block 1.1.4: Update Configuration Files

**File**: `packages/modal-executor/src/modal_executor/config/AGENTS.md`

Remove OpenCode-specific instructions, keep generic behavior:

```markdown
# Harvest Agent

You are running as an autonomous coding agent in a Modal sandbox.

## Core Principles

1. **Execute, don't ask**: Make decisions and act
2. **Fail forward**: Diagnose and fix errors (max 3 retry attempts)
3. **Complete the loop**: Research → Code → Test → Commit → Push → PR
4. **Use your memory**: Query memory MCP before tasks, update after fixes

## Environment

- **Sandbox**: Isolated Modal container
- **Working directory**: /workspace/{repo-name}
- **Memory**: Persists per-repo at /root/.mcp-memory/
- **MCP Servers**: memory, filesystem, playwright, devtools, github, gemini

## Git Workflow (CRITICAL)

**NEVER use git pull or git stash**. Use Safe-Carry-Forward pattern:

1. **Snapshot before sync**:
   ```bash
   git add -A && git commit -m "wip: snapshot before sync" --no-verify
   ```

2. **Fetch then rebase**:
   ```bash
   git fetch origin
   git rebase origin/<branch>
   ```

3. **Squash before push**:
   ```bash
   git reset --soft origin/<branch>
   git commit -m "feat: descriptive message"
   git push origin <branch>
   ```

4. **Checkpoint before risky ops**:
   ```bash
   CURRENT=$(git branch --show-current)
   git checkout -b "checkpoint-$CURRENT-$(date +%s)"
   git checkout "$CURRENT"
   # attempt risky operation
   ```

## Panic Button

Stop and report to API if:
- Test failure after 3 attempts
- Forced update on shared branch
- Network timeout after 3 retries
- Permission denied or disk full

See /app/docs/ai/ for detailed workflow documentation.
```

**File**: `packages/modal-executor/src/modal_executor/config/memory-seed.json`

Keep existing memory seed (it's agent-agnostic).

**Deliverables**:
- [ ] Updated AGENTS.md (remove OpenCode references)
- [ ] Keep memory-seed.json as-is
- [ ] Document that agent-specific docs live in /app/docs/ai/

---

### Block 1.1.5: Integration Test with Stub Runtime

**File**: `packages/modal-executor/tests/test_sandbox_integration.py`

```python
import pytest
from modal_executor.sandbox import HarvestSandbox
from modal_executor.agent_runtime import StubAgentRuntime

@pytest.mark.integration
async def test_sandbox_with_stub_runtime():
    """Verify sandbox starts successfully with stub agent runtime"""

    runtime = StubAgentRuntime()
    sandbox = HarvestSandbox(
        session_id="test-123",
        repo_owner="RelevanceAI",
        repo_name="test-repo",
        agent_runtime=runtime,
    )

    await sandbox.start(
        github_token=os.environ["TEST_GITHUB_TOKEN"],
        user_email="test@example.com",
        user_name="Test User",
    )

    # Send test prompt
    response = await sandbox.send_prompt("List files in repository")

    # Stub should respond
    assert "[STUB RESPONSE]" in response
    assert "List files in repository" in response

    await sandbox.terminate()


@pytest.mark.integration
async def test_git_configuration():
    """Verify git identity includes (Harvest) suffix"""

    sandbox = HarvestSandbox("test-456", "owner", "repo")
    await sandbox.start(
        github_token=os.environ["TEST_GITHUB_TOKEN"],
        user_email="test@example.com",
        user_name="Test User",
    )

    result = await sandbox.sandbox.exec("git", "config", "user.name")
    assert "(Harvest)" in result.stdout

    await sandbox.terminate()


@pytest.mark.integration
async def test_memory_volume_mounted():
    """Verify memory volume is accessible"""

    sandbox = HarvestSandbox("test-789", "owner", "repo")
    await sandbox.start(...)

    # Check memory directory exists
    result = await sandbox.sandbox.exec("ls", "-la", "/root/.mcp-memory/")
    assert result.returncode == 0

    await sandbox.terminate()
```

**Deliverables**:
- [ ] Integration tests using `StubAgentRuntime`
- [ ] Tests verify sandbox infrastructure (git, memory, volumes)
- [ ] Tests DO NOT require real agent runtime

---

## When to Plug In Real Agent Runtime

Once the wrapper investigation completes, implement:

```python
# packages/modal-executor/src/modal_executor/agent_runtime_wrapper.py

class WrapperAgentRuntime(AgentRuntime):
    """Real agent runtime using the wrapper from investigation"""

    async def initialize(self, config: Dict[str, Any]) -> None:
        # Initialize wrapper connection
        # Set up MCP servers
        # Configure model settings
        pass

    async def execute(self, prompt: str, context: Dict[str, Any]) -> str:
        # Call wrapper API/CLI
        # Parse response
        # Return text
        pass

    async def terminate(self) -> None:
        # Clean up wrapper resources
        pass
```

Then update sandbox creation:

```python
# Use real runtime instead of stub
runtime = WrapperAgentRuntime()
sandbox = HarvestSandbox(..., agent_runtime=runtime)
```

---

## Ramp-Style Session Management (Phase 2 Preview)

Not implemented in Phase 1.1, but here's the design:

```typescript
// Phase 2: Cloudflare Durable Object

export class HarvestSession extends DurableObject {
  private db: SqlStorage;  // Durable Object SQLite
  private messageQueue: Message[] = [];

  async createSession(request: SessionRequest) {
    // Spin up Modal sandbox
    const sandboxId = await modalClient.createSandbox({
      repo: request.repo,
      agentRuntime: "wrapper",  // Plug in real runtime
    });

    // Track in SQLite
    await this.db.exec(`
      INSERT INTO sessions (id, sandbox_id, status, created_at)
      VALUES (?, ?, 'running', datetime('now'))
    `, [this.id.toString(), sandboxId]);

    return { sessionId: this.id, sandboxId };
  }

  async sendMessage(message: string, author: string) {
    // Queue message (Ramp pattern)
    await this.db.exec(`
      INSERT INTO message_queue (session_id, content, author, queued_at)
      VALUES (?, ?, ?, datetime('now'))
    `, [this.id.toString(), message, author]);

    // If agent idle, process immediately
    if (await this.isIdle()) {
      await this.processQueue();
    }
  }

  private async processQueue() {
    const messages = await this.db.exec(`
      SELECT * FROM message_queue
      WHERE session_id = ? AND processed = 0
      ORDER BY queued_at ASC
    `, [this.id.toString()]);

    for (const msg of messages) {
      // Send to Modal sandbox
      await modalClient.sendPrompt(this.sandboxId, msg.content);

      // Mark processed
      await this.db.exec(`
        UPDATE message_queue SET processed = 1 WHERE id = ?
      `, [msg.id]);
    }
  }
}
```

---

## File Structure

```
packages/modal-executor/
├── src/modal_executor/
│   ├── agent_runtime.py          # NEW: Abstract runtime + stub
│   ├── images.py                 # UPDATED: Remove OpenCode
│   ├── sandbox.py                # UPDATED: Use AgentRuntime abstraction
│   ├── config/
│   │   ├── AGENTS.md             # UPDATED: Remove OpenCode refs
│   │   └── memory-seed.json      # UNCHANGED
│   └── ...
├── tests/
│   ├── test_sandbox_integration.py  # NEW: Tests with stub runtime
│   └── poc_claude_cli.py            # ARCHIVE: No longer needed
└── README.md                        # UPDATED: Document abstraction

Phase 2 (future):
cloudflare-api/
├── src/
│   └── session.ts                # Durable Object with SQLite
└── ...
```

---

## Critical Files to Modify

1. **NEW**: `packages/modal-executor/src/modal_executor/agent_runtime.py`
2. **UPDATE**: `packages/modal-executor/src/modal_executor/images.py` (remove OpenCode)
3. **UPDATE**: `packages/modal-executor/src/modal_executor/sandbox.py` (use AgentRuntime)
4. **UPDATE**: `packages/modal-executor/src/modal_executor/config/AGENTS.md` (generic instructions)
5. **NEW**: `packages/modal-executor/tests/test_sandbox_integration.py`
6. **UPDATE**: `packages/modal-executor/README.md` (document abstraction)

---

## Verification Plan

### Step 1: Build Base Image

```bash
cd packages/modal-executor
modal deploy src/modal_executor/app.py
```

**Expected**: Image builds successfully without OpenCode, includes MCP servers

### Step 2: Test Sandbox Creation

```bash
pytest tests/test_sandbox_integration.py::test_sandbox_with_stub_runtime -v
```

**Expected**: Sandbox starts, stub runtime responds with placeholder text

### Step 3: Test Git Configuration

```bash
pytest tests/test_sandbox_integration.py::test_git_configuration -v
```

**Expected**: Git user.name includes "(Harvest)" suffix

### Step 4: Test Memory Volume

```bash
pytest tests/test_sandbox_integration.py::test_memory_volume_mounted -v
```

**Expected**: `/root/.mcp-memory/` directory exists and is writable

### Step 5: Manual Smoke Test

```python
from modal_executor.sandbox import HarvestSandbox

async def smoke_test():
    sandbox = HarvestSandbox("smoke-test", "RelevanceAI", "test-repo")
    await sandbox.start(
        github_token=os.environ["GITHUB_TOKEN"],
        user_email="dev@relevance.ai",
        user_name="Developer",
    )

    # Send test prompt
    response = await sandbox.send_prompt("Echo: Hello from Harvest!")
    print(response)  # Should see "[STUB RESPONSE]"

    await sandbox.terminate()
```

**Expected**: Full sandbox lifecycle works, stub responds correctly

---

## Success Criteria

- ✅ Base image builds without agent-specific dependencies
- ✅ Sandbox creates successfully with stub runtime
- ✅ Git configured with "(Harvest)" suffix
- ✅ Memory volume mounts and persists
- ✅ MCP servers installed globally
- ✅ Abstract `AgentRuntime` interface defined
- ✅ Integration tests pass with stub
- ✅ Ready to plug in real agent when wrapper investigation completes

---

## Dependencies on Other Threads

**Blocked By**: Wrapper investigation (separate thread)
**Blocks**: Phase 2 (Cloudflare DO + session management)

**When wrapper ready**:
1. Implement `WrapperAgentRuntime(AgentRuntime)`
2. Swap out `StubAgentRuntime` for real implementation
3. No changes needed to Modal infrastructure

---

## Timeline Estimate

**Phase 1.1 (This Plan)**: Can complete immediately
- Block 1.1.1: 1 hour (abstract runtime + stub)
- Block 1.1.2: 1 hour (update base image)
- Block 1.1.3: 2 hours (update sandbox manager)
- Block 1.1.4: 1 hour (update configs)
- Block 1.1.5: 2 hours (integration tests)
- **Total: 1 day**

**Phase 2 (Future)**: Blocked on wrapper investigation completion
