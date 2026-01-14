"""Sandbox wrapper for executing code in Modal."""

import time
from typing import Optional

import modal

from modal_executor.app import app
from modal_executor.images import get_base_image
from modal_executor.types import ExecutionResult, ExecutionStatus
from modal_executor.volume import get_state_volume


class SandboxExecutor:
    """Wrapper for Modal Sandbox execution.
    
    Creates isolated Sandboxes for executing arbitrary Python code
    with timeout enforcement, stdout/stderr capture, and clean termination.
    
    Example:
        executor = SandboxExecutor()
        result = await executor.execute(
            code='print("Hello")',
            timeout_secs=30
        )
        print(result.stdout)  # "Hello\n"
    """
    
    def __init__(
        self,
        default_timeout_secs: int = 1800,  # 30 minutes
        mount_volume: bool = True,
    ):
        """Initialize executor.
        
        Args:
            default_timeout_secs: Default timeout for code execution
            mount_volume: Whether to mount shared state volume
        """
        self.default_timeout_secs = default_timeout_secs
        self.mount_volume = mount_volume
    
    async def execute(
        self,
        code: str,
        timeout_secs: Optional[int] = None,
        working_dir: str = "/workspace",
    ) -> ExecutionResult:
        """Execute Python code in isolated Sandbox.
        
        Args:
            code: Python code to execute
            timeout_secs: Execution timeout (uses default if not specified)
            working_dir: Working directory for code execution
            
        Returns:
            ExecutionResult with exit code, output, and execution metadata
        """
        timeout = timeout_secs or self.default_timeout_secs
        start_time = time.time()
        sandbox_id = ""
        sb = None
        
        try:
            # Build volumes dict
            volumes = {}
            if self.mount_volume:
                volumes["/mnt/state"] = get_state_volume()
            
            # Create Sandbox
            sb = modal.Sandbox.create(
                image=get_base_image(),
                volumes=volumes,
                timeout=timeout + 60,  # Buffer for setup/teardown
                app=app,
            )
            sandbox_id = sb.object_id
            
            # Ensure working directory exists
            sb.exec("mkdir", "-p", working_dir)
            
            # Write code to file
            code_path = f"{working_dir}/script.py"
            with sb.open(code_path, "w") as f:
                f.write(code)
            
            # Execute with timeout
            proc = sb.exec(
                "python",
                code_path,
                timeout=timeout,
                workdir=working_dir,
            )
            
            # Capture output
            stdout = proc.stdout.read()
            stderr = proc.stderr.read()
            returncode = proc.returncode
            
            duration = time.time() - start_time
            
            # Determine status
            status = ExecutionStatus.SUCCESS if returncode == 0 else ExecutionStatus.ERROR
            error_msg = None
            if returncode != 0:
                error_msg = f"Process exited with code {returncode}"
            
            return ExecutionResult(
                returncode=returncode,
                stdout=stdout,
                stderr=stderr,
                duration_secs=duration,
                sandbox_id=sandbox_id,
                status=status,
                error_message=error_msg,
            )
            
        except modal.exception.SandboxTimeoutError:
            duration = time.time() - start_time
            return ExecutionResult(
                returncode=-1,
                stdout="",
                stderr="",
                duration_secs=duration,
                sandbox_id=sandbox_id,
                status=ExecutionStatus.TIMEOUT,
                error_message=f"Execution timed out after {timeout} seconds",
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return ExecutionResult(
                returncode=-1,
                stdout="",
                stderr=str(e),
                duration_secs=duration,
                sandbox_id=sandbox_id,
                status=ExecutionStatus.CRASHED,
                error_message=f"Sandbox crashed: {type(e).__name__}: {e}",
            )
            
        finally:
            # Clean up Sandbox
            try:
                if sb is not None:
                    sb.terminate()
            except Exception:
                pass  # Best effort cleanup
    
    async def execute_shell(
        self,
        command: str,
        timeout_secs: Optional[int] = None,
        working_dir: str = "/workspace",
    ) -> ExecutionResult:
        """Execute shell command in isolated Sandbox.
        
        Args:
            command: Shell command to execute
            timeout_secs: Execution timeout
            working_dir: Working directory
            
        Returns:
            ExecutionResult with command output
        """
        # Wrap command in bash execution
        code = f'''
import subprocess
import sys

result = subprocess.run(
    {repr(command)},
    shell=True,
    capture_output=True,
    text=True,
    cwd={repr(working_dir)},
)

print(result.stdout, end="")
print(result.stderr, end="", file=sys.stderr)
sys.exit(result.returncode)
'''
        return await self.execute(code, timeout_secs, working_dir)
