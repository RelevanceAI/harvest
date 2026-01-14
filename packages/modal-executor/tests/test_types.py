"""Tests for type definitions."""

from modal_executor.types import ExecutionResult, ExecutionStatus


class TestExecutionResult:
    """Tests for ExecutionResult - has actual logic in succeeded property."""

    def test_succeeded_true_when_returncode_zero(self):
        """Test succeeded is True when returncode is 0 and status is SUCCESS."""
        result = ExecutionResult(
            returncode=0,
            stdout="output",
            stderr="",
            duration_secs=1.0,
            sandbox_id="sb_123",
            status=ExecutionStatus.SUCCESS,
        )
        assert result.succeeded is True

    def test_succeeded_false_when_returncode_nonzero(self):
        """Test succeeded is False when returncode is non-zero."""
        result = ExecutionResult(
            returncode=1,
            stdout="",
            stderr="error",
            duration_secs=1.0,
            sandbox_id="sb_123",
            status=ExecutionStatus.ERROR,
        )
        assert result.succeeded is False

    def test_succeeded_false_when_timeout(self):
        """Test succeeded is False on timeout."""
        result = ExecutionResult(
            returncode=0,
            stdout="",
            stderr="",
            duration_secs=30.0,
            sandbox_id="sb_123",
            status=ExecutionStatus.TIMEOUT,
        )
        assert result.succeeded is False


class TestExecutionStatus:
    """Tests for ExecutionStatus enum."""

    def test_status_values_exist(self):
        """Test all expected status values exist."""
        assert ExecutionStatus.SUCCESS.value == "success"
        assert ExecutionStatus.TIMEOUT.value == "timeout"
        assert ExecutionStatus.ERROR.value == "error"
        assert ExecutionStatus.CRASHED.value == "crashed"
