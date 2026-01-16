"""Tests for Claude CLI wrapper."""

from modal_executor.claude_cli import ClaudeCliWrapper


class TestClaudeCliWrapper:
    """Unit tests for ClaudeCliWrapper."""

    def test_credential_redaction_oauth_token(self):
        """Test that OAuth tokens are redacted from error messages.

        Security requirement: Error messages must not leak credentials.
        """
        cli = ClaudeCliWrapper()

        # Test OAuth token redaction
        stderr = "Error: Invalid token oauth_abc123xyz456"
        redacted = cli._redact_credentials(stderr)

        assert "oauth_abc123xyz456" not in redacted
        assert "oauth_REDACTED" in redacted

    def test_credential_redaction_github_tokens(self):
        """Test that GitHub tokens are redacted from error messages."""
        cli = ClaudeCliWrapper()

        # Test GitHub personal access token (ghp_)
        stderr = "Authentication failed with token ghp_1234567890abcdef"
        redacted = cli._redact_credentials(stderr)

        assert "ghp_1234567890abcdef" not in redacted
        assert "ghp_REDACTED" in redacted

        # Test GitHub OAuth token (gho_)
        stderr = "Failed: gho_abcdefghijk"
        redacted = cli._redact_credentials(stderr)

        assert "gho_abcdefghijk" not in redacted
        assert "gho_REDACTED" in redacted

        # Test GitHub fine-grained token (github_pat_)
        stderr = "Invalid: github_pat_11ABCDEFG0123456789"
        redacted = cli._redact_credentials(stderr)

        assert "github_pat_11ABCDEFG0123456789" not in redacted
        assert "github_pat_REDACTED" in redacted

    def test_credential_redaction_long_tokens(self):
        """Test that long alphanumeric strings (likely tokens) are redacted."""
        cli = ClaudeCliWrapper()

        # Test long alphanumeric string (40+ chars)
        long_token = "a" * 50
        stderr = f"Error authenticating with token: {long_token}"
        redacted = cli._redact_credentials(stderr)

        assert long_token not in redacted
        assert "TOKEN_REDACTED" in redacted

    def test_credential_redaction_multiple_tokens(self):
        """Test that multiple tokens in one message are all redacted."""
        cli = ClaudeCliWrapper()

        stderr = (
            "Failed with oauth_token123 and github token ghp_secret456 "
            "plus another token: github_pat_verylongtoken789"
        )
        redacted = cli._redact_credentials(stderr)

        # Verify all tokens redacted
        assert "oauth_token123" not in redacted
        assert "ghp_secret456" not in redacted
        assert "github_pat_verylongtoken789" not in redacted

        # Verify redaction markers present
        assert "oauth_REDACTED" in redacted
        assert "ghp_REDACTED" in redacted
        assert "github_pat_REDACTED" in redacted

    def test_credential_redaction_preserves_message(self):
        """Test that non-credential parts of message are preserved."""
        cli = ClaudeCliWrapper()

        stderr = "Authentication failed: Invalid token oauth_secret123. Please check credentials."
        redacted = cli._redact_credentials(stderr)

        # Non-credential text should be preserved
        assert "Authentication failed" in redacted
        assert "Invalid token" in redacted
        assert "Please check credentials" in redacted

        # Credential should be redacted
        assert "oauth_secret123" not in redacted
        assert "oauth_REDACTED" in redacted
