# Phase 1.1: Modal Sandbox Infrastructure

> Detailed implementation plan for the core execution environment

## Overview

This phase creates the Modal sandbox infrastructure that powers Harvest sessions. Each session runs in an isolated Modal sandbox with a full development environment, OpenCode agent, and GitHub integration.

**Key Difference from Docker Implementation**: The existing `relevance-chat-app/docker` setup uses Docker Compose with a single hardcoded repository. Harvest uses Modal sandboxes that:
1. Work with **any repository** (multi-repo support)
2. Use `/workspace` as root, with repos cloned to `/workspace/{repo-name}`
3. Support **concurrent sessions** across different repos
4. Use **snapshots** for fast startup (30-minute image refresh cycle)
5. Use **per-repo memory volumes** for persistent learning

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Modal Infrastructure                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐       ┌──────────────────┐                            │
│  │  Image Builder   │──────►│  Image Registry  │                            │
│  │  (Cron: 30min)   │       │  (Per-repo)      │                            │
│  └──────────────────┘       └──────────────────┘                            │
│                                     │                                        │
│                                     ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         Sandbox Instance                                │ │
│  │                                                                         │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │ │
│  │  │  /app           │  │  /workspace     │  │  /root          │         │ │
│  │  │  ├── AGENTS.md  │  │  ├── repo-a/    │  │  ├── .config/   │         │ │
│  │  │  ├── docs/ai/   │  │  ├── repo-b/    │  │  │   └── opencode/│        │ │
│  │  │  ├── memory-    │  │  └── ...        │  │  └── .mcp-memory/│        │ │
│  │  │  │   seed.json  │  │                 │  │      (volume)    │         │ │
│  │  │  └── opencode.  │  │                 │  │                  │         │ │
│  │  │      json       │  │                 │  │                  │         │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘         │ │
│  │                                                                         │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │ │
│  │  │  OpenCode       │  │  MCP Servers    │  │  Playwright     │         │ │
│  │  │  Server :8080   │  │  (memory, fs,   │  │  + Chromium     │         │ │
│  │  │                 │  │   playwright,   │  │                 │         │ │
│  │  │                 │  │   devtools...)  │  │                 │         │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌──────────────────┐                                                        │
│  │  Memory Volume   │  harvest-memory-{owner}-{repo}                        │
│  │  (Per-repo)      │  Persists across sessions                             │
│  └──────────────────┘                                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## File Resolution Strategy

**Problem**: Harvest docs and instructions are baked into the Modal image, but OpenCode runs in `/workspace/{repo-name}`. References like `@docs/ai/git.md` would fail because they're relative to the repo.

**Solution**: Use absolute paths to `/app/` for all Harvest-specific files.

### File Locations

| Location | Purpose | Persistence |
|----------|---------|-------------|
| `/app/` | Harvest instructions, docs, configs (baked into image) | Image rebuild |
| `/app/AGENTS.md` | Main agent instructions | Image rebuild |
| `/app/docs/ai/` | AI rules (git.md, memory.md, harvest-mode.md) | Image rebuild |
| `/app/memory-seed.json` | Initial memory entities | Image rebuild |
| `/app/opencode.json` | Global OpenCode config | Image rebuild |
| `/root/.config/opencode/` | OpenCode config (symlinked to /app/) | Image rebuild |
| `/root/.local/share/opencode/auth.json` | OAuth tokens (injected at startup) | Session |
| `/root/.mcp-memory/` | Memory storage (Modal Volume) | **Per-repo persistent** |
| `/workspace/{repo-name}/` | Cloned repository | Session (must push to persist) |

### OpenCode Config Resolution

```
/root/.config/opencode/opencode.json  →  symlink to /app/opencode.json
```

**`/app/opencode.json`**:
```json
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": [
    "/app/AGENTS.md",
    "/app/docs/ai/git.md",
    "/app/docs/ai/memory.md",
    "/app/docs/ai/harvest-mode.md"
  ],
  "permission": "allow",
  "mcp": {
    "memory": {
      "command": "mcp-server-memory",
      "env": {
        "MEMORY_FILE_PATH": "/root/.mcp-memory/memory.jsonl"
      }
    },
    "filesystem": {
      "command": "mcp-server-filesystem",
      "args": ["/workspace"]
    }
  }
}
```

---

## What We Learned from Docker Implementation

### Patterns to Replicate

| Pattern | Docker Implementation | Modal Implementation |
|---------|----------------------|---------------------|
| **Git credentials** | GitHub PAT in `/run/secrets/`, credential helper | GitHub PAT via Modal secrets, injected at runtime |
| **Agent config** | `.claude.json` with `hasCompletedOnboarding`, bypass permissions | OpenCode config with `"permission": "allow"` |
| **MCP servers** | Globally installed npm packages, `.mcp.json` template | Same - pre-install in image, config in `/app/opencode.json` |
| **Memory persistence** | Docker volume at `/home/autopilot/.mcp-memory/` | Modal volume per-repo at `/root/.mcp-memory/` |
| **Memory seeding** | `memory-seed.json` loaded on first start | Same pattern, adapted for Harvest context |
| **Optional MCP pattern** | Check env var exists before adding server | Same - conditional config based on secrets |

### Patterns Changed

| Pattern | Docker Implementation | Modal Implementation |
|---------|----------------------|---------------------|
| **Single repo** | Hardcoded clone of `relevance-chat-app` | Multi-repo: clone to `/workspace/{repo-name}` |
| **Workspace root** | `/workspace` IS the repo | `/workspace` contains multiple repos |
| **Image updates** | Manual `docker compose build` | Automated cron every 30 minutes |
| **Session storage** | Docker volumes | Modal snapshots |
| **Agent** | Claude Code CLI | OpenCode server |
| **Shell locale** | `locale-gen en_US.UTF-8` for ttyd | **Not needed** - no shell access |
| **Loki MCP** | Log queries via simple-loki-mcp | **Removed** - use Modal's built-in logging |

---

## Implementation Blocks

### Block 1.1.1: Base Modal Image

**Goal**: Create a base image with all system dependencies, OpenCode, and MCP servers.

**File**: `harvest/modal/images/base.py`

```python
import modal

# Base image with system dependencies
base_image = (
    modal.Image.debian_slim(python_version="3.12")
    # System packages
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
        "build-essential",  # For native npm packages
        # Playwright dependencies
        "libnss3",
        "libnspr4",
        "libatk1.0-0",
        "libatk-bridge2.0-0",
        "libcups2",
        "libdrm2",
        "libdbus-1-3",
        "libxkbcommon0",
        "libatspi2.0-0",
        "libxcomposite1",
        "libxdamage1",
        "libxfixes3",
        "libxrandr2",
        "libgbm1",
        "libasound2",
    ])
    # Alias fd (Debian naming quirk)
    .run_commands([
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
    # Pre-install MCP servers (required)
    .run_commands([
        "npm install -g @modelcontextprotocol/server-memory",
        "npm install -g @modelcontextprotocol/server-filesystem",
        "npm install -g @anthropic-ai/mcp-server-playwright@latest",
        "npm install -g chrome-devtools-mcp@latest",
    ])
    # Pre-install MCP servers (optional - loaded based on secrets)
    .run_commands([
        "npm install -g @houtini/gemini-mcp",
        "npm install -g @sentry/mcp-server",
        # Note: linear and posthog use mcp-remote pattern
    ])
    # Install Playwright browsers
    .run_commands([
        "npx playwright install chromium",
    ])
    # Create directory structure
    .run_commands([
        "mkdir -p /workspace",
        "mkdir -p /app/docs/ai",
        "mkdir -p /root/.config/opencode",
        "mkdir -p /root/.local/share/opencode",
        "mkdir -p /root/.mcp-memory",
    ])
    # Copy Harvest files into image (done via .copy_local_file or .add_local_file)
    # See Block 1.1.4 for file contents
)
```

**Deliverables**:
- [ ] Base image definition with all system deps
- [ ] Node.js 20 LTS installed
- [ ] GitHub CLI installed
- [ ] OpenCode installed globally
- [ ] All MCP servers pre-installed (required + optional)
- [ ] Playwright + Chromium installed
- [ ] Directory structure created

---

### Block 1.1.2: Repository Image Builder

**Goal**: Build per-repository images with dependencies pre-installed.

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
        # Prefer npm ci for reproducible installs
        if os.path.exists("package-lock.json"):
            subprocess.run(["npm", "ci"], check=True)
        else:
            subprocess.run(["npm", "install"], check=True)
        build_info["package_manager"] = "npm"
        
        # Run build if script exists
        with open("package.json") as f:
            pkg = json.load(f)
            if "build" in pkg.get("scripts", {}):
                subprocess.run(["npm", "run", "build"], check=False)
                
    elif os.path.exists("requirements.txt"):
        subprocess.run([
            "pip", "install", "-r", "requirements.txt",
            "--break-system-packages"  # Required in container (PEP 668)
        ], check=True)
        build_info["package_manager"] = "pip"
        
    elif os.path.exists("pyproject.toml"):
        subprocess.run([
            "pip", "install", "-e", ".",
            "--break-system-packages"
        ], check=True)
        build_info["package_manager"] = "pip"
    
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
- [ ] Dependency detection (npm ci preferred, pip with --break-system-packages)
- [ ] 30-minute cron job for image refresh
- [ ] Image registry volume for metadata

---

### Block 1.1.3: Sandbox Manager

**Goal**: Create and manage sandbox instances with proper git configuration.

**File**: `harvest/modal/sandbox.py`

```python
import modal
from harvest.modal.images.base import base_image

app = modal.App("harvest-sandbox")


class HarvestSandbox:
    """
    Manages a Modal sandbox for a Harvest session.
    
    Key design decisions:
    - /workspace is the root, repos cloned to /workspace/{repo-name}
    - OpenCode runs in server mode on port 8080
    - Memory persists via per-repo Modal volume
    - Git uses Safe-Carry-Forward pattern (no pull/stash)
    """
    
    def __init__(self, session_id: str, repo_owner: str, repo_name: str):
        self.session_id = session_id
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.repo_path = f"/workspace/{repo_name}"
        self.sandbox = None
        
        # Per-repo memory volume
        self.memory_volume = modal.Volume.from_name(
            f"harvest-memory-{repo_owner}-{repo_name}",
            create_if_missing=True
        )
    
    async def start(
        self,
        github_token: str,
        opencode_auth: dict,  # OAuth credentials for OpenCode
        user_email: str,
        user_name: str,
        optional_secrets: dict = None,  # LINEAR_API_KEY, etc.
    ):
        """
        Start a new sandbox with full configuration.
        """
        # Build secrets dict
        secrets = {
            "GITHUB_TOKEN": github_token,
            "GIT_USER_EMAIL": user_email,
            "GIT_USER_NAME": user_name,
        }
        
        # Add optional secrets if provided
        if optional_secrets:
            secrets.update(optional_secrets)
        
        self.sandbox = await modal.Sandbox.create(
            image=base_image,
            timeout=3600,  # 1 hour max
            secrets=[modal.Secret.from_dict(secrets)],
            volumes={
                "/root/.mcp-memory": self.memory_volume,
            },
        )
        
        # Setup sequence
        await self._clone_repo(github_token)
        await self._configure_git(user_email, user_name, github_token)
        await self._inject_opencode_auth(opencode_auth)
        await self._setup_mcp_config(optional_secrets or {})
        await self._seed_memory_if_needed()
        await self._start_opencode()
        
        return self.sandbox
    
    async def _clone_repo(self, github_token: str):
        """Clone the repository to /workspace/{repo-name}."""
        repo_url = f"https://x-access-token:{github_token}@github.com/{self.repo_owner}/{self.repo_name}.git"
        
        await self.sandbox.exec(
            "git", "clone", repo_url, self.repo_path
        )
    
    async def _configure_git(self, user_email: str, user_name: str, github_token: str):
        """
        Configure git identity and credentials.
        
        Uses credential helper for HTTPS, adds "(Harvest)" suffix for attribution.
        """
        # Credential helper
        await self.sandbox.exec(
            "git", "config", "--global", "credential.helper", "store"
        )
        await self.sandbox.exec(
            "bash", "-c",
            f"echo 'https://x-access-token:{github_token}@github.com' > ~/.git-credentials"
        )
        
        # Identity with (Harvest) suffix
        await self.sandbox.exec(
            "git", "config", "--global", "user.email", user_email
        )
        await self.sandbox.exec(
            "git", "config", "--global", "user.name", f"{user_name} (Harvest)"
        )
        
        # Safe defaults
        await self.sandbox.exec(
            "git", "config", "--global", "push.autoSetupRemote", "true"
        )
    
    async def _inject_opencode_auth(self, opencode_auth: dict):
        """
        Inject OpenCode OAuth credentials.
        
        OpenCode stores auth in ~/.local/share/opencode/auth.json
        """
        import json
        auth_json = json.dumps(opencode_auth)
        
        await self.sandbox.exec(
            "bash", "-c",
            f"echo '{auth_json}' > /root/.local/share/opencode/auth.json"
        )
    
    async def _setup_mcp_config(self, optional_secrets: dict):
        """
        Setup MCP configuration with optional servers based on available secrets.
        """
        # Base MCP config is in /app/opencode.json (baked into image)
        # Here we could extend it with optional servers if secrets are present
        
        # For now, optional servers are configured but will gracefully fail
        # if their API keys aren't present
        pass
    
    async def _seed_memory_if_needed(self):
        """
        Seed memory with initial entities if this is first use for this repo.
        """
        # Check if memory file exists
        result = await self.sandbox.exec(
            "bash", "-c",
            "test -f /root/.mcp-memory/memory.jsonl && echo 'exists' || echo 'empty'"
        )
        
        if "empty" in result.stdout:
            # First time - seed from /app/memory-seed.json
            await self.sandbox.exec(
                "bash", "-c",
                # Use memory MCP to create initial entities
                # This will be done via OpenCode on first prompt
                "echo 'Memory will be seeded on first prompt'"
            )
    
    async def _start_opencode(self):
        """
        Start OpenCode in server mode.
        """
        # Create symlink for config
        await self.sandbox.exec(
            "ln", "-sf", "/app/opencode.json", "/root/.config/opencode/opencode.json"
        )
        
        # Start OpenCode server in background
        await self.sandbox.exec(
            "bash", "-c",
            f"cd {self.repo_path} && nohup opencode serve --port 8080 > /tmp/opencode.log 2>&1 &"
        )
        
        # Wait for server to be ready
        await self.sandbox.exec(
            "bash", "-c",
            "for i in $(seq 1 30); do curl -s http://localhost:8080/health && break || sleep 1; done"
        )
    
    async def send_prompt(self, prompt: str) -> str:
        """
        Send a prompt to the OpenCode server.
        """
        import json
        
        result = await self.sandbox.exec(
            "curl", "-X", "POST",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"prompt": prompt}),
            "http://localhost:8080/api/prompt"
        )
        
        return result.stdout
    
    async def terminate(self):
        """Gracefully terminate the sandbox."""
        if self.sandbox:
            await self.sandbox.terminate()
```

**Deliverables**:
- [ ] Sandbox creation with volumes
- [ ] Repository cloning
- [ ] Git identity configuration with "(Harvest)" suffix
- [ ] OpenCode auth injection
- [ ] MCP config setup (required + optional)
- [ ] Memory seeding on first use
- [ ] OpenCode server startup
- [ ] Prompt sending via server API
- [ ] Graceful termination

---

### Block 1.1.4: OpenCode Configuration & Files

**Goal**: Define all files to be baked into the Modal image at `/app/`.

#### `/app/opencode.json`
```json
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": [
    "/app/AGENTS.md",
    "/app/docs/ai/git.md",
    "/app/docs/ai/memory.md",
    "/app/docs/ai/harvest-mode.md"
  ],
  "permission": "allow",
  "mcp": {
    "memory": {
      "command": "mcp-server-memory",
      "env": {
        "MEMORY_FILE_PATH": "/root/.mcp-memory/memory.jsonl"
      }
    },
    "filesystem": {
      "command": "mcp-server-filesystem",
      "args": ["/workspace"]
    },
    "playwright": {
      "command": "mcp-server-playwright"
    },
    "devtools": {
      "command": "chrome-devtools-mcp"
    },
    "gemini": {
      "command": "gemini-mcp",
      "env": {
        "GEMINI_API_KEY": "${GEMINI_API_KEY}"
      }
    }
  }
}
```

#### `/app/AGENTS.md`
```markdown
# Harvest Agent

You are running as an autonomous coding agent in a Modal sandbox.

## Core Principles

1. **Execute, don't ask**: Make decisions and act. Only pause for genuinely ambiguous requirements.
2. **Fail forward**: If something breaks, diagnose and fix it. Don't stop to report errors you can resolve.
3. **Complete the loop**: Finish tasks end-to-end including commits, pushes, and PRs.
4. **Use your memory**: Query memory before tasks, update after fixing errors.
5. **Communicate progress**: Use slack_update tool at meaningful milestones.

## Environment

- **Sandbox**: Isolated Modal container - safe for any operation
- **Persistence**: Only committed AND pushed changes survive session end
- **Working directory**: `/workspace/{repo-name}`
- **Multi-repo**: Can work with multiple repos in `/workspace/`
- **Memory**: Persists per-repo across sessions at `/root/.mcp-memory/`

## Available Tools

| Tool | Purpose |
|------|---------|
| **memory** | Persistent knowledge graph - query before tasks, update after errors |
| **filesystem** | Read/write files in /workspace |
| **playwright** | Browser automation for testing |
| **devtools** | Browser debugging when Playwright fails |
| **gemini** | Plan review and web research (if configured) |
| **git/gh** | Full git operations and GitHub CLI |

## Critical Rules

1. **Git**: Follow /app/docs/ai/git.md strictly. NEVER use `git pull` or `git stash`.
2. **Memory**: Follow /app/docs/ai/memory.md. Always update ErrorPatterns after fixing issues.
3. **Push before done**: Unpushed changes are lost when session ends.

## Detailed Documentation

- Git workflow: `/app/docs/ai/git.md`
- Memory usage: `/app/docs/ai/memory.md`
- Autonomous operation: `/app/docs/ai/harvest-mode.md`
```

**Deliverables**:
- [ ] `/app/opencode.json` - OpenCode configuration
- [ ] `/app/AGENTS.md` - Main agent instructions
- [ ] `/app/docs/ai/git.md` - Git workflow rules (copy from repo)
- [ ] `/app/docs/ai/memory.md` - Memory usage rules
- [ ] `/app/docs/ai/harvest-mode.md` - Autonomous operation rules
- [ ] `/app/memory-seed.json` - Initial memory entities
- [ ] Symlink setup: `/root/.config/opencode/opencode.json` → `/app/opencode.json`

---

### Block 1.1.5: MCP Server Configuration

**Goal**: Configure all MCP servers with required/optional pattern.

#### Required MCP Servers (always available)

| Server | Package | Purpose |
|--------|---------|---------|
| `memory` | `@modelcontextprotocol/server-memory` | Persistent knowledge graph |
| `filesystem` | `@modelcontextprotocol/server-filesystem` | File operations in /workspace |
| `playwright` | `@anthropic-ai/mcp-server-playwright` | Browser automation |
| `devtools` | `chrome-devtools-mcp` | Browser debugging |

#### Optional MCP Servers (loaded if secrets present)

| Server | Package | Required Secret | Purpose |
|--------|---------|-----------------|---------|
| `gemini` | `@houtini/gemini-mcp` | `GEMINI_API_KEY` | Plan review, web research |
| `linear` | via mcp-remote | `LINEAR_API_KEY` | Issue tracking |
| `posthog` | via mcp-remote | `POSTHOG_API_KEY` | Analytics, feature flags |
| `sentry` | `@sentry/mcp-server` | `SENTRY_AUTH_TOKEN` | Error tracking |

#### Configuration Pattern

Optional servers are configured in `opencode.json` but will gracefully fail if their environment variables aren't set. The setup script collects optional secrets and includes them in the Modal secret.

**Deliverables**:
- [ ] All MCP server packages pre-installed in image
- [ ] Required servers configured in opencode.json
- [ ] Optional servers configured with env var references
- [ ] Documentation of which secrets enable which servers

---

### Block 1.1.6: Memory Seeding & Persistence

**Goal**: Implement per-repo memory persistence with initial seeding.

#### Memory Volume Strategy

- Volume name: `harvest-memory-{repo_owner}-{repo_name}`
- Mount point: `/root/.mcp-memory/`
- Contains: `memory.jsonl` (MCP memory format)

#### Memory Seed JSON

```json
{
  "entities": [
    {
      "name": "HarvestSession",
      "entityType": "session_context",
      "observations": [
        "Running as autonomous agent in Modal sandbox",
        "Execute tasks end-to-end without asking for confirmation",
        "File changes only persist if committed and pushed to GitHub",
        "Working directory is /workspace with repos at /workspace/{repo-name}",
        "Can work with multiple repositories in same workspace",
        "Session may be paused/resumed via snapshots - memory persists per-repo",
        "Use slack_update tool to communicate progress to user"
      ]
    },
    {
      "name": "EnvironmentConfig",
      "entityType": "environment_knowledge",
      "observations": [
        "Running in Modal sandbox (isolated container)",
        "Node.js 20 LTS available globally",
        "GitHub CLI (gh) available for PR operations",
        "Playwright + Chromium available for browser automation",
        "Git configured with user identity including '(Harvest)' suffix",
        "MCP servers: memory (persistent per-repo), filesystem, playwright, devtools, gemini",
        "Optional MCP servers loaded based on available secrets: linear, posthog, sentry",
        "Instructions and workflow docs at /app/docs/ai/"
      ]
    },
    {
      "name": "GitWorkflow",
      "entityType": "process_knowledge",
      "observations": [
        "NEVER use git pull or git stash - use snapshot commits for safe sync (see /app/docs/ai/git.md)",
        "Safe-Carry-Forward pattern: snapshot uncommitted work, fetch, reset, cherry-pick",
        "Use --force-with-lease instead of --force for push operations",
        "Create checkpoint branches before risky operations (rebase, conflict resolution)",
        "Verify branch ownership before any force push (max 2 contributors including agent)",
        "Commits attributed with '(Harvest)' suffix in author name",
        "Always push changes before session ends - unpushed work is lost",
        "Clean-up mandate: squash WIP snapshots with git reset --soft before final push"
      ]
    },
    {
      "name": "WorkflowProcedures",
      "entityType": "process_knowledge",
      "observations": [
        "Run tests after making changes to verify correctness",
        "Create focused PRs - one logical change per PR",
        "Write clear PR descriptions explaining the 'why'",
        "Use conventional commit messages: type(scope): message [ID]",
        "Check existing AGENTS.md or project docs for repo-specific conventions",
        "Update slack thread with progress at meaningful milestones",
        "Never use --no-verify for real commits, only for WIP snapshots"
      ]
    },
    {
      "name": "ErrorPatterns",
      "entityType": "incident_knowledge",
      "observations": [
        "Modal sandbox: Changes lost if not committed and pushed before session ends",
        "MCP memory: Use create_entities for new, add_observations for updates",
        "Playwright: Browser automation available in sandbox, may increase startup time",
        "Git fetch: If (forced update) appears, remote was rebased - reset to remote",
        "npm ci vs npm install: Always prefer npm ci for reproducible installs"
      ]
    },
    {
      "name": "LearnedPatterns",
      "entityType": "codebase_knowledge",
      "observations": []
    }
  ],
  "relations": [
    {"from": "HarvestSession", "to": "EnvironmentConfig", "relationType": "operates_within"},
    {"from": "HarvestSession", "to": "GitWorkflow", "relationType": "must_follow"},
    {"from": "HarvestSession", "to": "WorkflowProcedures", "relationType": "should_follow"},
    {"from": "ErrorPatterns", "to": "EnvironmentConfig", "relationType": "informs"},
    {"from": "LearnedPatterns", "to": "HarvestSession", "relationType": "informs"},
    {"from": "WorkflowProcedures", "to": "GitWorkflow", "relationType": "depends_on"}
  ]
}
```

#### Seeding Logic

On sandbox start:
1. Check if `/root/.mcp-memory/memory.jsonl` exists (volume-backed)
2. If empty, seed via memory MCP `create_entities` and `create_relations` calls
3. Flag is the file existence itself - no separate flag needed

#### Memory Maintenance Rules

Include in `/app/docs/ai/memory.md`:
- Add timestamps `[YYYY-MM-DD]` to observations that may become stale
- Mark outdated facts with `SUPERSEDED [date]: <old> - Now: <new>`
- Trust recent observations when conflicts exist
- Consolidate when memory exceeds ~100 observations per entity

**Deliverables**:
- [ ] Per-repo Modal volume creation
- [ ] Memory seed JSON file
- [ ] Seeding logic in sandbox startup
- [ ] Memory maintenance documentation

---

### Block 1.1.7: Session Lifecycle Management

**Goal**: Manage the full lifecycle of a sandbox session.

**File**: `harvest/modal/session.py`

```python
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
    - Track session state
    - Handle follow-up prompts (queue during execution)
    - Terminate sessions
    
    Note: In production, state is managed by Cloudflare Durable Objects (Phase 2).
    This is the Modal-side session management.
    """
    
    def __init__(self):
        self.sessions: dict[str, SessionState] = {}
        self.sandboxes: dict[str, HarvestSandbox] = {}
    
    async def create_session(
        self,
        repo_owner: str,
        repo_name: str,
        branch: str,
        github_token: str,
        opencode_auth: dict,
        user_email: str,
        user_name: str,
        optional_secrets: dict = None,
    ) -> SessionState:
        """Create a new Harvest session."""
        session_id = str(uuid.uuid4())
        
        # Create and start sandbox
        sandbox = HarvestSandbox(session_id, repo_owner, repo_name)
        await sandbox.start(
            github_token=github_token,
            opencode_auth=opencode_auth,
            user_email=user_email,
            user_name=user_name,
            optional_secrets=optional_secrets,
        )
        
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
    
    async def terminate_session(self, session_id: str):
        """Terminate a session."""
        sandbox = self.sandboxes.get(session_id)
        if sandbox:
            await sandbox.terminate()
            del self.sandboxes[session_id]
        
        state = self.sessions.get(session_id)
        if state:
            state.status = "terminated"
    
    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Get session state."""
        return self.sessions.get(session_id)
```

**Deliverables**:
- [ ] Session creation with full configuration
- [ ] Session state tracking
- [ ] Prompt sending with activity tracking
- [ ] Session termination
- [ ] Session state queries

---

### Block 1.1.8: Setup Script Adaptation

**Goal**: Adapt the chat-app setup script for Modal secrets.

**Source**: `relevance-chat-app/scripts/autopilot/setup.ts`

#### Changes Required

| Aspect | Docker (Current) | Modal (New) |
|--------|------------------|-------------|
| **Secret storage** | Docker secrets in `/run/secrets/` | Modal secrets via `modal secret create harvest-{uuid}` |
| **User ID** | N/A | Generate UUID, store in `~/.harvest/user-id` |
| **Secret naming** | Individual secret files | Single combined secret `harvest-{uuid}` |
| **GitHub auth** | PAT directly | PAT (keep for MVP) |
| **Anthropic auth** | Claude OAuth token | OpenCode OAuth token |
| **Verification** | `docker compose up` | `modal run` test |

#### Secrets to Collect

**Required:**
- `GITHUB_TOKEN` - GitHub Personal Access Token
- OpenCode OAuth - Via `/connect` flow (stored separately in auth.json format)

**Optional:**
- `LINEAR_API_KEY` - Linear issue tracking
- `POSTHOG_API_KEY` - Analytics and feature flags
- `SENTRY_AUTH_TOKEN` - Error tracking
- `GEMINI_API_KEY` - Plan review and web research

#### Script Flow

1. Check for existing `~/.harvest/user-id`, generate UUID if missing
2. Prompt for required secrets (GitHub PAT)
3. Guide user through OpenCode OAuth flow (`opencode auth login`)
4. Prompt for optional secrets
5. Create Modal secret: `modal secret create harvest-{uuid} GITHUB_TOKEN=xxx LINEAR_API_KEY=yyy ...`
6. Store OpenCode auth separately (it uses its own auth.json format)
7. Run verification: `modal run harvest.modal.sandbox::test_sandbox`

#### File Location

`scripts/setup.ts` - Adapted from chat-app, uses same patterns but targets Modal.

**Deliverables**:
- [ ] Adapted setup script for Modal
- [ ] UUID generation and storage
- [ ] Modal secret creation via CLI
- [ ] OpenCode auth flow integration
- [ ] Verification test

---

## Testing Approach

### Modal Testing Philosophy

Modal is **infrastructure-as-code** - the definition IS the test in many cases. Focus on:

1. **Image builds** - No unit tests; verify by running `modal run` and checking build succeeds
2. **Sandbox functionality** - Integration tests with real Modal sandboxes
3. **Session logic** - Can unit test business logic by mocking Modal SDK

### Integration Tests

```python
# tests/modal/test_sandbox_integration.py

import pytest
import modal

@pytest.mark.integration
async def test_sandbox_starts_successfully():
    """Verify sandbox starts and OpenCode is accessible."""
    sandbox = HarvestSandbox("test-123", "owner", "repo")
    await sandbox.start(
        github_token=os.environ["TEST_GITHUB_TOKEN"],
        opencode_auth={"anthropic": {"token": "test"}},
        user_email="test@example.com",
        user_name="Test User",
    )
    
    # Verify OpenCode is running
    result = await sandbox.sandbox.exec("curl", "http://localhost:8080/health")
    assert "ok" in result.stdout.lower()
    
    await sandbox.terminate()


@pytest.mark.integration
async def test_git_identity_configured():
    """Verify git identity includes (Harvest) suffix."""
    sandbox = HarvestSandbox("test-123", "owner", "repo")
    await sandbox.start(...)
    
    result = await sandbox.sandbox.exec("git", "config", "user.name")
    assert "(Harvest)" in result.stdout
    
    await sandbox.terminate()


@pytest.mark.integration
async def test_memory_volume_persists():
    """Verify memory persists across sandbox restarts."""
    # First session - create memory entry
    sandbox1 = HarvestSandbox("test-1", "owner", "repo")
    await sandbox1.start(...)
    await sandbox1.sandbox.exec(
        "bash", "-c",
        "echo 'test entry' >> /root/.mcp-memory/memory.jsonl"
    )
    await sandbox1.terminate()
    
    # Second session - verify entry exists
    sandbox2 = HarvestSandbox("test-2", "owner", "repo")
    await sandbox2.start(...)
    result = await sandbox2.sandbox.exec("cat", "/root/.mcp-memory/memory.jsonl")
    assert "test entry" in result.stdout
    
    await sandbox2.terminate()
```

### Debugging

Use Modal's built-in tools:
- `modal.enable_output()` - See build logs
- `verbose=True` on sandbox creation - Execution logs
- `modal shell` - Debug images interactively

**Deliverables**:
- [ ] Integration test suite for sandbox functionality
- [ ] Test for git identity
- [ ] Test for memory persistence
- [ ] CI pipeline for running integration tests

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
│   └── session.py               # Session lifecycle
├── config/
│   ├── opencode.json            # OpenCode config (copied to /app/)
│   ├── memory-seed.json         # Memory seed (copied to /app/)
│   └── AGENTS.md                # Main instructions (copied to /app/)
├── docs/
│   └── ai/
│       ├── git.md               # Git workflow rules (copied to /app/docs/ai/)
│       ├── memory.md            # Memory usage rules (copied to /app/docs/ai/)
│       └── harvest-mode.md      # Autonomous operation (copied to /app/docs/ai/)
├── scripts/
│   └── setup.ts                 # Setup script (adapted from chat-app)
└── tests/
    └── modal/
        └── test_sandbox_integration.py
```

---

## Secrets Reference

### Modal Secret: `harvest-{user-uuid}`

Created by setup script, contains:

| Key | Required | Description |
|-----|----------|-------------|
| `GITHUB_TOKEN` | Yes | GitHub PAT for repo access |
| `LINEAR_API_KEY` | No | Linear issue tracking |
| `POSTHOG_API_KEY` | No | Analytics and feature flags |
| `SENTRY_AUTH_TOKEN` | No | Error tracking |
| `GEMINI_API_KEY` | No | Plan review and web research |

### OpenCode Auth: `~/.local/share/opencode/auth.json`

Managed separately via OpenCode's `/connect` flow. Injected into sandbox at startup.

Format (example):
```json
{
  "anthropic": {
    "type": "oauth",
    "token": "..."
  }
}
```

---

## Open Questions

1. **OpenCode Server API**: Need to verify exact endpoints for `/health`, `/api/prompt`, etc.

2. **Modal Snapshot Limits**: What are size/retention limits? Can we use snapshots for session pause/resume?

3. **Playwright in Modal**: Verify the browser automation works correctly in Modal's container environment.

4. **Memory Seeding Timing**: Should we seed via script at startup, or let OpenCode seed on first prompt?

---

## Next Steps

After completing Phase 1.1:

1. **Phase 1.2: GitHub App Integration** - Migrate from PAT to GitHub App tokens
2. **Phase 1.3: OpenCode Server Integration** - Custom tools (run_tests, slack_update)
3. **Phase 2.1: Cloudflare Workers** - API layer connecting to Modal sandboxes
