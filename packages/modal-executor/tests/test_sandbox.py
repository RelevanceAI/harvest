"""Tests for Sandbox executor."""

import pytest
from unittest.mock import patch

from modal_executor.sandbox import SandboxExecutor, HarvestSession


class TestSandboxExecutor:
    """Unit tests for SandboxExecutor."""
    
    def test_executor_initialization(self):
        """Test SandboxExecutor initializes with defaults."""
        with patch("modal_executor.sandbox.modal"):
            executor = SandboxExecutor()
            
            assert executor.default_timeout_secs == 1800
            assert executor.mount_volume is True
    
    def test_executor_custom_config(self):
        """Test SandboxExecutor with custom config."""
        with patch("modal_executor.sandbox.modal"):
            executor = SandboxExecutor(default_timeout_secs=60, mount_volume=False)
            
            assert executor.default_timeout_secs == 60
            assert executor.mount_volume is False


class TestHarvestSession:
    """Unit tests for HarvestSession dataclass."""
    
    def test_repo_path_property(self):
        """Test repo_path is computed correctly."""
        session = HarvestSession(
            session_id="test-123",
            repo_owner="TestOrg",
            repo_name="my-app",
        )
        assert session.repo_path == "/workspace/my-app"
    
    def test_memory_volume_name(self):
        """Test memory volume name format."""
        session = HarvestSession(
            session_id="test-123",
            repo_owner="RelevanceAI",
            repo_name="relevance-chat-app",
        )
        assert session.memory_volume_name == "harvest-memory-RelevanceAI-relevance-chat-app"


@pytest.mark.modal
class TestSandboxExecutorIntegration:
    """Integration tests requiring Modal credentials.
    
    Run with: pytest -m modal
    """
    
    @pytest.mark.asyncio
    async def test_code_execution_captures_stdout(self):
        """Verify stdout captured correctly."""
        import modal
        
        app = modal.App.lookup("harvest-agent-executor", create_if_missing=True)
        
        from modal_executor.images import get_base_image
        from modal_executor.volume import get_state_volume
        
        sb = modal.Sandbox.create(
            image=get_base_image(),
            volumes={"/mnt/state": get_state_volume()},
            timeout=60,
            app=app,
        )
        
        try:
            with sb.open("/workspace/test.py", "w") as f:
                f.write('print("Hello from sandbox")')
            
            result = sb.exec("python", "/workspace/test.py")
            
            assert result.stdout.read().strip() == "Hello from sandbox"
            assert result.returncode == 0
        finally:
            sb.terminate()
