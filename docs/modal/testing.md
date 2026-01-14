# Modal Executor Testing Guide

## Test Structure

```
packages/modal-executor/tests/
|-- __init__.py
|-- conftest.py          # Fixtures and configuration
|-- test_types.py        # Type definition tests
|-- test_sandbox.py      # Sandbox executor tests
|-- test_images.py       # Image configuration tests
```

## Running Tests

### Unit Tests (No Modal Required)

Unit tests use mocked Modal SDK - no credentials needed.

```bash
cd packages/modal-executor

# Run all unit tests
pytest -m "not modal"

# Run specific test file
pytest tests/test_types.py

# Verbose output
pytest -v -m "not modal"
```

### Integration Tests (Modal Required)

Integration tests execute against real Modal infrastructure.

```bash
cd packages/modal-executor

# Run integration tests (requires Modal auth)
pytest -m modal

# Run specific integration test
pytest -m modal tests/test_sandbox.py::TestSandboxExecutorIntegration::test_sandbox_creates_under_5_seconds
```

### All Tests

```bash
pytest
```

## Test Markers

| Marker | Description |
|--------|-------------|
| `@pytest.mark.modal` | Requires Modal credentials |
| `@pytest.mark.asyncio` | Async test |

## Writing Tests

### Unit Test Example

```python
class TestMyFeature:
    @pytest.fixture
    def mock_modal(self, mocker):
        mock = MagicMock()
        # Configure mock...
        mocker.patch.dict("sys.modules", {"modal": mock})
        return mock
    
    def test_something(self, mock_modal):
        from modal_executor import SandboxExecutor
        # Test with mocked Modal
```

### Integration Test Example

```python
@pytest.mark.modal
class TestMyFeatureIntegration:
    @pytest.mark.asyncio
    async def test_real_execution(self):
        from modal_executor import SandboxExecutor
        
        executor = SandboxExecutor()
        result = await executor.execute('print("test")')
        
        assert result.succeeded
```

## Test Fixtures

### `mock_modal`

Provides a fully mocked Modal SDK:

```python
def test_with_mock(self, mock_modal):
    mock_modal.Sandbox.create.return_value = ...
```

### `executor`

Creates a SandboxExecutor instance:

```python
@pytest.mark.asyncio
async def test_execution(self, executor):
    result = await executor.execute('print("hello")')
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e packages/modal-executor[dev]
      - run: pytest -m "not modal"

  integration-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e packages/modal-executor[dev]
      - run: pytest -m modal
    env:
      MODAL_TOKEN_ID: ${{ secrets.MODAL_TOKEN_ID }}
      MODAL_TOKEN_SECRET: ${{ secrets.MODAL_TOKEN_SECRET }}
```

## Coverage

Generate coverage report:

```bash
pytest --cov=modal_executor --cov-report=html
open htmlcov/index.html
```

## Debugging Tests

### Verbose Mode

```bash
pytest -v -s
```

### Stop on First Failure

```bash
pytest -x
```

### Run Specific Test

```bash
pytest tests/test_sandbox.py::TestSandboxExecutor::test_execute_simple_code
```

## Common Issues

### "Import modal could not be resolved"

Expected in unit tests - Modal is mocked. For integration tests, install Modal:

```bash
pip install modal
```

### Async Test Timeout

Increase timeout in conftest.py or test:

```python
@pytest.mark.asyncio
@pytest.mark.timeout(60)
async def test_slow_operation():
    ...
```

### Modal Auth Failures

Re-authenticate:

```bash
modal setup
```
