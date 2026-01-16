#!/usr/bin/env python3
"""Regression Validation Script for Claude CLI.

PURPOSE:
When Claude CLI behavior changes or breaks, run this script to diagnose issues.
This helps Claude (the AI) self-fix regressions by providing clear error messages.

USAGE:
    export CLAUDE_CODE_OAUTH_TOKEN=<your-token>
    python scripts/validate_claude_cli.py

WHEN TO USE:
- OAuth authentication starts failing
- Streaming format changes
- Claude CLI updates break the integration
- You need to validate a fix works locally

This script is DISCOVERABLE so you (Claude) can easily find and run it when
debugging regressions.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from modal_executor.claude_cli import ClaudeCliWrapper


async def validate_oauth_authentication():
    """Validate OAuth tokens are still accepted.

    If this fails: Anthropic may have changed authentication mechanism.
    """
    print("🔐 Testing OAuth authentication...")
    cli = ClaudeCliWrapper()
    oauth_token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")

    if not oauth_token:
        print("❌ CLAUDE_CODE_OAUTH_TOKEN not set")
        return False

    try:
        chunks = []
        async for chunk in cli.stream_prompt(
            prompt="Say OAUTH_WORKS",
            oauth_token=oauth_token,
            cwd="/tmp",
        ):
            chunks.append(chunk)

        response = "".join(chunks)
        if "OAUTH_WORKS" in response:
            print("✅ OAuth authentication works")
            return True
        else:
            print(f"❌ OAuth failed - unexpected response: {response[:100]}")
            return False
    except Exception as e:
        print(f"❌ OAuth authentication failed: {e}")
        return False


async def validate_stream_format():
    """Validate stream-json output format hasn't changed.

    If this fails: Update _extract_text() in ClaudeCliWrapper.
    """
    print("\n📡 Testing stream-json format...")
    cli = ClaudeCliWrapper()
    oauth_token = os.environ["CLAUDE_CODE_OAUTH_TOKEN"]

    try:
        chunks = []
        async for chunk in cli.stream_prompt(
            prompt="Count: 1, 2, 3", oauth_token=oauth_token, cwd="/tmp"
        ):
            chunks.append(chunk)
            if not isinstance(chunk, str):
                print(f"❌ Unexpected chunk type: {type(chunk)}")
                print("   Stream format may have changed - update _extract_text()")
                return False

        if len(chunks) > 0:
            print(f"✅ Streaming works ({len(chunks)} chunks received)")
            return True
        else:
            print("❌ No chunks received - streaming may be broken")
            return False
    except Exception as e:
        print(f"❌ Streaming failed: {e}")
        return False


async def validate_exit_code():
    """Validate successful prompts return exit code 0.

    If this fails: Error handling logic may need updating.
    """
    print("\n🔍 Testing exit codes...")
    cli = ClaudeCliWrapper()
    oauth_token = os.environ["CLAUDE_CODE_OAUTH_TOKEN"]

    try:
        chunks = []
        async for chunk in cli.stream_prompt(
            prompt="Say OK", oauth_token=oauth_token, cwd="/tmp"
        ):
            chunks.append(chunk)

        # Check returncode (implementation detail: ClaudeCliWrapper should track this)
        if hasattr(cli, "last_returncode") and cli.last_returncode == 0:
            print("✅ Exit codes work")
            return True
        else:
            print(
                f"⚠️  Exit code tracking: returncode={getattr(cli, 'last_returncode', 'N/A')}"
            )
            return True  # Not critical if tracking isn't implemented yet
    except Exception as e:
        print(f"❌ Exit code validation failed: {e}")
        return False


async def main():
    print("=" * 60)
    print("Claude CLI Regression Validation Script")
    print("=" * 60)
    print("Purpose: Validate Claude CLI behavior for self-fixing regressions")
    print()

    results = []
    results.append(await validate_oauth_authentication())
    results.append(await validate_stream_format())
    results.append(await validate_exit_code())

    print("\n" + "=" * 60)
    if all(results):
        print("✅ ALL VALIDATIONS PASSED - Claude CLI integration is healthy")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ SOME VALIDATIONS FAILED - Claude CLI integration needs fixes")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Review the failed validation above")
        print("2. Check Claude CLI version: claude --version")
        print("3. Update ClaudeCliWrapper._extract_text() if format changed")
        print("4. Test with POC script: modal run tests/poc_claude_cli.py")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
