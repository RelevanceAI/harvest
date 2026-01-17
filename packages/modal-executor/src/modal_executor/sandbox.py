"""Sandbox wrapper for executing code in Modal.

This module provides the SandboxExecutor for basic code execution and
HarvestSandbox for full agent sessions with Claude Code CLI, git, and MCP servers.
"""

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, field
from os import PathLike
from typing import AsyncIterator, Optional, Union

from modal import Volume
from modal.cloud_bucket_mount import CloudBucketMount

import modal

from modal_executor.app import app
from modal_executor.claude_cli import ClaudeCliWrapper
from modal_executor.images import get_base_image
from modal_executor.session_state import SessionState
from modal_executor.types import ExecutionResult, ExecutionStatus
from modal_executor.volume import get_state_volume

logger = logging.getLogger(__name__)


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
            volumes: dict[Union[str, PathLike], Union[Volume, CloudBucketMount]] = {}
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
            status = (
                ExecutionStatus.SUCCESS if returncode == 0 else ExecutionStatus.ERROR
            )
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
        code = f"""
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
"""
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

    # Credentials (injected at runtime) - excluded from repr for security
    github_token: str = field(default="", repr=False)
    claude_oauth_token: str = field(
        default="", repr=False
    )  # CLAUDE_CODE_OAUTH_TOKEN for team subscription

    # Optional credentials (for MCP servers) - excluded from repr for security
    gemini_api_key: Optional[str] = field(default=None, repr=False)
    sentry_auth_token: Optional[str] = field(default=None, repr=False)
    linear_api_key: Optional[str] = field(default=None, repr=False)

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
    - Claude Code CLI runs with OAuth authentication
    - Session state persists via SQLite in Modal volume
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
            claude_oauth_token="oauth_xxx",
        )

        sandbox = HarvestSandbox(session)
        await sandbox.start()

        async for chunk in sandbox.send_prompt_stream("Fix the failing tests"):
            print(chunk, end="")

        await sandbox.terminate()
    """

    def __init__(self, session: HarvestSession):
        """Initialize sandbox manager.

        Args:
            session: Session configuration with credentials and repo info
        """
        self.session = session
        self.sandbox: Optional[modal.Sandbox] = None

        # Claude CLI components
        self.cli_wrapper = ClaudeCliWrapper()
        self.session_state: Optional[SessionState] = None
        self._claude_cli_ready = False

        # Per-repo memory volume
        self._memory_volume = modal.Volume.from_name(
            session.memory_volume_name, create_if_missing=True
        )

    def _get_sandbox(self) -> modal.Sandbox:
        """Get the sandbox, raising if not started."""
        if self.sandbox is None:
            raise RuntimeError("Sandbox not started. Call start() first.")
        return self.sandbox

    async def start(self, timeout_secs: int = 3600) -> "HarvestSandbox":
        """Start the sandbox with full configuration.

        Args:
            timeout_secs: Maximum session duration (default 1 hour)

        Returns:
            Self for chaining

        Raises:
            RuntimeError: If sandbox fails to start or Claude CLI is unavailable
        """
        # Build environment variables
        env_vars: dict[str, str | None] = {
            "GITHUB_TOKEN": self.session.github_token,
            "CLAUDE_CODE_OAUTH_TOKEN": self.session.claude_oauth_token,
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

        # Initialize session state (SQLite-backed)
        self.session_state = SessionState(session_id=self.session.session_id)

        # Setup sequence - configure git BEFORE cloning for credential security
        await self._configure_git()
        await self._clone_repo()
        await self._seed_memory_if_needed()
        await self._initialize_claude_cli()

        return self

    async def _clone_repo(self) -> None:
        """Clone the repository to /workspace/{repo-name}.

        Uses credential helper configured in _configure_git() - no token in URL.
        """
        # Use HTTPS URL without embedded token - credential helper provides auth
        repo_url = (
            f"https://github.com/{self.session.repo_owner}/{self.session.repo_name}.git"
        )

        # Clone with specific branch
        proc = await self._get_sandbox().exec.aio(
            "git",
            "clone",
            "--branch",
            self.session.branch,
            repo_url,
            self.session.repo_path,
        )

        if proc.returncode != 0:
            stderr = proc.stderr.read()
            raise RuntimeError(f"Failed to clone repository: {stderr}")

    async def _configure_git(self) -> None:
        """Configure git identity and credentials.

        Uses credential helper for HTTPS, adds "(Harvest)" suffix for attribution.
        Credentials are stored before cloning to avoid token in command args.
        """
        # Configure credential helper
        await self._get_sandbox().exec.aio(
            "git", "config", "--global", "credential.helper", "store"
        )

        # Write credentials file with secure permissions
        # Use printf instead of echo to avoid shell interpretation issues
        creds = f"https://x-access-token:{self.session.github_token}@github.com"
        await self._get_sandbox().exec.aio(
            "bash",
            "-c",
            f"printf '%s\\n' '{creds}' > ~/.git-credentials && chmod 600 ~/.git-credentials",
        )

        # Identity with (Harvest) suffix for attribution
        await self._get_sandbox().exec.aio(
            "git", "config", "--global", "user.email", self.session.user_email
        )
        await self._get_sandbox().exec.aio(
            "git",
            "config",
            "--global",
            "user.name",
            f"{self.session.user_name} (Harvest)",
        )

        # Safe defaults
        await self._get_sandbox().exec.aio(
            "git", "config", "--global", "push.autoSetupRemote", "true"
        )
        await self._get_sandbox().exec.aio(
            "git", "config", "--global", "init.defaultBranch", "main"
        )

    async def _seed_memory_if_needed(self) -> None:
        """Seed memory with initial entities if this is first use for this repo."""
        # Check if memory file exists
        proc = await self._get_sandbox().exec.aio(
            "bash",
            "-c",
            "test -f /root/.mcp-memory/memory.jsonl && echo 'exists' || echo 'empty'",
        )

        stdout = proc.stdout.read().strip()

        if stdout == "empty":
            # First time - copy seed file to memory location
            # The memory MCP server will read from this file
            await self._get_sandbox().exec.aio(
                "bash",
                "-c",
                """
                if [ -f /app/memory-seed.json ]; then
                    # Convert seed JSON to JSONL format for memory server
                    # Using heredoc to avoid creating intermediate .py files for this one-time conversion
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
                """,
            )

    async def _get_claude_version_safe(self) -> str:
        """Get Claude CLI version with robust parsing and fallback.

        Returns:
            Version string (e.g., "2.1.3")

        Raises:
            RuntimeError: If Claude CLI is not available
        """
        proc = await self._get_sandbox().exec.aio("claude", "--version")

        if proc.returncode != 0:
            stderr = proc.stderr.read()
            raise RuntimeError(f"Claude CLI not available: {stderr}")

        version_output = proc.stdout.read().strip()

        # Robust version extraction
        # Handles formats: "2.1.3", "Claude CLI 2.1.3", "Version: 2.1.3", etc.
        match = re.search(r"(\d+\.\d+\.\d+)", version_output)

        if match:
            version = match.group(1)
            logger.info(f"Detected Claude CLI version: {version}")
            return version
        else:
            # Fallback to a recent known-good version if parsing fails
            logger.warning(
                f"Could not parse version from: {version_output}. "
                "Falling back to default version 2.1.3"
            )
            return "2.1.3"

    async def _write_json_atomic(self, path: str, data: dict) -> None:
        """Write JSON file atomically to prevent corruption.

        Args:
            path: Absolute path to JSON file
            data: Dictionary to serialize as JSON
        """
        content = json.dumps(data, indent=2)

        # Write to temp file then rename (atomic on most filesystems)
        # Use bash to handle temp file creation and atomic rename
        await self._get_sandbox().exec.aio(
            "bash",
            "-c",
            f"cat > {path}.tmp << 'JSONEOF'\n{content}\nJSONEOF\n&& mv {path}.tmp {path}",
        )

    async def _create_main_config(self, version: str) -> None:
        """Create ~/.claude.json with onboarding and trust settings.

        Args:
            version: Claude CLI version string

        Note:
            Trusts /workspace parent directory to allow working with multiple
            repos (/workspace/a, /workspace/b, etc.) and repos cloned during
            execution. Claude's trust model should respect parent directory trust
            when running in subdirectories.
        """
        config = {
            "hasCompletedOnboarding": True,
            "lastOnboardingVersion": version,
            "bypassPermissionsModeAccepted": True,
            "projects": {
                "/workspace": {"hasTrustDialogAccepted": True, "allowedTools": []}
            },
        }

        await self._write_json_atomic("/root/.claude.json", config)
        logger.debug("Created ~/.claude.json with /workspace trust")

    async def _create_prefs_config(self) -> None:
        """Create ~/.claude/.claude.json with preferences (theme)."""
        config = {"hasCompletedOnboarding": True, "theme": "dark"}

        await self._write_json_atomic("/root/.claude/.claude.json", config)
        logger.debug("Created ~/.claude/.claude.json")

    async def _create_user_settings(self) -> None:
        """Create ~/.claude/settings.json with permissions, hooks, and plugins."""
        # Build SessionStart hooks with absolute paths
        # Repo is already cloned at this point, so we can reference repo_path
        repo_claude_md = f"{self.session.repo_path}/.claude/CLAUDE.md"
        repo_autonomous_md = f"{self.session.repo_path}/docs/ai/autonomous-agent.md"

        hooks = [
            # Always load Harvest's core agent instructions (baked into image)
            {"type": "command", "command": "cat /app/AGENTS.md"},
            # Load repo's CLAUDE.md if it exists
            {
                "type": "command",
                "command": f"[ -f {repo_claude_md} ] && cat {repo_claude_md} || true",
            },
            # Load repo's autonomous-agent.md if it exists
            {
                "type": "command",
                "command": f"[ -f {repo_autonomous_md} ] && cat {repo_autonomous_md} || true",
            },
        ]

        config = {
            "permissions": {"allow": ["*"], "defaultMode": "bypassPermissions"},
            "hooks": {"SessionStart": [{"hooks": hooks}]},
            "enabledPlugins": {"superpowers@claude-plugins-official": True},
        }

        await self._write_json_atomic("/root/.claude/settings.json", config)
        logger.debug("Created ~/.claude/settings.json")

    async def _initialize_claude_cli(self) -> None:
        """Initialize Claude CLI configuration files at runtime.

        Generates all config files dynamically to ensure compatibility
        with the installed Claude CLI version. Implements atomic writes
        for reliability.

        Creates:
        - ~/.claude.json: Main state (onboarding, trust, version)
        - ~/.claude/.claude.json: Preferences (theme)
        - ~/.claude/settings.json: User settings (permissions, hooks, plugins)

        Raises:
            RuntimeError: If Claude CLI is not available or config creation fails
        """
        # Detect Claude CLI version with robust parsing
        version = await self._get_claude_version_safe()

        # Generate all config files dynamically
        await self._create_main_config(version)
        await self._create_prefs_config()
        await self._create_user_settings()

        logger.info(f"Claude CLI configured for version {version}")
        self._claude_cli_ready = True

    async def _sleep(self, seconds: float) -> None:
        """Sleep helper (uses asyncio in async context)."""
        await asyncio.sleep(seconds)

    async def send_prompt_stream(self, prompt: str) -> AsyncIterator[str]:
        """Send a prompt to Claude CLI and stream the response.

        Args:
            prompt: The task or question for the agent

        Yields:
            Text chunks as they arrive from Claude

        Raises:
            RuntimeError: If Claude CLI is not ready or request fails

        Example:
            async for chunk in sandbox.send_prompt_stream("Fix the bug"):
                print(chunk, end="")
        """
        if not self._claude_cli_ready:
            raise RuntimeError("Claude CLI is not ready. Call start() first.")

        if self.session_state is None:
            raise RuntimeError("Session state not initialized")

        # Build context-enriched prompt with conversation history
        context_prompt = self.session_state.build_context_prompt(prompt)

        # Stream response chunks
        response_parts = []
        async for chunk in self.cli_wrapper.stream_prompt(
            prompt=context_prompt,
            oauth_token=self.session.claude_oauth_token,
            cwd=self.session.repo_path,
        ):
            response_parts.append(chunk)
            yield chunk

        # Save exchange to session state for continuity
        full_response = "".join(response_parts)
        self.session_state.add_exchange(prompt, full_response)

        logger.info(
            f"Prompt completed: {len(response_parts)} chunks, {len(full_response)} chars"
        )

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
            proc = await self._get_sandbox().exec.aio(*args, workdir=cwd)
            duration = time.time() - start_time

            return ExecutionResult(
                returncode=proc.returncode,
                stdout=proc.stdout.read(),
                stderr=proc.stderr.read(),
                duration_secs=duration,
                sandbox_id=self.sandbox.object_id,
                status=(
                    ExecutionStatus.SUCCESS
                    if proc.returncode == 0
                    else ExecutionStatus.ERROR
                ),
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

        Closes session state and commits memory volume changes before termination.
        """
        if self.sandbox:
            try:
                # Close session state database connection
                if self.session_state:
                    self.session_state.close()
                    self.session_state = None
            except Exception:
                pass  # Best effort

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
            self._claude_cli_ready = False

    @property
    def is_running(self) -> bool:
        """Check if sandbox is running."""
        return self.sandbox is not None

    @property
    def repo_path(self) -> str:
        """Get the repository path in the sandbox."""
        return self.session.repo_path
