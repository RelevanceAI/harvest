# Harvest Implementation Plan

> A multi-phased approach to building a background coding agent inspired by Ramp's Inspect

## Status Overview (Updated: January 2026)

| Phase | Block | Status | Implementation |
|-------|-------|--------|----------------|
| **Phase 1: Foundation** | | **🟢 Partially Complete** | |
| | 1.1: Modal Sandbox Infrastructure | ✅ Complete | `packages/modal-executor/` |
| | 1.2: GitHub App Integration | ❌ Not Started | Using GitHub PAT (interim) |
| | 1.3: Agent Runtime | ✅ Complete | Claude Code CLI (superseded OpenCode) |
| **Phase 2: API Layer** | | ⏸️ Blocked | Awaiting `harvest-client` wrapper |
| **Phase 3: Client** | | ❌ Not Started | |
| **Phase 4: Intelligence** | | ❌ Not Started | |

**Current Blocker**: `harvest-client` Python package needs to be created to wrap `HarvestSandbox` for external consumption (estimated: 2-4 hours).

---

## Executive Summary

This plan outlines the implementation of Harvest, a background coding agent service that enables autonomous development across multiple repositories. The architecture is designed in isolated, healthy blocks that can be developed, tested, and deployed independently.

**Latest Update**: Phase 1.1 (Modal Sandbox Infrastructure) and 1.3 (Agent Runtime Integration) completed January 2026. Harvest now provides production-ready Modal sandboxes with Claude Code CLI, session state persistence, and full MCP server support.

---

## Phase 1: Foundation

### Block 1.1: Modal Sandbox Infrastructure ✅ **COMPLETE**
**Goal**: Create the core execution environment for coding sessions

**Status**: ✅ Completed January 2026
- Implementation: `packages/modal-executor/` (1,927 lines)
- Tests: 9 test files + 2 POC validation files
- Git commit: `7730454` - "feat: OpenCode → Claude Code CLI migration with streaming (#2)"

**Key Components**:
- ✅ Modal sandbox setup and configuration
- ✅ Image registry system for repository snapshots
- ✅ Automated image building pipeline (30-minute refresh cycle)
- ✅ Session state persistence via SQLite on Modal volumes

**Deliverables**:
- [x] Modal account setup and authentication
- [x] Base image builder script that clones repos and installs dependencies
- [x] Scheduled job (cron) for building images every 30 minutes
- [x] HarvestSandbox class with async API (`sandbox.py`: 615 lines)
- [x] Claude Code CLI integration with streaming (`claude_cli.py`: 232 lines)
- [x] Session state persistence (`session_state.py`: 166 lines)
- [x] MCP servers installed (memory, filesystem, playwright, devtools, github, gemini, sentry)
- [x] Git credential security with Safe-Carry-Forward workflow
- [x] Test harness for spinning up sandboxes from snapshots

**Technical Details**:
```python
# Core functionality needed:
- modal.Image.debian_slim() base configuration
- Git clone with GitHub App installation tokens
- Dependency installation (npm/pip/etc)
- Build command execution
- modal.Volume or modal.CloudBucketMount for snapshots
- Fast sandbox spin-up (<5 seconds target)
```

---

### Block 1.2: GitHub App Integration
**Goal**: Secure, automated GitHub access for repository operations

**Key Components**:
- GitHub App creation and configuration
- Installation token generation system
- Git operations wrapper (clone, commit, push)
- Dynamic git config management

**Deliverables**:
- [ ] GitHub App registered with appropriate permissions
- [ ] Token generation service
- [ ] Git wrapper library for sandbox operations
- [ ] User attribution system for commits
- [ ] Branch management utilities

**Technical Details**:
```python
# Required GitHub App permissions:
- Repository: Read & Write access
- Pull requests: Read & Write
- Contents: Read & Write
- Metadata: Read-only

# Git config management:
- Dynamic user.name and user.email setting per session
- Branch creation and management
- Commit attribution tracking
```

---

### Block 1.3: Agent Runtime Integration ✅ **COMPLETE** (Superseded)
**Goal**: Deploy AI coding agent within sandboxes

**Implementation Decision**: Migrated from OpenCode to **Claude Code CLI** (Anthropic's official CLI)
- Reason: Anthropic policy blocks third-party OAuth wrappers
- Solution: Direct Claude Code CLI integration with team subscription OAuth
- Status: ✅ Completed January 2026 (part of Block 1.1 implementation)

**What Was Built**:
- [x] Claude Code CLI installed in base sandbox images (`images.py:116`)
- [x] OAuth token authentication (`claude_cli.py`)
- [x] JSON streaming wrapper with async iteration (`claude_cli.py:63-150`)
- [x] MCP server integration (memory, filesystem, playwright, devtools, github, gemini)
- [x] Session state persistence for conversation continuity (`session_state.py`)

**Technical Details**:
```python
# Claude Code CLI integration with streaming:
async def stream_prompt(prompt: str, oauth_token: str) -> AsyncIterator[str]:
    proc = await asyncio.create_subprocess_exec(
        "claude", "--print", "--output-format", "stream-json", prompt,
        # ... streams JSON events line-by-line
    )
```

**Note**: Custom tools (test runner, slack updates) deferred to Phase 4 (Intelligence layer).

---

## Phase 2: API Layer

### Block 2.1: Cloudflare Workers + Durable Objects Setup
**Goal**: Create scalable, performant API with per-session state

**Key Components**:
- Cloudflare Workers deployment
- Durable Objects for session state
- SQLite database per session
- WebSocket handling via Agents SDK

**Deliverables**:
- [ ] Cloudflare Workers project structure
- [ ] Durable Object class for sessions
- [ ] SQLite schema design for session state
- [ ] WebSocket connection management
- [ ] Real-time streaming infrastructure

**Technical Details**:
```typescript
// Session Durable Object structure:
class SessionDurableObject {
  state: DurableObjectState;
  db: SqlStorage; // Per-session SQLite

  // Core methods:
  - createSession()
  - sendPrompt()
  - streamResponse()
  - updateStatus()
  - getHistory()
}

// Database schema:
- sessions table
- prompts table
- messages table
- file_changes table
- events table
```

---

### Block 2.2: REST & WebSocket API Endpoints
**Goal**: Expose comprehensive API for all client types

**Key Components**:
- RESTful endpoints for session management
- WebSocket endpoints for real-time communication
- Authentication middleware
- Rate limiting and quota management

**Deliverables**:
- [ ] API route definitions and handlers
- [ ] WebSocket connection upgrade logic
- [ ] Authentication flow (GitHub OAuth)
- [ ] Token validation and refresh
- [ ] API documentation (OpenAPI spec)

**Technical Details**:
```typescript
// Core API endpoints:
POST   /api/sessions              - Create new session
GET    /api/sessions/:id          - Get session details
POST   /api/sessions/:id/prompts  - Send prompt
DELETE /api/sessions/:id          - Stop/delete session
GET    /api/sessions/:id/events   - Stream events (WebSocket)
GET    /api/repositories          - List available repos
GET    /api/stats                 - Usage statistics
```

---

## Phase 3: Client

### Block 3.1: Slack Bot Client
**Goal**: Primary interface for team-based collaboration

**Key Components**:
- Slack app configuration
- Message handling and parsing
- Repository classifier (GPT-4o-mini)
- Rich message formatting (Block Kit)
- Thread-based conversations

**Deliverables**:
- [ ] Slack app registered and configured
- [ ] Bot event handlers (messages, mentions)
- [ ] Repository classification system
- [ ] Block Kit message templates
- [ ] Thread context tracking
- [ ] Status update messages from agent
- [ ] Custom emoji set

**Technical Details**:
```typescript
// Slack integration components:
- @slack/bolt framework setup
- Event listeners: app_mention, message, reaction_added
- Repository classifier prompt engineering
- Block Kit templates for:
  - Session start
  - Progress updates
  - PR creation
  - Error states
  - Session completion
```

---

## Phase 4: Intelligence

### Block 4.1: Core Agent Tools
**Goal**: Essential tools for agent to verify its work

**Key Components**:
- Test runner integration
- Slack status updates from agent

**Deliverables**:
- [ ] Test execution tool (pytest/jest/etc)
- [ ] Slack update tool for agent to post progress
- [ ] Tool registration with OpenCode

**Technical Details**:
```typescript
// Core tools to implement:
1. run_tests(test_path) - Execute test suite, return results
2. slack_update(message) - Post status to Slack thread
```

---

### Block 4.2: Basic Metrics Tracking
**Goal**: Track agent effectiveness and usage

**Key Components**:
- Session tracking
- PR creation/merge tracking
- Basic usage analytics

**Deliverables**:
- [ ] GitHub webhook handler (PR events)
- [ ] Session outcome tracking
- [ ] Basic metrics storage

**Technical Details**:
```typescript
// Metrics to track:
- Sessions started
- PRs created
- PRs merged
- Time to PR
- Time to merge
- Repository usage

// Implementation: TBD
// This is important but we need to figure out the right approach.
// Options to explore:
// - Simple database tables in Durable Objects
// - External analytics service
// - Event streaming to data warehouse
```

---

## Technical Stack Summary

### Infrastructure
- **Sandbox Environment**: Modal.com
- **API & State**: Cloudflare Workers + Durable Objects
- **Database**: SQLite (per session, via Durable Objects)
- **Authentication**: GitHub OAuth
- **Version Control**: GitHub App

### Core Services
- **Coding Agent**: OpenCode
- **Language Models**: Multi-model support (OpenAI, Anthropic, etc.)
- **Repository Classifier**: GPT-4o-mini or GPT-4o

### Client Technologies
- **Slack**: @slack/bolt

### Integrations
- **GitHub**: Octokit.js
- **Communication**: Slack API

---

## Development Principles

### Isolated Block Development
Each block should:
1. Have clear inputs and outputs
2. Be testable independently
3. Have defined interfaces
4. Not block other work
5. Be deployable separately

### Testing Strategy
- **Unit Tests**: 80%+ coverage for business logic
- **Integration Tests**: API endpoints, GitHub operations
- **E2E Tests**: Critical user flows (Slack)
- **Load Tests**: API and sandbox performance

### Deployment Strategy
- **Preview Environments**: Per-PR deployments
- **Staging**: Full production replica
- **Production**: Gradual rollout with feature flags
- **Rollback Plan**: Automated rollback on error spike

---

## Risk Mitigation

### Technical Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Modal sandbox latency | Medium | High | Implement warm pooling, optimize images |
| OpenCode integration issues | Low | High | Deep dive into docs, engage with maintainers |
| WebSocket reliability | Medium | Medium | Implement reconnection logic, heartbeats |
| Cost overruns | Medium | High | Implement strict quotas, monitoring, alerts |

### Adoption Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Low user adoption | Medium | High | Viral Slack integration, showcase wins |
| Poor PR quality | Medium | High | Implement quality checks, skills library |
| Team resistance | Low | Medium | Gradual rollout, training, support |

---

## Conclusion

This plan provides a structured approach to building Harvest, with each block designed to be independently developed and tested. The phased approach allows for early validation of core concepts while building toward a comprehensive system.

The key to success is maintaining focus on the core value proposition: **enabling developers to ship more, faster, with AI as a true collaborative partner**.

Let's harvest some code! 🌾

---

---

# Future Enhancements

> Blocks deferred from MVP. To be prioritized based on learnings and user feedback.

---

## Multiplayer & Collaboration System
**Goal**: Enable real-time collaboration on sessions

**Key Components**:
- Multi-user session access
- Prompt attribution system
- Real-time state synchronization
- Presence indicators

**Deliverables**:
- [ ] Collaborator management system
- [ ] Per-prompt authorship tracking
- [ ] Broadcast system for state updates
- [ ] User presence tracking
- [ ] Conflict resolution for simultaneous prompts

**Technical Details**:
```typescript
// Multiplayer features:
- Add/remove collaborators
- Per-user cursor/activity indicators
- Prompt queue with author attribution
- Real-time file change notifications
- Chat/comment system within sessions
```

---

## Custom Chat App
**Goal**: Native chat interface for Harvest (not generic web UI)

**Note**: This will be our own chat application, not a standard web dashboard.

**Key Components**:
- Real-time chat interface
- Session management
- Integration with existing systems

**Deliverables**:
- [ ] Chat application design
- [ ] Real-time messaging infrastructure
- [ ] Session history and management
- [ ] Mobile support

---

## Chrome Extension
**Goal**: Visual editing interface for React applications

**Key Components**:
- Chrome extension with sidebar API
- DOM and React tree inspector
- Screenshot tool with element selection
- Chat interface within extension

**Deliverables**:
- [ ] Chrome extension manifest v3 setup
- [ ] Sidebar chat interface
- [ ] Element selection and inspection tool
- [ ] React component tree extraction
- [ ] Integration with Harvest API
- [ ] Extension update server
- [ ] MDM deployment configuration

**Technical Details**:
```typescript
// Extension structure:
- manifest.json (v3)
- content_script.js (DOM/React inspection)
- sidebar.html (chat interface)
- background.js (API communication)

// React inspection:
- Access __REACT_DEVTOOLS_GLOBAL_HOOK__
- Extract fiber tree
- Serialize component hierarchy
- Capture styles and props
```

---

## Warm Sandbox Pooling
**Goal**: Minimize session start latency

**Key Components**:
- Pre-warmed sandbox pool
- Pool size management
- Pool refresh on new image builds
- Repository usage prediction

**Deliverables**:
- [ ] Sandbox pool manager
- [ ] Pool size algorithm (based on usage)
- [ ] Pool expiration and refresh logic
- [ ] Usage analytics for pool sizing
- [ ] Monitoring and alerting

**Technical Details**:
```python
# Pool management:
- Maintain N warm sandboxes per high-traffic repo
- Expire sandboxes older than latest image build
- Monitor pool utilization
- Scale pool based on time of day
- Priority allocation for frequent users
```

---

## Advanced Agent Tools
**Goal**: Extend agent capabilities beyond basic test running

**Key Components**:
- Session spawning tool (child sessions)
- Session status checking tool
- Feature flag queries (LaunchDarkly)
- Telemetry access (Datadog/Sentry)
- Visual verification tools

**Deliverables**:
- [ ] Child session spawner tool
- [ ] Session status checker tool
- [ ] Feature flag query tool
- [ ] Telemetry query tool
- [ ] Screenshot comparison tool
- [ ] Skills library (common patterns)

**Technical Details**:
```typescript
// Advanced tools to implement:
1. spawn_session(repo, prompt, context)
2. check_session_status(session_id)
3. query_feature_flags(flag_name)
4. search_telemetry(query, time_range)
5. take_screenshot(url)
6. compare_screenshots(before, after)
```

---

## Advanced Analytics
**Goal**: Deep insights into agent effectiveness

**Key Components**:
- Cost tracking per session
- A/B testing framework for prompts
- User adoption analytics
- Model performance comparison

**Deliverables**:
- [ ] Cost attribution system
- [ ] Prompt experimentation framework
- [ ] Analytics dashboard
- [ ] Model usage distribution tracking

---

## Full Monitoring & Observability
**Goal**: Comprehensive visibility into system health

**Key Components**:
- Structured logging
- Distributed tracing
- Metrics collection
- Alerting rules
- Incident response runbooks

**Deliverables**:
- [ ] Logging infrastructure (Cloudflare Logs)
- [ ] Tracing integration (Datadog/Honeycomb)
- [ ] Metrics dashboards (Grafana/Datadog)
- [ ] Alert definitions (PagerDuty/Opsgenie)
- [ ] Runbooks for common issues

**Technical Details**:
```typescript
// Key metrics to monitor:
- Sandbox spin-up latency (p50, p95, p99)
- API response times
- WebSocket connection health
- Error rates by endpoint
- Model API latency
- Cost per session
- Active sessions count
- Queue depth

// Alerts:
- Sandbox spin-up > 10s
- API error rate > 5%
- WebSocket disconnects > 10%
- Cost spike (>2x daily average)
```

---

## Security Audits & Compliance
**Goal**: Formal security validation

**Key Components**:
- Security audit
- Penetration testing
- SOC 2 documentation
- Secrets rotation automation

**Deliverables**:
- [ ] Security audit of all components
- [ ] Secrets rotation policy
- [ ] Audit log implementation
- [ ] SOC 2 documentation (if needed)
- [ ] Penetration testing

---

## Documentation & Onboarding
**Goal**: Enable team adoption and contribution

**Key Components**:
- User documentation
- Developer documentation
- API documentation
- Video tutorials
- Onboarding flows

**Deliverables**:
- [ ] User guide (how to use Harvest)
- [ ] Developer guide (how to extend Harvest)
- [ ] API documentation (OpenAPI + examples)
- [ ] Architecture documentation
- [ ] Video walkthroughs
- [ ] In-app onboarding flows
- [ ] FAQ and troubleshooting guide
