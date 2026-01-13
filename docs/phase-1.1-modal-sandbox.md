# Phase 1.1: Modal Sandbox Infrastructure

> Detailed implementation plan for the core execution environment

## Overview

This phase creates the Modal sandbox infrastructure that powers Harvest sessions. Each session runs in an isolated Modal sandbox with a full development environment, OpenCode agent, and GitHub integration.

**Key Difference from Docker Implementation**: The existing `relevance-chat-app/docker` setup uses Docker Compose with a single hardcoded repository. Harvest uses Modal sandboxes that:
1. Work with **any repository** (multi-repo support)
2. Use `/workspace` as root, with repos cloned to `/workspace/{repo-name}`
3. Support **concurrent sessions** across different repos
4. Use **snapshots** for fast startup (30-minute image refresh cycle)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Modal Infrastructure                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐     ┌──────────────────┐                  │
│  │  Image Builder   │────►│  Image Registry  │                  │
│  │  (Cron: 30min)   │     │  (Per-repo)      │                  │
│  └──────────────────┘     └──────────────────┘                  │
│                                   │                              │
│                                   ▼                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Sandbox Instance                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │   │
│  │  │  /workspace │  │  OpenCode   │  │  GitHub     │       │   │
│  │  │  ├── repo-a │  │  Server     │  │  Integration│       │   │
│  │  │  ├── repo-b │  │             │  │             │       │   │
│  │  │  └── ...    │  │             │  │             │       │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## What We Learned from Docker Implementation

### Key Patterns to Replicate

| Pattern | Docker Implementation | Modal Implementation |
|---------|----------------------|---------------------|
| **Non-root user** | `useradd -u 10001 autopilot` | Modal runs as root by default; create harvest user in image |
| **UTF-8 locale** | `locale-gen en_US.UTF-8` | Same - needed for terminal Unicode support |
| **Git credentials** | GitHub PAT in `/run/secrets/`, credential helper | GitHub App installation tokens, injected at runtime |
| **Agent config** | `.claude.json` with `hasCompletedOnboarding`, bypass permissions | OpenCode config - similar pattern, different files |
| **Workspace trust** | `hasTrustDialogAccepted: true` per project | OpenCode equivalent - research needed |
| **MCP servers** | Globally installed npm packages, `.mcp.json` template | Same approach - pre-install in image |
| **Environment vars** | Written to `~/.autopilot-env`, sourced from `.bashrc` | Inject via Modal sandbox environment |
| **Session persistence** | tmux session with pipe to Docker logs | OpenCode server mode handles this |

### Key Patterns to Change

| Pattern | Docker Implementation | Modal Implementation |
|---------|----------------------|---------------------|
| **Single repo** | Hardcoded clone of `relevance-chat-app` | Multi-repo: clone to `/workspace/{repo-name}` |
| **Workspace root** | `/workspace` IS the repo | `/workspace` contains multiple repos |
| **Image updates** | Manual `docker compose build` | Automated cron every 30 minutes |
| **Session storage** | Docker volumes | Modal snapshots |
| **Agent** | Claude Code CLI | OpenCode server |

---

## Implementation Blocks

### Block 1.1.1: Base Modal Image

**Goal**: Create a base image with all system dependencies

**File**: `harvest/modal/images/base.py`

```python
import modal

# Base image with system dependencies
base_image = (
    modal.Image.debian_slim(python_version="3.12")
    # System packages (from Docker implementation)
    .apt_install([
        "git",
        "curl",
        "wget",
        "jq",
        "ripgrep",
        "tree",
        "fd-find",
        "vim",
        "less",
        "locales",
        "build-essential",  # For native npm packages
    ])
    # Generate UTF-8 locale
    .run_commands([
        "echo 'en_US.UTF-8 UTF-8' >> /etc/locale.gen",
        "locale-gen en_US.UTF-8",
        "update-locale LANG=en_US.UTF-8",
        # Alias fd (Debian naming quirk)
        "ln -s $(which fdfind) /usr/local/bin/fd || true",
    ])
    # Install Node.js 20 LTS
    .run_commands([
        "curl -fsSL https://deb.nodesource.com/setup_20.x | bash -",
        "apt-get install -y nodejs",
    ])
    # Install GitHub CLI
    .run_commands([
        "curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg",
        "chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg",
        "echo 'deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main' | tee /etc/apt/sources.list.d/github-cli.list > /dev/null",
        "apt-get update && apt-get install -y gh",
    ])
    # Install OpenCode
    .run_commands([
        "npm install -g opencode@latest",
    ])
    # Pre-install MCP servers (avoids npx latency)
    .run_commands([
        "npm install -g @modelcontextprotocol/server-memory @modelcontextprotocol/server-filesystem",
    ])
    # Create workspace directory
    .run_commands([
        "mkdir -p /workspace",
    ])
    # Set environment
    .env({
        "LANG": "en_US.UTF-8",
        "LANGUAGE": "en_US:en",
        "LC_ALL": "en_US.UTF-8",
        "TERM": "xterm-256color",
    })
)
```

**Deliverables**:
- [ ] Base image definition with all system deps
- [ ] Node.js 20 LTS installed
- [ ] GitHub CLI installed
- [ ] OpenCode installed globally
- [ ] MCP servers pre-installed
- [ ] UTF-8 locale configured

---

### Block 1.1.2: Repository Image Builder

**Goal**: Build per-repository images with dependencies pre-installed

**File**: `harvest/modal/images/repo_builder.py`

```python
import modal
from harvest.modal.images.base import base_image

app = modal.App("harvest-image-builder")

# Volume for storing built images metadata
image_registry = modal.Volume.from_name("harvest-image-registry", create_if_missing=True)

@app.function(
    image=base_image,
    secrets=[modal.Secret.from_name("harvest-github")],
    timeout=1800,  # 30 minutes max for large repos
)
def build_repo_image(
    repo_owner: str,
    repo_name: str,
    branch: str = "main",
) -> dict:
    """
    Build a pre-warmed image for a repository.
    
    1. Clone the repository
    2. Install dependencies (npm/pip/etc)
    3. Run initial build commands
    4. Return metadata for snapshot
    """
    import os
    import subprocess
    import json
    
    github_token = os.environ["GITHUB_TOKEN"]
    repo_url = f"https://x-access-token:{github_token}@github.com/{repo_owner}/{repo_name}.git"
    repo_path = f"/workspace/{repo_name}"
    
    # Clone repository
    subprocess.run([
        "git", "clone", "--depth", "1", "--branch", branch,
        repo_url, repo_path
    ], check=True)
    
    os.chdir(repo_path)
    
    # Detect and install dependencies
    build_info = {"repo": f"{repo_owner}/{repo_name}", "branch": branch}
    
    if os.path.exists("package.json"):
        subprocess.run(["npm", "ci"], check=True)
        build_info["package_manager"] = "npm"
        
        # Run build if script exists
        with open("package.json") as f:
            pkg = json.load(f)
            if "build" in pkg.get("scripts", {}):
                subprocess.run(["npm", "run", "build"], check=False)  # Don't fail on build errors
                
    elif os.path.exists("requirements.txt"):
        subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True)
        build_info["package_manager"] = "pip"
        
    elif os.path.exists("pyproject.toml"):
        subprocess.run(["pip", "install", "-e", "."], check=True)
        build_info["package_manager"] = "pip"
    
    # Run tests once to warm caches
    if os.path.exists("package.json"):
        subprocess.run(["npm", "test"], check=False, timeout=300)
    
    return build_info


@app.function(schedule=modal.Period(minutes=30))
def refresh_all_images():
    """
    Cron job: Rebuild all registered repository images every 30 minutes.
    """
    # TODO: Read from registry which repos to build
    # For now, hardcoded list
    repos = [
        ("RelevanceAI", "relevance-chat-app", "main"),
        # Add more repos here
    ]
    
    for owner, name, branch in repos:
        build_repo_image.spawn(owner, name, branch)
```

**Deliverables**:
- [ ] Repository image builder function
- [ ] Dependency detection (npm, pip, pyproject.toml)
- [ ] Initial build/test run for cache warming
- [ ] 30-minute cron job for image refresh
- [ ] Image registry volume for metadata

---

### Block 1.1.3: Sandbox Manager

**Goal**: Create and manage sandbox instances from snapshots

**File**: `harvest/modal/sandbox.py`

```python
import modal
from harvest.modal.images.base import base_image

app = modal.App("harvest-sandbox")

# Shared volume for snapshots
snapshots = modal.Volume.from_name("harvest-snapshots", create_if_missing=True)


class HarvestSandbox:
    """
    Manages a Modal sandbox for a Harvest session.
    
    Key design decisions:
    - /workspace is the root, repos cloned to /workspace/{repo-name}
    - OpenCode runs in server mode
    - Snapshots enable fast restore after exit
    """
    
    def __init__(self, session_id: str, repo_owner: str, repo_name: str):
        self.session_id = session_id
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.repo_path = f"/workspace/{repo_name}"
        self.sandbox = None
    
    async def start(self, github_token: str, user_email: str, user_name: str):
        """
        Start a new sandbox or restore from snapshot.
        """
        # Try to restore from snapshot first
        snapshot_id = f"{self.repo_owner}-{self.repo_name}-latest"
        
        try:
            self.sandbox = await modal.Sandbox.create(
                image=base_image,
                snapshot_id=snapshot_id,
                timeout=3600,  # 1 hour max
                secrets=[modal.Secret.from_dict({
                    "GITHUB_TOKEN": github_token,
                    "GIT_USER_EMAIL": user_email,
                    "GIT_USER_NAME": user_name,
                })],
            )
        except modal.exception.NotFoundError:
            # No snapshot, start fresh
            self.sandbox = await modal.Sandbox.create(
                image=base_image,
                timeout=3600,
            )
            await self._setup_fresh(github_token, user_email, user_name)
        
        # Sync with latest code (at most 30 min behind)
        await self._sync_repo(github_token)
        
        # Configure git identity
        await self._configure_git(user_email, user_name, github_token)
        
        # Start OpenCode server
        await self._start_opencode()
        
        return self.sandbox
    
    async def _setup_fresh(self, github_token: str, user_email: str, user_name: str):
        """
        First-time setup for a fresh sandbox.
        """
        repo_url = f"https://x-access-token:{github_token}@github.com/{self.repo_owner}/{self.repo_name}.git"
        
        await self.sandbox.exec(
            "git", "clone", repo_url, self.repo_path
        )
        
        # Install dependencies
        await self.sandbox.exec(
            "bash", "-c",
            f"cd {self.repo_path} && npm ci || pip install -r requirements.txt || true"
        )
    
    async def _sync_repo(self, github_token: str):
        """
        Sync repository with latest changes (max 30 min behind due to image refresh).
        """
        await self.sandbox.exec(
            "bash", "-c",
            f"cd {self.repo_path} && git fetch origin && git reset --hard origin/$(git rev-parse --abbrev-ref HEAD)"
        )
    
    async def _configure_git(self, user_email: str, user_name: str, github_token: str):
        """
        Configure git identity and credentials.
        
        From Docker implementation:
        - Use credential helper for HTTPS
        - Set user.name and user.email for commits
        - Add "(Harvest)" suffix to name for attribution
        """
        await self.sandbox.exec(
            "git", "config", "--global", "credential.helper", "store"
        )
        await self.sandbox.exec(
            "bash", "-c",
            f"echo 'https://x-access-token:{github_token}@github.com' > ~/.git-credentials"
        )
        await self.sandbox.exec(
            "git", "config", "--global", "user.email", user_email
        )
        await self.sandbox.exec(
            "git", "config", "--global", "user.name", f"{user_name} (Harvest)"
        )
    
    async def _start_opencode(self):
        """
        Start OpenCode in server mode.
        
        OpenCode server exposes an API that our orchestrator communicates with.
        """
        # Create OpenCode config directory
        await self.sandbox.exec("mkdir", "-p", "/root/.config/opencode")
        
        # Write OpenCode config (equivalent to Claude's .claude.json)
        # TODO: Research OpenCode config format
        
        # Start OpenCode server in background
        await self.sandbox.exec(
            "bash", "-c",
            f"cd {self.repo_path} && opencode serve --port 8080 &"
        )
    
    async def send_prompt(self, prompt: str) -> str:
        """
        Send a prompt to the OpenCode server running in the sandbox.
        """
        # TODO: Implement OpenCode SDK communication
        pass
    
    async def snapshot(self) -> str:
        """
        Take a snapshot for later restoration.
        """
        snapshot_id = f"{self.session_id}-{int(time.time())}"
        await self.sandbox.snapshot(snapshot_id)
        return snapshot_id
    
    async def terminate(self):
        """
        Gracefully terminate the sandbox.
        """
        if self.sandbox:
            await self.sandbox.terminate()
```

**Deliverables**:
- [ ] Sandbox creation from snapshot
- [ ] Fresh sandbox setup fallback
- [ ] Repository sync (git fetch/reset)
- [ ] Git identity configuration with "(Harvest)" suffix
- [ ] OpenCode server startup
- [ ] Snapshot save/restore
- [ ] Graceful termination

---

### Block 1.1.4: OpenCode Configuration

**Goal**: Configure OpenCode for autonomous operation (equivalent to Docker's claude.json setup)

**File**: `harvest/modal/opencode_config.py`

```python
"""
OpenCode configuration for Harvest sandboxes.

Equivalent to the Docker implementation's:
- ~/.claude.json (onboarding, trust)
- ~/.claude/.credentials.json (auth)
- ~/.claude/settings.json (permissions, hooks)
- /workspace/.mcp.json (MCP servers)
- /workspace/.claude/claude.md (instructions)
"""

import json


def generate_opencode_config(repo_path: str) -> dict:
    """
    Generate OpenCode configuration files.
    
    Returns dict of {filepath: content} to write.
    """
    configs = {}
    
    # Main OpenCode config
    # TODO: Research actual OpenCode config format
    configs["/root/.config/opencode/config.json"] = json.dumps({
        "server": {
            "port": 8080,
            "host": "0.0.0.0",
        },
        "permissions": {
            "allow": ["*"],  # Bypass permissions for autonomous operation
        },
        "trustedDirectories": ["/workspace"],
    }, indent=2)
    
    # MCP servers configuration
    configs[f"{repo_path}/.mcp.json"] = json.dumps({
        "mcpServers": {
            "memory": {
                "type": "stdio",
                "command": "mcp-server-memory",
                "env": {
                    "MEMORY_FILE_PATH": "/root/.mcp-memory/memory.jsonl"
                }
            },
            "filesystem": {
                "type": "stdio",
                "command": "mcp-server-filesystem",
                "args": ["/workspace"]
            },
            # GitHub MCP will use the injected token
            "github": {
                "type": "http",
                "url": "https://api.githubcopilot.com/mcp",
                "headers": {
                    "Authorization": "Bearer ${GITHUB_TOKEN}"
                }
            }
        }
    }, indent=2)
    
    # Harvest instructions (equivalent to autopilot-instructions.md)
    configs[f"{repo_path}/.opencode/instructions.md"] = """# Harvest Mode

You are running as an autonomous agent in a Modal sandbox.

## Autonomous Operation

- **Execute, don't ask**: Make decisions and act. Only pause for genuinely ambiguous requirements.
- **Fail forward**: If something breaks, diagnose and fix it. Don't stop to report errors you can resolve.
- **Complete the loop**: Finish tasks end-to-end including commits, pushes, and updating tracking systems.

## Environment

- Isolated in Modal sandbox - cannot affect other systems
- File changes only persist if committed and pushed
- Working directory: /workspace/{repo-name}
- Multiple repos may exist in /workspace

## Tools Available

- **run_tests**: Execute test suite and return results
- **slack_update**: Post status updates to Slack thread
- **git**: Full git operations (commit, push, branch)
- **gh**: GitHub CLI for PR creation
"""
    
    return configs


def generate_mcp_config(repo_path: str, github_token: str) -> str:
    """
    Generate MCP configuration with token substitution.
    """
    config = {
        "mcpServers": {
            "memory": {
                "type": "stdio",
                "command": "mcp-server-memory",
                "env": {
                    "MEMORY_FILE_PATH": "/root/.mcp-memory/memory.jsonl"
                }
            },
            "filesystem": {
                "type": "stdio",
                "command": "mcp-server-filesystem",
                "args": ["/workspace"]
            },
            "github": {
                "type": "http",
                "url": "https://api.githubcopilot.com/mcp",
                "headers": {
                    "Authorization": f"Bearer {github_token}"
                }
            }
        }
    }
    return json.dumps(config, indent=2)
```

**Deliverables**:
- [ ] OpenCode config generation
- [ ] MCP servers configuration
- [ ] Harvest instructions file
- [ ] Token substitution in configs
- [ ] Research OpenCode actual config format

---

### Block 1.1.5: Session Lifecycle Management

**Goal**: Manage the full lifecycle of a sandbox session

**File**: `harvest/modal/session.py`

```python
import modal
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
import uuid

from harvest.modal.sandbox import HarvestSandbox


@dataclass
class SessionState:
    session_id: str
    repo_owner: str
    repo_name: str
    branch: str
    status: str  # "starting", "running", "paused", "terminated"
    created_at: datetime
    last_activity: datetime
    snapshot_id: Optional[str] = None
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None


class SessionManager:
    """
    Manages Harvest session lifecycle.
    
    Responsibilities:
    - Create new sessions
    - Restore paused sessions from snapshot
    - Track session state
    - Handle follow-up prompts (queue vs. interrupt)
    """
    
    def __init__(self):
        # In production, this would be backed by Durable Objects
        self.sessions: dict[str, SessionState] = {}
        self.sandboxes: dict[str, HarvestSandbox] = {}
    
    async def create_session(
        self,
        repo_owner: str,
        repo_name: str,
        branch: str,
        github_token: str,
        user_email: str,
        user_name: str,
    ) -> SessionState:
        """
        Create a new Harvest session.
        """
        session_id = str(uuid.uuid4())
        
        # Create sandbox
        sandbox = HarvestSandbox(session_id, repo_owner, repo_name)
        await sandbox.start(github_token, user_email, user_name)
        
        # Track state
        state = SessionState(
            session_id=session_id,
            repo_owner=repo_owner,
            repo_name=repo_name,
            branch=branch,
            status="running",
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
        )
        
        self.sessions[session_id] = state
        self.sandboxes[session_id] = sandbox
        
        return state
    
    async def restore_session(self, session_id: str) -> SessionState:
        """
        Restore a paused session from snapshot.
        """
        state = self.sessions.get(session_id)
        if not state:
            raise ValueError(f"Session {session_id} not found")
        
        if not state.snapshot_id:
            raise ValueError(f"Session {session_id} has no snapshot")
        
        # Restore sandbox from snapshot
        sandbox = HarvestSandbox(session_id, state.repo_owner, state.repo_name)
        # TODO: Pass snapshot_id to sandbox.start()
        
        state.status = "running"
        state.last_activity = datetime.utcnow()
        self.sandboxes[session_id] = sandbox
        
        return state
    
    async def pause_session(self, session_id: str) -> str:
        """
        Pause a session and take a snapshot.
        """
        sandbox = self.sandboxes.get(session_id)
        if not sandbox:
            raise ValueError(f"Session {session_id} not running")
        
        # Take snapshot
        snapshot_id = await sandbox.snapshot()
        
        # Update state
        state = self.sessions[session_id]
        state.status = "paused"
        state.snapshot_id = snapshot_id
        
        # Terminate sandbox
        await sandbox.terminate()
        del self.sandboxes[session_id]
        
        return snapshot_id
    
    async def terminate_session(self, session_id: str):
        """
        Terminate a session without snapshot.
        """
        sandbox = self.sandboxes.get(session_id)
        if sandbox:
            await sandbox.terminate()
            del self.sandboxes[session_id]
        
        state = self.sessions.get(session_id)
        if state:
            state.status = "terminated"
    
    async def send_prompt(self, session_id: str, prompt: str) -> str:
        """
        Send a prompt to a running session.
        
        Design decision: Queue prompts during execution.
        From Ramp article: "We chose to queue them, as we found it not only
        easier to manage, but also helpful for sending over thoughts on
        next steps while the AI is still working."
        """
        sandbox = self.sandboxes.get(session_id)
        if not sandbox:
            raise ValueError(f"Session {session_id} not running")
        
        # Update activity timestamp
        state = self.sessions[session_id]
        state.last_activity = datetime.utcnow()
        
        # Send to sandbox
        return await sandbox.send_prompt(prompt)
```

**Deliverables**:
- [ ] Session creation
- [ ] Session restoration from snapshot
- [ ] Session pause with snapshot
- [ ] Session termination
- [ ] Prompt queuing during execution
- [ ] Activity tracking

---

## File Structure

```
harvest/
├── modal/
│   ├── __init__.py
│   ├── images/
│   │   ├── __init__.py
│   │   ├── base.py              # Base image definition
│   │   └── repo_builder.py      # Per-repo image builder + cron
│   ├── sandbox.py               # Sandbox manager
│   ├── session.py               # Session lifecycle
│   └── opencode_config.py       # OpenCode configuration
├── config/
│   └── harvest_instructions.md  # Agent instructions
└── tests/
    └── modal/
        ├── test_sandbox.py
        └── test_session.py
```

---

## Key Design Decisions

### 1. `/workspace` as Root (Multi-Repo Support)

**Why**: Unlike the Docker implementation which clones a single repo to `/workspace`, Harvest needs to support multiple repositories. A session might need to:
- Work on `repo-a` primarily
- Reference `repo-b` for shared code
- Spawn child sessions for different repos

**Implementation**:
```
/workspace/
├── relevance-chat-app/    # Primary repo for this session
├── shared-components/     # Referenced repo
└── ...
```

### 2. Snapshot-Based Fast Startup

**Why**: Session start time is critical for user experience. From Ramp article: "Because Inspect sessions are fast to start and effectively free to run, you can use them without rationing."

**Implementation**:
- Image builder runs every 30 minutes
- Fresh sessions start from snapshot (< 5 seconds)
- Git sync fetches only last 30 minutes of changes
- OpenCode can start reading files while sync completes

### 3. Git Identity with "(Harvest)" Suffix

**Why**: Clear attribution in git history. From Docker implementation: "Commits show as 'Dave C (Autopilot) <email>'".

**Implementation**:
```bash
git config user.name "Dave C (Harvest)"
git config user.email "dave@example.com"
```

### 4. OpenCode Server Mode

**Why**: OpenCode is designed as a server-first architecture with typed SDK. From Ramp article: "It is structured as a server first, with its TUI and desktop app just being clients on top."

**Implementation**:
- OpenCode runs as HTTP server on port 8080
- Harvest API communicates via OpenCode SDK
- Enables custom tools, plugins, and hooks

---

## Testing Plan

### Unit Tests

```python
# test_sandbox.py

async def test_sandbox_creation():
    """Verify sandbox starts with correct environment."""
    sandbox = HarvestSandbox("test-123", "owner", "repo")
    await sandbox.start(token, email, name)
    
    # Verify workspace structure
    result = await sandbox.exec("ls", "/workspace")
    assert "repo" in result
    
    # Verify git config
    result = await sandbox.exec("git", "config", "user.name")
    assert "(Harvest)" in result


async def test_snapshot_restore():
    """Verify snapshot creates and restores correctly."""
    sandbox = HarvestSandbox("test-123", "owner", "repo")
    await sandbox.start(token, email, name)
    
    # Make a change
    await sandbox.exec("touch", "/workspace/repo/test-file.txt")
    
    # Snapshot
    snapshot_id = await sandbox.snapshot()
    await sandbox.terminate()
    
    # Restore
    sandbox2 = HarvestSandbox("test-456", "owner", "repo")
    await sandbox2.start_from_snapshot(snapshot_id)
    
    # Verify file exists
    result = await sandbox2.exec("ls", "/workspace/repo/test-file.txt")
    assert "test-file.txt" in result
```

### Integration Tests

```python
# test_session.py

async def test_full_session_lifecycle():
    """Test create -> prompt -> pause -> restore -> terminate."""
    manager = SessionManager()
    
    # Create
    state = await manager.create_session(
        "owner", "repo", "main",
        github_token, email, name
    )
    assert state.status == "running"
    
    # Send prompt
    result = await manager.send_prompt(state.session_id, "List files")
    assert result is not None
    
    # Pause
    snapshot_id = await manager.pause_session(state.session_id)
    assert snapshot_id is not None
    
    # Restore
    state = await manager.restore_session(state.session_id)
    assert state.status == "running"
    
    # Terminate
    await manager.terminate_session(state.session_id)
    assert state.status == "terminated"
```

---

## Open Questions (To Research)

1. **OpenCode Config Format**: What's the actual config file structure for OpenCode? Need to research docs and source.

2. **OpenCode Server API**: What endpoints does OpenCode server expose? How do we send prompts programmatically?

3. **Modal Snapshot Size Limits**: Are there size limits on snapshots? How long do they persist?

4. **Modal Sandbox Networking**: Can sandboxes communicate with external services (GitHub API, Slack API)?

5. **OpenCode Permissions**: How do we bypass permission prompts in OpenCode (equivalent to `--dangerously-skip-permissions`)?

---

## Next Steps

After completing Phase 1.1:

1. **Phase 1.2: GitHub App Integration** - Secure token generation, webhook handling
2. **Phase 1.3: OpenCode Server Integration** - Deep dive into OpenCode SDK, custom tools
3. **Phase 2.1: Cloudflare Workers** - API layer connecting to Modal sandboxes
