#!/bin/bash
# Test script for Claude Agent SDK message flow
# Runs sample prompts and displays the JSON message stream
#
# REQUIRES: CLAUDE_CODE_OAUTH_TOKEN environment variable

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

IMAGE="harvest-daytona-snapshot:latest"

# Load from .env if present
if [ -f "../.env" ]; then
    export $(grep -v '^#' ../.env | xargs)
fi

if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check for OAuth token
if [ -z "$CLAUDE_CODE_OAUTH_TOKEN" ]; then
    echo -e "${RED}Error: CLAUDE_CODE_OAUTH_TOKEN not set${NC}"
    echo ""
    echo "Set it via environment variable or create .env file:"
    echo "  export CLAUDE_CODE_OAUTH_TOKEN=your_token_here"
    echo "  # or"
    echo "  echo 'CLAUDE_CODE_OAUTH_TOKEN=your_token' > .env"
    exit 1
fi

echo -e "${YELLOW}Testing Claude Agent SDK Message Flow${NC}"
echo "Image: $IMAGE"
echo ""

# The TypeScript code to run inside the container
# This demonstrates the message types that relevance-api-node will receive
TEST_CODE='
import { query } from "@anthropic-ai/claude-agent-sdk";

const prompt = process.argv[2] || "List files in /app and describe what you see";

console.log("=== Prompt: " + prompt + " ===");
console.log("");

try {
  const response = query({
    prompt: prompt,
    options: {
      model: "claude-sonnet-4-5",
      workingDirectory: "/app"
    }
  });

  let messageCount = 0;
  const startTime = Date.now();

  for await (const message of response) {
    messageCount++;

    // Format message for display based on type
    const type = message.type || "unknown";

    switch (type) {
      case "system/init":
        console.log(`[system/init] session_id=${message.session_id || "?"}, model=${message.model || "?"}`);
        if (message.tools) {
          console.log(`             tools=[${message.tools.slice(0, 5).join(", ")}...]`);
        }
        break;

      case "assistant":
        // Check for tool_use
        if (message.content) {
          for (const block of message.content) {
            if (block.type === "text") {
              const text = block.text.substring(0, 100);
              console.log(`[assistant]   "${text}${block.text.length > 100 ? "..." : ""}"`);
            } else if (block.type === "tool_use") {
              const input = JSON.stringify(block.input || {}).substring(0, 50);
              console.log(`[assistant]   tool_use: ${block.name}(${input}${input.length > 50 ? "..." : ""})`);
            }
          }
        }
        break;

      case "user":
        // Tool results
        if (message.content) {
          for (const block of message.content) {
            if (block.type === "tool_result") {
              const result = JSON.stringify(block.content || "").substring(0, 80);
              console.log(`[user]        tool_result: ${result}${result.length > 80 ? "..." : ""}`);
            }
          }
        }
        break;

      case "result":
        const duration = Date.now() - startTime;
        console.log(`[result]      success=${message.is_error === false}, cost=$${(message.cost_usd || 0).toFixed(4)}, duration=${duration}ms`);
        break;

      default:
        // Log other message types in compact form
        console.log(`[${type}]      ${JSON.stringify(message).substring(0, 80)}...`);
    }
  }

  console.log("");
  console.log(`Total messages: ${messageCount}`);

} catch (err) {
  console.error("Error:", err.message);
  process.exit(1);
}
'

# Run the test inside the container
echo -e "${CYAN}Running SDK test...${NC}"
echo ""

docker run --rm \
    -e CLAUDE_CODE_OAUTH_TOKEN="$CLAUDE_CODE_OAUTH_TOKEN" \
    "$IMAGE" \
    bash -c "
        cd /tmp && \
        npm init -y > /dev/null 2>&1 && \
        npm install @anthropic-ai/claude-agent-sdk > /dev/null 2>&1 && \
        echo '$TEST_CODE' > test.ts && \
        npx tsx test.ts 'List files in /app and briefly describe what configuration files you see'
    "

echo ""
echo -e "${GREEN}Test complete!${NC}"
echo ""
echo "This demonstrates the message stream that relevance-api-node receives."
echo "Each message type maps to frontend actions:"
echo "  - system/init  → Initialize session, show available tools"
echo "  - assistant    → Display text, show tool usage"
echo "  - user         → Show tool results"
echo "  - result       → Display final status, cost tracking"
