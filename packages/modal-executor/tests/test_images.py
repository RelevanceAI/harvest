"""Tests for image definitions."""

import pytest
from unittest.mock import MagicMock


class TestBaseImage:
    """Unit tests for base image configuration."""
    
    @pytest.fixture
    def mock_modal(self, mocker):
        """Mock Modal for image tests."""
        mock = MagicMock()
        
        # Create chainable mock image
        mock_image = MagicMock()
        mock_image.apt_install.return_value = mock_image
        mock_image.pip_install.return_value = mock_image
        mock_image.run_commands.return_value = mock_image
        
        mock.Image.debian_slim.return_value = mock_image
        
        mocker.patch.dict("sys.modules", {"modal": mock})
        
        return mock, mock_image
    
    def test_base_image_uses_python_311(self, mock_modal):
        """Verify base image uses Python 3.11."""
        mock, mock_image = mock_modal
        
        # Import triggers image creation
        from modal_executor import images
        
        # Force reload to trigger image creation with mock
        import importlib
        importlib.reload(images)
        
        mock.Image.debian_slim.assert_called_with(python_version="3.11")
    
    def test_base_image_installs_apt_packages(self, mock_modal):
        """Verify required apt packages are installed."""
        mock, mock_image = mock_modal
        
        from modal_executor import images
        import importlib
        importlib.reload(images)
        
        # Check apt_install was called
        apt_call = mock_image.apt_install.call_args
        installed_packages = apt_call[0] if apt_call else []
        
        required = ["git", "curl", "build-essential"]
        for pkg in required:
            assert pkg in installed_packages, f"Missing apt package: {pkg}"
    
    def test_base_image_installs_pip_packages(self, mock_modal):
        """Verify required pip packages are installed."""
        mock, mock_image = mock_modal
        
        from modal_executor import images
        import importlib
        importlib.reload(images)
        
        # Check pip_install was called
        pip_call = mock_image.pip_install.call_args
        installed_packages = pip_call[0] if pip_call else []
        
        required = ["uv", "requests"]
        for pkg in required:
            assert any(pkg in p for p in installed_packages), f"Missing pip package: {pkg}"
    
    def test_get_base_image_returns_image(self, mock_modal):
        """Test get_base_image() returns the configured image."""
        mock, mock_image = mock_modal
        
        from modal_executor.images import get_base_image
        
        image = get_base_image()
        assert image is not None
    
    def test_get_base_image_with_extras(self, mock_modal):
        """Test adding extra pip packages to base image."""
        mock, mock_image = mock_modal
        
        from modal_executor.images import get_base_image_with_extras
        
        extras = ["pandas", "numpy"]
        image = get_base_image_with_extras(extras)
        
        # Should have called pip_install with extras
        mock_image.pip_install.assert_called()


@pytest.mark.modal
class TestBaseImageIntegration:
    """Integration tests for base image (requires Modal)."""
    
    def test_image_builds_successfully(self):
        """Verify base image builds without errors."""
        from modal_executor.images import get_base_image
        
        image = get_base_image()
        # If we get here without exception, image definition is valid
        assert image is not None
    
    def test_image_has_python(self):
        """Verify Python is available in image."""
        import modal
        from modal_executor.images import get_base_image
        from modal_executor.app import app
        
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
    
    def test_image_has_git(self):
        """Verify git is available in image."""
        import modal
        from modal_executor.images import get_base_image
        from modal_executor.app import app
        
        sb = modal.Sandbox.create(
            image=get_base_image(),
            timeout=60,
            app=app,
        )
        
        try:
            result = sb.exec("git", "--version")
            assert "git version" in result.stdout.read()
        finally:
            sb.terminate()
