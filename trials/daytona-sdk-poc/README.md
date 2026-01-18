# Daytona + Claude Agent SDK POC

## Purpose

Validate blockers before building full implementation:
1. SDK can be invoked programmatically inside Daytona sandbox
2. SDK output (streaming messages) is parseable
3. OAuth token works via env var

## Status: ✅ PASSED

All blockers resolved on 2026-01-17.

## Prerequisites

1. Daytona credentials configured: `export DAYTONA_API_KEY=...`
2. Claude Code OAuth token: `export CLAUDE_CODE_OAUTH_TOKEN=...`
3. Node.js 20+

Or create `../.env.local` with:
```
DAYTONA_API_KEY=your-key
CLAUDE_CODE_OAUTH_TOKEN=your-token
```

## Setup

```bash
cd trials/daytona-sdk-poc
pnpm install
```

## Run POC

```bash
pnpm exec tsx test-sdk-invocation.ts
```

## Results

### SDK Message Types

The Agent SDK streams 3 message types:

1. **`system`** (subtype: `init`)
   - `session_id` - Unique session identifier
   - `cwd` - Working directory (/home/daytona)
   - `tools` - Available tools (Task, Bash, Read, Edit, Write, etc.)
   - `model` - Model used (claude-sonnet-4-5)
   - `mcp_servers` - MCP servers available
   - `slash_commands` - Available commands
   - `agents` - Sub-agents available

2. **`assistant`**
   - `message.content` - Array of content blocks (text, tool_use)
   - `message.usage` - Token usage breakdown
   - `session_id` - Session reference

3. **`result`** (subtype: `success`)
   - `result` - Final text result
   - `total_cost_usd` - Total cost
   - `duration_ms` - Execution time
   - `usage` - Aggregate token usage
   - `modelUsage` - Per-model breakdown
   - `session_id` - Session reference

### Sample Output

```json
{
  "type": "system",
  "subtype": "init",
  "session_id": "d5d86c66-c93d-4981-9241-bd4d67628ccc",
  "tools": ["Task", "Bash", "Read", "Edit", "Write", ...],
  "model": "claude-sonnet-4-5"
}

{
  "type": "assistant",
  "message": {
    "content": [{"type": "text", "text": "OK"}],
    "usage": {"input_tokens": 3, "output_tokens": 1}
  }
}

{
  "type": "result",
  "subtype": "success",
  "result": "OK",
  "total_cost_usd": 0.0117,
  "duration_ms": 2783
}
```

## Key Findings

1. **No PTY required** - SDK works via `sandbox.process.codeRun()`
2. **TypeScript sandbox** - Use `language: "typescript"` when creating sandbox
3. **OAuth via env var** - `CLAUDE_CODE_OAUTH_TOKEN` passed to sandbox works
4. **Session management** - SDK provides session_id for resume/fork
5. **Cost tracking** - `total_cost_usd` and `modelUsage` available in result

## Next Steps

Proceed to Task 1: Create Daytona Snapshot with pre-installed SDK.
