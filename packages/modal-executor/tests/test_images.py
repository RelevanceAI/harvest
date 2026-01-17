"""Tests for image definitions."""

import pytest


class TestBaseImage:
    """Unit tests for base image configuration."""

    def test_get_base_image_returns_image(self):
        """Test get_base_image() returns something."""
        from modal_executor.images import get_base_image

        image = get_base_image()
        assert image is not None

    def test_config_dir_exists(self):
        """Test that config directory and required rule files exist."""
        from modal_executor.images import _CONFIG_DIR, _ROOT_DIR

        assert _CONFIG_DIR.exists()
        # autonomous-agent.md is now baked from docs/ai/ instead of config/AGENTS.md
        autonomous_md = _ROOT_DIR / "docs" / "ai" / "autonomous-agent.md"
        assert autonomous_md.exists(), "autonomous-agent.md must exist for image build"
        assert (_CONFIG_DIR / "memory-seed.json").exists()
        # Template is documentation only - actual settings generated at runtime
        assert (_CONFIG_DIR / "settings.json.template").exists()


@pytest.mark.modal
class TestBaseImageIntegration:
    """Integration tests for base image (requires Modal).

    Run with: pytest -m modal
    """

    def test_image_has_python(self):
        """Verify Python is available in image."""
        import modal
        from modal_executor.images import get_base_image

        app = modal.App.lookup("harvest-agent-executor", create_if_missing=True)

        sb = modal.Sandbox.create(
            image=get_base_image(),
            timeout=60,
            app=app,
        )

        try:
            result = sb.exec("python", "--version")
            assert "Python 3.11" in result.stdout.read()
        finally:
            sb.terminate()
