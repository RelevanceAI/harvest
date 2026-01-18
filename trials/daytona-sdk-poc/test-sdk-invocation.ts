/**
 * POC: Validate Claude Agent SDK works in Daytona sandbox
 *
 * Blockers to validate:
 * 1. SDK can be invoked programmatically inside sandbox
 * 2. SDK output (streaming messages) is parseable
 * 3. OAuth token works via env var
 */

import { config } from "dotenv";
import { Daytona } from "@daytonaio/sdk";

// Load from .env.local if present (check both poc dir and parent)
config({ path: ".env.local" });
config({ path: "../.env.local" });

const DAYTONA_API_KEY = process.env.DAYTONA_API_KEY;
const CLAUDE_CODE_OAUTH_TOKEN = process.env.CLAUDE_CODE_OAUTH_TOKEN;

if (!DAYTONA_API_KEY) {
  console.error("Missing DAYTONA_API_KEY");
  process.exit(1);
}

if (!CLAUDE_CODE_OAUTH_TOKEN) {
  console.error("Missing CLAUDE_CODE_OAUTH_TOKEN");
  process.exit(1);
}

// The code we'll run inside the Daytona sandbox to test the SDK
const SDK_TEST_CODE = `
import { query } from "@anthropic-ai/claude-agent-sdk";

async function testSDK() {
  const messages = [];

  try {
    const response = query({
      prompt: "List the files in the current directory and tell me what you see",
      options: {
        model: "claude-sonnet-4-5"
      }
    });

    for await (const message of response) {
      messages.push(message);

      // Log each message as JSON for parsing
      console.log(JSON.stringify(message));
    }

    // Final summary
    console.log("---SUMMARY---");
    console.log(JSON.stringify({
      success: true,
      messageCount: messages.length,
      messageTypes: messages.map(m => m.type)
    }));

  } catch (err: unknown) {
    console.log("---ERROR---");
    const error = err as Error & { code?: string };
    console.log(JSON.stringify({
      success: false,
      error: error.message,
      code: error.code
    }));
  }
}

testSDK();
`;

async function runPOC() {
  console.log("=== Daytona + Claude Agent SDK POC ===\n");

  const daytona = new Daytona({
    apiKey: DAYTONA_API_KEY,
  });

  console.log("1. Creating Daytona sandbox...");
  const sandbox = await daytona.create({
    language: "typescript",
    autoStopInterval: 10,
    autoArchiveInterval: 20,
    autoDeleteInterval: -1,
    envVars: {
      CLAUDE_CODE_OAUTH_TOKEN: CLAUDE_CODE_OAUTH_TOKEN,
    },
  });

  console.log(`   Sandbox created: ${sandbox.id}\n`);

  try {
    // Step 2: Install Claude Agent SDK
    console.log("2. Installing @anthropic-ai/claude-agent-sdk...");
    console.log("   (This may take a while - package is ~70MB)");
    const installResult = await sandbox.process.executeCommand(
      "npm init -y && npm install @anthropic-ai/claude-agent-sdk",
      undefined,
      undefined,
      180000 // 3 min timeout
    );
    console.log(`   Exit code: ${installResult.exitCode}`);
    if (installResult.exitCode !== 0) {
      console.log(`   Install failed: ${installResult.result}`);
      return;
    }
    console.log("   SDK installed successfully\n");

    // Step 3: Run SDK code inside sandbox
    console.log("3. Running SDK test code inside sandbox...");
    console.log("   Code will: import SDK, call query(), iterate messages\n");

    const codeResult = await sandbox.process.codeRun(
      SDK_TEST_CODE,
      undefined,
      120000 // 2 min timeout
    );

    console.log("=== SDK OUTPUT ===");
    console.log(codeResult.result);
    console.log("=== EXIT CODE ===");
    console.log(codeResult.exitCode);

    // Step 4: Parse and analyze output
    console.log("\n4. Analyzing output...");
    const lines = codeResult.result.trim().split("\n");
    const messages = [];
    let summary = null;
    let error = null;

    for (const line of lines) {
      if (line === "---SUMMARY---") continue;
      if (line === "---ERROR---") continue;

      try {
        const parsed = JSON.parse(line);
        if (parsed.success !== undefined) {
          summary = parsed;
        } else if (parsed.error !== undefined && parsed.success === false) {
          error = parsed;
        } else {
          messages.push(parsed);
        }
      } catch {
        // Not JSON, skip
        console.log(`   Non-JSON line: ${line.substring(0, 50)}...`);
      }
    }

    console.log(`   Parsed ${messages.length} SDK messages`);
    if (messages.length > 0) {
      console.log("   Message types:", messages.map(m => m.type).join(", "));
    }

    // Summary
    console.log("\n=== POC SUMMARY ===");
    console.log(`Sandbox ID: ${sandbox.id}`);
    console.log(`SDK installed: YES`);
    console.log(`Code execution: ${codeResult.exitCode === 0 ? "SUCCESS" : "FAILED"}`);
    console.log(`Messages received: ${messages.length}`);

    if (summary) {
      console.log(`Summary: ${JSON.stringify(summary)}`);
    }
    if (error) {
      console.log(`Error: ${JSON.stringify(error)}`);
    }

    // Show sample messages
    if (messages.length > 0) {
      console.log("\n=== SAMPLE MESSAGES ===");
      messages.slice(0, 5).forEach((m, i) => {
        console.log(`[${i}] ${JSON.stringify(m).substring(0, 200)}...`);
      });
    }

  } catch (error) {
    console.error("POC failed:", error);
  } finally {
    console.log("\n5. Cleaning up sandbox...");
    await sandbox.delete();
    console.log("   Sandbox deleted");
  }
}

runPOC().catch(console.error);
