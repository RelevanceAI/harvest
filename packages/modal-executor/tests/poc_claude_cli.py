"""
POC Test: Claude Code CLI + OAuth in Modal Containers

Tests whether Claude Code CLI can authenticate with CLAUDE_CODE_OAUTH_TOKEN
in a headless Modal container environment.

Critical questions this answers:
1. Does OAuth work in headless containers?
2. Can we parse JSON stream output?
3. What's the latency?
4. Does conversation continuity work?

Usage:
    # 1. Create Modal secret with OAuth token
    modal secret create claude-code-oauth CLAUDE_CODE_OAUTH_TOKEN=<your-token>

    # 2. Run the test
    modal run tests/poc_claude_cli.py
"""

import asyncio
import json
import os
import modal

from poc_image import poc_image

app = modal.App("claude-cli-poc")


class ClaudeCodeCLIWrapper:
    """Proof-of-concept wrapper for Claude Code CLI with OAuth"""

    @staticmethod
    async def execute(
        prompt: str,
        oauth_token: str,
        cwd: str = "/test-repo"
    ) -> dict:
        """
        Execute a single prompt via Claude Code CLI.

        Returns dict with:
        - success: bool
        - response: str (parsed text response)
        - raw_output: str (full JSON stream)
        - duration_secs: float
        - error: str (if failed)
        """
        import time
        start_time = time.time()

        # Set OAuth token in environment
        env = os.environ.copy()
        env['CLAUDE_CODE_OAUTH_TOKEN'] = oauth_token

        try:
            # Invoke Claude Code CLI in headless mode
            proc = await asyncio.create_subprocess_exec(
                "claude",
                "-p", prompt,
                "--output-format", "stream-json",
                "--dangerously-skip-permissions",
                cwd=cwd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await proc.communicate()
            duration = time.time() - start_time

            # Check if authentication failed
            stderr_text = stderr.decode()
            if "unauthorized" in stderr_text.lower() or "authentication" in stderr_text.lower():
                return {
                    "success": False,
                    "error": f"Authentication failed: {stderr_text}",
                    "duration_secs": duration
                }

            # Parse JSON stream
            raw_output = stdout.decode()
            response_text = parse_json_stream(raw_output)

            return {
                "success": True,
                "response": response_text,
                "raw_output": raw_output,
                "duration_secs": duration,
                "return_code": proc.returncode
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "duration_secs": time.time() - start_time
            }


def parse_json_stream(stream: str) -> str:
    """
    Parse Claude Code CLI JSON stream output.

    Format appears to be newline-delimited JSON events.
    Extract text content from assistant messages.
    """
    lines = stream.strip().split('\n')
    text_parts = []

    for line in lines:
        if not line.strip():
            continue

        try:
            event = json.loads(line)

            # Look for text content in various possible formats
            # (Need to discover actual format through testing)
            if isinstance(event, dict):
                # Try common patterns
                if 'type' in event and event['type'] == 'message':
                    if 'content' in event:
                        text_parts.append(str(event['content']))
                elif 'text' in event:
                    text_parts.append(event['text'])
                elif 'content' in event and isinstance(event['content'], str):
                    text_parts.append(event['content'])

        except json.JSONDecodeError:
            # Skip invalid JSON lines
            continue

    return '\n'.join(text_parts) if text_parts else stream


@app.function(
    image=poc_image,
    secrets=[modal.Secret.from_name("claude-code-oauth")],
    timeout=300
)
async def test_claude_cli_oauth():
    """
    Test if Claude Code CLI works with OAuth in Modal container.

    Expected secret format:
    {
        "CLAUDE_CODE_OAUTH_TOKEN": "your-oauth-token"
    }
    """
    oauth_token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")

    if not oauth_token:
        return {
            "error": "CLAUDE_CODE_OAUTH_TOKEN not found in environment",
            "success": False
        }

    # Test 1: Simple prompt
    print("Test 1: Basic prompt execution...")
    result1 = await ClaudeCodeCLIWrapper.execute(
        prompt="Say 'Hello from Modal' and nothing else",
        oauth_token=oauth_token
    )

    print(f"✓ Test 1 Result: {result1}")

    # Test 2: Multi-turn simulation (separate invocations)
    print("\nTest 2: Multi-turn conversation simulation...")
    result2a = await ClaudeCodeCLIWrapper.execute(
        prompt="Remember this number: 42. Say 'Remembered'",
        oauth_token=oauth_token
    )

    result2b = await ClaudeCodeCLIWrapper.execute(
        prompt="What number did I just tell you to remember?",
        oauth_token=oauth_token
    )

    print(f"✓ Test 2a Result: {result2a}")
    print(f"✓ Test 2b Result: {result2b}")
    print(f"  Note: Expected to fail (no continuity) - result2b won't know '42'")

    # Test 3: Performance check
    print("\nTest 3: Performance (5 sequential calls)...")
    durations = []
    for i in range(5):
        result = await ClaudeCodeCLIWrapper.execute(
            prompt=f"Count to {i+1}",
            oauth_token=oauth_token
        )
        durations.append(result.get('duration_secs', 0))

    avg_duration = sum(durations) / len(durations)
    print(f"✓ Average latency: {avg_duration:.2f}s")
    print(f"  Min: {min(durations):.2f}s, Max: {max(durations):.2f}s")

    return {
        "test1_basic": result1,
        "test2_continuity": {
            "first": result2a,
            "second": result2b,
            "has_continuity": "42" in result2b.get('response', '')
        },
        "test3_performance": {
            "avg_latency_secs": avg_duration,
            "min_latency_secs": min(durations),
            "max_latency_secs": max(durations),
            "all_durations": durations
        }
    }


@app.local_entrypoint()
def main():
    """Run the POC test"""
    print("🧪 Claude Code CLI + OAuth POC Test")
    print("=" * 60)

    result = test_claude_cli_oauth.remote()

    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS")
    print("=" * 60)

    print(json.dumps(result, indent=2))

    # Assess viability
    print("\n" + "=" * 60)
    print("✅ VIABILITY ASSESSMENT")
    print("=" * 60)

    test1 = result.get('test1_basic', {})
    test2 = result.get('test2_continuity', {})
    test3 = result.get('test3_performance', {})

    print(f"✓ Authentication works: {test1.get('success', False)}")
    print(f"✗ Conversation continuity: {test2.get('has_continuity', False)}")
    print(f"⚠ Average latency: {test3.get('avg_latency_secs', 0):.2f}s")

    if test1.get('success'):
        print("\n🎉 PROCEED: Claude Code CLI + OAuth works in Modal!")
        print("⚠️  WARNING: No conversation continuity - need workaround")
    else:
        print("\n🛑 BLOCKED: Claude Code CLI + OAuth does NOT work")
        print(f"   Error: {test1.get('error', 'Unknown')}")
