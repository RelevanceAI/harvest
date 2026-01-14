"""Test fixtures for Modal Executor."""

import pytest
from unittest.mock import MagicMock, AsyncMock

# Mark all tests in this directory as potentially using Modal
pytest_plugins = []

# Configure pytest-asyncio
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "modal: tests that require Modal credentials")
    config.addinivalue_line("markers", "asyncio: tests that use asyncio")


@pytest.fixture
def mock_modal(mocker):
    """Mock Modal SDK for unit tests."""
    mock = MagicMock()
    
    # Mock Sandbox
    mock_sandbox = MagicMock()
    mock_sandbox.object_id = "sb_test_123"
    mock_sandbox.exec.return_value = MagicMock(
        stdout=MagicMock(read=MagicMock(return_value="test output\n")),
        stderr=MagicMock(read=MagicMock(return_value="")),
        returncode=0,
    )
    mock_sandbox.open.return_value.__enter__ = MagicMock()
    mock_sandbox.open.return_value.__exit__ = MagicMock()
    
    mock.Sandbox.create.return_value = mock_sandbox
    
    # Mock Volume
    mock_volume = MagicMock()
    mock.Volume.from_name.return_value = mock_volume
    
    # Mock Image
    mock_image = MagicMock()
    mock.Image.debian_slim.return_value = mock_image
    mock_image.apt_install.return_value = mock_image
    mock_image.pip_install.return_value = mock_image
    mock_image.run_commands.return_value = mock_image
    
    # Patch modal module
    mocker.patch.dict("sys.modules", {"modal": mock})
    
    return mock


@pytest.fixture
def mock_sandbox(mock_modal):
    """Get the mock Sandbox from mock_modal."""
    return mock_modal.Sandbox.create.return_value


@pytest.fixture
async def executor():
    """Create a SandboxExecutor for testing.
    
    Note: For unit tests, use with mock_modal fixture.
    For integration tests, use without mock (requires Modal credentials).
    """
    from modal_executor import SandboxExecutor
    return SandboxExecutor(default_timeout_secs=30)
