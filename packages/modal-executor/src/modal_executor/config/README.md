# Modal Executor Configuration Files

This directory contains configuration files for the Harvest autonomous agent running in Modal sandboxes.

## settings.json.template

**Purpose:** Documentation reference showing the structure of the autonomous agent's Claude CLI settings.

**Important:** This is NOT used at runtime. The actual `settings.json` is generated dynamically in `sandbox.py::_create_user_settings()`.

**Runtime behavior:**
- All Harvest rules are baked into the Modal image at `/app/`
- SessionStart hooks load `/app/claude.md` and `/app/autonomous-agent.md`
- No repo-specific overrides - simple and predictable

**Why template exists:**
- Shows developers what settings structure looks like
- Documents the SessionStart hook pattern
- Provides reference for debugging

## memory-seed.json

Initial knowledge graph for the MCP memory server. Contains base knowledge about Harvest, repositories, and conventions.

## AGENTS.md

**Status:** Active file, baked into Modal image at `/app/AGENTS.md`

Contains core autonomous agent instructions for Harvest. This file is loaded via SessionStart hooks in all agent sessions.
