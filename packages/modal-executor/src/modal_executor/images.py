"""Base image definitions for Modal Sandboxes.

This module defines the base image for Harvest agent sandboxes, including:
- Python 3.11 with common packages
- Node.js 22 with Volta for version management
- Playwright with Chromium for browser automation
- OpenCode for AI agent operation
- All required MCP servers
- GitHub CLI for repository operations
"""

from pathlib import Path

import modal

# Path to config files (relative to this module)
_CONFIG_DIR = Path(__file__).parent / "config"

# =============================================================================
# Base Image Definition
# =============================================================================

_base_image = (
    modal.Image.debian_slim(python_version="3.11")
    
    # -------------------------------------------------------------------------
    # System Packages
    # -------------------------------------------------------------------------
    .apt_install(
        # Version control
        "git",
        # HTTP/network tools
        "curl",
        "wget",
        # Build tools for native extensions
        "build-essential",
        "libffi-dev",
        "libssl-dev",
        "zlib1g-dev",
        # Text processing
        "jq",
        # Shell tools
        "ripgrep",
        "tree",
        "fd-find",
        "vim",
        "less",
        # Playwright/Chromium dependencies
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
        "libpango-1.0-0",
        "libcairo2",
        # Process management
        "procps",
    )
    
    # -------------------------------------------------------------------------
    # Alias fd (Debian naming quirk: fdfind -> fd)
    # -------------------------------------------------------------------------
    .run_commands("ln -sf $(which fdfind) /usr/local/bin/fd || true")
    
    # -------------------------------------------------------------------------
    # Node.js 22 via NodeSource
    # -------------------------------------------------------------------------
    .run_commands(
        "curl -fsSL https://deb.nodesource.com/setup_22.x | bash -",
        "apt-get install -y nodejs",
    )
    
    # -------------------------------------------------------------------------
    # Volta (Node version manager)
    # -------------------------------------------------------------------------
    .run_commands(
        "curl https://get.volta.sh | bash -s -- --skip-setup",
        "echo 'export VOLTA_HOME=\"$HOME/.volta\"' >> /root/.bashrc",
        "echo 'export PATH=\"$VOLTA_HOME/bin:$PATH\"' >> /root/.bashrc",
    )
    .env({"VOLTA_HOME": "/root/.volta", "PATH": "/root/.volta/bin:/usr/local/bin:/usr/bin:/bin"})
    
    # -------------------------------------------------------------------------
    # pnpm (for monorepos)
    # -------------------------------------------------------------------------
    .run_commands("npm install -g pnpm")
    
    # -------------------------------------------------------------------------
    # GitHub CLI
    # -------------------------------------------------------------------------
    .run_commands(
        "curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg",
        "chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg",
        "echo 'deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main' | tee /etc/apt/sources.list.d/github-cli.list > /dev/null",
        "apt-get update && apt-get install -y gh",
    )
    
    # -------------------------------------------------------------------------
    # OpenCode (AI coding agent)
    # -------------------------------------------------------------------------
    .run_commands("npm install -g opencode@latest")
    
    # -------------------------------------------------------------------------
    # MCP Servers - Required (always available)
    # -------------------------------------------------------------------------
    .run_commands(
        # Memory - persistent knowledge graph
        "npm install -g @modelcontextprotocol/server-memory",
        # Filesystem - file operations in /workspace
        "npm install -g @modelcontextprotocol/server-filesystem",
        # Playwright - browser automation
        "npm install -g @anthropic-ai/mcp-server-playwright@latest || npm install -g @playwright/mcp@latest",
        # DevTools - Chrome DevTools Protocol debugging
        "npm install -g chrome-devtools-mcp@latest",
    )
    
    # -------------------------------------------------------------------------
    # MCP Servers - Optional (graceful fail if no API key)
    # -------------------------------------------------------------------------
    .run_commands(
        # GitHub - repo operations (also have gh CLI)
        "npm install -g @anthropic-ai/mcp-server-github@latest || true",
        # Gemini - plan review & web research
        "npm install -g @houtini/gemini-mcp || true",
        # Sentry - error tracking
        "npm install -g @sentry/mcp-server || true",
    )
    
    # -------------------------------------------------------------------------
    # Playwright Browsers (Chromium only for size)
    # -------------------------------------------------------------------------
    .run_commands(
        "npx playwright install chromium",
        "npx playwright install-deps chromium",
    )
    
    # -------------------------------------------------------------------------
    # Python Packages
    # -------------------------------------------------------------------------
    .pip_install(
        # Fast package installer
        "uv",
        # Common Python packages for agent work
        "requests",
        "httpx",
        "pydantic>=2.0",
        # File handling
        "python-dotenv",
        "pyyaml",
        # Async support
        "aiofiles",
    )
    
    # -------------------------------------------------------------------------
    # Directory Structure
    # -------------------------------------------------------------------------
    .run_commands(
        # Workspace for repositories
        "mkdir -p /workspace",
        # App directory for Harvest config (baked into image)
        "mkdir -p /app/docs/ai",
        "mkdir -p /app/docs/mcp",
        # OpenCode configuration
        "mkdir -p /root/.config/opencode",
        "mkdir -p /root/.local/share/opencode",
        # MCP memory storage (will be mounted as volume)
        "mkdir -p /root/.mcp-memory",
        # Cache directories
        "mkdir -p /mnt/state/.cache",
        "mkdir -p /mnt/state/git-repos",
        "mkdir -p /mnt/state/checkpoints",
    )
    
    # -------------------------------------------------------------------------
    # Harvest Configuration Files (baked into image)
    # -------------------------------------------------------------------------
    .add_local_file(str(_CONFIG_DIR / "opencode.json"), "/root/.config/opencode/config.json")
    .add_local_file(str(_CONFIG_DIR / "AGENTS.md"), "/app/AGENTS.md")
    .add_local_file(str(_CONFIG_DIR / "memory-seed.json"), "/app/memory-seed.json")
)


# =============================================================================
# Public API
# =============================================================================

def get_base_image() -> modal.Image:
    """Get the base image for Sandbox execution.
    
    This image includes:
    - Python 3.11 with common packages
    - Node.js 22 with Volta for version management
    - Playwright with Chromium for browser automation
    - OpenCode for AI agent operation
    - All required MCP servers (memory, filesystem, playwright, devtools)
    - Optional MCP servers (github, gemini, sentry)
    - GitHub CLI for repository operations
    
    Returns:
        Configured Modal Image ready for agent sandboxes
    """
    return _base_image


def get_base_image_with_extras(pip_packages: list[str] | None = None, npm_packages: list[str] | None = None) -> modal.Image:
    """Get base image with additional packages.
    
    Args:
        pip_packages: Additional pip packages to install
        npm_packages: Additional npm packages to install globally
        
    Returns:
        Extended Modal Image
        
    Example:
        image = get_base_image_with_extras(
            pip_packages=["pandas", "numpy"],
            npm_packages=["typescript"]
        )
    """
    image = _base_image
    
    if pip_packages:
        image = image.pip_install(*pip_packages)
    
    if npm_packages:
        for pkg in npm_packages:
            image = image.run_commands(f"npm install -g {pkg}")
    
    return image


def get_image_for_repo(repo_name: str, node_version: str | None = None) -> modal.Image:
    """Get an image configured for a specific repository.
    
    This can be extended to handle repo-specific requirements.
    
    Args:
        repo_name: Name of the repository
        node_version: Specific Node.js version (uses Volta to install)
        
    Returns:
        Image configured for the repository
    """
    image = _base_image
    
    if node_version:
        # Use Volta to install specific Node version
        image = image.run_commands(
            f"/root/.volta/bin/volta install node@{node_version}"
        )
    
    return image
