# GitHub Actions CI for Harvest AI

This repository uses GitHub Actions for continuous integration.

## Workflows

### CI Workflow (`.github/workflows/ci.yml`)

Triggers on:
- Push to any branch
- Pull requests to main
- Manual workflow dispatch

Jobs:
- **validate-docs**: Validates documentation references in `llms.txt`
- **validate-separation**: Ensures mode-specific files don't cross-reference

## Local Development

To run the same checks locally:

```bash
# Install dependencies
pnpm install

# Run validation
pnpm run validate
```

## Daytona Snapshot Testing

For testing the Daytona executor snapshot image:

```bash
cd packages/daytona-executor/snapshot

# Build the image
./build.sh

# Test without API keys
./test-snapshot.sh

# Test with Claude Agent SDK (requires CLAUDE_CODE_OAUTH_TOKEN)
./test.sh "your prompt"
```
