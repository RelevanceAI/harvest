# Modal Setup Guide

This guide covers setting up Modal for the Harvest Agent Executor.

## Prerequisites

- Python 3.11+
- pip or uv

## Quick Start

### 1. Install Modal CLI

```bash
pip install modal
# or
uv pip install modal
```

### 2. Authenticate

```bash
modal setup
```

This opens a browser window for authentication. Follow the prompts to log in.

### 3. Verify Setup

```bash
modal list
```

You should see an empty list or existing apps.

## Installing Modal Executor

From the repository root:

```bash
# Install with development dependencies
pip install -e packages/modal-executor[dev]
# or
uv pip install -e packages/modal-executor[dev]
```

## Running the App

### Local Development (Ephemeral)

```bash
# Run the app locally
modal run packages/modal-executor/src/modal_executor/app.py
```

### Deploy (Persistent)

```bash
# Deploy for persistent access + cron jobs
modal deploy packages/modal-executor/src/modal_executor/app.py
```

### Health Check

```bash
# Check deployed app status
modal app list
```

## CI/CD Setup

For automated deployments, create service credentials:

### 1. Create Service User

In Modal Dashboard: Settings > Service Users > Create

### 2. Generate Token

```bash
modal token new
```

### 3. Set Environment Variables

```bash
export MODAL_TOKEN_ID="your-token-id"
export MODAL_TOKEN_SECRET="your-token-secret"
```

Or in CI/CD secrets:
- `MODAL_TOKEN_ID`
- `MODAL_TOKEN_SECRET`

## Testing

### Unit Tests (No Modal Required)

```bash
cd packages/modal-executor
pytest -m "not modal"
```

### Integration Tests (Modal Required)

```bash
cd packages/modal-executor
pytest -m modal
```

## Troubleshooting

### "Import modal could not be resolved"

Install Modal:
```bash
pip install modal
```

### Authentication Errors

Re-authenticate:
```bash
modal setup
```

### Image Build Failures

Force rebuild:
```bash
MODAL_FORCE_BUILD=1 modal run ...
```

### Timeout Issues

Check Modal dashboard for logs: https://modal.com/apps

## Cost Monitoring

Monitor usage in Modal Dashboard: https://modal.com/usage

Typical costs:
- Sandbox execution: ~$0.0008 per 30-second run
- Volume storage: Included
- Cron jobs: Same as function execution

## Next Steps

- [Base Image Spec](../modal/base-image-spec.md)
- [Testing Guide](../modal/testing.md)
- [Block 1.1 Plan](../../.claude/plans/feat-modal-sandbox-block-1-1/plan_2026-01-14_2215.md)
