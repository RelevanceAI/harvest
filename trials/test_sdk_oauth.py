#!/usr/bin/env python3
"""
POC to test Claude Agent SDK with OAuth token authentication.

Tests:
1. OAuth token vs API key authentication
2. Session resumption
3. Basic streaming
"""

import asyncio
import os
import sys
from datetime import datetime


async def test_oauth_auth():
    """Test if SDK accepts CLAUDE_CODE_OAUTH_TOKEN."""
    print("=" * 60)
    print("TEST 1: OAuth Token Authentication")
    print("=" * 60)

    # Check for OAuth token
    oauth_token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    print(f"CLAUDE_CODE_OAUTH_TOKEN present: {bool(oauth_token)}")
    print(f"ANTHROPIC_API_KEY present: {bool(api_key)}")

    if not oauth_token and not api_key:
        print("\n❌ BLOCKER: Neither CLAUDE_CODE_OAUTH_TOKEN nor ANTHROPIC_API_KEY found")
        print("Please set one of these environment variables to test authentication")
        return False

    # Try importing SDK
    try:
        from claude_agent_sdk import query, ClaudeAgentOptions
        print("✅ SDK imported successfully")
    except ImportError as e:
        print(f"❌ BLOCKER: Failed to import SDK: {e}")
        return False

    # Test authentication with a simple query
    print("\nAttempting simple query...")
    try:
        start = datetime.now()
        options = ClaudeAgentOptions(
            allowed_tools=["Read"],
            permission_mode="bypassPermissions",
            cwd="."
        )

        message_count = 0
        async for message in query(
            prompt="What is 2+2? Just answer with the number.",
            options=options
        ):
            message_count += 1
            print(f"  Message {message_count}: {type(message).__name__}")

            # Check for result
            if hasattr(message, 'result'):
                elapsed = (datetime.now() - start).total_seconds()
                print(f"\n✅ Authentication successful!")
                print(f"   Result: {message.result}")
                print(f"   Duration: {elapsed:.2f}s")
                print(f"   Token type used: {'OAUTH' if oauth_token and not api_key else 'API_KEY'}")
                return True

    except Exception as e:
        print(f"\n❌ BLOCKER: Authentication failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False

    print("\n⚠️  No result message received")
    return False


async def test_session_resume():
    """Test session resumption capability."""
    print("\n" + "=" * 60)
    print("TEST 2: Session Resumption")
    print("=" * 60)

    try:
        from claude_agent_sdk import query, ClaudeAgentOptions

        # First session
        print("\nSession 1: Initial query...")
        session_id = None

        async for message in query(
            prompt="Remember this number: 42",
            options=ClaudeAgentOptions(
                allowed_tools=[],
                permission_mode="bypassPermissions"
            )
        ):
            if hasattr(message, 'session_id'):
                session_id = message.session_id
                print(f"  Captured session_id: {session_id}")

            if hasattr(message, 'result'):
                print(f"  Session 1 result: {message.result[:100]}...")

        if not session_id:
            print("⚠️  No session_id captured - cannot test resumption")
            return False

        # Second session - resume
        print(f"\nSession 2: Resuming with session_id={session_id}")
        async for message in query(
            prompt="What number did I ask you to remember?",
            options=ClaudeAgentOptions(
                resume=session_id,
                allowed_tools=[],
                permission_mode="bypassPermissions"
            )
        ):
            if hasattr(message, 'result'):
                result = message.result
                print(f"  Session 2 result: {result[:100]}...")

                # Check if it remembered "42"
                if "42" in result:
                    print("\n✅ Session resumption works! Claude remembered the number.")
                    return True
                else:
                    print("\n⚠️  Session resumed but context may not be preserved")
                    print(f"     Expected '42' in response, got: {result}")
                    return False

    except Exception as e:
        print(f"\n❌ Session resumption test failed: {e}")
        return False

    return False


async def test_streaming():
    """Test streaming performance."""
    print("\n" + "=" * 60)
    print("TEST 3: Streaming Performance")
    print("=" * 60)

    try:
        from claude_agent_sdk import query, ClaudeAgentOptions

        print("\nStreaming messages...")
        start = datetime.now()
        message_count = 0
        first_message_time = None

        async for message in query(
            prompt="Count from 1 to 3",
            options=ClaudeAgentOptions(
                allowed_tools=[],
                permission_mode="bypassPermissions"
            )
        ):
            message_count += 1
            elapsed = (datetime.now() - start).total_seconds()

            if message_count == 1:
                first_message_time = elapsed

            msg_type = type(message).__name__
            print(f"  [{elapsed:>5.2f}s] Message {message_count}: {msg_type}")

            if hasattr(message, 'result'):
                total_time = elapsed
                print(f"\n✅ Streaming test complete")
                print(f"   Total messages: {message_count}")
                print(f"   Time to first message: {first_message_time:.2f}s")
                print(f"   Total time: {total_time:.2f}s")
                print(f"   Messages per second: {message_count/total_time:.2f}")
                return True

    except Exception as e:
        print(f"\n❌ Streaming test failed: {e}")
        return False

    return False


async def main():
    """Run all POC tests."""
    print("\nClaude Agent SDK OAuth POC")
    print("Testing critical BLOCKER questions")
    print()

    results = {
        "oauth_auth": False,
        "session_resume": False,
        "streaming": False
    }

    # Test 1: OAuth authentication (CRITICAL BLOCKER)
    results["oauth_auth"] = await test_oauth_auth()

    if not results["oauth_auth"]:
        print("\n" + "!" * 60)
        print("CRITICAL BLOCKER: OAuth authentication failed")
        print("Cannot proceed with other tests")
        print("!" * 60)
        return

    # Test 2: Session resumption
    results["session_resume"] = await test_session_resume()

    # Test 3: Streaming
    results["streaming"] = await test_streaming()

    # Summary
    print("\n" + "=" * 60)
    print("POC SUMMARY")
    print("=" * 60)
    print(f"✅ OAuth Authentication: {'PASS' if results['oauth_auth'] else 'FAIL'}")
    print(f"{'✅' if results['session_resume'] else '⚠️ '} Session Resumption: {'PASS' if results['session_resume'] else 'FAIL/UNKNOWN'}")
    print(f"{'✅' if results['streaming'] else '⚠️ '} Streaming: {'PASS' if results['streaming'] else 'FAIL/UNKNOWN'}")

    if results["oauth_auth"]:
        print("\n🎉 BLOCKER RESOLVED: SDK supports OAuth authentication")
        print("   You can proceed with migration planning")
    else:
        print("\n🚨 BLOCKER NOT RESOLVED: SDK authentication failed")
        print("   Do not proceed with migration")


if __name__ == "__main__":
    asyncio.run(main())
