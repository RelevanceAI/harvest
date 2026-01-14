"""Tests for type definitions."""

import pytest
from modal_executor.types import ExecutionResult, ExecutionStatus


class TestExecutionResult:
    """Tests for ExecutionResult dataclass."""
    
    def test_success_result(self):
        """Test creating a successful result."""
        result = ExecutionResult(
            returncode=0,
            stdout="Hello world\n",
            stderr="",
            duration_secs=1.5,
            sandbox_id="sb_123",
        )
        
        assert result.returncode == 0
        assert result.stdout == "Hello world\n"
        assert result.stderr == ""
        assert result.duration_secs == 1.5
        assert result.sandbox_id == "sb_123"
        assert result.status == ExecutionStatus.SUCCESS
        assert result.error_message is None
        assert result.succeeded is True
    
    def test_error_result(self):
        """Test creating an error result."""
        result = ExecutionResult(
            returncode=1,
            stdout="",
            stderr="Error: something went wrong",
            duration_secs=0.5,
            sandbox_id="sb_456",
            status=ExecutionStatus.ERROR,
            error_message="Process exited with code 1",
        )
        
        assert result.returncode == 1
        assert result.status == ExecutionStatus.ERROR
        assert result.succeeded is False
        assert "exited with code 1" in result.error_message
    
    def test_timeout_result(self):
        """Test creating a timeout result."""
        result = ExecutionResult(
            returncode=-1,
            stdout="",
            stderr="",
            duration_secs=30.0,
            sandbox_id="sb_789",
            status=ExecutionStatus.TIMEOUT,
            error_message="Execution timed out after 30 seconds",
        )
        
        assert result.returncode == -1
        assert result.status == ExecutionStatus.TIMEOUT
        assert result.succeeded is False
    
    def test_crashed_result(self):
        """Test creating a crashed result."""
        result = ExecutionResult(
            returncode=-1,
            stdout="",
            stderr="Sandbox crashed: MemoryError",
            duration_secs=5.0,
            sandbox_id="sb_crash",
            status=ExecutionStatus.CRASHED,
            error_message="Sandbox crashed: MemoryError",
        )
        
        assert result.status == ExecutionStatus.CRASHED
        assert result.succeeded is False
    
    def test_repr(self):
        """Test string representation."""
        result = ExecutionResult(
            returncode=0,
            stdout="",
            stderr="",
            duration_secs=2.5,
            sandbox_id="sb_repr",
        )
        
        repr_str = repr(result)
        assert "success" in repr_str
        assert "returncode=0" in repr_str
        assert "2.50s" in repr_str


class TestExecutionStatus:
    """Tests for ExecutionStatus enum."""
    
    def test_status_values(self):
        """Test all status values exist."""
        assert ExecutionStatus.SUCCESS.value == "success"
        assert ExecutionStatus.TIMEOUT.value == "timeout"
        assert ExecutionStatus.ERROR.value == "error"
        assert ExecutionStatus.CRASHED.value == "crashed"
    
    def test_status_is_string(self):
        """Test status can be used as string."""
        assert str(ExecutionStatus.SUCCESS) == "ExecutionStatus.SUCCESS"
        assert ExecutionStatus.SUCCESS.value == "success"
