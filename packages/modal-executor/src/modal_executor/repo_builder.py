"""Repository image builder with dependency pre-installation.

This module provides functions to build pre-warmed images for repositories,
with dependencies already installed for faster sandbox startup.
"""

import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import modal

from modal_executor.app import app
from modal_executor.images import get_base_image


# =============================================================================
# Configuration
# =============================================================================

# Volume for storing build metadata
IMAGE_REGISTRY_VOLUME_NAME = "harvest-image-registry"

# Default repositories to keep warm
DEFAULT_REPOS = [
    ("RelevanceAI", "relevance-chat-app", "main"),
    ("RelevanceAI", "relevance-api-node", "main"),
    ("RelevanceAI", "relevance-app", "main"),
]


# =============================================================================
# Types
# =============================================================================


@dataclass
class RepoBuildInfo:
    """Information about a built repository image."""

    repo_owner: str
    repo_name: str
    branch: str
    package_manager: Optional[str]
    node_version: Optional[str]
    build_timestamp: str
    build_duration_secs: float
    success: bool
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "repo_owner": self.repo_owner,
            "repo_name": self.repo_name,
            "branch": self.branch,
            "package_manager": self.package_manager,
            "node_version": self.node_version,
            "build_timestamp": self.build_timestamp,
            "build_duration_secs": self.build_duration_secs,
            "success": self.success,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RepoBuildInfo":
        """Create from dictionary."""
        return cls(**data)


# =============================================================================
# Helper Functions (run inside sandbox)
# =============================================================================


# Volta Limitation: Manual Version Detection Required
#
# While Volta is installed in the base image for automatic Node version switching,
# it only works in interactive shells with hook initialization. Volta intercepts
# `cd` commands via shell hooks to read .nvmrc/package.json and switch versions.
#
# In this context, we use subprocess.run() to execute commands in non-interactive
# processes. These don't load shell hooks, so Volta's automatic switching never
# triggers. We must manually replicate Volta's detection logic:
#   1. Read .nvmrc, .node-version, or package.json ourselves
#   2. Explicitly call `volta install node@{version}`
#   3. Volta's shims in PATH will then use the installed version
#
# This is a common limitation of version managers (nvm, rbenv, pyenv) in
# non-interactive/subprocess contexts.
def _detect_node_version(repo_path: str) -> Optional[str]:
    """Detect Node.js version from .nvmrc, .node-version, or package.json."""
    # Check .nvmrc
    nvmrc_path = os.path.join(repo_path, ".nvmrc")
    if os.path.exists(nvmrc_path):
        with open(nvmrc_path) as f:
            version = f.read().strip()
            # Remove 'v' prefix if present
            return version.lstrip("v")

    # Check .node-version
    node_version_path = os.path.join(repo_path, ".node-version")
    if os.path.exists(node_version_path):
        with open(node_version_path) as f:
            return f.read().strip().lstrip("v")

    # Check package.json engines
    pkg_path = os.path.join(repo_path, "package.json")
    if os.path.exists(pkg_path):
        with open(pkg_path) as f:
            pkg = json.load(f)
            engines = pkg.get("engines", {})
            node_engine = engines.get("node", "")
            # Parse simple version constraints (e.g., ">=18", "^20", "22")
            if node_engine:
                # Extract first number sequence
                match = re.search(r"\d+", node_engine)
                if match:
                    return match.group()

    return None


def _detect_package_manager(repo_path: str) -> Optional[str]:
    """Detect package manager from lock files."""
    if os.path.exists(os.path.join(repo_path, "pnpm-lock.yaml")):
        return "pnpm"
    if os.path.exists(os.path.join(repo_path, "yarn.lock")):
        return "yarn"
    if os.path.exists(os.path.join(repo_path, "package-lock.json")):
        return "npm"
    if os.path.exists(os.path.join(repo_path, "package.json")):
        return "npm"  # Default to npm for Node projects
    if os.path.exists(os.path.join(repo_path, "requirements.txt")):
        return "pip"
    if os.path.exists(os.path.join(repo_path, "pyproject.toml")):
        return "pip"
    return None


def _install_dependencies(repo_path: str, package_manager: str) -> None:
    """Install dependencies using detected package manager."""
    os.chdir(repo_path)

    if package_manager == "pnpm":
        # Use pnpm with frozen lockfile for reproducibility
        subprocess.run(["pnpm", "install", "--frozen-lockfile"], check=True)

    elif package_manager == "yarn":
        subprocess.run(["yarn", "install", "--frozen-lockfile"], check=True)

    elif package_manager == "npm":
        # Prefer npm ci for reproducible installs
        if os.path.exists("package-lock.json"):
            subprocess.run(["npm", "ci"], check=True)
        else:
            subprocess.run(["npm", "install"], check=True)

    elif package_manager == "pip":
        if os.path.exists("requirements.txt"):
            subprocess.run(
                [
                    "pip",
                    "install",
                    "-r",
                    "requirements.txt",
                    "--break-system-packages",  # Required in container (PEP 668)
                ],
                check=True,
            )
        elif os.path.exists("pyproject.toml"):
            subprocess.run(
                ["pip", "install", "-e", ".", "--break-system-packages"], check=True
            )


def _run_build_if_available(repo_path: str, package_manager: str) -> bool:
    """Run build script if available. Returns True if build ran."""
    os.chdir(repo_path)

    if package_manager in ("npm", "pnpm", "yarn"):
        pkg_path = os.path.join(repo_path, "package.json")
        if os.path.exists(pkg_path):
            with open(pkg_path) as f:
                pkg = json.load(f)
                scripts = pkg.get("scripts", {})

                # Run build if available
                if "build" in scripts:
                    cmd = [package_manager, "run", "build"]
                    if package_manager == "npm":
                        cmd = ["npm", "run", "build"]
                    # Don't check=True - build might fail but that's OK for warm-up
                    result = subprocess.run(cmd)
                    return result.returncode == 0

    return False


# =============================================================================
# Modal Functions
# =============================================================================


@app.function(
    image=get_base_image(),
    secrets=[modal.Secret.from_name("harvest-github")],
    timeout=1800,  # 30 minutes max for large repos
)
def build_repo_image(
    repo_owner: str,
    repo_name: str,
    branch: str = "main",
) -> dict:
    """Build a pre-warmed image for a repository.

    1. Clone the repository
    2. Manually detect Node version and install via Volta
       (Volta's auto-switching doesn't work in subprocess contexts)
    3. Install dependencies (npm/pnpm/pip)
    4. Run initial build commands
    5. Return metadata about the build

    Args:
        repo_owner: GitHub repository owner
        repo_name: GitHub repository name
        branch: Branch to clone (default: main)

    Returns:
        RepoBuildInfo as dictionary
    """
    start_time = time.time()
    github_token = os.environ["GITHUB_TOKEN"]
    repo_url = (
        f"https://x-access-token:{github_token}@github.com/{repo_owner}/{repo_name}.git"
    )
    repo_path = f"/workspace/{repo_name}"

    build_info = RepoBuildInfo(
        repo_owner=repo_owner,
        repo_name=repo_name,
        branch=branch,
        package_manager=None,
        node_version=None,
        build_timestamp=datetime.utcnow().isoformat(),
        build_duration_secs=0,
        success=False,
    )

    try:
        # Clone repository
        subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", branch, repo_url, repo_path],
            check=True,
        )

        # Detect Node version and switch via Volta
        node_version = _detect_node_version(repo_path)
        if node_version:
            build_info.node_version = node_version
            subprocess.run(
                ["/root/.volta/bin/volta", "install", f"node@{node_version}"],
                check=False,
            )  # Don't fail if Volta can't find exact version

        # Detect and install dependencies
        package_manager = _detect_package_manager(repo_path)
        if package_manager:
            build_info.package_manager = package_manager
            _install_dependencies(repo_path, package_manager)

        # Run build
        _run_build_if_available(repo_path, package_manager or "npm")

        build_info.success = True

    except subprocess.CalledProcessError as e:
        build_info.error_message = f"Command failed: {e.cmd} (exit code {e.returncode})"
    except Exception as e:
        build_info.error_message = f"{type(e).__name__}: {e}"

    build_info.build_duration_secs = time.time() - start_time
    return build_info.to_dict()


@app.function(
    schedule=modal.Period(minutes=30),
    secrets=[modal.Secret.from_name("harvest-github")],
)
def refresh_all_images() -> list[dict]:
    """Cron job: Rebuild all registered repository images every 30 minutes.

    This keeps images warm with the latest dependencies installed,
    reducing sandbox startup time for users.

    Returns:
        List of build results
    """
    results = []

    for owner, name, branch in DEFAULT_REPOS:
        try:
            # Spawn builds in parallel
            result = build_repo_image.remote(owner, name, branch)
            results.append(result)
        except Exception as e:
            results.append(
                {
                    "repo_owner": owner,
                    "repo_name": name,
                    "branch": branch,
                    "success": False,
                    "error_message": str(e),
                }
            )

    return results


@app.function(
    image=get_base_image(),
    volumes={
        "/mnt/registry": modal.Volume.from_name(
            IMAGE_REGISTRY_VOLUME_NAME, create_if_missing=True
        )
    },
)
def get_build_status(repo_owner: str, repo_name: str) -> Optional[dict]:
    """Get the latest build status for a repository.

    Args:
        repo_owner: GitHub repository owner
        repo_name: GitHub repository name

    Returns:
        RepoBuildInfo as dictionary, or None if not found
    """
    registry_path = f"/mnt/registry/{repo_owner}_{repo_name}.json"

    if os.path.exists(registry_path):
        with open(registry_path) as f:
            return json.load(f)

    return None


@app.function(
    image=get_base_image(),
    volumes={
        "/mnt/registry": modal.Volume.from_name(
            IMAGE_REGISTRY_VOLUME_NAME, create_if_missing=True
        )
    },
)
def save_build_status(build_info: dict) -> None:
    """Save build status to registry.

    Args:
        build_info: RepoBuildInfo as dictionary
    """
    repo_owner = build_info["repo_owner"]
    repo_name = build_info["repo_name"]
    registry_path = f"/mnt/registry/{repo_owner}_{repo_name}.json"

    with open(registry_path, "w") as f:
        json.dump(build_info, f, indent=2)


@app.function()
def list_registered_repos() -> list[tuple[str, str, str]]:
    """List all registered repositories.

    Returns:
        List of (owner, name, branch) tuples
    """
    return list(DEFAULT_REPOS)


@app.function()
def register_repo(repo_owner: str, repo_name: str, branch: str = "main") -> None:
    """Register a new repository for automatic builds.

    Note: For MVP, this just triggers an immediate build.
    Full registry management will be added later.

    Args:
        repo_owner: GitHub repository owner
        repo_name: GitHub repository name
        branch: Branch to build (default: main)
    """
    # Trigger immediate build
    build_repo_image.spawn(repo_owner, repo_name, branch)
