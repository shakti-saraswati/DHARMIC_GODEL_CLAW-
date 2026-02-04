# Test Suite Quick Start

Get the Dharmic Agent test suite running in 60 seconds.

## 1. Install Dependencies

```bash
cd /Users/dhyana/DHARMIC_GODEL_CLAW/tests
pip install -r requirements-test.txt
```

This installs:
- pytest (test framework)
- pytest-asyncio (async test support)
- pytest-mock (mocking utilities)
- pytest-cov (coverage reporting)
- PyYAML (config parsing)

## 2. Run All Tests

```bash
# Method 1: Direct pytest
pytest

# Method 2: Using runner script
./run_tests.sh

# Method 3: Verbose output
pytest -v
```

Expected output:
```
====================================== test session starts =======================================
collected 108 items

test_dharmic_agent.py::TestTelosLayer::test_load_telos PASSED                              [  0%]
test_dharmic_agent.py::TestTelosLayer::test_evolve_proximate_telos PASSED                  [  1%]
...
test_runtime.py::TestRuntimeLifecycle::test_start_stop PASSED                              [100%]

====================================== 108 passed in 2.34s =======================================
```

## 3. Run Specific Tests

```bash
# Test one component
pytest test_dharmic_agent.py

# Test one class
pytest test_dharmic_agent.py::TestTelosLayer

# Test one method
pytest test_dharmic_agent.py::TestTelosLayer::test_load_telos
```

## 4. Check Coverage

```bash
pytest --cov=../src/core --cov-report=term --cov-report=html
open htmlcov/index.html
```

## Test Files

| File | Tests | What It Tests |
|------|-------|---------------|
| `test_dharmic_agent.py` | 12 | DharmicAgent, TelosLayer, StrangeLoopMemory |
| `test_email_daemon.py` | 11 | EmailDaemon, IMAP, SMTP |
| `test_claude_max.py` | 13 | ClaudeMax CLI wrapper |
| `test_memory.py` | 28 | All 5 memory layers + persistence |
| `test_vault_bridge.py` | 24 | VaultBridge read/write/search |
| `test_runtime.py` | 16 | Runtime, heartbeat, specialists |

**Total: 108 tests**

## Common Commands

```bash
# Verbose with output
pytest -v -s

# Stop on first failure
pytest -x

# Run only failed tests from last run
pytest --lf

# Show slowest tests
pytest --durations=10

# Quiet mode (only show failures)
pytest -q
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'pytest'"
```bash
pip install -r requirements-test.txt
```

### "ImportError: cannot import name 'DharmicAgent'"
The test files automatically add `src/core` to the Python path. Make sure you're in the project root:
```bash
cd /Users/dhyana/DHARMIC_GODEL_CLAW
python3 -c "import sys; sys.path.insert(0, 'src/core'); import dharmic_agent; print('OK')"
```

### Tests are slow
Tests should run in < 5 seconds total. If slower:
```bash
# Show test durations
pytest --durations=10
```

### Mock errors
Make sure pytest-mock is installed:
```bash
pip install pytest-mock
```

## What's Tested

- ✓ Agent initialization (with/without dependencies)
- ✓ Telos loading and evolution
- ✓ All 5 memory layers (observations → development)
- ✓ Memory persistence across instances
- ✓ Email daemon (IMAP + SMTP)
- ✓ Claude Max CLI invocation
- ✓ Vault operations (read/write/search)
- ✓ Runtime heartbeat
- ✓ Specialist spawning
- ✓ Code swarm invocation
- ✓ Error handling and fallbacks

## No Credentials Needed

All tests use mocks. No need for:
- ❌ API keys
- ❌ Email credentials
- ❌ Claude CLI access
- ❌ Network connection

Tests run completely offline.

## Next Steps

1. **Run tests**: `pytest`
2. **Check coverage**: `pytest --cov=../src/core --cov-report=html`
3. **Read details**: See `README.md` for comprehensive documentation
4. **Add tests**: Follow patterns in existing test files

## Help

- **Full docs**: `README.md`
- **Coverage summary**: `TEST_SUMMARY.md`
- **Test structure**: Check `conftest.py` for fixtures

---

**You're ready to go!** Run `pytest` now.
