# Harvest Agent Snapshot Image for Daytona
# Pre-built image with Claude Agent SDK and full development environment

FROM node:20-slim AS base

# Avoid prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Python for tooling
    python3.11 \
    python3-pip \
    python3-venv \
    # Git for version control
    git \
    # Search tools (Claude uses these heavily)
    ripgrep \
    fd-find \
    # Build tools for native modules
    build-essential \
    # Utilities
    curl \
    ca-certificates \
    gnupg \
    # For Playwright/Chromium
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Create symlink for fd (Debian names it fdfind)
RUN ln -s /usr/bin/fdfind /usr/bin/fd || true

# Install pnpm globally (for project tooling)
RUN npm install -g pnpm

# Install Claude Agent SDK globally
RUN npm install -g @anthropic-ai/claude-code

# Install MCP servers globally
# Core servers
RUN npm install -g @modelcontextprotocol/server-memory
RUN npm install -g @modelcontextprotocol/server-filesystem

# Integration servers
RUN npm install -g @modelcontextprotocol/server-github
RUN npm install -g @houtini/gemini-mcp
RUN npm install -g @sentry/mcp-server

# Remote MCP proxy (for hosted servers like Linear)
RUN npm install -g mcp-remote

# Browser automation (includes Playwright)
RUN npm install -g @playwright/mcp

# Install Chromium for Playwright
RUN npx playwright install chromium
RUN npx playwright install-deps chromium

# Create non-root user for security
# Use 10001 to match relevance-chat-app conventions
ARG UID=10001
ARG GID=10001
RUN groupadd -g ${GID} harvest \
    && useradd -u ${UID} -g harvest -m -s /bin/bash harvest

# Create app directory structure
RUN mkdir -p /app/docs/ai/shared /app/docs/mcp \
    && chown -R harvest:harvest /app

# Copy baked configuration files
# These are copied by build.sh from source of truth locations
COPY --chown=harvest:harvest config/claude.md /app/claude.md
COPY --chown=harvest:harvest config/autonomous-agent.md /app/autonomous-agent.md
COPY --chown=harvest:harvest config/docs/ai/shared/ /app/docs/ai/shared/
COPY --chown=harvest:harvest config/docs/mcp/ /app/docs/mcp/
COPY --chown=harvest:harvest config/memory-seed.json /app/memory-seed.json

# Set working directory
WORKDIR /app

# Switch to non-root user
USER harvest

# Verify installations
RUN node --version \
    && npm --version \
    && python3 --version \
    && git --version \
    && rg --version \
    && fd --version \
    && which claude || echo "claude installed at $(npm root -g)/@anthropic-ai/claude-code"

# Default command (can be overridden)
CMD ["bash"]
