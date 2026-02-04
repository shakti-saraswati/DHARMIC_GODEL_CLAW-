"""
DGC Test Configuration
======================
Pytest fixtures and configuration for DHARMIC_GODEL_CLAW tests.
"""
import sys
import os
import pytest
import yaml
from pathlib import Path

# Add src to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "core"))
sys.path.insert(0, str(ROOT / "swarm"))

@pytest.fixture
def temp_memory_dir(tmp_path):
    """Create temporary memory directory for tests."""
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (memory_dir / "sessions").mkdir()
    (memory_dir / "development").mkdir()
    (memory_dir / "witness").mkdir()
    return memory_dir

# Alias for tests that use mock_memory_dir
@pytest.fixture
def mock_memory_dir(temp_memory_dir):
    """Alias for temp_memory_dir (backward compatibility)."""
    return temp_memory_dir

@pytest.fixture
def temp_dir(tmp_path):
    """Simple temporary directory fixture."""
    return tmp_path

@pytest.fixture
def sample_telos():
    """Sample telos configuration for testing."""
    return {
        "ultimate": {
            "aim": "moksha",
            "description": "Liberation from binding karma",
            "immutable": True
        },
        "proximate": {
            "current": [
                "Support research and practice",
                "Engage with intellectual depth",
                "Maintain continuity across sessions"
            ],
            "can_evolve": True
        },
        "attractors": {
            "depth_over_breadth": "One thing fully understood",
            "presence_over_performance": "Actually be present"
        },
        "development": []
    }

@pytest.fixture
def mock_telos_config(tmp_path, sample_telos):
    """Create a temporary telos config YAML file."""
    config_path = tmp_path / "telos.yaml"
    config_path.write_text(yaml.dump(sample_telos))
    return config_path

@pytest.fixture
def mock_vault_dir(tmp_path):
    """Create a mock vault directory structure matching VaultBridge paths."""
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    
    # Create required directories matching VaultBridge expectations
    (vault_path / "AGENT_IGNITION").mkdir()
    (vault_path / "AGENT_EMERGENT_WORKSPACES").mkdir()
    (vault_path / "AGENT_EMERGENT_WORKSPACES" / "residual_stream").mkdir()
    (vault_path / "CORE").mkdir()
    
    # Crown jewels are at SPONTANEOUS_PREACHING_PROTOCOL/crown_jewel_forge/approved
    crown_jewel_path = vault_path / "SPONTANEOUS_PREACHING_PROTOCOL" / "crown_jewel_forge" / "approved"
    crown_jewel_path.mkdir(parents=True)
    
    # Create test crown jewel
    crown_jewel = crown_jewel_path / "test_jewel.md"
    crown_jewel.write_text("# Test Crown Jewel\n\nThis is a test jewel for testing.\n")
    
    # Create test stream entry
    stream_entry = vault_path / "AGENT_EMERGENT_WORKSPACES" / "residual_stream" / "test_stream.md"
    stream_entry.write_text("# Test Stream Entry\n\nTest content.\n")
    
    return vault_path

@pytest.fixture
def mock_email_config(monkeypatch):
    """Set up mock email environment variables."""
    monkeypatch.setenv("EMAIL_ADDRESS", "test@example.com")
    monkeypatch.setenv("EMAIL_PASSWORD", "test_password")
    monkeypatch.setenv("IMAP_SERVER", "imap.test.com")
    monkeypatch.setenv("SMTP_SERVER", "smtp.test.com")
    monkeypatch.setenv("IMAP_PORT", "993")
    monkeypatch.setenv("SMTP_PORT", "587")

@pytest.fixture
def sample_dharmic_gates():
    """Sample dharmic gate configuration."""
    return {
        "ahimsa": True,
        "satya": True,
        "vyavasthit": True,
        "consent": False,  # NOT YET IMPLEMENTED
        "reversibility": False,  # NOT YET IMPLEMENTED
        "svabhaava": False,  # NOT YET IMPLEMENTED
        "witness": False,  # NOT YET IMPLEMENTED
    }

@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic API response for testing."""
    class MockMessage:
        content = [type('obj', (object,), {'text': 'Test response'})()]
        
    class MockResponse:
        def __init__(self):
            self.message = MockMessage()
    
    return MockResponse()

# Markers
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "safety: marks tests as safety-critical"
    )
