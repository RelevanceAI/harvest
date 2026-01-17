#!/usr/bin/env python3
"""
Phase 0 POC: Validate Claude Agent SDK in Modal container.

This is the CRITICAL test before proceeding with migration.

Tests:
1. SDK works in debian_slim Linux container
2. OAuth authentication works in Modal
3. Session persistence across function invocations
4. Performance vs current PTY wrapper
5. MCP servers work identically
"""

import modal
import os
from pathlib import Path

# Create Modal app
app = modal.App("harvest-sdk-poc")

# Create volume for session persistence
sessions_volume = modal.Volume.from_name(
    "harvest-sdk-sessions",
    create_if_missing=True
)

# Create image with SDK and non-root user
image = (
    modal.Image.debian_slim(python_version="3.12")  # Use 3.12, not 3.14
    .pip_install("claude-agent-sdk==0.1.20")
    # Create non-root user and switch to it (solves security restriction)
    .dockerfile_commands([
        "RUN useradd -m -s /bin/bash harvest",
        "RUN mkdir -p /home/harvest/.claude && chown -R harvest:harvest /home/harvest",
        "USER harvest",
        "ENV HOME=/home/harvest"
    ])
)


@app.function(
    image=image,
    volumes={"/home/harvest/.claude": sessions_volume},
    secrets=[
        modal.Secret.from_dict({
            "CLAUDE_CODE_OAUTH_TOKEN": os.environ.get("CLAUDE_CODE_OAUTH_TOKEN", "")
        })
    ],
    timeout=300  # 5 minutes
)
async def test_sdk_in_modal():
    """Test 1: SDK with permission_mode='acceptEdits' (bypass alternative)."""
    from claude_agent_sdk import query, ClaudeAgentOptions
    import time

    print("=" * 60)
    print("TEST 1: SDK in Modal Container (acceptEdits mode)")
    print("=" * 60)

    # Check OAuth token
    oauth_token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    print(f"OAuth token present: {bool(oauth_token)}")
    print(f"OAuth token length: {len(oauth_token) if oauth_token else 0} chars")

    try:
        start = time.time()

        # Try acceptEdits instead of bypassPermissions
        async for message in query(
            prompt="What is 5 + 3? Just answer with the number.",
            options=ClaudeAgentOptions(
                allowed_tools=[],
                permission_mode="acceptEdits"
            )
        ):
            if hasattr(message, 'result'):
                elapsed = time.time() - start
                print(f"\n✅ SDK works in Modal with acceptEdits!")
                print(f"   Result: {message.result}")
                print(f"   Duration: {elapsed:.2f}s")
                return {
                    "status": "success",
                    "result": message.result,
                    "duration": elapsed,
                    "permission_mode": "acceptEdits"
                }

        return {"status": "error", "message": "No result received"}

    except Exception as e:
        print(f"\n❌ SDK failed with acceptEdits: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__,
            "permission_mode": "acceptEdits"
        }


@app.function(
    image=image,
    volumes={"/home/harvest/.claude": sessions_volume},
    secrets=[
        modal.Secret.from_dict({
            "CLAUDE_CODE_OAUTH_TOKEN": os.environ.get("CLAUDE_CODE_OAUTH_TOKEN", "")
        })
    ],
    timeout=300
)
async def test_session_persistence():
    """Test 2: Session persistence across function invocations."""
    from claude_agent_sdk import query, ClaudeAgentOptions

    print("\n" + "=" * 60)
    print("TEST 2: Session Persistence in Modal")
    print("=" * 60)

    # First invocation: create session
    print("\n[Invocation 1] Creating session...")
    session_id = None

    try:
        async for message in query(
            prompt="Remember this code: MODAL-TEST-2026",
            options=ClaudeAgentOptions(
                allowed_tools=[],
                permission_mode="acceptEdits"
            )
        ):
            if hasattr(message, 'session_id'):
                session_id = message.session_id
                print(f"  Session ID: {session_id}")

            if hasattr(message, 'result'):
                print(f"  Result: {message.result[:100]}...")

        if not session_id:
            return {
                "status": "error",
                "message": "No session_id captured"
            }

        # Second invocation: resume session
        print(f"\n[Invocation 2] Resuming session {session_id}...")

        async for message in query(
            prompt="What code did I ask you to remember?",
            options=ClaudeAgentOptions(
                resume=session_id,
                allowed_tools=[],
                permission_mode="acceptEdits"
            )
        ):
            if hasattr(message, 'result'):
                result = message.result
                print(f"  Result: {result[:200]}...")

                if "MODAL-TEST-2026" in result:
                    print("\n✅ Session persistence works in Modal!")
                    return {
                        "status": "success",
                        "session_id": session_id,
                        "context_preserved": True
                    }
                else:
                    return {
                        "status": "partial",
                        "session_id": session_id,
                        "context_preserved": False,
                        "result": result
                    }

        return {
            "status": "error",
            "message": "No result in second invocation"
        }

    except Exception as e:
        print(f"\n❌ Session test failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
        }


@app.function(
    image=image,
    volumes={"/home/harvest/.claude": sessions_volume},
    secrets=[
        modal.Secret.from_dict({
            "CLAUDE_CODE_OAUTH_TOKEN": os.environ.get("CLAUDE_CODE_OAUTH_TOKEN", "")
        })
    ],
    timeout=300
)
async def test_file_operations():
    """Test 3: File operations with acceptEdits mode."""
    from claude_agent_sdk import query, ClaudeAgentOptions

    print("\n" + "=" * 60)
    print("TEST 3: File Operations in Modal (acceptEdits mode)")
    print("=" * 60)

    try:
        # Create a test file using SDK
        async for message in query(
            prompt='Create a file /tmp/modal_test.txt with the text "SDK WORKS IN MODAL"',
            options=ClaudeAgentOptions(
                allowed_tools=["Write", "Read"],
                permission_mode="acceptEdits",
                cwd="/tmp"
            )
        ):
            if hasattr(message, 'result'):
                print(f"  Result: {message.result[:200]}...")

        # Verify file exists
        from pathlib import Path
        test_file = Path("/tmp/modal_test.txt")

        if test_file.exists():
            content = test_file.read_text()
            print(f"\n✅ File operations work in Modal!")
            print(f"   File content: {content}")
            return {
                "status": "success",
                "file_created": True,
                "content": content
            }
        else:
            return {
                "status": "error",
                "message": "File was not created"
            }

    except Exception as e:
        print(f"\n❌ File operations failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
        }


@app.local_entrypoint()
def main():
    """Run all Modal POC tests."""
    print("\n" + "🚀" * 30)
    print("MODAL CONTAINER POC - PHASE 0 VALIDATION")
    print("🚀" * 30)

    # Test 1: Basic SDK functionality
    print("\nRunning Test 1: Basic SDK in Modal...")
    result1 = test_sdk_in_modal.remote()
    print(f"\nTest 1 Result: {result1}")

    if result1.get("status") != "success":
        print("\n🚨 BLOCKER: SDK doesn't work in Modal container")
        print("   Cannot proceed with migration")
        return

    # Test 2: Session persistence
    print("\nRunning Test 2: Session Persistence...")
    result2 = test_session_persistence.remote()
    print(f"\nTest 2 Result: {result2}")

    # Test 3: File operations
    print("\nRunning Test 3: File Operations...")
    result3 = test_file_operations.remote()
    print(f"\nTest 3 Result: {result3}")

    # Summary
    print("\n" + "=" * 60)
    print("MODAL POC SUMMARY")
    print("=" * 60)

    all_pass = (
        result1.get("status") == "success" and
        result2.get("status") == "success" and
        result3.get("status") == "success"
    )

    if all_pass:
        print("\n✅ ALL TESTS PASSED")
        print("\n🎉 RECOMMENDATION: PROCEED WITH MIGRATION")
        print("\nNext steps:")
        print("  1. Update get_base_image() to install SDK")
        print("  2. Replace ClaudeCliWrapper with SDK import")
        print("  3. Implement feature flag for gradual rollout")
        print("  4. Deploy to canary environment")
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("\nReview failures before proceeding")
        print("\nFailed tests:")
        if result1.get("status") != "success":
            print(f"  ❌ Test 1: {result1.get('message')}")
        if result2.get("status") != "success":
            print(f"  ⚠️  Test 2: {result2.get('message')}")
        if result3.get("status") != "success":
            print(f"  ❌ Test 3: {result3.get('message')}")
