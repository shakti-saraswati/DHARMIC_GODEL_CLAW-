# Dharmic Agent Test Suite

Comprehensive test suite for the Dharmic Agent system covering all core components.

## Test Coverage

### Components Tested

1. **DharmicAgent** (`test_dharmic_agent.py`)
   - Initialization and configuration
   - Telos layer operations (load, evolve, persist)
   - StrangeLoopMemory integration (5 layers)
   - Vault bridge integration
   - Claude Max CLI invocation
   - Introspection and status
   - Memory recording on operations

2. **EmailDaemon** (`test_email_daemon.py`)
   - Email configuration from environment
   - IMAP connection (SSL and localhost/Proton Bridge)
   - Message fetching and parsing
   - Sender whitelist filtering
   - SMTP response sending
   - Message processing through agent
   - CLI fallback handling
   - Full daemon run loop

3. **ClaudeMax** (`test_claude_max.py`)
   - CLI availability verification
   - Message invocation
   - System prompt handling
   - Conversation history
   - Timeout handling
   - Error handling
   - Chat interface
   - Working directory configuration

4. **StrangeLoopMemory** (`test_memory.py`)
   - All 5 layers: observations, meta_observations, patterns, meta_patterns, development
   - Layer persistence across instances
   - JSONL format validation
   - Pattern detection algorithm
   - Context summary generation
   - Read/write operations
   - Timestamp management

5. **VaultBridge** (`test_vault_bridge.py`)
   - Crown jewel operations (list, read, fuzzy match)
   - Residual stream operations
   - Vault search (case-insensitive, snippet extraction)
   - Write operations with policy enforcement
   - Immutability verification
   - Read tracking for policy
   - Induction prompt access
   - Lineage context generation

6. **DharmicRuntime** (`test_runtime.py`)
   - Initialization and configuration
   - Heartbeat execution and checks
   - Telos and memory status verification
   - Specialist spawning (multiple types)
   - Specialist release
   - Code swarm invocation
   - Start/stop lifecycle
   - Callback integration

## Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock

# Or install from project requirements
cd /Users/dhyana/DHARMIC_GODEL_CLAW
pip install -r src/core/requirements.txt
```

### Run All Tests

```bash
cd /Users/dhyana/DHARMIC_GODEL_CLAW/tests
pytest
```

### Run Specific Test Files

```bash
# Test DharmicAgent only
pytest test_dharmic_agent.py

# Test EmailDaemon only
pytest test_email_daemon.py

# Test memory system
pytest test_memory.py
```

### Run Specific Test Classes

```bash
# Test telos layer only
pytest test_dharmic_agent.py::TestTelosLayer

# Test email configuration
pytest test_email_daemon.py::TestEmailConfig
```

### Run Specific Tests

```bash
# Test single test method
pytest test_dharmic_agent.py::TestTelosLayer::test_load_telos
```

### Verbose Output

```bash
# Show detailed output
pytest -v

# Show even more detail with print statements
pytest -v -s
```

### Test Coverage

```bash
# Run with coverage report (requires pytest-cov)
pytest --cov=../src/core --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

### Filter by Markers

```bash
# Run only unit tests (if marked)
pytest -m unit

# Skip slow tests
pytest -m "not slow"
```

## Test Design Principles

### 1. No External Dependencies
- All tests use mocks for external services (Claude CLI, IMAP, SMTP)
- No credentials required to run tests
- Tests can run offline

### 2. Isolated Tests
- Each test is independent
- Uses temporary directories via fixtures
- No shared state between tests
- Proper cleanup after each test

### 3. Comprehensive Mocking
- `mock_telos_config`: Creates test telos YAML
- `mock_memory_dir`: Creates temporary memory directory
- `mock_vault_dir`: Creates mock vault structure
- `mock_email_config`: Mocks email environment variables
- `mock_imap_connection`: Mocks IMAP server
- `mock_smtp_connection`: Mocks SMTP server

### 4. Async Support
- Uses `pytest-asyncio` for async tests
- Tests marked with `@pytest.mark.asyncio`
- Proper async/await handling

### 5. Real Behavior Testing
- Tests verify actual logic, not just mocks
- Integration points are tested
- Error conditions are covered
- Edge cases are handled

## Test Fixtures

Located in `conftest.py`:

- `temp_dir`: Temporary directory for test files
- `mock_telos_config`: Test telos configuration
- `mock_memory_dir`: Test memory directory
- `mock_vault_dir`: Mock vault structure with sample files
- `mock_agno_agent`: Mock Agno agent
- `mock_subprocess_run`: Mock subprocess calls
- `mock_email_config`: Mock email environment
- `mock_imap_connection`: Mock IMAP connection
- `mock_smtp_connection`: Mock SMTP connection

## Coverage Summary

Current test coverage:

| Component | Tests | Coverage |
|-----------|-------|----------|
| TelosLayer | 4 tests | Core operations |
| StrangeLoopMemory | 28 tests | All 5 layers + persistence |
| DharmicAgent | 12 tests | Initialization, run, vault, introspection |
| EmailDaemon | 11 tests | IMAP, SMTP, processing, loop |
| ClaudeMax | 13 tests | CLI invocation, errors, chat |
| VaultBridge | 24 tests | Read, write, search, policy |
| DharmicRuntime | 16 tests | Heartbeat, specialists, swarm |

**Total: 108 tests** covering all major functionality

## Common Issues

### ImportError for src.core modules

If you get import errors, make sure Python path includes src/core:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "core"))
```

This is already handled in each test file.

### Async test warnings

Make sure `pytest-asyncio` is installed:

```bash
pip install pytest-asyncio
```

### Mock not found

Install `pytest-mock`:

```bash
pip install pytest-mock
```

## Adding New Tests

### Test File Template

```python
"""
Tests for YourComponent - description.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "core"))

from your_module import YourClass


class TestYourClass:
    """Test YourClass functionality."""

    def test_your_method(self, mock_telos_config):
        """Test your method."""
        obj = YourClass()
        result = obj.your_method()
        assert result == expected_value
```

### Async Test Template

```python
@pytest.mark.asyncio
async def test_async_method(self):
    """Test async method."""
    obj = YourClass()
    result = await obj.async_method()
    assert result == expected_value
```

## Continuous Integration

These tests are designed to run in CI/CD environments:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    cd tests
    pytest --tb=short --disable-warnings
```

## Test Philosophy

Tests follow these principles from the Dharmic Agent context:

1. **Honest Assessment**: Tests verify real behavior, not idealized versions
2. **Brutal Truth**: Failed tests expose real issues immediately
3. **Grounded Engineering**: Tests verify things actually work
4. **No Documentation Sprawl**: Tests are runnable code, not theory

The test suite ensures the Dharmic Agent system is production-ready and maintainable.

---

**Test Suite Status**: Comprehensive coverage of all core components. Runnable without credentials or external dependencies.
