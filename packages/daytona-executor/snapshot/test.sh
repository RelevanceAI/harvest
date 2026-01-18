#!/bin/bash
# Test script for Claude Agent SDK in the Harvest Docker image
#
# Usage:
#   ./test.sh                    # Interactive mode
#   ./test.sh "your prompt"      # Single prompt mode
#
# REQUIRES: CLAUDE_CODE_OAUTH_TOKEN environment variable

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

IMAGE="harvest-daytona-snapshot:latest"

# Load from .env files if present
for envfile in "../.env" "../.env.local" ".env" ".env.local"; do
    if [ -f "$envfile" ]; then
        set -a
        # shellcheck source=/dev/null
        source "$envfile"
        set +a
    fi
done

if [ -z "$CLAUDE_CODE_OAUTH_TOKEN" ]; then
    echo -e "${RED}Error: CLAUDE_CODE_OAUTH_TOKEN not set${NC}"
    echo ""
    echo "Set it via environment variable or .env.local file:"
    echo "  export CLAUDE_CODE_OAUTH_TOKEN=your_token_here"
    exit 1
fi

# TypeScript code that handles both single prompt and interactive modes
TEST_CODE='
import { query } from "@anthropic-ai/claude-agent-sdk";
import * as readline from "readline";

function formatMessage(message: any): void {
  const type = message.type || "unknown";
  const subtype = message.subtype ? `/${message.subtype}` : "";
  const prefix = `\x1b[36m[${type}${subtype}]\x1b[0m`;
  const content = message.message?.content || message.content;

  switch (type) {
    case "system":
      if (message.subtype === "init") {
        console.log(`${prefix} session_id=${message.session_id}`);
        console.log(`         model=${message.model}`);
        if (message.tools) {
          console.log(`         tools: ${message.tools.length} available`);
        }
      } else {
        console.log(`${prefix} ${JSON.stringify(message, null, 2)}`);
      }
      break;

    case "assistant":
      if (content) {
        for (const block of content) {
          if (block.type === "text") {
            console.log(`\x1b[32m[assistant]\x1b[0m ${block.text}`);
          } else if (block.type === "tool_use") {
            console.log(`\x1b[33m[tool_use]\x1b[0m ${block.name}`);
            console.log(`           ${JSON.stringify(block.input, null, 2)}`);
          } else if (block.type === "thinking") {
            console.log(`\x1b[35m[thinking]\x1b[0m ${block.thinking}`);
          }
        }
      } else {
        console.log(`${prefix} ${JSON.stringify(message, null, 2)}`);
      }
      break;

    case "user":
      if (content) {
        for (const block of content) {
          if (block.type === "tool_result") {
            const result = typeof block.content === "string"
              ? block.content
              : JSON.stringify(block.content, null, 2);
            console.log(`\x1b[34m[tool_result]\x1b[0m\n${result}`);
          }
        }
      }
      break;

    case "result":
      console.log(`\x1b[32m[result]\x1b[0m`);
      console.log(`         success: ${!message.is_error}`);
      console.log(`         cost: $${(message.cost_usd || 0).toFixed(4)}`);
      break;

    default:
      console.log(`${prefix} ${JSON.stringify(message, null, 2)}`);
  }
}

async function runQuery(userPrompt: string): Promise<void> {
  console.log("\n" + "=".repeat(60));
  console.log(`Prompt: ${userPrompt}`);
  console.log("=".repeat(60) + "\n");

  const response = query({
    prompt: userPrompt,
    options: {
      model: "claude-sonnet-4-5",
      workingDirectory: "/app"
    }
  });

  let messageCount = 0;
  for await (const message of response) {
    messageCount++;
    formatMessage(message);
  }

  console.log(`\n--- ${messageCount} messages ---\n`);
}

async function interactive(): Promise<void> {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  const prompt = (q: string): Promise<string> =>
    new Promise((resolve) => rl.question(q, resolve));

  console.log("\x1b[33mInteractive Claude Agent SDK Session\x1b[0m");
  console.log("Type prompts or .exit to quit\n");

  while (true) {
    const input = await prompt("\x1b[1m>\x1b[0m ");
    if (input.trim() === ".exit") {
      console.log("Goodbye!");
      break;
    }
    if (!input.trim()) continue;

    try {
      await runQuery(input);
    } catch (err: any) {
      console.error(`\x1b[31mError:\x1b[0m ${err.message}`);
    }
  }

  rl.close();
}

async function main() {
  const singlePrompt = process.argv[2];
  if (singlePrompt) {
    await runQuery(singlePrompt);
  } else {
    await interactive();
  }
}

main();
'

PROMPT_ARG="$1"

echo -e "${YELLOW}Claude Agent SDK Test${NC}"
echo "Image: $IMAGE"
if [ -n "$PROMPT_ARG" ]; then
    echo "Mode: Single prompt"
else
    echo "Mode: Interactive"
fi
echo ""

echo -e "${CYAN}Starting container...${NC}"
echo ""

if [ -n "$PROMPT_ARG" ]; then
    # Single prompt mode - no TTY needed
    docker run --rm \
        -e CLAUDE_CODE_OAUTH_TOKEN="$CLAUDE_CODE_OAUTH_TOKEN" \
        "$IMAGE" \
        bash -c "
            cd /tmp && \
            npm init -y > /dev/null 2>&1 && \
            npm install @anthropic-ai/claude-agent-sdk > /dev/null 2>&1 && \
            cat > test.ts << 'ENDOFCODE'
$TEST_CODE
ENDOFCODE
            npx tsx test.ts '$PROMPT_ARG'
        "
else
    # Interactive mode - needs TTY
    docker run -it --rm \
        -e CLAUDE_CODE_OAUTH_TOKEN="$CLAUDE_CODE_OAUTH_TOKEN" \
        "$IMAGE" \
        bash -c "
            cd /tmp && \
            npm init -y > /dev/null 2>&1 && \
            npm install @anthropic-ai/claude-agent-sdk > /dev/null 2>&1 && \
            cat > test.ts << 'ENDOFCODE'
$TEST_CODE
ENDOFCODE
            npx tsx test.ts
        "
fi
