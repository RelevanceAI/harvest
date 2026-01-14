"""Tests for HarvestSandbox configuration files."""

import json
from pathlib import Path


class TestOpenCodeConfig:
    """Tests for OpenCode configuration files."""

    def test_opencode_json_valid(self):
        """Test opencode.json is valid JSON with required MCP servers."""
        config_path = (
            Path(__file__).parent.parent / "src/modal_executor/config/opencode.json"
        )

        with open(config_path) as f:
            config = json.load(f)

        assert "mcp" in config
        assert "memory" in config["mcp"]
        assert "filesystem" in config["mcp"]
        assert "playwright" in config["mcp"]

    def test_agents_md_has_key_sections(self):
        """Test AGENTS.md has required instruction sections."""
        agents_path = (
            Path(__file__).parent.parent / "src/modal_executor/config/AGENTS.md"
        )
        content = agents_path.read_text()

        assert "Git Workflow" in content
        assert "Safe-Carry-Forward" in content
        assert "Panic Button" in content
        assert "MCP Servers" in content

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
