#!/bin/bash
# Test runner script for Dharmic Agent test suite

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================"
echo "Dharmic Agent Test Suite"
echo -e "======================================${NC}"
echo

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest not found${NC}"
    echo "Install with: pip install -r requirements-test.txt"
    exit 1
fi

# Navigate to test directory
cd "$(dirname "$0")"

echo -e "${BLUE}Running tests...${NC}"
echo

# Default: run all tests with verbose output
if [ $# -eq 0 ]; then
    pytest -v --tb=short --disable-warnings
else
    # Run with custom arguments
    pytest "$@"
fi

TEST_RESULT=$?

echo
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}======================================"
    echo "All tests passed!"
    echo -e "======================================${NC}"
else
    echo -e "${RED}======================================"
    echo "Some tests failed"
    echo -e "======================================${NC}"
fi

exit $TEST_RESULT
