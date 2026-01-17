"""Tests for HarvestSandbox configuration files."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestAgentConfig:
    """Tests for agent configuration files."""

    def test_autonomous_agent_md_has_key_sections(self):
        """Test autonomous-agent.md has required instruction sections."""
        from modal_executor.images import _ROOT_DIR

        autonomous_path = _ROOT_DIR / "docs" / "ai" / "autonomous-agent.md"
        content = autonomous_path.read_text()

        # Check for key autonomous agent concepts and structure
        assert "Autonomous" in content, "Should mention autonomous operation"
        assert "Modal" in content, "Should reference Modal sandbox environment"
        assert (
            "Execute" in content or "execute" in content
        ), "Should emphasize execution autonomy"
        assert "@docs/ai/shared/" in content, "Should reference shared rules"

    def test_memory_seed_json_valid(self):
        """Test memory-seed.json has required entities."""
        seed_path = (
            Path(__file__).parent.parent / "src/modal_executor/config/memory-seed.json"
        )

        with open(seed_path) as f:
            seed = json.load(f)

        assert "entities" in seed
        assert "relations" in seed

        entity_names = [e["name"] for e in seed["entities"]]
        assert "HarvestSession" in entity_names
        assert "EnvironmentConfig" in entity_names
        assert "GitWorkflow" in entity_names
        assert "ErrorPatterns" in entity_names


class TestClaudeVersionParsing:
    """Tests for _get_claude_version_safe method."""

    def _create_test_sandbox(self):
        """Create a HarvestSandbox instance for testing."""
        from modal_executor.sandbox import HarvestSandbox, HarvestSession

        session = HarvestSession(
            session_id="test-123",
            repo_owner="TestOrg",
            repo_name="test-repo",
        )

        with patch("modal_executor.sandbox.modal"):
            return HarvestSandbox(session)

    @pytest.mark.asyncio
    async def test_parses_simple_version(self):
        """Test parsing simple version like '2.1.3'."""
        sandbox = self._create_test_sandbox()

        # Mock the sandbox process
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout.read.return_value = "2.1.3"

        mock_sandbox = MagicMock()
        mock_sandbox.exec.aio = AsyncMock(return_value=mock_proc)
        sandbox._get_sandbox = MagicMock(return_value=mock_sandbox)

        version = await sandbox._get_claude_version_safe()
        assert version == "2.1.3"

    @pytest.mark.asyncio
    async def test_parses_version_with_prefix(self):
        """Test parsing version with prefix like 'Claude CLI 2.1.3'."""
        sandbox = self._create_test_sandbox()

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout.read.return_value = "Claude CLI 2.1.3"

        mock_sandbox = MagicMock()
        mock_sandbox.exec.aio = AsyncMock(return_value=mock_proc)
        sandbox._get_sandbox = MagicMock(return_value=mock_sandbox)

        version = await sandbox._get_claude_version_safe()
        assert version == "2.1.3"

    @pytest.mark.asyncio
    async def test_parses_version_with_label(self):
        """Test parsing version with label like 'Version: 2.1.3'."""
        sandbox = self._create_test_sandbox()

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout.read.return_value = "Version: 2.1.3"

        mock_sandbox = MagicMock()
        mock_sandbox.exec.aio = AsyncMock(return_value=mock_proc)
        sandbox._get_sandbox = MagicMock(return_value=mock_sandbox)

        version = await sandbox._get_claude_version_safe()
        assert version == "2.1.3"

    @pytest.mark.asyncio
    async def test_parses_version_with_extra_text(self):
        """Test parsing version embedded in text."""
        sandbox = self._create_test_sandbox()

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout.read.return_value = "claude version 3.0.1 (build 456)"

        mock_sandbox = MagicMock()
        mock_sandbox.exec.aio = AsyncMock(return_value=mock_proc)
        sandbox._get_sandbox = MagicMock(return_value=mock_sandbox)

        version = await sandbox._get_claude_version_safe()
        assert version == "3.0.1"

    @pytest.mark.asyncio
    async def test_fallback_when_no_version_found(self):
        """Test fallback to default version when parsing fails."""
        sandbox = self._create_test_sandbox()

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout.read.return_value = "unexpected output"

        mock_sandbox = MagicMock()
        mock_sandbox.exec.aio = AsyncMock(return_value=mock_proc)
        sandbox._get_sandbox = MagicMock(return_value=mock_sandbox)

        version = await sandbox._get_claude_version_safe()
        assert version == "2.1.3"  # Fallback version

    @pytest.mark.asyncio
    async def test_raises_when_claude_not_available(self):
        """Test raises RuntimeError when Claude CLI is not available."""
        sandbox = self._create_test_sandbox()

        mock_proc = MagicMock()
        mock_proc.returncode = 127
        mock_proc.stderr.read.return_value = "command not found: claude"

        mock_sandbox = MagicMock()
        mock_sandbox.exec.aio = AsyncMock(return_value=mock_proc)
        sandbox._get_sandbox = MagicMock(return_value=mock_sandbox)

        with pytest.raises(RuntimeError, match="Claude CLI not available"):
            await sandbox._get_claude_version_safe()


class TestJsonAtomicWrite:
    """Tests for _write_json_atomic method."""

    def _create_test_sandbox(self):
        """Create a HarvestSandbox instance for testing."""
        from modal_executor.sandbox import HarvestSandbox, HarvestSession

        session = HarvestSession(
            session_id="test-123",
            repo_owner="TestOrg",
            repo_name="test-repo",
        )

        with patch("modal_executor.sandbox.modal"):
            return HarvestSandbox(session)

    @pytest.mark.asyncio
    async def test_writes_json_with_atomic_pattern(self):
        """Test that JSON is written using atomic temp file pattern."""
        sandbox = self._create_test_sandbox()

        mock_sandbox = MagicMock()
        mock_sandbox.exec.aio = AsyncMock()
        sandbox._get_sandbox = MagicMock(return_value=mock_sandbox)

        test_data = {"key": "value", "nested": {"foo": "bar"}}
        await sandbox._write_json_atomic("/test/path.json", test_data)

        # Verify bash command was called with atomic pattern
        mock_sandbox.exec.aio.assert_called_once()
        args = mock_sandbox.exec.aio.call_args[0]

        assert args[0] == "bash"
        assert args[1] == "-c"
        # Verify atomic pattern: write to .tmp then mv
        assert "/test/path.json.tmp" in args[2]
        assert "mv /test/path.json.tmp /test/path.json" in args[2]
        # Verify JSON content is in the command
        assert '"key": "value"' in args[2]

    @pytest.mark.asyncio
    async def test_writes_formatted_json(self):
        """Test that JSON is properly formatted with indent."""
        sandbox = self._create_test_sandbox()

        mock_sandbox = MagicMock()
        mock_sandbox.exec.aio = AsyncMock()
        sandbox._get_sandbox = MagicMock(return_value=mock_sandbox)

        test_data = {"a": 1, "b": 2}
        await sandbox._write_json_atomic("/test/config.json", test_data)

        args = mock_sandbox.exec.aio.call_args[0]
        command = args[2]

        # Verify indentation exists (formatted JSON)
        assert '  "a": 1' in command or '  "a":1' in command
