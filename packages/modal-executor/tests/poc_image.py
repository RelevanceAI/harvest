"""
POC Image for testing Claude Code CLI with OAuth in Modal containers.

This minimal image tests if Claude Code CLI can authenticate with OAuth tokens
in a headless Modal environment.
"""

import modal

# Minimal test image with Claude Code CLI
poc_image = (
    modal.Image.debian_slim(python_version="3.11")
    # Install curl first (needed for Node.js setup)
    .apt_install("curl")
    # Install Node.js (required for npx in MCP servers)
    .run_commands(
        [
            "curl -fsSL https://deb.nodesource.com/setup_22.x | bash -",
            "apt-get install -y nodejs",
        ]
    )
    # Install Claude Code CLI
    .run_commands(["npm install -g @anthropic-ai/claude-code@latest"])
    # Install minimal MCP server for testing
    .run_commands(["npm install -g @modelcontextprotocol/server-memory"])
    # Create test directories
    .run_commands(
        [
            "mkdir -p /workspace/.claude",
            "mkdir -p /test-repo",
        ]
    )
)
