# Security Audit: Credential Management

**Date**: 2026-01-15
**Scope**: PR #2 - OpenCode → Claude Code CLI migration
**Auditor**: Claude (Sonnet 4.5)

## Executive Summary

**Overall Risk**: 🟡 **MEDIUM** - Several credential exposure vectors identified that should be addressed before production deployment.

## Findings

### 🔴 CRITICAL: Dataclass Auto-Repr Exposes Credentials

**Location**: `packages/modal-executor/src/modal_executor/sandbox.py:213`

**Issue**:
```python
@dataclass
class HarvestSession:
    github_token: str = ""
    claude_oauth_token: str = ""
    gemini_api_key: Optional[str] = None
    sentry_auth_token: Optional[str] = None
    linear_api_key: Optional[str] = None
```

**Risk**: Dataclass `__repr__()` includes ALL fields. If this object is ever logged, printed, or included in error messages, credentials are exposed.

**Example**:
```python
session = HarvestSession(...)
print(session)  # Exposes all tokens!
logger.info(f"Starting session: {session}")  # Leaks credentials to logs!
```

**Recommendation**:
```python
@dataclass
class HarvestSession:
    """Configuration for a Harvest agent session."""

    session_id: str
    repo_owner: str
    repo_name: str
    branch: str = "main"
    user_email: str = ""
    user_name: str = ""

    # Credentials - excluded from repr
    github_token: str = field(default="", repr=False)
    claude_oauth_token: str = field(default="", repr=False)
    gemini_api_key: Optional[str] = field(default=None, repr=False)
    sentry_auth_token: Optional[str] = field(default=None, repr=False)
    linear_api_key: Optional[str] = field(default=None, repr=False)
```

---

### 🟡 MEDIUM: Git Clone URL Contains Token in Command Args

**Location**: `packages/modal-executor/src/modal_executor/sandbox.py:355-358`

**Issue**:
```python
repo_url = (
    f"https://x-access-token:{self.session.github_token}"
    f"@github.com/{self.session.repo_owner}/{self.session.repo_name}.git"
)

proc = await self._get_sandbox().exec.aio(
    "git", "clone", "--branch", self.session.branch,
    repo_url,  # Token visible in process args!
    self.session.repo_path,
)
```

**Risk**: The GitHub token is visible in process arguments. While the sandbox is isolated, process listings (`ps aux`) would show the token.

**Impact**: Low in isolated sandboxes, but violates best practices.

**Recommendation**: Use git credential helper or environment variables:
```python
# Option 1: Set GIT_ASKPASS with credential helper
await self._get_sandbox().exec.aio(
    "bash", "-c",
    f"GIT_USERNAME=x-access-token GIT_PASSWORD={self.session.github_token} "
    f"git clone --branch {self.session.branch} "
    f"https://github.com/{self.session.repo_owner}/{self.session.repo_name}.git "
    f"{self.session.repo_path}"
)

# Option 2: Setup credential helper first, then clone
# (Current approach at line 380-388 is correct but done AFTER clone)
```

---

### 🟡 MEDIUM: Credentials Written to Plaintext File

**Location**: `packages/modal-executor/src/modal_executor/sandbox.py:385-388`

**Issue**:
```python
creds = f"https://x-access-token:{self.session.github_token}@github.com"
await self._get_sandbox().exec.aio(
    "bash", "-c", f"echo '{creds}' > ~/.git-credentials"
)
```

**Risk**:
- GitHub token stored in plaintext in `~/.git-credentials`
- Single quotes don't protect against shell injection if token contains `'`
- File has default permissions (may be readable by other processes)

**Recommendation**:
```python
# Use git credential-store command (safer)
proc = await self._get_sandbox().exec.aio(
    "git", "credential-store", "store",
    stdin=f"url=https://github.com\nusername=x-access-token\npassword={self.session.github_token}\n"
)

# Or set file permissions explicitly
await self._get_sandbox().exec.aio(
    "bash", "-c",
    f"echo '{creds}' > ~/.git-credentials && chmod 600 ~/.git-credentials"
)
```

---

### 🟡 MEDIUM: Claude CLI Stderr May Leak OAuth Token

**Location**: `packages/modal-executor/src/modal_executor/claude_cli.py:104-106`

**Issue**:
```python
if self.last_returncode != 0:
    error_msg = f"Claude CLI exited with code {self.last_returncode}"
    if self.last_stderr:
        error_msg += f": {self.last_stderr[:500]}"  # Logged and raised!
    logger.error(error_msg)
    raise RuntimeError(error_msg)
```

**Risk**: If Claude CLI fails and prints the OAuth token in stderr (e.g., "Invalid token: oauth_xxx..."), it gets logged and included in exception messages.

**Recommendation**:
```python
# Redact potential tokens from stderr
def _redact_credentials(text: str) -> str:
    """Redact potential credentials from error messages."""
    import re
    # Redact common token patterns
    text = re.sub(r'oauth_[a-zA-Z0-9_-]+', 'oauth_REDACTED', text)
    text = re.sub(r'ghp_[a-zA-Z0-9]+', 'ghp_REDACTED', text)
    text = re.sub(r'[a-zA-Z0-9_-]{40,}', 'TOKEN_REDACTED', text)
    return text

if self.last_returncode != 0:
    error_msg = f"Claude CLI exited with code {self.last_returncode}"
    if self.last_stderr:
        redacted_stderr = self._redact_credentials(self.last_stderr[:500])
        error_msg += f": {redacted_stderr}"
    logger.error(error_msg)
    raise RuntimeError(error_msg)
```

---

### 🟢 LOW: Modal Secrets API Key Exposure

**Location**: `packages/modal-executor/src/modal_executor/sandbox.py:335`

**Issue**:
```python
secrets=[modal.Secret.from_dict(env_vars)]
```

**Risk**: Modal's `Secret.from_dict()` creates ephemeral secrets. These are safer than permanent secrets, but still exist in Modal's infrastructure.

**Status**: ✅ **ACCEPTABLE** - This is the recommended Modal pattern. Modal handles secret encryption and isolation.

**Recommendation**: Consider migrating to named secrets for production:
```python
# Create named secret once:
# modal secret create harvest-secrets GITHUB_TOKEN=xxx CLAUDE_CODE_OAUTH_TOKEN=yyy

# Use in code:
secrets=[modal.Secret.from_name("harvest-secrets")]
```

---

### 🟢 LOW: Environment Variable Exposure to Subprocess

**Location**: `packages/modal-executor/src/modal_executor/claude_cli.py:69-70`

**Issue**:
```python
env = os.environ.copy()
env["CLAUDE_CODE_OAUTH_TOKEN"] = oauth_token
```

**Risk**: OAuth token passed via environment variable to subprocess. While safer than command args, still visible to process inspection tools.

**Status**: ✅ **ACCEPTABLE** - This is the standard pattern for Claude CLI authentication. The subprocess is isolated within the sandbox.

---

## Summary of Recommendations

### Priority 1 (Critical - Fix Before Production)
1. ✅ Add `repr=False` to all credential fields in `HarvestSession` dataclass
2. ✅ Redact credentials from Claude CLI stderr before logging

### Priority 2 (Medium - Fix Soon)
3. Use git credential helper instead of inline tokens in clone URL
4. Set proper permissions (600) on `~/.git-credentials`
5. Consider using `git credential-store` command instead of echo

### Priority 3 (Low - Consider for Production)
6. Migrate to Modal named secrets instead of `from_dict()`
7. Add audit logging for credential access

## Current vs. Recommended Flow

### Current (Has Issues):
```
1. Create HarvestSession with credentials (repr exposes them)
2. Clone repo with token in URL (visible in ps aux)
3. Write credentials to file with echo (shell injection risk)
4. Log stderr directly (may contain tokens)
```

### Recommended:
```
1. Create HarvestSession with credentials (repr=False protects)
2. Setup credential helper FIRST
3. Clone repo using credential helper (no token in args)
4. Redact credentials from stderr before logging
```

## Testing Recommendations

Add security tests:
```python
def test_session_repr_does_not_leak_credentials():
    session = HarvestSession(
        github_token="ghp_secret123",
        claude_oauth_token="oauth_secret456",
    )
    repr_str = repr(session)
    assert "ghp_secret123" not in repr_str
    assert "oauth_secret456" not in repr_str

def test_git_credentials_file_has_secure_permissions():
    # Verify ~/.git-credentials is 600
    ...

def test_stderr_redaction():
    cli = ClaudeCliWrapper()
    stderr = "Error: Invalid token oauth_abc123xyz"
    redacted = cli._redact_credentials(stderr)
    assert "oauth_abc123xyz" not in redacted
    assert "oauth_REDACTED" in redacted
```

---

**Audit Date**: 2026-01-15
**Next Audit**: After Priority 1 fixes implemented
