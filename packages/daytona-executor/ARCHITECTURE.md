# Harvest Architecture: Daytona + Claude Agent SDK

## System Overview Diagram

```mermaid
graph TB
    subgraph "User Interface"
        UI[Relevance Chat UI]
        TV[HarvestToolViewer<br/>Right Pane]
    end

    subgraph "External Triggers"
        SL[Slack Bot]
        GH[GitHub Webhooks]
    end

    subgraph "Relevance Backend"
        TR[TriggerRunner]
        CM[ConversationManager]
        HP[HarvestPresetAgent]
        HR[HarvestRuntime.ts]
        MM[MessageMapper]
    end

    subgraph "Daytona Cloud"
        DS[Daytona SDK]
        SB[Sandbox<br/>harvest-snapshot]
    end

    subgraph "Inside Sandbox"
        SDK[Claude Agent SDK]
        QF[query function]
        SM[Session Manager]
    end

    subgraph "Claude Agent"
        CA[Claude Sonnet 4.5]
        TL[Tools: Bash, Read, Write, Edit]
        MCP[MCP Servers]
    end

    subgraph "External Services"
        GHA[GitHub API]
        GEM[Gemini API]
        LIN[Linear API]
        GIT[Git Operations]
    end

    %% User flows
    UI -->|Send prompt| TR
    SL -->|Event| TR
    GH -->|Webhook| TR

    TR --> CM
    CM --> HP
    HP --> HR

    %% Daytona flow
    HR -->|daytona.create| DS
    DS -->|Spawn| SB
    HR -->|codeRun SDK_CODE| SB

    %% SDK flow
    SB --> SDK
    SDK --> QF
    QF --> SM
    SM --> CA

    %% Tool execution
    CA --> TL
    TL --> GHA
    TL --> GIT
    CA --> MCP
    MCP --> GEM
    MCP --> LIN

    %% Response flow
    CA -->|Messages| QF
    QF -->|JSON stream| SB
    SB -->|stdout| HR
    HR -->|Parse| MM
    MM -->|Yield| CM
    CM -->|Stream| UI
    CM -->|Tool calls| TV

    %% Styling
    style UI fill:#e3f2fd
    style TV fill:#e3f2fd
    style SB fill:#fff3e0
    style SDK fill:#fff3e0
    style CA fill:#f3e5f5
    style TL fill:#f3e5f5
```

---

## Message Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant ChatUI
    participant Relevance
    participant Daytona
    participant Sandbox
    participant SDK
    participant Claude

    User->>ChatUI: "Fix the tests"
    ChatUI->>Relevance: POST /conversation/message

    Relevance->>Daytona: daytona.create(snapshot)
    Daytona-->>Relevance: sandbox instance

    Relevance->>Sandbox: codeRun(SDK_CODE)

    Note over Sandbox,SDK: Inside Sandbox
    Sandbox->>SDK: query({ prompt, options })

    SDK-->>Sandbox: { type: "system", subtype: "init", session_id: "abc" }
    Sandbox-->>Relevance: JSON line
    Relevance->>Relevance: Store session_id

    SDK->>Claude: Send prompt
    Claude-->>SDK: "I'll run the tests..."
    SDK-->>Sandbox: { type: "assistant", content: [text] }
    Sandbox-->>Relevance: JSON line
    Relevance-->>ChatUI: Stream text

    Claude->>Claude: tool_use: Bash("npm test")
    SDK-->>Sandbox: { type: "assistant", content: [tool_use] }
    Sandbox-->>Relevance: JSON line
    Relevance-->>ChatUI: Show tool call

    Note over Claude: Execute npm test

    SDK-->>Sandbox: { type: "user", content: [tool_result] }
    Sandbox-->>Relevance: JSON line
    Relevance-->>ChatUI: Show output

    Claude-->>SDK: "Tests pass now"
    SDK-->>Sandbox: { type: "result", total_cost_usd: 0.02 }
    Sandbox-->>Relevance: JSON line
    Relevance-->>ChatUI: Show completion + cost

    Relevance->>Sandbox: sandbox.stop()
```

---

## Session Resume Flow

```mermaid
sequenceDiagram
    participant User
    participant Relevance
    participant Sandbox
    participant SDK

    Note over User,SDK: First Message
    User->>Relevance: "Analyze the codebase"
    Relevance->>Sandbox: query({ prompt, resume: undefined })
    SDK-->>Relevance: { type: "system", session_id: "abc123" }
    Note over Relevance: Store session_id="abc123"
    SDK-->>Relevance: ... response ...

    Note over User,SDK: Follow-up Message (same conversation)
    User->>Relevance: "Now add tests"
    Relevance->>Sandbox: query({ prompt, resume: "abc123" })
    Note over SDK: Resume existing session
    SDK-->>Relevance: { type: "system", session_id: "abc123" }
    Note over SDK: Has full context from first message
    SDK-->>Relevance: "Based on my earlier analysis..."
```

---

## Cancellation Flow

```mermaid
sequenceDiagram
    participant User
    participant ChatUI
    participant Relevance
    participant Sandbox
    participant SDK

    User->>ChatUI: Send long task
    Relevance->>Sandbox: codeRun(SDK_CODE)
    SDK->>SDK: Processing...

    Note over User: Clicks Cancel
    User->>ChatUI: Click Cancel
    ChatUI->>Relevance: POST /harvest/cancel/:id
    Relevance->>Sandbox: process.signal("SIGTERM")

    Note over Sandbox: AbortController.abort()
    SDK-->>Sandbox: { type: "error", code: "ABORTED" }
    Sandbox-->>Relevance: JSON line
    Relevance-->>ChatUI: "Cancelled"
```

---

## Component Layers

```mermaid
graph LR
    subgraph "Layer 1: UI"
        A1[Chat Interface]
        A2[HarvestToolViewer]
    end

    subgraph "Layer 2: Relevance API"
        B1[HarvestPresetAgent]
        B2[HarvestRuntime]
        B3[MessageMapper]
    end

    subgraph "Layer 3: Daytona"
        C1[Daytona SDK]
        C2[Sandbox Instance]
    end

    subgraph "Layer 4: Claude Agent SDK"
        D1[query function]
        D2[Session Manager]
        D3[Tool Executor]
    end

    subgraph "Layer 5: Claude"
        E1[Claude Sonnet 4.5]
    end

    A1 --> B1
    A2 --> B3
    B1 --> B2
    B2 --> C1
    C1 --> C2
    C2 --> D1
    D1 --> D2
    D2 --> D3
    D3 --> E1
```

---

## SDK Message Types

```mermaid
stateDiagram-v2
    [*] --> SystemInit: Session starts
    SystemInit --> AssistantText: Claude responds
    AssistantText --> AssistantToolUse: Needs tool
    AssistantToolUse --> UserToolResult: Tool executed
    UserToolResult --> AssistantText: Continue
    UserToolResult --> AssistantToolUse: Another tool
    AssistantText --> Result: Complete
    Result --> [*]

    note right of SystemInit: session_id, tools, model
    note right of AssistantToolUse: tool_use name, input
    note right of UserToolResult: tool_result content, is_error
    note right of Result: total_cost_usd, success
```

---

## Deployment Architecture

```mermaid
graph TB
    subgraph "Relevance Cloud"
        API[relevance-api-node]
        CHAT[relevance-chat-app]
        DB[(Project Keys DB)]
    end

    subgraph "Daytona Cloud"
        SNAP[harvest-snapshot<br/>Pre-built Image]
        SB1[Sandbox 1<br/>User A]
        SB2[Sandbox 2<br/>User B]
        SB3[Sandbox N<br/>User N]
    end

    subgraph "Anthropic"
        CLAUDE[Claude API]
    end

    CHAT --> API
    API --> DB
    API --> SNAP
    SNAP --> SB1
    SNAP --> SB2
    SNAP --> SB3
    SB1 --> CLAUDE
    SB2 --> CLAUDE
    SB3 --> CLAUDE

    style SNAP fill:#fff3e0
    style SB1 fill:#e8f5e9
    style SB2 fill:#e8f5e9
    style SB3 fill:#e8f5e9
```

---

## Secrets Flow

```mermaid
sequenceDiagram
    participant User
    participant Relevance
    participant DB as Project Keys DB
    participant Daytona
    participant Sandbox
    participant SDK

    User->>Relevance: Configure API keys
    Relevance->>DB: Store encrypted

    User->>Relevance: Send prompt
    Relevance->>DB: GetUserProjectKey("anthropic")
    DB-->>Relevance: oauth_token_xxx
    Relevance->>DB: GetUserProjectKey("github")
    DB-->>Relevance: ghp_xxx

    Relevance->>Daytona: create({ envVars: { CLAUDE_CODE_OAUTH_TOKEN, GITHUB_TOKEN } })

    Note over Daytona: Encrypted in transit
    Note over Sandbox: Available as env vars

    Sandbox->>SDK: Uses CLAUDE_CODE_OAUTH_TOKEN
    SDK->>SDK: Authenticated requests

    Note over Sandbox: Secrets destroyed on stop
```

---

## Key Advantages Over Old Architecture

```mermaid
graph LR
    subgraph "Old Architecture ❌"
        direction TB
        O1[User] --> O2[Relevance]
        O2 --> O3[HarvestRuntime TS]
        O3 --> O4[harvest-client Python]
        O4 --> O5[Modal API]
        O5 --> O6[PTY Manager]
        O6 --> O7[asyncio.Queue]
        O7 --> O8[Stop Hook Detection]
        O8 --> O9[Parse terminal output]
        O9 --> O10[Claude CLI]
    end

    subgraph "New Architecture ✅"
        direction TB
        N1[User] --> N2[Relevance]
        N2 --> N3[HarvestRuntime TS]
        N3 --> N4[Daytona SDK TS]
        N4 --> N5[Sandbox]
        N5 --> N6[Claude Agent SDK]
        N6 --> N7[query AsyncIterator]
        N7 --> N8[Structured JSON]
        N8 --> N9[Type-safe objects]
        N9 --> N10[Claude API]
    end

    style O4 fill:#ffcdd2
    style O6 fill:#ffcdd2
    style O7 fill:#ffcdd2
    style O8 fill:#ffcdd2
    style O9 fill:#ffcdd2
    style N4 fill:#c8e6c9
    style N6 fill:#c8e6c9
    style N7 fill:#c8e6c9
    style N8 fill:#c8e6c9
    style N9 fill:#c8e6c9
```

**Eliminated complexity:**
- ❌ Python subprocess
- ❌ PTY management
- ❌ Stop hook parsing
- ❌ asyncio.Queue
- ❌ Terminal output parsing
- ❌ Root user workarounds

**Gained benefits:**
- ✅ TypeScript end-to-end
- ✅ Structured message types
- ✅ Built-in session management
- ✅ Built-in cost tracking
- ✅ Non-root execution
- ✅ Faster cold starts
