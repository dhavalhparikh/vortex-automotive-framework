#!/bin/bash
#
# Super Simple Auto-Testing Script
#
# Automatically discovers hardware devices from platform config and runs tests.
# No more manual --device mappings!
#
# Usage:
#     ./auto_test.sh my_platform -m smoke
#     ./auto_test.sh my_platform tests/suites/cli_tests/
#     ./auto_test.sh my_platform --collect-only
#

set -e

# Check for --rebuild flag first
REBUILD=false
if [[ "$1" == "--rebuild" ]]; then
    REBUILD=true
    shift  # Remove --rebuild from arguments
fi

# Check if platform argument provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 [--rebuild] <platform_name> [test_args...]"
    echo ""
    echo "Available platforms:"
    ls config/hardware/*.yaml | xargs -n1 basename -s .yaml | sed 's/^/  /'
    echo ""
    echo "Examples:"
    echo "  $0 mock_platform -m smoke"
    echo "  $0 --rebuild custom_cli_platform tests/suites/cli_tests/"
    exit 1
fi

PLATFORM=$1
shift  # Remove platform from arguments

echo "🚀 Auto-testing with platform: $PLATFORM"
echo "📋 Test arguments: $@"
echo ""

# Build Docker image if it doesn't exist or if --rebuild was requested
if ! docker image inspect automotive-tests >/dev/null 2>&1 || [[ "$REBUILD" == "true" ]]; then
    if [[ "$REBUILD" == "true" ]]; then
        echo "🔨 Rebuilding Docker image..."
        docker build --no-cache -t automotive-tests .
    else
        echo "🔨 Building Docker image..."
        docker build -t automotive-tests .
    fi
    echo ""
fi

# Run with automatic device discovery
python3 scripts/auto_docker.py run --platform "$PLATFORM" -- "$@"