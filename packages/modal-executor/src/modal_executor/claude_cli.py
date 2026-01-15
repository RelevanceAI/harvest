"""Async wrapper for Claude Code CLI with streaming support.

This module provides a streaming wrapper around the Claude Code CLI tool.
Handles:
- OAuth token authentication
- Stream-json output parsing
- Async iteration for real-time chunks
- Error handling and exit codes

Architecture:
- Runs `claude --print --output-format stream-json` as subprocess
- Parses newline-delimited JSON events
- Yields text chunks as they arrive
- Tracks returncode for error handling
"""

import asyncio
import json
import logging
import os
from typing import AsyncIterator, Optional

logger = logging.getLogger(__name__)


class ClaudeCliWrapper:
    """Stream-capable wrapper for Claude Code CLI.

    Example:
        cli = ClaudeCliWrapper()
        async for chunk in cli.stream_prompt(
            prompt="Say hello",
            oauth_token=os.environ["CLAUDE_CODE_OAUTH_TOKEN"],
            cwd="/workspace"
        ):
            print(chunk, end="")
    """

    def __init__(self):
        self.last_returncode: Optional[int] = None
        self.last_stderr: Optional[str] = None

    async def stream_prompt(
        self,
        prompt: str,
        oauth_token: str,
        cwd: str = "/workspace",
        timeout: int = 1800,  # 30 minutes default
    ) -> AsyncIterator[str]:
        """Stream Claude CLI output in real-time.

        Args:
            prompt: The prompt to send to Claude
            oauth_token: CLAUDE_CODE_OAUTH_TOKEN for authentication
            cwd: Working directory for the command
            timeout: Maximum execution time in seconds (default: 30min)

        Yields:
            Text chunks as they arrive from Claude

        Raises:
            RuntimeError: If Claude CLI fails or exits with non-zero code
            asyncio.TimeoutError: If execution exceeds timeout

        Example:
            async for chunk in cli.stream_prompt("Count to 3", token):
                print(chunk, end="")
        """
        env = os.environ.copy()
        env["CLAUDE_CODE_OAUTH_TOKEN"] = oauth_token
        env["HOME"] = "/root"

        logger.info(f"Starting Claude CLI with prompt: {prompt[:100]}...")

        try:
            proc = await asyncio.create_subprocess_exec(
                "claude",
                "--print",
                "--output-format",
                "stream-json",
                prompt,
                cwd=cwd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Stream JSON chunks from stdout
            async for chunk in self._stream_json_chunks(proc, timeout):
                yield chunk

            # Wait for process to complete and capture returncode
            await asyncio.wait_for(proc.wait(), timeout=10)
            self.last_returncode = proc.returncode

            # Capture stderr for debugging
            if proc.stderr:
                stderr_data = await proc.stderr.read()
                self.last_stderr = stderr_data.decode("utf-8", errors="replace")

            # Check for errors
            if self.last_returncode != 0:
                error_msg = f"Claude CLI exited with code {self.last_returncode}"
                if self.last_stderr:
                    error_msg += f": {self.last_stderr[:500]}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)

            logger.info("Claude CLI completed successfully (returncode=0)")

        except asyncio.TimeoutError:
            logger.error(f"Claude CLI timed out after {timeout}s")
            if proc:
                proc.kill()
                await proc.wait()
            raise
        except Exception as e:
            logger.error(f"Claude CLI error: {e}")
            raise

    async def _stream_json_chunks(
        self, proc: asyncio.subprocess.Process, timeout: int
    ) -> AsyncIterator[str]:
        """Stream and parse JSON chunks from Claude CLI stdout.

        Args:
            proc: The subprocess running Claude CLI
            timeout: Maximum time to wait for chunks

        Yields:
            Parsed text chunks from JSON events
        """
        if proc.stdout is None:
            return

        try:
            # Read lines with timeout to prevent hanging
            async for line in self._read_lines_with_timeout(proc.stdout, timeout):
                if not line.strip():
                    continue

                try:
                    event = json.loads(line)
                    text = self._extract_text(event)
                    if text:
                        yield text
                except json.JSONDecodeError as e:
                    # Log but continue - some lines might not be JSON
                    logger.debug(f"Failed to parse JSON line: {e}")
                    continue

        except asyncio.TimeoutError:
            logger.error("Timeout while streaming chunks")
            raise

    async def _read_lines_with_timeout(
        self, stream: asyncio.StreamReader, timeout: int
    ) -> AsyncIterator[str]:
        """Read lines from stream with per-line timeout.

        Args:
            stream: Async stream to read from
            timeout: Timeout for each readline operation

        Yields:
            Decoded lines from the stream
        """
        while True:
            try:
                line_bytes = await asyncio.wait_for(stream.readline(), timeout=timeout)
                if not line_bytes:
                    # EOF reached
                    break
                yield line_bytes.decode("utf-8", errors="replace")
            except asyncio.TimeoutError:
                logger.warning("Timeout reading line from Claude CLI")
                raise

    def _extract_text(self, event: dict) -> str:
        """Parse Claude CLI JSON stream events.

        The Claude CLI emits newline-delimited JSON events in various formats.
        This extracts text content from known event types.

        Args:
            event: Parsed JSON event from Claude CLI

        Returns:
            Extracted text content, or empty string if not a text event

        Known event formats (subject to change):
        - {"type": "content_block_delta", "delta": {"text": "..."}}
        - {"text": "..."}
        - ... (format may evolve - check with validate_claude_cli.py)
        """
        # Format 1: content_block_delta (streaming API format)
        if event.get("type") == "content_block_delta":
            delta = event.get("delta", {})
            return delta.get("text", "")

        # Format 2: Direct text field
        if "text" in event:
            return event["text"]

        # Format 3: content field (fallback)
        if "content" in event and isinstance(event["content"], str):
            return event["content"]

        # Unknown format - return empty
        return ""
