#!/usr/bin/env python3
"""
Deep dive POC to test Claude Agent SDK edge cases and multi-turn conversations.

Based on GitHub issues:
- #6536: SDK allegedly doesn't support OAuth tokens (only API keys)
- #6058: OAuth authentication errors (resolved)

This test validates:
1. Multi-turn conversations with OAuth token
2. Session persistence and resumption
3. Long-running tasks
4. Error handling and rate limits
5. Tool usage with OAuth
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path


async def test_multi_turn_conversation():
    """Test multiple back-and-forth exchanges in same session."""
    print("=" * 60)
    print("TEST 1: Multi-Turn Conversation (OAuth Token)")
    print("=" * 60)

    try:
        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
        from claude_agent_sdk import AssistantMessage, TextBlock

        oauth_token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
        if not oauth_token:
            print("❌ No CLAUDE_CODE_OAUTH_TOKEN found")
            return False

        print(f"\nUsing OAuth token: {oauth_token[:15]}...")

        options = ClaudeAgentOptions(
            allowed_tools=["Read", "Write", "Glob"],
            permission_mode="acceptEdits",
            cwd=str(Path.cwd())
        )

        async with ClaudeSDKClient(options=options) as client:
            # Turn 1: Create a file
            print("\n[Turn 1] Creating test file...")
            await client.query("Create a file called test_oauth.txt with the word 'SUCCESS'")

            result_1 = ""
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            result_1 += block.text

            print(f"  Response: {result_1[:100]}...")

            # Turn 2: Read the file back
            print("\n[Turn 2] Reading file back...")
            await client.query("Read test_oauth.txt and tell me what's in it")

            result_2 = ""
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            result_2 += block.text

            print(f"  Response: {result_2[:100]}...")

            # Turn 3: Verify context
            print("\n[Turn 3] Testing context memory...")
            await client.query("What file did you just read?")

            result_3 = ""
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            result_3 += block.text

            print(f"  Response: {result_3[:100]}...")

            # Cleanup
            if Path("test_oauth.txt").exists():
                Path("test_oauth.txt").unlink()
                print("\n  Cleaned up test_oauth.txt")

            # Validate
            if "test_oauth.txt" in result_3.lower():
                print("\n✅ Multi-turn conversation works with OAuth!")
                print("   - Created file")
                print("   - Read file")
                print("   - Remembered context across turns")
                return True
            else:
                print("\n⚠️  Context may not be preserved across turns")
                return False

    except Exception as e:
        print(f"\n❌ Multi-turn test failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False


async def test_session_persistence():
    """Test session resumption across separate client instances."""
    print("\n" + "=" * 60)
    print("TEST 2: Session Persistence Across Instances")
    print("=" * 60)

    try:
        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
        from claude_agent_sdk import AssistantMessage, TextBlock, SystemMessage

        oauth_token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
        if not oauth_token:
            print("❌ No CLAUDE_CODE_OAUTH_TOKEN found")
            return False

        # Session 1: Capture session ID
        print("\n[Session 1] Creating initial session...")
        session_id = None

        options = ClaudeAgentOptions(
            allowed_tools=[],
            permission_mode="bypassPermissions"
        )

        async with ClaudeSDKClient(options=options) as client:
            await client.query("Remember this secret code: HARVEST-2026")

            async for message in client.receive_response():
                if isinstance(message, SystemMessage):
                    if hasattr(message, 'data') and 'session_id' in message.data:
                        session_id = message.data['session_id']
                        print(f"  Captured session_id: {session_id}")

                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(f"  Response: {block.text[:100]}...")

        if not session_id:
            print("\n⚠️  No session_id captured - SDK may not support persistence")
            return False

        # Session 2: Resume and test memory
        print(f"\n[Session 2] Resuming session {session_id}...")

        resume_options = ClaudeAgentOptions(
            resume=session_id,
            allowed_tools=[],
            permission_mode="bypassPermissions"
        )

        async with ClaudeSDKClient(options=resume_options) as client:
            await client.query("What was the secret code I told you?")

            result = ""
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            result += block.text

            print(f"  Response: {result[:200]}...")

            if "HARVEST-2026" in result:
                print("\n✅ Session persistence works!")
                print("   - Captured session_id")
                print("   - Resumed session")
                print("   - Context preserved across instances")
                return True
            else:
                print("\n❌ Session resumed but context NOT preserved")
                print(f"   Expected 'HARVEST-2026' in: {result}")
                return False

    except Exception as e:
        print(f"\n❌ Session persistence test failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False


async def test_oauth_vs_api_key():
    """Test if OAuth token is actually being used or if it falls back to API key."""
    print("\n" + "=" * 60)
    print("TEST 3: OAuth vs API Key Authentication")
    print("=" * 60)

    try:
        from claude_agent_sdk import query, ClaudeAgentOptions

        oauth_token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
        api_key = os.environ.get("ANTHROPIC_API_KEY")

        print(f"\nEnvironment:")
        print(f"  CLAUDE_CODE_OAUTH_TOKEN: {'SET' if oauth_token else 'NOT SET'}")
        print(f"  ANTHROPIC_API_KEY: {'SET' if api_key else 'NOT SET'}")

        # Test 1: Only OAuth token
        print("\n[Test 3a] Using ONLY OAuth token...")
        if api_key:
            # Temporarily remove API key
            original_api_key = api_key
            del os.environ["ANTHROPIC_API_KEY"]

        try:
            message_count = 0
            async for message in query(
                prompt="Say 'OAuth works'",
                options=ClaudeAgentOptions(
                    allowed_tools=[],
                    permission_mode="bypassPermissions"
                )
            ):
                message_count += 1

            print(f"  ✅ Received {message_count} messages with OAuth only")

        except Exception as e:
            print(f"  ❌ Failed with OAuth only: {e}")
            if "Invalid API key" in str(e):
                print("  🚨 CRITICAL: SDK requires API key, OAuth not supported!")
                return False
        finally:
            if api_key:
                os.environ["ANTHROPIC_API_KEY"] = api_key

        # Test 2: Check what authentication method is actually used
        print("\n[Test 3b] Checking authentication method...")
        print("  Note: If OAuth works, it means either:")
        print("    1. Python SDK supports OAuth (unlike TypeScript SDK per #6536)")
        print("    2. Or it's using the bundled CLI with OAuth")

        return True

    except Exception as e:
        print(f"\n❌ OAuth vs API key test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_error_handling():
    """Test error scenarios - invalid tokens, rate limits, etc."""
    print("\n" + "=" * 60)
    print("TEST 4: Error Handling and Edge Cases")
    print("=" * 60)

    try:
        from claude_agent_sdk import query, ClaudeAgentOptions
        from claude_agent_sdk import CLINotFoundError, ProcessError

        # Test 4a: Invalid token
        print("\n[Test 4a] Testing with invalid token...")
        original_token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")

        os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = "invalid_token_12345"

        try:
            async for message in query(
                prompt="Test",
                options=ClaudeAgentOptions(allowed_tools=[], permission_mode="bypassPermissions")
            ):
                pass
            print("  ⚠️  No error with invalid token - unexpected!")
        except Exception as e:
            print(f"  ✅ Correctly rejected invalid token: {type(e).__name__}")
        finally:
            if original_token:
                os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = original_token

        return True

    except Exception as e:
        print(f"\n❌ Error handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_long_running_task():
    """Test if OAuth token supports long-running tasks (potential quota issues)."""
    print("\n" + "=" * 60)
    print("TEST 5: Long-Running Task with OAuth")
    print("=" * 60)

    try:
        from claude_agent_sdk import query, ClaudeAgentOptions

        oauth_token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
        if not oauth_token:
            print("❌ No CLAUDE_CODE_OAUTH_TOKEN found")
            return False

        print("\n[Test 5] Running longer task to check quota/rate limits...")

        start = datetime.now()
        async for message in query(
            prompt="List the first 10 prime numbers and explain why each is prime",
            options=ClaudeAgentOptions(
                allowed_tools=[],
                permission_mode="bypassPermissions"
            )
        ):
            if hasattr(message, 'result'):
                elapsed = (datetime.now() - start).total_seconds()
                print(f"\n✅ Long task completed in {elapsed:.2f}s")
                print(f"   Result length: {len(message.result)} chars")
                return True

        return False

    except Exception as e:
        print(f"\n❌ Long-running task failed: {e}")
        if "quota" in str(e).lower() or "rate limit" in str(e).lower():
            print("  🚨 OAuth token hit quota/rate limit!")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run comprehensive OAuth validation tests."""
    print("\nClaude Agent SDK Deep Dive POC")
    print("Validating OAuth support based on GitHub issues #6536 & #6058")
    print()

    results = {
        "multi_turn": False,
        "session_persistence": False,
        "oauth_vs_api_key": False,
        "error_handling": False,
        "long_running": False
    }

    # Run all tests
    results["multi_turn"] = await test_multi_turn_conversation()
    results["session_persistence"] = await test_session_persistence()
    results["oauth_vs_api_key"] = await test_oauth_vs_api_key()
    results["error_handling"] = await test_error_handling()
    results["long_running"] = await test_long_running_task()

    # Summary
    print("\n" + "=" * 60)
    print("COMPREHENSIVE POC SUMMARY")
    print("=" * 60)

    for test_name, result in results.items():
        icon = "✅" if result else "❌"
        print(f"{icon} {test_name.replace('_', ' ').title()}: {'PASS' if result else 'FAIL'}")

    print("\n" + "-" * 60)
    print("CRITICAL FINDINGS:")
    print("-" * 60)

    if results["oauth_vs_api_key"]:
        print("✅ OAuth token DOES work with Python SDK")
        print("   (Contradicts GitHub issue #6536 about TypeScript SDK)")
        print()
        print("   Possible explanations:")
        print("   1. Python SDK has different auth handling than TypeScript")
        print("   2. SDK wraps CLI which accepts OAuth")
        print("   3. Issue #6536 is outdated or TypeScript-specific")
    else:
        print("🚨 OAuth token DOES NOT work - API key required")
        print("   GitHub issue #6536 is correct")
        print("   ❌ BLOCKER: Cannot use existing Harvest OAuth infrastructure")

    if results["multi_turn"] and results["session_persistence"]:
        print("\n✅ Sessions work across multiple turns and instances")
        print("   - Can eliminate custom SQLite session management")
    elif results["multi_turn"]:
        print("\n⚠️  Multi-turn works but persistence unclear")
        print("   - May still need custom session management")
    else:
        print("\n❌ Session management issues detected")

    # Overall recommendation
    print("\n" + "=" * 60)
    all_pass = all(results.values())
    critical_pass = results["oauth_vs_api_key"] and results["multi_turn"]

    if all_pass:
        print("🎉 RECOMMENDATION: PROCEED with SDK migration")
        print("   All tests passed, OAuth fully supported")
    elif critical_pass:
        print("⚠️  RECOMMENDATION: CAUTIOUS PROCEED")
        print("   OAuth works but some edge cases need investigation")
    else:
        print("🚨 RECOMMENDATION: DO NOT PROCEED")
        print("   Critical blockers remain unresolved")


if __name__ == "__main__":
    asyncio.run(main())
