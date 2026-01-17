# Claude Agent SDK POC Scripts

**Investigation Date**: 2026-01-17
**Status**: Archived (investigation complete)

These scripts were used to investigate whether the Claude Agent SDK could replace Harvest's custom PTY wrapper.

**Conclusion**: SDK is incompatible with Modal's architecture. See `.claude/plans/claude-agent-sdk-migration-decision.md` for full decision.

---

## Scripts

### `test_sdk_oauth.py`
**Purpose**: Validate OAuth token authentication works with Python SDK
**Result**: ✅ PASS - OAuth works perfectly on macOS
**Run**: `python test_sdk_oauth.py` (requires `CLAUDE_CODE_OAUTH_TOKEN` env var)

### `test_sdk_deep_dive.py`
**Purpose**: Comprehensive validation (multi-turn, sessions, OAuth, errors, long-running)
**Result**: ✅ 5/5 tests passed locally
**Run**: `python test_sdk_deep_dive.py` (requires `CLAUDE_CODE_OAUTH_TOKEN` env var)

### `test_modal_sdk_poc.py`
**Purpose**: Critical blocker test - validate SDK in Modal containers
**Result**: ❌ BLOCKED - Modal runs as root, SDK refuses `bypassPermissions` as root
**Run**: `modal run test_modal_sdk_poc.py` (requires Modal auth + OAuth token)

---

## Key Findings

**What Works**:
- ✅ OAuth authentication (`CLAUDE_CODE_OAUTH_TOKEN`)
- ✅ Session persistence (`resume=session_id`)
- ✅ Multi-turn conversations
- ✅ All SDK features work locally on macOS

**The Blocker**:
```
Modal: USER directive → Skipped (platform limitation)
Claude SDK: bypassPermissions + root → Refused (security design)
Result: Architectural deadlock
```

**Decision**: Keep custom PTY wrapper - it's the right solution for Modal.

---

## For Future Reference

**Don't re-run these unless**:
- Modal adds non-root container support
- Anthropic adds root override for `bypassPermissions`
- Business accepts always-on infrastructure costs ($300-500/month)

Otherwise, the findings remain valid and the decision stands.
