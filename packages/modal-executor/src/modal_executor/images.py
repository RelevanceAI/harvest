"""Base image definitions for Modal Sandboxes."""

import modal

# Base image with Python 3.11 and common development tools
_base_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        # Version control
        "git",
        # HTTP/network tools
        "curl",
        "wget",
        # Build tools for native extensions
        "build-essential",
        "libffi-dev",
        "libssl-dev",
        "zlib1g-dev",
        # Text processing
        "jq",
    )
    .pip_install(
        # Fast package installer
        "uv",
        # Common Python packages for agent work
        "requests",
        "httpx",
        "pydantic>=2.0",
        # File handling
        "python-dotenv",
        "pyyaml",
    )
    .run_commands(
        # Create standard directories
        "mkdir -p /workspace",
        "mkdir -p /mnt/state/.cache",
        "mkdir -p /mnt/state/git-repos",
        "mkdir -p /mnt/state/checkpoints",
    )
)


def get_base_image() -> modal.Image:
    """Get the base image for Sandbox execution.
    
    Returns:
        Configured Modal Image with Python 3.11 and development tools
    """
    return _base_image


def get_base_image_with_extras(pip_packages: list[str]) -> modal.Image:
    """Get base image with additional pip packages.
    
    Args:
        pip_packages: List of pip packages to install
        
    Returns:
        Extended Modal Image
        
    Example:
        image = get_base_image_with_extras(["pandas", "numpy"])
    """
    return _base_image.pip_install(*pip_packages)
