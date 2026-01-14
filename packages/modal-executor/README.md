# Modal Executor

Modal Sandbox executor for Harvest AI agent - enables isolated execution of AI-generated code.

## Features

- **Sandbox Execution**: Run arbitrary Python code in isolated Modal Sandboxes
- **Persistent State**: Shared Volume for caching and state between executions
- **Scheduled Refresh**: Automatic 30-minute environment refresh via cron
- **Timeout Enforcement**: Configurable execution timeouts with clean termination

## Installation

```bash
# From repository root
pip install -e packages/modal-executor[dev]

# Or with uv
uv pip install -e packages/modal-executor[dev]
```

## Setup

1. Install Modal CLI:
   ```bash
   pip install modal
   ```

2. Authenticate with Modal:
   ```bash
   modal setup
   ```

3. Verify setup:
   ```bash
   modal list
   ```

## Usage

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

## Development

```bash
# Run tests (mocked, no Modal required)
pytest

# Run integration tests (requires Modal credentials)
pytest -m modal

# Deploy to Modal
modal deploy src/modal_executor/app.py
```

## Configuration

Environment variables:
- `MODAL_TOKEN_ID`: Modal API token ID (for CI/CD)
- `MODAL_TOKEN_SECRET`: Modal API token secret (for CI/CD)

## Architecture

```
Modal App (harvest-agent-executor)
|-- Base Image: debian_slim + Python 3.11 + tools
|-- Sandboxes: Ephemeral execution environments
|-- Volumes: Persistent state (/mnt/state/)
|__ Scheduler: 30-min refresh cron job
```

See [Block 1.1 Plan](../../.claude/plans/feat-modal-sandbox-block-1-1/plan_2026-01-14_2215.md) for detailed architecture.
