"""Tests for Sandbox executor."""

import pytest
import time
from unittest.mock import MagicMock, patch

from modal_executor.types import ExecutionResult, ExecutionStatus


class TestSandboxExecutor:
    """Unit tests for SandboxExecutor (mocked Modal)."""
    
    @pytest.fixture
    def mock_modal_module(self, mocker):
        """Set up mocked Modal module."""
        mock_modal = MagicMock()
        
        # Mock Sandbox
        mock_sandbox = MagicMock()
        mock_sandbox.object_id = "sb_test_123"
        
        # Mock exec result
        mock_exec_result = MagicMock()
        mock_exec_result.stdout = MagicMock()
        mock_exec_result.stdout.read.return_value = "Hello from sandbox\n"
        mock_exec_result.stderr = MagicMock()
        mock_exec_result.stderr.read.return_value = ""
        mock_exec_result.returncode = 0
        mock_sandbox.exec.return_value = mock_exec_result
        
        # Mock file operations
        mock_file = MagicMock()
        mock_sandbox.open.return_value.__enter__ = MagicMock(return_value=mock_file)
        mock_sandbox.open.return_value.__exit__ = MagicMock(return_value=None)
        
        mock_modal.Sandbox.create.return_value = mock_sandbox
        
        # Mock Volume
        mock_modal.Volume.from_name.return_value = MagicMock()
        
        # Mock Image
        mock_image = MagicMock()
        mock_modal.Image.debian_slim.return_value = mock_image
        mock_image.apt_install.return_value = mock_image
        mock_image.pip_install.return_value = mock_image
        mock_image.run_commands.return_value = mock_image
        
        # Mock App
        mock_modal.App.return_value = MagicMock()
        
        mocker.patch.dict("sys.modules", {"modal": mock_modal})
        
        return mock_modal, mock_sandbox
    
    @pytest.mark.asyncio
    async def test_execute_simple_code(self, mock_modal_module):
        """Test executing simple Python code."""
        mock_modal, mock_sandbox = mock_modal_module
        
        # Import after mocking
        from modal_executor.sandbox import SandboxExecutor
        
        executor = SandboxExecutor()
        result = await executor.execute('print("Hello")')
        
        assert result.returncode == 0
        assert result.stdout == "Hello from sandbox\n"
        assert result.stderr == ""
        assert result.status == ExecutionStatus.SUCCESS
        assert result.succeeded is True
        assert result.sandbox_id == "sb_test_123"
    
    @pytest.mark.asyncio
    async def test_execute_with_error(self, mock_modal_module):
        """Test handling execution errors."""
        mock_modal, mock_sandbox = mock_modal_module
        
        # Configure mock to return error
        mock_exec_result = MagicMock()
        mock_exec_result.stdout.read.return_value = ""
        mock_exec_result.stderr.read.return_value = "NameError: name 'undefined' is not defined"
        mock_exec_result.returncode = 1
        mock_sandbox.exec.return_value = mock_exec_result
        
        from modal_executor.sandbox import SandboxExecutor
        
        executor = SandboxExecutor()
        result = await executor.execute('print(undefined)')
        
        assert result.returncode == 1
        assert result.status == ExecutionStatus.ERROR
        assert result.succeeded is False
        assert "NameError" in result.stderr
    
    @pytest.mark.asyncio
    async def test_execute_with_timeout(self, mock_modal_module, mocker):
        """Test timeout handling."""
        mock_modal, mock_sandbox = mock_modal_module
        
        # Mock timeout exception
        class MockTimeoutError(Exception):
            pass
        
        mock_modal.exception = MagicMock()
        mock_modal.exception.SandboxTimeoutError = MockTimeoutError
        mock_sandbox.exec.side_effect = MockTimeoutError("Timeout!")
        
        from modal_executor.sandbox import SandboxExecutor
        
        executor = SandboxExecutor()
        result = await executor.execute('import time; time.sleep(100)', timeout_secs=5)
        
        assert result.returncode == -1
        assert result.status == ExecutionStatus.TIMEOUT
        assert "timed out" in result.error_message
    
    @pytest.mark.asyncio
    async def test_sandbox_cleanup_called(self, mock_modal_module):
        """Test that Sandbox is terminated after execution."""
        mock_modal, mock_sandbox = mock_modal_module
        
        from modal_executor.sandbox import SandboxExecutor
        
        executor = SandboxExecutor()
        await executor.execute('print("test")')
        
        mock_sandbox.terminate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_custom_timeout(self, mock_modal_module):
        """Test custom timeout is passed to Sandbox."""
        mock_modal, mock_sandbox = mock_modal_module
        
        from modal_executor.sandbox import SandboxExecutor
        
        executor = SandboxExecutor(default_timeout_secs=60)
        await executor.execute('print("test")', timeout_secs=120)
        
        # Verify exec was called with custom timeout
        exec_calls = mock_sandbox.exec.call_args_list
        # The python execution call should have timeout=120
        for call in exec_calls:
            if call.kwargs.get("timeout"):
                assert call.kwargs["timeout"] == 120
    
    @pytest.mark.asyncio
    async def test_volume_mounting(self, mock_modal_module):
        """Test volume is mounted when enabled."""
        mock_modal, mock_sandbox = mock_modal_module
        
        from modal_executor.sandbox import SandboxExecutor
        
        executor = SandboxExecutor(mount_volume=True)
        await executor.execute('print("test")')
        
        # Verify Sandbox.create was called with volumes
        create_call = mock_modal.Sandbox.create.call_args
        assert "/mnt/state" in create_call.kwargs.get("volumes", {})
    
    @pytest.mark.asyncio
    async def test_no_volume_when_disabled(self, mock_modal_module):
        """Test volume is not mounted when disabled."""
        mock_modal, mock_sandbox = mock_modal_module
        
        from modal_executor.sandbox import SandboxExecutor
        
        executor = SandboxExecutor(mount_volume=False)
        await executor.execute('print("test")')
        
        # Verify Sandbox.create was called without volumes (empty dict)
        create_call = mock_modal.Sandbox.create.call_args
        assert create_call.kwargs.get("volumes", {}) == {}


@pytest.mark.modal
class TestSandboxExecutorIntegration:
    """Integration tests requiring Modal credentials.
    
    Run with: pytest -m modal
    Skip with: pytest -m "not modal"
    """
    
    @pytest.mark.asyncio
    async def test_sandbox_creates_under_5_seconds(self):
        """Verify cold-start time <5s."""
        from modal_executor import SandboxExecutor
        
        executor = SandboxExecutor()
        start = time.time()
        result = await executor.execute('print("Hello")')
        duration = time.time() - start
        
        assert duration < 5.0, f"Cold start took {duration}s (>5s limit)"
        assert result.succeeded
    
    @pytest.mark.asyncio
    async def test_code_execution_captures_stdout(self):
        """Verify stdout/stderr captured correctly."""
        from modal_executor import SandboxExecutor
        
        executor = SandboxExecutor()
        result = await executor.execute('print("Hello from sandbox")')
        
        assert result.stdout.strip() == "Hello from sandbox"
        assert result.returncode == 0
    
    @pytest.mark.asyncio
    async def test_timeout_enforced(self):
        """Verify timeout kills long-running code."""
        from modal_executor import SandboxExecutor
        
        executor = SandboxExecutor()
        result = await executor.execute(
            'import time; time.sleep(60)',
            timeout_secs=2
        )
        
        assert result.status == ExecutionStatus.TIMEOUT
        assert result.duration_secs < 10  # Should timeout quickly
    
    @pytest.mark.asyncio
    async def test_volume_mounted_and_writable(self):
        """Verify /mnt/state volume is accessible."""
        from modal_executor import SandboxExecutor
        
        executor = SandboxExecutor()
        result = await executor.execute('''
import os
test_file = "/mnt/state/test_write.txt"
with open(test_file, "w") as f:
    f.write("test content")
print("Written successfully")
print(os.path.exists(test_file))
''')
        
        assert result.returncode == 0
        assert "Written successfully" in result.stdout
        assert "True" in result.stdout
