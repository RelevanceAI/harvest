"""Sandbox wrapper for executing code in Modal.

This module provides the SandboxExecutor for basic code execution and
HarvestSandbox for full agent sessions with OpenCode, git, and MCP servers.
"""

import json
import time
from dataclasses import dataclass, field
from typing import Optional

import modal

from modal_executor.app import app
from modal_executor.images import get_base_image
from modal_executor.types import ExecutionResult, ExecutionStatus
from modal_executor.volume import get_state_volume


# =============================================================================
# Basic Sandbox Executor (for simple code execution)
# =============================================================================

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


# =============================================================================
# Harvest Session Sandbox (full agent environment)
# =============================================================================

@dataclass
class HarvestSession:
    """Configuration for a Harvest agent session."""
    
    session_id: str
    repo_owner: str
    repo_name: str
    branch: str = "main"
    
    # Git identity
    user_email: str = ""
    user_name: str = ""
    
    # Credentials (injected at runtime)
    github_token: str = ""
    anthropic_api_key: str = ""
    
    # Optional credentials (for MCP servers)
    gemini_api_key: Optional[str] = None
    sentry_auth_token: Optional[str] = None
    linear_api_key: Optional[str] = None
    
    # OpenCode auth (OAuth tokens if using opencode.ai)
    opencode_auth: dict = field(default_factory=dict)
    
    @property
    def repo_path(self) -> str:
        """Path to repository in workspace."""
        return f"/workspace/{self.repo_name}"
    
    @property
    def memory_volume_name(self) -> str:
        """Name of per-repo memory volume."""
        return f"harvest-memory-{self.repo_owner}-{self.repo_name}"


class HarvestSandbox:
    """Manages a Modal sandbox for a Harvest agent session.
    
    Key design decisions:
    - /workspace is the root, repos cloned to /workspace/{repo-name}
    - OpenCode runs in server mode on port 8080
    - Memory persists via per-repo Modal volume
    - Git uses Safe-Carry-Forward pattern (no pull/stash)
    - Git identity includes "(Harvest)" suffix for attribution
    
    Example:
        session = HarvestSession(
            session_id="abc123",
            repo_owner="RelevanceAI",
            repo_name="relevance-chat-app",
            user_email="dev@example.com",
            user_name="Developer",
            github_token="ghp_xxx",
            anthropic_api_key="sk-ant-xxx",
        )
        
        sandbox = HarvestSandbox(session)
        await sandbox.start()
        
        response = await sandbox.send_prompt("Fix the failing tests")
        print(response)
        
        await sandbox.terminate()
    """
    
    def __init__(self, session: HarvestSession):
        """Initialize sandbox manager.
        
        Args:
            session: Session configuration with credentials and repo info
        """
        self.session = session
        self.sandbox: Optional[modal.Sandbox] = None
        self._opencode_ready = False
        
        # Per-repo memory volume
        self._memory_volume = modal.Volume.from_name(
            session.memory_volume_name,
            create_if_missing=True
        )
    
    async def start(self, timeout_secs: int = 3600) -> "HarvestSandbox":
        """Start the sandbox with full configuration.
        
        Args:
            timeout_secs: Maximum session duration (default 1 hour)
            
        Returns:
            Self for chaining
            
        Raises:
            RuntimeError: If sandbox fails to start or OpenCode doesn't respond
        """
        # Build environment variables
        env_vars = {
            "GITHUB_TOKEN": self.session.github_token,
            "ANTHROPIC_API_KEY": self.session.anthropic_api_key,
            "GIT_USER_EMAIL": self.session.user_email,
            "GIT_USER_NAME": self.session.user_name,
            "HARVEST_SESSION_ID": self.session.session_id,
            "HARVEST_REPO": f"{self.session.repo_owner}/{self.session.repo_name}",
        }
        
        # Add optional credentials
        if self.session.gemini_api_key:
            env_vars["GEMINI_API_KEY"] = self.session.gemini_api_key
        if self.session.sentry_auth_token:
            env_vars["SENTRY_AUTH_TOKEN"] = self.session.sentry_auth_token
        if self.session.linear_api_key:
            env_vars["LINEAR_API_KEY"] = self.session.linear_api_key
        
        # Create sandbox with volumes
        self.sandbox = await modal.Sandbox.create.aio(
            image=get_base_image(),
            timeout=timeout_secs,
            secrets=[modal.Secret.from_dict(env_vars)],
            volumes={
                "/root/.mcp-memory": self._memory_volume,
            },
            app=app,
        )
        
        # Setup sequence
        await self._clone_repo()
        await self._configure_git()
        await self._inject_opencode_auth()
        await self._seed_memory_if_needed()
        await self._start_opencode()
        
        return self
    
    async def _clone_repo(self) -> None:
        """Clone the repository to /workspace/{repo-name}."""
        repo_url = (
            f"https://x-access-token:{self.session.github_token}"
            f"@github.com/{self.session.repo_owner}/{self.session.repo_name}.git"
        )
        
        # Clone with specific branch
        proc = await self.sandbox.exec.aio(
            "git", "clone",
            "--branch", self.session.branch,
            repo_url,
            self.session.repo_path,
        )
        
        if proc.returncode != 0:
            stderr = proc.stderr.read()
            raise RuntimeError(f"Failed to clone repository: {stderr}")
    
    async def _configure_git(self) -> None:
        """Configure git identity and credentials.
        
        Uses credential helper for HTTPS, adds "(Harvest)" suffix for attribution.
        """
        # Store credentials
        await self.sandbox.exec.aio(
            "git", "config", "--global", "credential.helper", "store"
        )
        
        # Write credentials file
        creds = f"https://x-access-token:{self.session.github_token}@github.com"
        await self.sandbox.exec.aio(
            "bash", "-c", f"echo '{creds}' > ~/.git-credentials"
        )
        
        # Identity with (Harvest) suffix for attribution
        await self.sandbox.exec.aio(
            "git", "config", "--global", "user.email", self.session.user_email
        )
        await self.sandbox.exec.aio(
            "git", "config", "--global", "user.name", f"{self.session.user_name} (Harvest)"
        )
        
        # Safe defaults
        await self.sandbox.exec.aio(
            "git", "config", "--global", "push.autoSetupRemote", "true"
        )
        await self.sandbox.exec.aio(
            "git", "config", "--global", "init.defaultBranch", "main"
        )
    
    async def _inject_opencode_auth(self) -> None:
        """Inject OpenCode OAuth credentials if provided.
        
        OpenCode stores auth in ~/.local/share/opencode/auth.json
        """
        if not self.session.opencode_auth:
            return
        
        auth_json = json.dumps(self.session.opencode_auth)
        await self.sandbox.exec.aio(
            "bash", "-c",
            f"mkdir -p /root/.local/share/opencode && echo '{auth_json}' > /root/.local/share/opencode/auth.json"
        )
    
    async def _seed_memory_if_needed(self) -> None:
        """Seed memory with initial entities if this is first use for this repo."""
        # Check if memory file exists
        proc = await self.sandbox.exec.aio(
            "bash", "-c",
            "test -f /root/.mcp-memory/memory.jsonl && echo 'exists' || echo 'empty'"
        )
        
        stdout = proc.stdout.read().strip()
        
        if stdout == "empty":
            # First time - copy seed file to memory location
            # The memory MCP server will read from this file
            await self.sandbox.exec.aio(
                "bash", "-c",
                """
                if [ -f /app/memory-seed.json ]; then
                    # Convert seed JSON to JSONL format for memory server
                    python3 << 'EOF'
import json

with open('/app/memory-seed.json') as f:
    seed = json.load(f)

with open('/root/.mcp-memory/memory.jsonl', 'w') as out:
    # Write entities
    for entity in seed.get('entities', []):
        record = {
            'type': 'entity',
            'name': entity['name'],
            'entityType': entity['entityType'],
            'observations': entity.get('observations', [])
        }
        out.write(json.dumps(record) + '\\n')
    
    # Write relations
    for relation in seed.get('relations', []):
        record = {
            'type': 'relation',
            'from': relation['from'],
            'to': relation['to'],
            'relationType': relation['relationType']
        }
        out.write(json.dumps(record) + '\\n')

print('Memory seeded successfully')
EOF
                fi
                """
            )
    
    async def _start_opencode(self) -> None:
        """Start OpenCode in server mode on port 8080."""
        # Start OpenCode server in background
        await self.sandbox.exec.aio(
            "bash", "-c",
            f"cd {self.session.repo_path} && nohup opencode serve --port 8080 > /tmp/opencode.log 2>&1 &"
        )
        
        # Wait for server to be ready (up to 30 seconds)
        for attempt in range(30):
            proc = await self.sandbox.exec.aio(
                "bash", "-c",
                "curl -s http://localhost:8080/health || echo 'not_ready'"
            )
            stdout = proc.stdout.read().strip()
            
            if stdout != "not_ready" and "error" not in stdout.lower():
                self._opencode_ready = True
                return
            
            await self._sleep(1)
        
        # Check logs for errors
        proc = await self.sandbox.exec.aio("cat", "/tmp/opencode.log")
        logs = proc.stdout.read()
        raise RuntimeError(f"OpenCode server failed to start. Logs:\n{logs}")
    
    async def _sleep(self, seconds: float) -> None:
        """Sleep helper (uses asyncio in async context)."""
        import asyncio
        await asyncio.sleep(seconds)
    
    async def send_prompt(self, prompt: str) -> str:
        """Send a prompt to the OpenCode server.
        
        Args:
            prompt: The task or question for the agent
            
        Returns:
            Agent response as string
            
        Raises:
            RuntimeError: If OpenCode is not ready or request fails
        """
        if not self._opencode_ready:
            raise RuntimeError("OpenCode server is not ready")
        
        payload = json.dumps({"prompt": prompt})
        
        proc = await self.sandbox.exec.aio(
            "curl", "-s", "-X", "POST",
            "-H", "Content-Type: application/json",
            "-d", payload,
            "http://localhost:8080/api/prompt"
        )
        
        return proc.stdout.read()
    
    async def get_opencode_logs(self) -> str:
        """Get OpenCode server logs for debugging."""
        proc = await self.sandbox.exec.aio("cat", "/tmp/opencode.log")
        return proc.stdout.read()
    
    async def exec(self, *args: str, workdir: Optional[str] = None) -> ExecutionResult:
        """Execute a command in the sandbox.
        
        Args:
            *args: Command and arguments
            workdir: Working directory (defaults to repo path)
            
        Returns:
            ExecutionResult with output
        """
        if not self.sandbox:
            raise RuntimeError("Sandbox not started")
        
        start_time = time.time()
        cwd = workdir or self.session.repo_path
        
        try:
            proc = await self.sandbox.exec.aio(*args, workdir=cwd)
            duration = time.time() - start_time
            
            return ExecutionResult(
                returncode=proc.returncode,
                stdout=proc.stdout.read(),
                stderr=proc.stderr.read(),
                duration_secs=duration,
                sandbox_id=self.sandbox.object_id,
                status=ExecutionStatus.SUCCESS if proc.returncode == 0 else ExecutionStatus.ERROR,
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return ExecutionResult(
                returncode=-1,
                stdout="",
                stderr=str(e),
                duration_secs=duration,
                sandbox_id=self.sandbox.object_id if self.sandbox else "",
                status=ExecutionStatus.CRASHED,
                error_message=str(e),
            )
    
    async def terminate(self) -> None:
        """Gracefully terminate the sandbox.
        
        Commits memory volume changes before termination.
        """
        if self.sandbox:
            try:
                # Commit volume changes
                self._memory_volume.commit()
            except Exception:
                pass  # Best effort
            
            try:
                await self.sandbox.terminate.aio()
            except Exception:
                pass  # Best effort
            
            self.sandbox = None
            self._opencode_ready = False
    
    @property
    def is_running(self) -> bool:
        """Check if sandbox is running."""
        return self.sandbox is not None
    
    @property
    def repo_path(self) -> str:
        """Get the repository path in the sandbox."""
        return self.session.repo_path
