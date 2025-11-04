#!/bin/bash
"""
Super Simple Auto-Testing Script

Automatically discovers hardware devices from platform config and runs tests.
No more manual --device mappings!

Usage:
    ./auto_test.sh my_platform -m smoke
    ./auto_test.sh my_platform tests/suites/cli_tests/
    ./auto_test.sh my_platform --collect-only
"""

set -e

# Check if platform argument provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <platform_name> [test_args...]"
    echo ""
    echo "Available platforms:"
    ls config/hardware/*.yaml | xargs -n1 basename -s .yaml | sed 's/^/  /'
    echo ""
    echo "Examples:"
    echo "  $0 mock_platform -m smoke"
    echo "  $0 my_custom_platform tests/suites/cli_tests/"
    exit 1
fi

PLATFORM=$1
shift  # Remove platform from arguments

echo "🚀 Auto-testing with platform: $PLATFORM"
echo "📋 Test arguments: $@"
echo ""

# Build Docker image if it doesn't exist
if ! docker image inspect automotive-tests >/dev/null 2>&1; then
    echo "🔨 Building Docker image..."
    docker build -t automotive-tests .
    echo ""
fi

# Run with automatic device discovery
python3 scripts/auto_docker.py run --platform "$PLATFORM" "$@"