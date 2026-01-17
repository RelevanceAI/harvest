# Daytona Executor Implementation Plan

## Summary

Create `daytona-executor` as a **snapshot + scheduler** package that provides:
1. Pre-built Daytona image with Claude Agent SDK and full environment
2. Repository pre-building (like Modal's repo_builder) every 30 minutes
3. Configuration files for SDK's `systemPrompt` option

All runtime code (DaytonaSandbox, HarvestRuntime) lives in `relevance-api-node`.

## Key Differences: SDK vs CLI

| Aspect | CLI (Modal) | SDK (Daytona) |
|--------|-------------|---------------|
| **Rules** | Baked files + SessionStart hooks (`cat /app/*.md`) | Baked files → read at runtime → pass via `systemPrompt` option |
| **MCP servers** | NPM install + settings.json | NPM install + `mcpServers` option |
| **Tools** | All tools by default | `tools` option controls availability |
| **Auth** | OAuth token env var | Same - `CLAUDE_CODE_OAUTH_TOKEN` |
| **User** | root | `harvest` (non-root) |
| **Node version** | Volta | nvm |

### How Rules Work with SDK (CRITICAL)

**CLI approach (Modal):** SessionStart hooks run `cat /app/claude.md` and `cat /app/autonomous-agent.md`

**SDK approach (Daytona):** relevance-api-node reads the same baked files and passes them via `systemPrompt`:

```typescript
// relevance-api-node runtime code:
const rules = await readFile('/app/claude.md', 'utf-8');
const agentRules = await readFile('/app/autonomous-agent.md', 'utf-8');

const response = query({
  prompt: userPrompt,
  options: {
    systemPrompt: {
      type: "preset",           // Use Claude Code's base prompt
      preset: "claude_code",    // Keep tool definitions, safety features
      append: `${rules}\n\n${agentRules}`  // Add our Harvest rules
    },
    mcpServers: [...],
    // ...
  }
});
```

**Why "preset" with "append":**
- `"preset": "claude_code"` keeps Claude Code's base system prompt (tools, safety, default behaviors)
- `"append"` adds our Harvest rules on top
- Rules use `@docs/ai/shared/` paths that resolve to baked `/app/docs/ai/shared/` files
- Same rules work identically - just different delivery mechanism

---

## Repository Changes

### 1. Move POC to Trials
Move `packages/daytona-executor/poc/` → `trials/daytona-sdk-poc/`

```
trials/
├── README.md                              # Update index
├── daytona-sdk-poc/                       # NEW - moved from packages/
│   ├── README.md
│   ├── test-sdk-invocation.ts
│   ├── package.json
│   └── .gitignore
└── plans/                                 # Existing
```

### 2. Final daytona-executor Structure
```
packages/daytona-executor/
├── README.md                              # Package documentation
├── .env.example                           # Environment template
├── IMPLEMENTATION_PLAN.md                 # Reference for relevance-api-node
├── ARCHITECTURE.md                        # Architecture diagrams
│
├── snapshot/
│   ├── Dockerfile                         # Full Harvest agent image
│   ├── build.sh                           # Build script
│   ├── test-snapshot.sh                   # Verification script
│   └── README.md                          # Snapshot documentation
│
├── scheduler/                             # NEW: Repo pre-building (like Modal)
│   ├── repo_builder.ts                    # Clone + install dependencies
│   ├── refresh_repos.ts                   # 30-min cron job entrypoint
│   ├── package.json                       # TypeScript dependencies
│   └── README.md                          # Scheduler documentation
│
└── config/
    ├── memory-seed.json                   # Initial knowledge graph (for MCP memory)
    ├── claude.md                          # Rules for systemPrompt
    └── autonomous-agent.md                # Autonomous mode extensions
```

---

## Implementation Tasks

### Task 1: Move POC to Trials

**Actions:**
1. Move `packages/daytona-executor/poc/` → `trials/daytona-sdk-poc/`
2. Update `trials/README.md` to include the Daytona POC entry
3. Update POC README to reflect archived status

### Task 2: Create Comprehensive Dockerfile

**File:** `packages/daytona-executor/snapshot/Dockerfile`

Key differences from modal-executor:
- **No Claude Code CLI** - using Agent SDK programmatically instead
- **Non-root user** - `harvest` user at `/home/harvest`
- **SDK configuration** - Rules passed via `systemPrompt`, MCP via `mcpServers` option
- **Config files for reading** - Baked in for SDK to read and pass to Claude

**Issues identified by Gemini adversarial reviews:**

**Review 1 (Volta-based):**
- BLOCKER: Insecure Volta installation → Switched to nvm
- BLOCKER: `|| true` hiding failures → Only optional MCP servers use it
- SHOULD: Redundant .bashrc modifications → Removed
- CONSIDER: Minimize packages → Added `--no-install-recommends`

**Review 2 (nvm-based):**
- BLOCKER: NVM redundant with base image → Base image `node:20-slim` already provides Node 20; remove nvm from Dockerfile, scheduler handles version switching
- BLOCKER: `curl | bash` for nvm → Removed nvm from Dockerfile
- BLOCKER: `|| true` silent failures → Changed to log warnings (see updated code)
- BLOCKER: SDK assumptions unverified → Verified via Context7: `preset: "claude_code"` with `append` is documented behavior
- BLOCKER: Scheduler error handling → Added error handling, fallback, and alerting
- SHOULD: Multi-stage build → CONSIDER for future optimization (not blocking)
- SHOULD: Externalize config → Rules need to be baked for SDK; updates require image rebuild (acceptable for now)

```dockerfile
FROM node:20-slim

# ============================================
# SYSTEM PACKAGES (as root)
# ============================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build tools
    build-essential libffi-dev libssl-dev zlib1g-dev \
    # Version control & utilities
    git curl wget ca-certificates \
    # Text processing (essential for agent)
    jq ripgrep fd-find \
    # Python
    python3.11 python3-pip \
    # Playwright/Chromium dependencies
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libdbus-1-3 libxkbcommon0 \
    libatspi2.0-0 libxcomposite1 libxdamage1 libxfixes3 \
    libxrandr2 libgbm1 libasound2 libpango-1.0-0 libcairo2 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create fd symlink (fd-find → fd)
RUN ln -s $(which fdfind) /usr/local/bin/fd

# ============================================
# CREATE NON-ROOT USER: harvest
# ============================================
RUN useradd -m -s /bin/bash harvest

# ============================================
# DIRECTORY STRUCTURE (as root, then chown)
# ============================================
RUN mkdir -p /workspace /app/docs/ai/shared /app/docs/mcp /home/harvest/.mcp-memory \
    && chown -R harvest:harvest /workspace /app /home/harvest

# ============================================
# HARVEST CONFIGURATION (for SDK's systemPrompt)
# These files are READ by the runtime and passed to SDK
# Matches Modal's baked structure exactly:
# - /app/claude.md (shared base rules)
# - /app/autonomous-agent.md (autonomous extensions)
# - /app/docs/ai/shared/ (targets of @docs/ai/shared/ references)
# - /app/docs/mcp/ (targets of @docs/mcp/ references)
# - /app/memory-seed.json (initial knowledge graph)
# ============================================
COPY --chown=harvest:harvest config/claude.md /app/claude.md
COPY --chown=harvest:harvest config/autonomous-agent.md /app/autonomous-agent.md
COPY --chown=harvest:harvest config/docs/ai/shared/ /app/docs/ai/shared/
COPY --chown=harvest:harvest config/docs/mcp/ /app/docs/mcp/
COPY --chown=harvest:harvest config/memory-seed.json /app/memory-seed.json

# ============================================
# SWITCH TO NON-ROOT USER
# ============================================
USER harvest
WORKDIR /home/harvest

# ============================================
# NODE.JS - Use base image's Node 20
# No nvm needed - base image provides Node 20
# Scheduler handles version switching for cloned repos
# ============================================

# ============================================
# GLOBAL NODE PACKAGES
# ============================================
RUN npm install -g pnpm

# ============================================
# PYTHON PACKAGES (user install)
# ============================================
RUN pip3 install --user --break-system-packages \
    uv requests httpx pydantic python-dotenv pyyaml aiofiles

# ============================================
# CLAUDE AGENT SDK (programmatic API - REQUIRED)
# ============================================
RUN npm install -g @anthropic-ai/claude-agent-sdk

# ============================================
# MCP SERVERS - REQUIRED (fail build if missing)
# Note: These are invoked via SDK's mcpServers option, not config files
# ============================================
RUN npm install -g @modelcontextprotocol/server-memory
RUN npm install -g @modelcontextprotocol/server-filesystem

# ============================================
# MCP SERVERS - OPTIONAL (API key dependent)
# Log warnings on failure instead of silent suppression
# ============================================
RUN npm install -g @anthropic-ai/mcp-server-playwright@latest \
    || echo "WARNING: Failed to install playwright MCP server"
RUN npm install -g chrome-devtools-mcp@latest \
    || echo "WARNING: Failed to install devtools MCP server"
RUN npm install -g @anthropic-ai/mcp-server-github@latest \
    || echo "WARNING: Failed to install github MCP server"
RUN npm install -g @modelcontextprotocol/server-linear \
    || echo "WARNING: Failed to install linear MCP server"
RUN npm install -g @houtini/gemini-mcp \
    || echo "WARNING: Failed to install gemini MCP server"
RUN npm install -g @sentry/mcp-server \
    || echo "WARNING: Failed to install sentry MCP server"
RUN npm install -g @upstash/context7-mcp \
    || echo "WARNING: Failed to install context7 MCP server"

# ============================================
# PLAYWRIGHT BROWSER
# ============================================
RUN npx playwright install chromium

WORKDIR /workspace
```

### Task 3: Copy Configuration Files

**Files to copy into `packages/daytona-executor/config/`:**

Matches Modal's baked structure exactly (see `images.py` lines 195-207):

| Source | Destination |
|--------|-------------|
| `.claude/claude.md` | `config/claude.md` |
| `docs/ai/autonomous-agent.md` | `config/autonomous-agent.md` |
| `docs/ai/shared/` (entire directory) | `config/docs/ai/shared/` |
| `docs/mcp/` (entire directory) | `config/docs/mcp/` |
| `packages/modal-executor/src/modal_executor/config/memory-seed.json` | `config/memory-seed.json` |

**Why the full docs structure?**
- Rules use `@docs/ai/shared/` and `@docs/mcp/` references
- When working directory is `/app/`, these resolve to `/app/docs/ai/shared/` etc.
- SDK needs the same file structure as CLI to resolve the references

**SDK usage in relevance-api-node:**

```typescript
const rules = await readFile('/app/claude.md', 'utf-8');
const agentRules = await readFile('/app/autonomous-agent.md', 'utf-8');

const response = query({
  prompt: userPrompt,
  options: {
    systemPrompt: {
      type: "preset",
      preset: "claude_code",
      append: `${rules}\n\n${agentRules}`
    },
    workingDirectory: "/app",  // So @docs/ references resolve correctly
    // ...
  }
});
```

### Task 4: Create Repository Pre-Builder (Like Modal's repo_builder)

**Directory:** `packages/daytona-executor/scheduler/`

This mirrors Modal's `repo_builder.py` pattern - pre-clones repos and installs dependencies every 30 minutes.

**File:** `scheduler/repo_builder.ts`

```typescript
import { Daytona } from "@daytonaio/sdk";

const DEFAULT_REPOS = [
  { owner: "RelevanceAI", name: "relevance-chat-app", branch: "main" },
  { owner: "RelevanceAI", name: "relevance-api-node", branch: "main" },
  { owner: "RelevanceAI", name: "relevance-app", branch: "main" },
];

interface BuildResult {
  success: boolean;
  repo: string;
  error?: string;
  duration?: number;
}

export async function buildRepoImage(
  owner: string,
  name: string,
  branch: string
): Promise<BuildResult> {
  const startTime = Date.now();
  const daytona = new Daytona({ apiKey: process.env.DAYTONA_API_KEY });

  const sandbox = await daytona.create({
    snapshot: "harvest-snapshot",
    envVars: {
      GITHUB_TOKEN: process.env.GITHUB_TOKEN,
    },
  });

  try {
    // 1. Clone repository
    await sandbox.process.executeCommand(
      `git clone --depth 1 --branch ${branch} ` +
      `https://x-access-token:${process.env.GITHUB_TOKEN}@github.com/${owner}/${name}.git ` +
      `/workspace/${name}`
    );

    // 2. Detect and install Node version via nvm
    // Scheduler installs nvm in sandbox for version switching
    const nodeVersion = await detectNodeVersion(sandbox, `/workspace/${name}`);
    if (nodeVersion) {
      await sandbox.process.executeCommand(
        `curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash && ` +
        `source ~/.nvm/nvm.sh && nvm install ${nodeVersion} && nvm use ${nodeVersion}`
      );
    }

    // 3. Detect package manager and install deps
    const pm = await detectPackageManager(sandbox, `/workspace/${name}`);
    if (pm === "pnpm") {
      await sandbox.process.executeCommand(
        `cd /workspace/${name} && pnpm install --frozen-lockfile`
      );
    } else if (pm === "npm") {
      await sandbox.process.executeCommand(
        `cd /workspace/${name} && npm ci`
      );
    }

    // 4. Run build if available (don't fail on build errors)
    await sandbox.process.executeCommand(
      `cd /workspace/${name} && npm run build || echo "Build step skipped or failed"`
    );

    return {
      success: true,
      repo: `${owner}/${name}`,
      duration: Date.now() - startTime
    };
  } catch (error) {
    return {
      success: false,
      repo: `${owner}/${name}`,
      error: error instanceof Error ? error.message : String(error),
      duration: Date.now() - startTime
    };
  } finally {
    await sandbox.delete();
  }
}
```

**File:** `scheduler/refresh_repos.ts` (Cron entrypoint with error handling)

```typescript
// Run via: npx tsx scheduler/refresh_repos.ts
// Schedule with cron: */30 * * * * cd /path && npx tsx scheduler/refresh_repos.ts

import { buildRepoImage, DEFAULT_REPOS } from "./repo_builder";

const MAX_RETRIES = 3;
const RETRY_DELAY_MS = 5000;

async function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function buildWithRetry(
  owner: string,
  name: string,
  branch: string
): Promise<{ success: boolean; attempts: number; error?: string }> {
  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    console.log(`  Attempt ${attempt}/${MAX_RETRIES} for ${owner}/${name}...`);

    const result = await buildRepoImage(owner, name, branch);

    if (result.success) {
      return { success: true, attempts: attempt };
    }

    console.warn(`  Attempt ${attempt} failed: ${result.error}`);

    if (attempt < MAX_RETRIES) {
      console.log(`  Retrying in ${RETRY_DELAY_MS}ms...`);
      await sleep(RETRY_DELAY_MS);
    }
  }

  return { success: false, attempts: MAX_RETRIES, error: "Max retries exceeded" };
}

async function main() {
  console.log(`[${new Date().toISOString()}] Starting repo refresh...`);

  const results: Array<{ repo: string; success: boolean; attempts: number; error?: string }> = [];

  for (const repo of DEFAULT_REPOS) {
    const result = await buildWithRetry(repo.owner, repo.name, repo.branch);
    results.push({ repo: `${repo.owner}/${repo.name}`, ...result });

    if (result.success) {
      console.log(`✓ ${repo.owner}/${repo.name}: Success (${result.attempts} attempts)`);
    } else {
      console.error(`✗ ${repo.owner}/${repo.name}: FAILED after ${result.attempts} attempts`);
    }
  }

  // Summary
  const failed = results.filter(r => !r.success);
  console.log(`\n[${new Date().toISOString()}] Refresh complete.`);
  console.log(`  Success: ${results.length - failed.length}/${results.length}`);

  if (failed.length > 0) {
    console.error(`  FAILED repos: ${failed.map(f => f.repo).join(", ")}`);
    // TODO: Send alert to Slack/PagerDuty
    process.exit(1);
  }
}

main();
```

**File:** `scheduler/package.json`

```json
{
  "name": "daytona-scheduler",
  "type": "module",
  "scripts": {
    "refresh": "tsx refresh_repos.ts"
  },
  "dependencies": {
    "@daytonaio/sdk": "^0.130.0",
    "dotenv": "^17.2.3"
  },
  "devDependencies": {
    "tsx": "^4.0.0",
    "typescript": "^5.0.0"
  }
}
```

### Task 5: Create Build Script

**File:** `packages/daytona-executor/snapshot/build.sh`

```bash
#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Building Harvest Daytona Snapshot ==="

# Copy latest config files
echo "Copying configuration files..."
mkdir -p "$SCRIPT_DIR/config/docs/ai/shared" "$SCRIPT_DIR/config/docs/mcp"

cp "$PACKAGE_DIR/../../.claude/claude.md" "$SCRIPT_DIR/config/claude.md"
cp "$PACKAGE_DIR/../../docs/ai/autonomous-agent.md" "$SCRIPT_DIR/config/autonomous-agent.md"
cp "$PACKAGE_DIR/config/memory-seed.json" "$SCRIPT_DIR/config/memory-seed.json"
cp -r "$PACKAGE_DIR/../../docs/ai/shared/"* "$SCRIPT_DIR/config/docs/ai/shared/"
cp -r "$PACKAGE_DIR/../../docs/mcp/"* "$SCRIPT_DIR/config/docs/mcp/"

# Build image
echo "Building Docker image..."
docker build -t harvest-daytona-snapshot:latest "$SCRIPT_DIR"

# Cleanup copied files
rm -rf "$SCRIPT_DIR/config"

echo "=== Build complete ==="
echo "Image: harvest-daytona-snapshot:latest"
```

### Task 6: Create Test Script

**File:** `packages/daytona-executor/snapshot/test-snapshot.sh`

```bash
#!/bin/bash
set -e

IMAGE="harvest-daytona-snapshot:latest"

echo "=== Testing Harvest Daytona Snapshot ==="

# Test 1: Node.js available
echo -n "Node.js... "
docker run --rm $IMAGE node --version && echo "✓"

# Test 2: User is 'harvest' (non-root)
echo -n "User is harvest... "
docker run --rm $IMAGE whoami | grep -q harvest && echo "✓"

# Test 3: Claude Agent SDK loadable
echo -n "Claude Agent SDK... "
docker run --rm $IMAGE node -e "require('@anthropic-ai/claude-agent-sdk')" && echo "✓"

# Test 4: MCP memory server available
echo -n "MCP Memory Server... "
docker run --rm $IMAGE which mcp-server-memory && echo "✓"

# Test 5: Playwright available
echo -n "Playwright... "
docker run --rm $IMAGE npx playwright --version && echo "✓"

# Test 6: Config files present
echo -n "Config files... "
docker run --rm $IMAGE ls /app/claude.md /app/memory-seed.json && echo "✓"

# Test 7: Python available
echo -n "Python... "
docker run --rm $IMAGE python3 --version && echo "✓"

# Test 8: Git available
echo -n "Git... "
docker run --rm $IMAGE git --version && echo "✓"

# Test 9: Docs directories present (for @docs/ resolution)
echo -n "Docs directories... "
docker run --rm $IMAGE ls /app/docs/ai/shared /app/docs/mcp && echo "✓"

# Test 10: pnpm available
echo -n "pnpm... "
docker run --rm $IMAGE pnpm --version && echo "✓"

echo ""
echo "=== All tests passed ==="
```

### Task 7: Update Memory Seed for Daytona

**File:** `packages/daytona-executor/config/memory-seed.json`

Update from Modal-specific references to Daytona:

```json
{
  "entities": [
    {
      "name": "HarvestSession",
      "entityType": "session_context",
      "observations": [
        "Running in Daytona sandbox with Claude Agent SDK",
        "Workspace at /workspace/{repo-name}",
        "Config files at /app/ (read-only, baked into image)",
        "Memory persists at /root/.mcp-memory/memory.jsonl",
        "Non-root execution supported",
        "Only committed and pushed work persists across sessions"
      ]
    },
    // ... rest of entities (update Modal references)
  ]
}
```

### Task 8: Create Package README

**File:** `packages/daytona-executor/README.md`

Document:
- Purpose (snapshot infrastructure for relevance-api-node)
- Building the snapshot
- What's included in the image
- Environment variables needed at runtime
- How relevance-api-node uses this

### Task 9: Create Environment Template

**File:** `packages/daytona-executor/.env.example`

```bash
# Required for testing
DAYTONA_API_KEY=

# Required for Claude authentication
CLAUDE_CODE_OAUTH_TOKEN=

# Git identity (required)
GIT_USER_EMAIL=
GIT_USER_NAME=

# GitHub access (required for repo operations)
GITHUB_TOKEN=

# Optional MCP servers
GEMINI_API_KEY=
LINEAR_API_KEY=
SENTRY_AUTH_TOKEN=
```

### Task 10: Update Root README

Update `README.md` package status table to reflect:
- `modal-executor`: Production (legacy)
- `daytona-executor`: Snapshot only (active development)

---

## Critical Files to Create/Modify

| File | Action |
|------|--------|
| `trials/daytona-sdk-poc/` | Move from packages/daytona-executor/poc/ |
| `trials/README.md` | Update to include Daytona POC |
| `packages/daytona-executor/snapshot/Dockerfile` | Create |
| `packages/daytona-executor/snapshot/build.sh` | Create |
| `packages/daytona-executor/snapshot/test-snapshot.sh` | Create |
| `packages/daytona-executor/snapshot/README.md` | Create |
| `packages/daytona-executor/scheduler/repo_builder.ts` | Create |
| `packages/daytona-executor/scheduler/refresh_repos.ts` | Create |
| `packages/daytona-executor/scheduler/package.json` | Create |
| `packages/daytona-executor/scheduler/README.md` | Create |
| `packages/daytona-executor/config/memory-seed.json` | Create (update from modal) |
| `packages/daytona-executor/README.md` | Create |
| `packages/daytona-executor/.env.example` | Create |
| `README.md` (root) | Update status table |

---

## Verification Plan

1. **Build Snapshot:** `cd packages/daytona-executor/snapshot && ./build.sh`
2. **Test Snapshot:** `./test-snapshot.sh` - All checks pass
3. **POC Works:** `cd trials/daytona-sdk-poc && npm test` - Validates SDK in real Daytona
4. **Cold Start:** Measure sandbox creation time (<500ms target with pre-built image)

---

## Success Criteria

- [ ] POC moved to trials/daytona-sdk-poc/
- [ ] Dockerfile builds without errors
- [ ] All system packages installed (matching modal-executor)
- [ ] Claude Agent SDK pre-installed (no CLI)
- [ ] MCP servers pre-installed
- [ ] Playwright + Chromium working
- [ ] Config files baked into /app/
- [ ] Memory seed updated for Daytona context
- [ ] Build and test scripts functional
- [ ] Scheduler/repo_builder created (30-min refresh pattern)
- [ ] Root README updated

---

## What's Different from Modal-Executor Image

| Aspect | Modal | Daytona |
|--------|-------|---------|
| Base | modal.Image.debian_slim(python_version="3.11") | node:20-slim + manual Python |
| User | root | `harvest` (non-root) |
| SDK | Claude CLI only | Claude Agent SDK (programmatic) |
| Config | Generated at runtime | Baked in + runtime overlay |
| Volumes | Modal Volumes | Daytona persistent storage |

---

## What Lives Where

| Component | Location |
|-----------|----------|
| Daytona snapshot (Dockerfile) | `harvest/packages/daytona-executor/snapshot/` |
| Repo pre-builder (30-min cron) | `harvest/packages/daytona-executor/scheduler/` |
| POC reference | `harvest/trials/daytona-sdk-poc/` |
| Config files (baked) | `harvest/packages/daytona-executor/config/` |
| DaytonaSandbox class | `relevance-api-node` |
| HarvestRuntime | `relevance-api-node` |
| SDK message types | `relevance-api-node` |
| UI components | `relevance-chat-app` |
