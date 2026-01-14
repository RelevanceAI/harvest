"""Tests for repository image builder."""

import os
import tempfile
import json


class TestDetectionFunctions:
    """Tests for dependency detection functions - these have real logic."""

    def test_detect_node_version_from_nvmrc(self):
        """Test Node version detection from .nvmrc file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nvmrc_path = os.path.join(tmpdir, ".nvmrc")
            with open(nvmrc_path, "w") as f:
                f.write("22")

            from modal_executor.repo_builder import _detect_node_version

            version = _detect_node_version(tmpdir)

            assert version == "22"

    def test_detect_node_version_strips_v_prefix(self):
        """Test Node version detection strips 'v' prefix."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nvmrc_path = os.path.join(tmpdir, ".nvmrc")
            with open(nvmrc_path, "w") as f:
                f.write("v20.10.0")

            from modal_executor.repo_builder import _detect_node_version

            version = _detect_node_version(tmpdir)

            assert version == "20.10.0"

    def test_detect_node_version_from_package_json_engines(self):
        """Test Node version detection from package.json engines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg_path = os.path.join(tmpdir, "package.json")
            with open(pkg_path, "w") as f:
                json.dump({"name": "test", "engines": {"node": ">=20"}}, f)

            from modal_executor.repo_builder import _detect_node_version

            version = _detect_node_version(tmpdir)

            assert version == "20"

    def test_detect_node_version_none_when_missing(self):
        """Test Node version detection returns None when no config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from modal_executor.repo_builder import _detect_node_version

            version = _detect_node_version(tmpdir)

            assert version is None

    def test_detect_package_manager_pnpm(self):
        """Test pnpm detection from lock file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = os.path.join(tmpdir, "pnpm-lock.yaml")
            with open(lock_path, "w") as f:
                f.write("lockfileVersion: 6.0")

            from modal_executor.repo_builder import _detect_package_manager

            pm = _detect_package_manager(tmpdir)

            assert pm == "pnpm"

    def test_detect_package_manager_yarn(self):
        """Test yarn detection from lock file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = os.path.join(tmpdir, "yarn.lock")
            with open(lock_path, "w") as f:
                f.write("# yarn.lock")

            from modal_executor.repo_builder import _detect_package_manager

            pm = _detect_package_manager(tmpdir)

            assert pm == "yarn"

    def test_detect_package_manager_npm(self):
        """Test npm detection from package-lock.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = os.path.join(tmpdir, "package-lock.json")
            with open(lock_path, "w") as f:
                json.dump({"lockfileVersion": 3}, f)

            from modal_executor.repo_builder import _detect_package_manager

            pm = _detect_package_manager(tmpdir)

            assert pm == "npm"

    def test_detect_package_manager_pip_requirements(self):
        """Test pip detection from requirements.txt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            req_path = os.path.join(tmpdir, "requirements.txt")
            with open(req_path, "w") as f:
                f.write("requests==2.28.0")

            from modal_executor.repo_builder import _detect_package_manager

            pm = _detect_package_manager(tmpdir)

            assert pm == "pip"

    def test_detect_package_manager_none(self):
        """Test package manager detection returns None for unknown project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from modal_executor.repo_builder import _detect_package_manager

            pm = _detect_package_manager(tmpdir)

            assert pm is None


class TestDefaultRepos:
    """Tests for default repository configuration."""

    def test_default_repos_defined(self):
        """Test default repos list is defined."""
        from modal_executor.repo_builder import DEFAULT_REPOS

        assert len(DEFAULT_REPOS) > 0

    def test_default_repos_format(self):
        """Test default repos have correct format (owner, name, branch)."""
        from modal_executor.repo_builder import DEFAULT_REPOS

        for repo in DEFAULT_REPOS:
            assert len(repo) == 3
            owner, name, branch = repo
            assert isinstance(owner, str)
            assert isinstance(name, str)
            assert isinstance(branch, str)
