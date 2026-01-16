"""Type definitions for Modal Executor."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ExecutionStatus(str, Enum):
    """Status of code execution."""

    SUCCESS = "success"
    TIMEOUT = "timeout"
    ERROR = "error"
    CRASHED = "crashed"


@dataclass
class ExecutionResult:
    """Result from Sandbox code execution.

    Attributes:
        returncode: Process exit code (0 = success, non-zero = error)
        stdout: Captured standard output
        stderr: Captured standard error
        duration_secs: Execution time in seconds
        sandbox_id: Modal Sandbox object ID for debugging
        status: High-level execution status
        error_message: Human-readable error description (if applicable)
    """

    returncode: int
    stdout: str
    stderr: str
    duration_secs: float
    sandbox_id: str
    status: ExecutionStatus = ExecutionStatus.SUCCESS
    error_message: Optional[str] = None

    @property
    def succeeded(self) -> bool:
        """Check if execution completed successfully."""
        return self.returncode == 0 and self.status == ExecutionStatus.SUCCESS

    def __repr__(self) -> str:
        return (
            f"ExecutionResult(status={self.status.value}, "
            f"returncode={self.returncode}, "
            f"duration={self.duration_secs:.2f}s)"
        )
