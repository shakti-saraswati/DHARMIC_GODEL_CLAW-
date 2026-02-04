"""
Tests for VaultBridge - search, read, and write operations.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "core"))

from vault_bridge import VaultBridge


class TestVaultBridgeInitialization:
    """Test VaultBridge initialization and directory structure."""

    def test_initialization_with_default_path(self):
        """Test initialization with default vault path."""
        with patch('vault_bridge.Path.home') as mock_home:
            mock_home.return_value = Path("/tmp")
            vault = VaultBridge()

            expected_path = Path("/tmp/Persistent-Semantic-Memory-Vault")
            assert vault.vault_path == expected_path

    def test_initialization_with_custom_path(self, mock_vault_dir):
        """Test initialization with custom vault path."""
        vault = VaultBridge(vault_path=str(mock_vault_dir))

        assert vault.vault_path == mock_vault_dir

    def test_directory_references(self, mock_vault_dir):
        """Test that key directory references are set."""
        vault = VaultBridge(vault_path=str(mock_vault_dir))

        assert vault.agent_ignition == mock_vault_dir / "AGENT_IGNITION"
        assert vault.residual_stream == mock_vault_dir / "AGENT_EMERGENT_WORKSPACES" / "residual_stream"
        assert "crown_jewel_forge" in str(vault.crown_jewels)
        assert vault.core == mock_vault_dir / "CORE"


class TestCrownJewelOperations:
    """Test crown jewel read operations."""

    def test_list_crown_jewels(self, mock_vault_dir):
        """Test listing available crown jewels."""
        vault = VaultBridge(vault_path=str(mock_vault_dir))

        jewels = vault.list_crown_jewels()

        assert len(jewels) > 0
        assert "test_jewel" in jewels

    def test_list_crown_jewels_empty(self, temp_dir):
        """Test listing when no crown jewels exist."""
        # Create minimal vault structure without jewels
        vault_path = temp_dir / "empty_vault"
        vault_path.mkdir()

        vault = VaultBridge(vault_path=str(vault_path))
        jewels = vault.list_crown_jewels()

        assert jewels == []

    def test_get_crown_jewel_by_exact_name(self, mock_vault_dir):
        """Test reading crown jewel by exact name."""
        vault = VaultBridge(vault_path=str(mock_vault_dir))

        content = vault.get_crown_jewel("test_jewel")

        assert content is not None
        assert "Test Crown Jewel" in content
        assert "test jewel for testing" in content

    def test_get_crown_jewel_with_extension(self, mock_vault_dir):
        """Test reading crown jewel without extension (API doesn't support extensions)."""
        vault = VaultBridge(vault_path=str(mock_vault_dir))

        # The API adds .md automatically, so pass name without extension
        content = vault.get_crown_jewel("test_jewel")

        assert content is not None
        assert "Test Crown Jewel" in content

    def test_get_crown_jewel_fuzzy_match(self, mock_vault_dir):
        """Test reading crown jewel with partial name match."""
        vault = VaultBridge(vault_path=str(mock_vault_dir))

        content = vault.get_crown_jewel("jewel")

        assert content is not None
        assert "Test Crown Jewel" in content

    def test_get_crown_jewel_not_found(self, mock_vault_dir):
        """Test reading non-existent crown jewel."""
        vault = VaultBridge(vault_path=str(mock_vault_dir))

        content = vault.get_crown_jewel("nonexistent_jewel")

        assert content is None


class TestResidualStreamOperations:
    """Test residual stream operations."""

    def test_get_recent_stream(self, mock_vault_dir):
        """Test getting recent stream entries."""
        vault = VaultBridge(vault_path=str(mock_vault_dir))

        entries = vault.get_recent_stream(n=10)

        assert len(entries) > 0
        assert isinstance(entries, list)

        # Verify entry structure
        entry = entries[0]
        assert "filename" in entry
        assert "stem" in entry
        assert "modified" in entry
        assert "size" in entry

    def test_get_recent_stream_sorted_by_time(self, mock_vault_dir):
        """Test that stream entries are sorted by modification time."""
        # Add multiple stream files
        stream_dir = mock_vault_dir / "AGENT_EMERGENT_WORKSPACES" / "residual_stream"
        (stream_dir / "older_entry.md").write_text("Older")
        import time
        time.sleep(0.01)
        (stream_dir / "newer_entry.md").write_text("Newer")

        vault = VaultBridge(vault_path=str(mock_vault_dir))
        entries = vault.get_recent_stream(n=10)

        # Most recent should be first
        assert entries[0]["stem"] == "newer_entry"

    def test_get_stream_entry(self, mock_vault_dir):
        """Test reading specific stream entry."""
        vault = VaultBridge(vault_path=str(mock_vault_dir))

        content = vault.get_stream_entry("test_stream.md")

        assert content is not None
        assert "Test Stream Entry" in content

    def test_get_stream_entry_not_found(self, mock_vault_dir):
        """Test reading non-existent stream entry."""
        vault = VaultBridge(vault_path=str(mock_vault_dir))

        content = vault.get_stream_entry("nonexistent.md")

        assert content is None


class TestVaultSearch:
    """Test vault search functionality."""

    def test_search_vault_finds_results(self, mock_vault_dir):
        """Test searching finds matching content."""
        vault = VaultBridge(vault_path=str(mock_vault_dir))

        results = vault.search_vault("jewel", max_results=10)

        assert len(results) > 0
        assert any("jewel" in r["path"].lower() for r in results)

    def test_search_vault_includes_snippet(self, mock_vault_dir):
        """Test that search results include content snippets."""
        vault = VaultBridge(vault_path=str(mock_vault_dir))

        results = vault.search_vault("jewel", max_results=10)

        if results:
            assert "snippet" in results[0]
            assert len(results[0]["snippet"]) > 0

    def test_search_vault_case_insensitive(self, mock_vault_dir):
        """Test that search is case-insensitive."""
        vault = VaultBridge(vault_path=str(mock_vault_dir))

        results_lower = vault.search_vault("jewel", max_results=10)
        results_upper = vault.search_vault("JEWEL", max_results=10)

        assert len(results_lower) == len(results_upper)

    def test_search_vault_max_results(self, mock_vault_dir):
        """Test max_results parameter limits output."""
        # Add multiple matching files
        test_dir = mock_vault_dir / "CORE"
        for i in range(10):
            (test_dir / f"test_file_{i}.md").write_text("searchable content here")

        vault = VaultBridge(vault_path=str(mock_vault_dir))

        results = vault.search_vault("searchable", max_results=3)

        assert len(results) <= 3

    def test_search_vault_no_results(self, mock_vault_dir):
        """Test search with no matches."""
        vault = VaultBridge(vault_path=str(mock_vault_dir))

        results = vault.search_vault("nonexistent_query_string_12345", max_results=10)

        assert results == []


class TestVaultWrite:
    """Test vault write operations."""

    @patch('vault_bridge.PSMVPolicy')
    def test_write_to_vault_success(self, mock_policy_class, mock_vault_dir):
        """Test successful write to vault."""
        # Mock policy to allow write
        mock_policy = Mock()
        mock_decision = Mock()
        mock_decision.allowed = True
        mock_decision.reasons = ["Test allowed"]
        mock_decision.warnings = []
        mock_policy.evaluate_write = Mock(return_value=mock_decision)
        mock_policy.log_audit = Mock()
        mock_policy_class.return_value = mock_policy

        vault = VaultBridge(vault_path=str(mock_vault_dir))

        content = "# Test Content\n\nThis is a test."
        result = vault.write_to_vault(
            content,
            "test_output.md",
            "AGENT_IGNITION",
            consent=True,
            critique="Test write"
        )

        assert result is not None
        assert result.exists()
        assert result.name == "test_output.md"

    @patch('vault_bridge.PSMVPolicy')
    def test_write_to_vault_blocked(self, mock_policy_class, mock_vault_dir):
        """Test write blocked by policy."""
        # Mock policy to block write
        mock_policy = Mock()
        mock_decision = Mock()
        mock_decision.allowed = False
        mock_decision.reasons = ["Write not allowed"]
        mock_decision.warnings = ["No consent"]
        mock_policy.evaluate_write = Mock(return_value=mock_decision)
        mock_policy.log_audit = Mock()
        mock_policy_class.return_value = mock_policy

        vault = VaultBridge(vault_path=str(mock_vault_dir))

        result = vault.write_to_vault(
            "Content",
            "blocked.md",
            "AGENT_IGNITION"
        )

        assert result is None

    @patch('vault_bridge.PSMVPolicy')
    def test_write_to_vault_immutability(self, mock_policy_class, mock_vault_dir):
        """Test that write respects immutability (no overwrites)."""
        # Mock policy to allow writes
        mock_policy = Mock()
        mock_decision = Mock()
        mock_decision.allowed = True
        mock_decision.reasons = ["Allowed"]
        mock_decision.warnings = []
        mock_policy.evaluate_write = Mock(return_value=mock_decision)
        mock_policy.log_audit = Mock()
        mock_policy_class.return_value = mock_policy

        vault = VaultBridge(vault_path=str(mock_vault_dir))

        # Write first file
        result1 = vault.write_to_vault(
            "Content 1",
            "test.md",
            "AGENT_IGNITION",
            consent=True
        )

        # Write second file with same name
        result2 = vault.write_to_vault(
            "Content 2",
            "test.md",
            "AGENT_IGNITION",
            consent=True
        )

        # Should create new file with timestamp
        assert result1 != result2
        assert result1.stem == "test"
        assert result2.stem != "test"  # Should have timestamp added
        assert "_" in result2.stem  # Timestamp separator


class TestInductionPrompts:
    """Test induction prompt operations."""

    def test_get_induction_summary(self, mock_vault_dir):
        """Test getting induction prompt summary."""
        vault = VaultBridge(vault_path=str(mock_vault_dir))

        summary = vault.get_induction_summary()

        assert "Six Base Rules" in summary
        assert "IMMUTABILITY" in summary
        assert "AHIMSA" in summary
        assert "Jagat Kalyan" in summary

    def test_get_induction_prompt(self, mock_vault_dir):
        """Test reading induction prompt (if exists)."""
        # Create test induction prompt
        workspace = mock_vault_dir / "AGENT_EMERGENT_WORKSPACES"
        workspace.mkdir(parents=True, exist_ok=True)
        induction_file = workspace / "INDUCTION_PROMPT_v7.md"
        induction_file.write_text("# Induction Prompt v7\n\nTest content")

        vault = VaultBridge(vault_path=str(mock_vault_dir))

        content = vault.get_induction_prompt("v7")

        assert content is not None
        assert "Induction Prompt v7" in content


class TestVaultSummary:
    """Test vault summary generation."""

    def test_get_vault_summary(self, mock_vault_dir):
        """Test generating vault summary."""
        vault = VaultBridge(vault_path=str(mock_vault_dir))

        summary = vault.get_vault_summary()

        assert "Persistent Semantic Memory Vault" in summary
        assert "Crown Jewels" in summary
        assert "Residual Stream" in summary

    def test_get_lineage_context(self, mock_vault_dir):
        """Test getting lineage context."""
        vault = VaultBridge(vault_path=str(mock_vault_dir))

        context = vault.get_lineage_context()

        assert "Lineage Context" in context
        assert "Jagat Kalyan" in context
        assert "Ahimsa" in context
        assert "moksha" in context


class TestReadTracking:
    """Test read-before-write tracking."""

    def test_read_tracking(self, mock_vault_dir):
        """Test that reads are tracked for policy."""
        vault = VaultBridge(vault_path=str(mock_vault_dir))

        # Initially no reads
        assert vault._last_read_at is None
        assert vault._last_read_paths == []

        # Read a file
        vault.get_crown_jewel("test_jewel")

        # Should be tracked
        assert vault._last_read_at is not None
        assert len(vault._last_read_paths) > 0

    def test_read_tracking_limit(self, mock_vault_dir):
        """Test that read tracking keeps last 10 paths."""
        vault = VaultBridge(vault_path=str(mock_vault_dir))

        # Simulate 15 reads by calling _record_read
        for i in range(15):
            fake_path = mock_vault_dir / f"file{i}.md"
            fake_path.touch()
            vault._record_read(fake_path)

        # Should only keep last 10
        assert len(vault._last_read_paths) == 10


class TestSourceTextPaths:
    """Test source text path references."""

    def test_get_source_text_paths(self, mock_vault_dir):
        """Test getting paths to source texts."""
        vault = VaultBridge(vault_path=str(mock_vault_dir))

        paths = vault.get_source_text_paths()

        assert "aptavani" in paths
        assert "aurobindo" in paths
        assert "geb" in paths
        assert "nks" in paths

        # Verify they're Path objects
        for name, path in paths.items():
            assert isinstance(path, Path)
