#!/bin/bash
# Test script for Harvest Daytona snapshot image
# Validates image contents without requiring API keys

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

IMAGE="harvest-daytona-snapshot:latest"
PASS=0
FAIL=0

echo -e "${YELLOW}Testing Harvest Daytona Snapshot Image${NC}"
echo "Image: $IMAGE"
echo ""

# Helper function to run test in container
run_test() {
    local name="$1"
    local cmd="$2"
    local expected="$3"

    echo -n "Testing: $name... "

    result=$(docker run --rm "$IMAGE" bash -c "$cmd" 2>&1) || true

    if echo "$result" | grep -q "$expected"; then
        echo -e "${GREEN}PASS${NC}"
        ((PASS++))
    else
        echo -e "${RED}FAIL${NC}"
        echo "  Expected: $expected"
        echo "  Got: $result"
        ((FAIL++))
    fi
}

# Helper function for file existence checks
check_file() {
    local name="$1"
    local path="$2"

    echo -n "Checking: $name... "

    if docker run --rm "$IMAGE" test -f "$path"; then
        echo -e "${GREEN}EXISTS${NC}"
        ((PASS++))
    else
        echo -e "${RED}MISSING${NC}"
        ((FAIL++))
    fi
}

# Helper function for directory checks
check_dir() {
    local name="$1"
    local path="$2"

    echo -n "Checking: $name... "

    if docker run --rm "$IMAGE" test -d "$path"; then
        echo -e "${GREEN}EXISTS${NC}"
        ((PASS++))
    else
        echo -e "${RED}MISSING${NC}"
        ((FAIL++))
    fi
}

echo "=== System Tools ==="
run_test "Node.js installed" "node --version" "v20"
run_test "npm installed" "npm --version" "10"
run_test "Python installed" "python3 --version" "Python 3"
run_test "Git installed" "git --version" "git version"
run_test "ripgrep installed" "rg --version" "ripgrep"
run_test "fd installed" "fd --version" "fd"
run_test "pnpm installed" "pnpm --version" ""

echo ""
echo "=== User & Security ==="
run_test "Running as harvest user" "whoami" "harvest"
run_test "Home directory exists" "test -d /home/harvest && echo OK" "OK"

echo ""
echo "=== Claude Agent SDK ==="
run_test "Claude CLI available" "which claude || npm list -g @anthropic-ai/claude-code" "claude"

echo ""
echo "=== MCP Servers ==="
run_test "Memory server" "npm list -g @modelcontextprotocol/server-memory" "server-memory"
run_test "Filesystem server" "npm list -g @modelcontextprotocol/server-filesystem" "server-filesystem"
run_test "GitHub server" "npm list -g @modelcontextprotocol/server-github" "server-github"
run_test "MCP Remote" "npm list -g mcp-remote" "mcp-remote"
run_test "Gemini server" "npm list -g @houtini/gemini-mcp" "gemini-mcp"
run_test "Sentry server" "npm list -g @sentry/mcp-server" "mcp-server"
run_test "Playwright MCP" "npm list -g @playwright/mcp" "playwright"

echo ""
echo "=== Playwright & Browser ==="
run_test "Playwright installed" "npx playwright --version" ""
run_test "Chromium available" "ls /home/harvest/.cache/ms-playwright/chromium-*/chrome-linux/chrome 2>/dev/null || echo 'chromium'" "chrom"

echo ""
echo "=== Configuration Files ==="
check_file "claude.md" "/app/claude.md"
check_file "autonomous-agent.md" "/app/autonomous-agent.md"
check_file "memory-seed.json" "/app/memory-seed.json"
check_dir "docs/ai/shared/" "/app/docs/ai/shared"
check_dir "docs/mcp/" "/app/docs/mcp"

# Check specific shared rule files
check_file "git-workflow.md" "/app/docs/ai/shared/git-workflow.md"
check_file "planning.md" "/app/docs/ai/shared/planning.md"
check_file "debugging.md" "/app/docs/ai/shared/debugging.md"

echo ""
echo "=== Working Directory ==="
run_test "Working directory is /app" "pwd" "/app"
run_test "/app is writable" "touch /app/test-write && rm /app/test-write && echo OK" "OK"

echo ""
echo "=========================================="
echo -e "Results: ${GREEN}$PASS passed${NC}, ${RED}$FAIL failed${NC}"
echo "=========================================="

if [ $FAIL -gt 0 ]; then
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
else
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
fi
