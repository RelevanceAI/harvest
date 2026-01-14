# GitHub Actions CI for Harvest AI

This repository uses GitHub Actions for continuous integration and deployment.

## Workflows

### 1. CI Workflow (`.github/workflows/ci.yml`)
Triggers on:
- Push to main/develop branches
- Pull requests to main/develop
- Manual workflow dispatch

Jobs:
- **lint**: Code formatting (black), linting (ruff), type checking (mypy)
- **test**: Unit tests with pytest, matrix testing across Python 3.11/3.12
- **build**: Package building and validation

### 2. Modal Integration Tests (`.github/workflows/modal-tests.yml`)
Triggers on:
- Push to main/develop/feature branches
- Pull requests
- Daily schedule

Jobs:
- **modal-tests**: Modal integration tests (requires Modal credentials)
- **security-scan**: Security vulnerability scanning with bandit and safety

### 3. Release Workflow (`.github/workflows/release.yml`)
Triggers on:
- Git tags matching `v*` pattern

Jobs:
- **release**: Creates GitHub release and publishes to PyPI

## Required Secrets

For full functionality, add these secrets to your repository:

### Modal Integration
- `MODAL_TOKEN_ID`: Modal API token ID
- `MODAL_TOKEN_SECRET`: Modal API token secret

### PyPI Publishing
- `PYPI_API_TOKEN`: PyPI API token for package publishing

## Local Development

To run the same checks locally:

```bash
# Install dev dependencies
cd packages/modal-executor
pip install -e .[dev]

# Run linting
ruff check src/ tests/
black --check src/ tests/
mypy src/

# Run tests
pytest -m "not modal" --cov=modal_executor

# Run Modal tests (requires credentials)
pytest -m modal
```

## Security Scanning

The CI includes automated security scanning:
- **bandit**: Python security linter
- **safety**: Dependency vulnerability checker

Security reports are uploaded as artifacts for review.