# Implementation Plan: Harvest with Daytona + Claude Agent SDK

**Date:** 2026-01-17
**Status:** POC Complete, Ready for Implementation
**Previous Plan:** `.claude/plans/feat-harvest-pty-interactive-sessions/` (superseded)

---

## Executive Summary

Implement Harvest coding agent using **Daytona sandboxes** with the **Claude Agent SDK** (`@anthropic-ai/claude-agent-sdk`) for Relevance Chat UI integration.

**Key Changes from Previous Plan:**
- ❌ ~~Modal~~ → ✅ **Daytona** (non-root user, faster cold starts)
- ❌ ~~PTY + CLI~~ → ✅ **Claude Agent SDK** (programmatic API)
- ❌ ~~Stop hook detection~~ → ✅ **Structured message types** (system, assistant, result)
- ❌ ~~Python subprocess~~ → ✅ **TypeScript all the way**
- ❌ ~~Message queue + asyncio~~ → ✅ **SDK handles session internally**

**Result:** Dramatically simpler architecture with better reliability.

---

## POC Validation (Completed 2026-01-17)

### Blockers Resolved

| Blocker | Status | Evidence |
|---------|--------|----------|
| SDK invokes in Daytona | ✅ | `sandbox.process.codeRun()` works |
| Streaming messages parseable | ✅ | JSON messages with types |
| OAuth token works | ✅ | `CLAUDE_CODE_OAUTH_TOKEN` env var |
| Non-root execution | ✅ | Runs as `daytona` user |

### SDK Message Types Discovered

```
1. system (init)     → session_id, tools, model, cwd
2. assistant         → message.content (text, tool_use)
3. user              → tool_result (after tool execution)
4. result (success)  → final result, total_cost_usd, usage
```

### Sample Output (Tool Call Flow)

```json
// 1. Init
{"type":"system","subtype":"init","session_id":"abc123","tools":["Bash","Read","Write",...]}

// 2. Assistant announces action
{"type":"assistant","message":{"content":[{"type":"text","text":"I'll list the files..."}]}}

// 3. Assistant requests tool
{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Bash","input":{"command":"ls -la"}}]}}

// 4. Tool result
{"type":"user","message":{"content":[{"type":"tool_result","content":"total 48\ndrwxr-xr-x..."}]}}

// 5. Final response
{"type":"assistant","message":{"content":[{"type":"text","text":"Here's what I found..."}]}}

// 6. Completion
{"type":"result","subtype":"success","result":"...","total_cost_usd":0.0194}
```

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│ External Triggers (Slack, GitHub webhooks, Chat UI)             │
└────────────────────┬────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│ Relevance Backend                                                │
│  ├── TriggerRunner (buffer, deduplication)                      │
│  ├── ConversationManager (streaming to UI)                      │
│  └── HarvestPresetAgent                                         │
│       └── HarvestRuntime.ts                                     │
└────────────────────┬────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│ Daytona SDK (TypeScript)                                        │
│  ├── daytona.create({ language: "typescript" })                 │
│  ├── sandbox.process.codeRun(SDK_CODE)                          │
│  └── Streams JSON messages back                                 │
└────────────────────┬────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│ Daytona Sandbox                                                  │
│  ├── @anthropic-ai/claude-agent-sdk (installed)                 │
│  ├── query({ prompt, options }) → AsyncIterator<Message>        │
│  ├── Session management (resume, fork)                          │
│  └── Non-root user: /home/daytona                               │
└────────────────────┬────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│ Claude Agent (inside sandbox)                                    │
│  ├── Tools: Bash, Read, Write, Edit, Glob, Grep, WebSearch...  │
│  ├── MCP Servers (if configured)                                │
│  └── Git operations, file system access                         │
└─────────────────────────────────────────────────────────────────┘
```

### Chat UI Experience

```
┌─────────────────────────────────────────────────────────────────┐
│ Chat UI (relevance-chat-app)                                    │
├──────────────────────────┬──────────────────────────────────────┤
│ LEFT PANE: Conversation  │ RIGHT PANE: HarvestToolViewer        │
│                          │                                      │
│ User: Fix the tests      │ ┌──────────────────────────────────┐│
│                          │ │ 🔧 Bash: npm test                ││
│ Claude: I'll analyze     │ │ ┌────────────────────────────────┐││
│ the test failures...     │ │ │ FAIL src/classifier.test.ts   │││
│                          │ │ │   ● Expected 'foo' got 'bar'  │││
│                          │ │ └────────────────────────────────┘││
│                          │ └──────────────────────────────────┘│
│                          │                                      │
│                          │ ┌──────────────────────────────────┐│
│                          │ │ ✏️ Edit: src/classifier.ts       ││
│                          │ │ @@ -42,3 +42,3 @@               ││
│                          │ │ - return 'foo';                  ││
│                          │ │ + return 'bar';                  ││
│                          │ └──────────────────────────────────┘│
│                          │                                      │
│ [Send] [Cancel]          │ 💰 Cost: $0.02 | ⏱️ 12s             │
└──────────────────────────┴──────────────────────────────────────┘
```

### Data Flow

```
User sends: "Fix the tests"
  ↓
HarvestRuntime creates/resumes Daytona sandbox
  ↓
Runs Claude Agent SDK code inside sandbox:
  query({ prompt: "Fix the tests", options: {...} })
  ↓
SDK streams messages:
  • system (init) → Session started
  • assistant → "I'll analyze..." (text)
  • assistant → tool_use: Bash("npm test")
  • user → tool_result: "FAIL src/..."
  • assistant → tool_use: Read("src/classifier.ts")
  • user → tool_result: file contents
  • assistant → tool_use: Edit(...)
  • user → tool_result: "File updated"
  • assistant → "Tests should pass now" (text)
  • result → { total_cost_usd: 0.02, success: true }
  ↓
HarvestRuntime maps messages → ConversationManager
  ↓
Chat UI displays in left pane (conversation) + right pane (tools)
```

---

## Comparison: Old vs New Architecture

| Aspect | Old (PTY + Modal) | New (Agent SDK + Daytona) |
|--------|-------------------|---------------------------|
| **Sandbox** | Modal | Daytona |
| **Root user issue** | ❌ Blocked | ✅ Non-root |
| **Cold start** | ~3-5s (snapshots) | ~90-200ms (snapshots) |
| **Claude integration** | CLI via PTY | Programmatic SDK |
| **Message parsing** | Stop hook (`<<<CLAUDE_DONE>>>`) | Structured JSON types |
| **Session management** | Manual (SQLite) | SDK built-in |
| **Cost tracking** | Manual calculation | SDK provides `total_cost_usd` |
| **Tool calls** | Parse terminal output | Structured `tool_use`/`tool_result` |
| **Cancellation** | SIGINT to PTY | `AbortController` signal |
| **Language** | Python subprocess | TypeScript all the way |
| **Complexity** | High (5 components) | Low (3 components) |

---

## Implementation Tasks

### Task 1: Create Daytona Snapshot

**Goal:** Pre-built snapshot with Claude Agent SDK installed for faster cold starts.

**Location:** `packages/daytona-executor/snapshot/`

**Files:**
```
snapshot/
├── Dockerfile
├── devcontainer.json
└── README.md
```

**Dockerfile:**
```dockerfile
FROM node:20-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    ripgrep \
    python3.11 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install uv for Python
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Claude Agent SDK globally
RUN npm install -g @anthropic-ai/claude-agent-sdk

# Create non-root user (Daytona uses 'daytona')
RUN useradd -m -s /bin/bash daytona
USER daytona
WORKDIR /home/daytona

ENV PATH="/home/daytona/.local/bin:$PATH"
```

**Success criteria:**
- [ ] Snapshot builds and registers in Daytona
- [ ] `@anthropic-ai/claude-agent-sdk` available via `require()`
- [ ] Running as `daytona` user (non-root)
- [ ] Cold start < 500ms

---

### Task 2: HarvestRuntime Backend Integration

**Goal:** TypeScript runtime that creates Daytona sandboxes and runs Agent SDK.

**Location:** `relevance-api-node/apps/nodeapi/src/agent/preset_agents/harvest/`

**Files:**
```
harvest/
├── agent.ts              # PresetAgent definition
├── runtime.ts            # HarvestRuntime (Daytona + SDK)
├── message-mapper.ts     # SDK messages → Relevance conversation
├── types.ts              # TypeScript types
└── README.md
```

**runtime.ts pattern:**
```typescript
import { Daytona } from "@daytonaio/sdk";

const HARVEST_SNAPSHOT = "harvest-snapshot";

// Code to run inside sandbox
const SDK_RUNNER_CODE = `
import { query } from "@anthropic-ai/claude-agent-sdk";

const prompt = process.env.HARVEST_PROMPT;
const sessionId = process.env.HARVEST_SESSION_ID;

const response = query({
  prompt,
  options: {
    model: "claude-sonnet-4-5",
    resume: sessionId || undefined,
  }
});

for await (const message of response) {
  console.log(JSON.stringify(message));
}
`;

export const HarvestRuntime = async function* (convo: ConversationManager) {
  const daytona = new Daytona({ apiKey: process.env.DAYTONA_API_KEY });

  // Create or resume sandbox
  const sandbox = await daytona.create({
    snapshot: HARVEST_SNAPSHOT,
    envVars: {
      CLAUDE_CODE_OAUTH_TOKEN: await getClaudeToken(convo),
      HARVEST_PROMPT: getLatestPrompt(convo),
      HARVEST_SESSION_ID: convo.session_id || "",
    },
  });

  try {
    // Run SDK code inside sandbox
    const result = await sandbox.process.codeRun(SDK_RUNNER_CODE, undefined, 600000);

    // Parse and yield messages
    for (const line of result.result.split("\n")) {
      if (!line.trim()) continue;

      try {
        const message = JSON.parse(line);
        yield* mapMessageToConversation(message, convo);
      } catch {
        // Non-JSON line, skip
      }
    }
  } finally {
    // Don't delete - keep for session resume
    await sandbox.stop();
  }
};
```

**Success criteria:**
- [ ] HarvestRuntime creates Daytona sandbox
- [ ] SDK code runs inside sandbox
- [ ] Messages stream back to Relevance
- [ ] Session ID preserved for resume

---

### Task 3: SDK Message → Relevance Mapping

**Goal:** Convert Agent SDK messages to Relevance conversation format.

**Location:** `harvest/message-mapper.ts`

**Message type handling:**
```typescript
type SDKMessage =
  | { type: "system"; subtype: "init"; session_id: string; tools: string[] }
  | { type: "assistant"; message: { content: ContentBlock[] } }
  | { type: "user"; message: { content: ToolResult[] } }
  | { type: "result"; subtype: "success"; total_cost_usd: number; result: string };

async function* mapMessageToConversation(
  message: SDKMessage,
  convo: ConversationManager
): AsyncGenerator<ToolOutput> {
  switch (message.type) {
    case "system":
      if (message.subtype === "init") {
        convo.session_id = message.session_id;
        // Don't yield - internal state
      }
      break;

    case "assistant":
      for (const block of message.message.content) {
        if (block.type === "text") {
          yield { assistant_message: block.text };
        } else if (block.type === "tool_use") {
          yield {
            tool_call: {
              id: block.id,
              name: block.name,
              input: block.input,
            },
          };
        }
      }
      break;

    case "user":
      for (const result of message.message.content) {
        if (result.type === "tool_result") {
          yield {
            tool_result: {
              tool_use_id: result.tool_use_id,
              content: result.content,
              is_error: result.is_error,
            },
          };
        }
      }
      break;

    case "result":
      yield {
        completion: {
          result: message.result,
          cost_usd: message.total_cost_usd,
        },
      };
      break;
  }
}
```

**Success criteria:**
- [ ] All SDK message types mapped
- [ ] Tool calls render in HarvestToolViewer
- [ ] Cost displayed to user
- [ ] Session ID preserved

---

### Task 4: HarvestToolViewer Frontend

**Goal:** React components to render SDK messages in Chat UI right pane.

**Location:** `relevance-chat-app/src/components/ToolDisplay/HarvestToolViewer/`

**Reference:** `anthropics/claude-code-sdk-demos/simple-chatapp/client/components/`

**Files:**
```
HarvestToolViewer/
├── index.tsx              # Main component
├── ToolCallView.tsx       # Renders tool_use messages
├── FileEditView.tsx       # Renders Edit tool (diff view)
├── BashOutputView.tsx     # Renders Bash output
├── ThinkingView.tsx       # Renders thinking blocks (if enabled)
└── CostSummary.tsx        # Shows total_cost_usd
```

**index.tsx pattern:**
```typescript
export const HarvestToolViewer: React.FC<Props> = ({ messages }) => {
  return (
    <div className="harvest-tool-viewer">
      {messages.map((msg, i) => {
        switch (msg.tool_name) {
          case "Bash":
            return <BashOutputView key={i} {...msg} />;
          case "Edit":
          case "Write":
            return <FileEditView key={i} {...msg} />;
          case "Read":
            return <FileReadView key={i} {...msg} />;
          default:
            return <ToolCallView key={i} {...msg} />;
        }
      })}

      {costInfo && <CostSummary cost={costInfo} />}
    </div>
  );
};
```

**Success criteria:**
- [ ] Bash output with syntax highlighting
- [ ] File edits as diffs
- [ ] Collapsible tool calls
- [ ] Cost summary at bottom

---

### Task 5: Session Management

**Goal:** Resume conversations across multiple prompts.

**Implementation:**
```typescript
// In HarvestRuntime
const session_id = convo.getMetadata("harvest_session_id");

const result = await sandbox.process.codeRun(`
  const response = query({
    prompt: ${JSON.stringify(prompt)},
    options: {
      model: "claude-sonnet-4-5",
      resume: ${session_id ? JSON.stringify(session_id) : "undefined"},
    }
  });
  // ...
`);

// After init message, save session_id
if (message.type === "system" && message.subtype === "init") {
  convo.setMetadata("harvest_session_id", message.session_id);
}
```

**Success criteria:**
- [ ] First message creates new session
- [ ] Subsequent messages resume session
- [ ] Context preserved across prompts
- [ ] Session stored in conversation metadata

---

### Task 6: Cancellation

**Goal:** User can cancel mid-execution.

**Pattern:**
```typescript
// In sandbox code
const controller = new AbortController();

// Listen for cancel signal from parent
process.on("SIGTERM", () => controller.abort());

const response = query({
  prompt,
  options: {
    signal: controller.signal,
  }
});
```

**Relevance integration:**
```typescript
// Cancel endpoint
app.post("/api/harvest/cancel/:conversation_id", async (req, res) => {
  const sandbox = await getSandboxForConversation(req.params.conversation_id);
  if (sandbox) {
    await sandbox.process.signal("SIGTERM");
    res.json({ success: true });
  } else {
    res.status(404).json({ error: "Session not found" });
  }
});
```

**Success criteria:**
- [ ] Cancel button in Chat UI
- [ ] Sends SIGTERM to sandbox
- [ ] SDK aborts gracefully
- [ ] Conversation shows "Cancelled"

---

### Task 7: Testing & Validation

**Test scenarios:**

1. **Basic execution**
   - [ ] Send prompt, receive streaming response
   - [ ] Tool calls display correctly
   - [ ] Cost shown at completion

2. **Session continuity**
   - [ ] Send first prompt
   - [ ] Send follow-up prompt
   - [ ] Context from first preserved

3. **Cancellation**
   - [ ] Start long task
   - [ ] Click cancel
   - [ ] Verify graceful termination

4. **Error handling**
   - [ ] Invalid OAuth token
   - [ ] Sandbox timeout
   - [ ] SDK error

5. **Concurrent sessions**
   - [ ] Multiple users simultaneously
   - [ ] No cross-contamination

---

## Dependencies

**NPM packages:**
- `@daytonaio/sdk` - Daytona TypeScript SDK
- `@anthropic-ai/claude-agent-sdk` - Claude Agent SDK (in sandbox)

**Services:**
- Daytona cloud account
- Claude OAuth token (per user)
- GitHub token (for MCP server)

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| SDK API changes | Medium | Pin version, monitor releases |
| Daytona outages | High | Fallback to direct API calls? |
| Token expiry | Low | Relevance handles OAuth refresh |
| Large responses | Medium | Implement streaming, pagination |
| Cost overruns | Medium | Budget limits per session |

---

## Rollout Plan

**Week 1: Infrastructure**
- Day 1-2: Daytona snapshot (Task 1)
- Day 3-4: HarvestRuntime (Task 2)
- Day 5: Message mapping (Task 3)

**Week 2: Frontend + Polish**
- Day 1-2: HarvestToolViewer (Task 4)
- Day 3: Session management (Task 5)
- Day 4: Cancellation (Task 6)
- Day 5: Testing (Task 7)

**Week 3: Production**
- Day 1-2: Staging deployment
- Day 3: Internal dogfooding
- Day 4: Bug fixes
- Day 5: Production release (feature flag)

---

## Success Metrics

- Cold start time < 500ms (with snapshot)
- Message latency < 100ms (streaming)
- Cancel response < 2s
- Zero permission-related failures
- Cost tracking accuracy 100%

---

## Appendix: POC Code

See `packages/daytona-executor/poc/test-sdk-invocation.ts` for working POC.
