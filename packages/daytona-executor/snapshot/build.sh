#!/bin/bash
# Build script for Harvest Daytona snapshot image
# Copies config files from source of truth locations and builds Docker image

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building Harvest Daytona Snapshot Image${NC}"

# Find project root reliably (works from any directory)
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
    echo -e "${RED}Error: Not in a git repository${NC}"
    exit 1
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_CONTEXT="$SCRIPT_DIR/build-context"

echo "Project root: $PROJECT_ROOT"
echo "Script dir: $SCRIPT_DIR"
echo "Build context: $BUILD_CONTEXT"

# Clean previous build context
rm -rf "$BUILD_CONTEXT"

# Create temp build context directory structure
mkdir -p "$BUILD_CONTEXT/config/docs/ai/shared"
mkdir -p "$BUILD_CONTEXT/config/docs/mcp"

echo -e "${YELLOW}Copying configuration files from source of truth...${NC}"

# Copy from source of truth (absolute paths)
# Main Claude rules
if [ -f "$PROJECT_ROOT/.claude/CLAUDE.md" ]; then
    cp "$PROJECT_ROOT/.claude/CLAUDE.md" "$BUILD_CONTEXT/config/claude.md"
    echo "  - claude.md (from .claude/CLAUDE.md)"
else
    echo -e "${RED}Error: .claude/CLAUDE.md not found${NC}"
    exit 1
fi

# Autonomous agent rules
if [ -f "$PROJECT_ROOT/docs/ai/autonomous-agent.md" ]; then
    cp "$PROJECT_ROOT/docs/ai/autonomous-agent.md" "$BUILD_CONTEXT/config/autonomous-agent.md"
    echo "  - autonomous-agent.md"
else
    echo -e "${RED}Error: docs/ai/autonomous-agent.md not found${NC}"
    exit 1
fi

# Shared AI rules
if [ -d "$PROJECT_ROOT/docs/ai/shared" ]; then
    cp -r "$PROJECT_ROOT/docs/ai/shared/"* "$BUILD_CONTEXT/config/docs/ai/shared/"
    echo "  - docs/ai/shared/ ($(ls "$BUILD_CONTEXT/config/docs/ai/shared/" | wc -l | tr -d ' ') files)"
else
    echo -e "${RED}Error: docs/ai/shared/ not found${NC}"
    exit 1
fi

# MCP documentation
if [ -d "$PROJECT_ROOT/docs/mcp" ]; then
    cp -r "$PROJECT_ROOT/docs/mcp/"* "$BUILD_CONTEXT/config/docs/mcp/"
    echo "  - docs/mcp/ ($(ls "$BUILD_CONTEXT/config/docs/mcp/" | wc -l | tr -d ' ') files)"
else
    echo -e "${RED}Error: docs/mcp/ not found${NC}"
    exit 1
fi

# Memory seed (unique to this package)
if [ -f "$SCRIPT_DIR/../config/memory-seed.json" ]; then
    cp "$SCRIPT_DIR/../config/memory-seed.json" "$BUILD_CONTEXT/config/memory-seed.json"
    echo "  - memory-seed.json"
else
    echo -e "${RED}Error: config/memory-seed.json not found${NC}"
    exit 1
fi

# Copy Dockerfile to build context
cp "$SCRIPT_DIR/Dockerfile" "$BUILD_CONTEXT/"

echo -e "${YELLOW}Building Docker image...${NC}"

# Build the image
docker build \
    -t harvest-daytona-snapshot:latest \
    -f "$BUILD_CONTEXT/Dockerfile" \
    "$BUILD_CONTEXT"

BUILD_STATUS=$?

# Cleanup build context
rm -rf "$BUILD_CONTEXT"

if [ $BUILD_STATUS -eq 0 ]; then
    echo -e "${GREEN}Build successful!${NC}"
    echo ""
    echo "Image: harvest-daytona-snapshot:latest"
    echo ""
    echo "Next steps:"
    echo "  1. Run validation: ./test-snapshot.sh"
    echo "  2. Test SDK: ./test.sh (requires CLAUDE_CODE_OAUTH_TOKEN)"
    echo "  3. Push to registry: docker push <registry>/harvest-daytona-snapshot:latest"
else
    echo -e "${RED}Build failed!${NC}"
    exit 1
fi
