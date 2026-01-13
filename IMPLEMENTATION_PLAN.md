# Harvest Implementation Plan

> A multi-phased approach to building a background coding agent inspired by Ramp's Inspect

## Executive Summary

This plan outlines the implementation of Harvest, a background coding agent service that enables autonomous development across multiple repositories. The architecture is designed in isolated, healthy blocks that can be developed, tested, and deployed independently.

---

## Phase 1: Foundation Layer (Weeks 1-3)

### Block 1.1: Modal Sandbox Infrastructure
**Goal**: Create the core execution environment for coding sessions

**Key Components**:
- Modal sandbox setup and configuration
- Image registry system for repository snapshots
- Automated image building pipeline (30-minute refresh cycle)
- Snapshot storage and restoration system

**Deliverables**:
- [ ] Modal account setup and authentication
- [ ] Base image builder script that clones repos and installs dependencies
- [ ] Scheduled job (cron) for building images every 30 minutes
- [ ] Snapshot save/restore functionality
- [ ] Test harness for spinning up sandboxes from snapshots

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

**Success Metrics**:
- Sandbox spin-up time < 5 seconds from snapshot
- Image builds complete successfully for test repositories
- Zero state leakage between sandbox sessions

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

**Success Metrics**:
- Successfully clone private repositories
- Commit and push changes with proper attribution
- Generate installation tokens on-demand

---

### Block 1.3: OpenCode Server Integration
**Goal**: Deploy OpenCode as the core coding agent within sandboxes

**Key Components**:
- OpenCode server installation in Modal images
- Plugin system setup
- Custom tool development framework
- Event listener infrastructure

**Deliverables**:
- [ ] OpenCode installed in base sandbox images
- [ ] Server startup scripts and configuration
- [ ] Plugin scaffolding for custom tools
- [ ] Event hook system (tool.execute.before/after)
- [ ] File operation blocking mechanism (during sync)

**Technical Details**:
```typescript
// Custom OpenCode plugins needed:
- Session spawn tool (create child sessions)
- Session status checker
- Slack messaging tool
- Screenshot capture tool
- Visual verification tool
- File sync blocker plugin
```

**Success Metrics**:
- OpenCode server starts reliably in sandboxes
- Plugins load and execute correctly
- Event hooks trigger appropriately
- API communication established

---

## Phase 2: API & State Management (Weeks 4-6)

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
  - addCollaborator()
}

// Database schema:
- sessions table
- prompts table
- messages table
- collaborators table
- file_changes table
- events table
```

**Success Metrics**:
- Handle 100+ concurrent sessions without degradation
- Real-time message streaming latency < 100ms
- Zero data loss during failover
- Session state persists across client disconnects

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
POST   /api/sessions/:id/collaborators - Add collaborator
GET    /api/repositories          - List available repos
GET    /api/stats                 - Usage statistics
```

**Success Metrics**:
- All endpoints respond < 200ms (p95)
- WebSocket connections stable for 1+ hours
- Authentication flow completes successfully
- API documentation is complete and accurate

---

### Block 2.3: Multiplayer & Collaboration System
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

**Success Metrics**:
- Multiple users can work in same session simultaneously
- All users see updates within 500ms
- Prompt authorship correctly attributed
- No race conditions in prompt queue

---

## Phase 3: Client Interfaces (Weeks 7-10)

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

**Success Metrics**:
- Repository classification accuracy > 90%
- Bot responds within 2 seconds of mention
- Messages render correctly in all Slack clients
- Thread context properly maintained

---

### Block 3.2: Web Interface
**Goal**: Comprehensive web-based client with advanced features

**Key Components**:
- React-based web app
- Real-time chat interface
- Hosted VS Code integration
- Session management dashboard
- Statistics and analytics page

**Deliverables**:
- [ ] Next.js/React web application
- [ ] Real-time chat UI with streaming
- [ ] code-server integration (VS Code)
- [ ] Session list and management views
- [ ] Usage statistics dashboard
- [ ] Mobile-responsive design
- [ ] Desktop streaming view (for visual verification)

**Technical Details**:
```typescript
// Web app stack:
- Next.js 14+ (App Router)
- React 18+
- TailwindCSS for styling
- WebSocket client for real-time updates
- code-server iframe integration
- Chart.js or Recharts for statistics

// Key views:
- /sessions - List all sessions
- /sessions/:id - Session chat interface
- /sessions/:id/code - VS Code editor
- /sessions/:id/preview - Desktop stream
- /stats - Usage analytics
```

**Success Metrics**:
- Page load time < 2 seconds
- WebSocket reconnection handled gracefully
- VS Code loads within 5 seconds
- Mobile experience is fully functional
- Statistics update in real-time

---

### Block 3.3: Chrome Extension
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

**Success Metrics**:
- Extension loads without errors
- Element selection works on major React apps
- Component tree extraction is accurate
- MDM deployment successful

---

## Phase 4: Intelligence & Optimization (Weeks 11-13)

### Block 4.1: Warm Sandbox Pooling
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

**Success Metrics**:
- Session start time < 2 seconds for pooled repos
- Pool hit rate > 80% for top repos
- Pool cost optimized (no excessive idle sandboxes)

---

### Block 4.2: Agent Tools & Skills
**Goal**: Extend agent capabilities with custom tools

**Key Components**:
- Session spawning tool (child sessions)
- Session status checking tool
- Test runner integration
- Feature flag queries (LaunchDarkly)
- Telemetry access (Datadog/Sentry)
- Visual verification tools

**Deliverables**:
- [ ] Child session spawner tool
- [ ] Session status checker tool
- [ ] Test execution tool (pytest/jest/etc)
- [ ] Feature flag query tool
- [ ] Telemetry query tool
- [ ] Screenshot comparison tool
- [ ] Skills library (common patterns)

**Technical Details**:
```typescript
// Custom tools to implement:
1. spawn_session(repo, prompt, context)
2. check_session_status(session_id)
3. run_tests(test_path)
4. query_feature_flags(flag_name)
5. search_telemetry(query, time_range)
6. take_screenshot(url)
7. compare_screenshots(before, after)
8. slack_update(message)
```

**Success Metrics**:
- All tools execute reliably
- Child sessions spawn successfully
- Agent uses tools appropriately
- Skills encode best practices

---

### Block 4.3: Quality Metrics & Analytics
**Goal**: Track and improve agent effectiveness

**Key Components**:
- PR merge rate tracking
- Session outcome classification
- Usage analytics per user/repo
- Cost tracking per session
- A/B testing framework for prompts

**Deliverables**:
- [ ] GitHub webhook handler (PR events)
- [ ] Session outcome tracking
- [ ] Analytics database schema
- [ ] Dashboard for metrics
- [ ] Cost attribution system
- [ ] Prompt experimentation framework

**Technical Details**:
```typescript
// Metrics to track:
- Sessions started
- PRs created
- PRs merged
- Time to PR
- Time to merge
- Cost per session
- Cost per merged PR
- User adoption rate
- Repository usage
- Model usage distribution
- Error rates
```

**Success Metrics**:
- PR merge rate > 30%
- All metrics collected accurately
- Dashboard updates in real-time
- Cost tracking accurate to within 5%

---

## Phase 5: Production Hardening (Weeks 14-16)

### Block 5.1: Monitoring & Observability
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

**Success Metrics**:
- All critical metrics monitored
- Alerts fire reliably
- Mean time to detection < 5 minutes
- Dashboards provide actionable insights

---

### Block 5.2: Security & Compliance
**Goal**: Ensure secure operation and data protection

**Key Components**:
- Authentication and authorization
- Secret management
- Network isolation
- Audit logging
- Compliance documentation

**Deliverables**:
- [ ] Security audit of all components
- [ ] Secrets rotation policy
- [ ] Network security groups
- [ ] Audit log implementation
- [ ] SOC 2 documentation (if needed)
- [ ] Penetration testing

**Technical Details**:
```typescript
// Security measures:
- GitHub OAuth for authentication
- JWT tokens with short expiration
- API rate limiting per user
- Sandbox network isolation
- Secret injection (not hardcoded)
- Encrypted data at rest
- TLS for all connections
- Regular security updates
```

**Success Metrics**:
- Zero high-severity vulnerabilities
- All secrets rotated automatically
- Audit logs complete and searchable
- Security review passed

---

### Block 5.3: Documentation & Onboarding
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

**Technical Details**:
```markdown
// Documentation structure:
/docs
  /user-guide
    - getting-started.md
    - slack-usage.md
    - web-interface.md
    - chrome-extension.md
  /developer-guide
    - architecture.md
    - local-development.md
    - adding-tools.md
    - creating-skills.md
  /api
    - openapi.yaml
    - examples.md
  /videos
    - intro.mp4
    - slack-demo.mp4
    - web-demo.mp4
```

**Success Metrics**:
- Documentation covers all features
- New users can start session within 5 minutes
- Developer can add new tool within 2 hours
- Positive feedback on documentation

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
- **Web**: Next.js 14+, React 18+, TailwindCSS
- **Chrome Extension**: Manifest v3, Plasmo framework
- **Hosted Editor**: code-server

### Integrations
- **GitHub**: Octokit.js
- **Feature Flags**: LaunchDarkly SDK
- **Monitoring**: Datadog, Sentry
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
- **E2E Tests**: Critical user flows (Slack, Web)
- **Load Tests**: API and sandbox performance
- **Security Tests**: Penetration testing, vulnerability scans

### Deployment Strategy
- **Preview Environments**: Per-PR deployments
- **Staging**: Full production replica
- **Production**: Gradual rollout with feature flags
- **Rollback Plan**: Automated rollback on error spike

---

## Success Criteria

### Phase 1 Success
- ✅ Sandbox spins up in < 5 seconds
- ✅ GitHub operations work reliably
- ✅ OpenCode executes commands successfully

### Phase 2 Success
- ✅ API handles 100+ concurrent sessions
- ✅ WebSocket streaming works reliably
- ✅ Multiplayer sessions function correctly

### Phase 3 Success
- ✅ Slack bot classifies repos > 90% accuracy
- ✅ Web interface is fully functional
- ✅ Chrome extension works on target apps

### Phase 4 Success
- ✅ Session start time < 2 seconds (pooled)
- ✅ All custom tools work reliably
- ✅ Metrics dashboard is live

### Phase 5 Success
- ✅ No critical security vulnerabilities
- ✅ All documentation complete
- ✅ Team trained and onboarded

### Overall Success (6 months post-launch)
- 🎯 **30%+ of PRs created by Harvest**
- 🎯 **80%+ user adoption on engineering team**
- 🎯 **60%+ PR merge rate**
- 🎯 **< $X per merged PR** (define based on budget)

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

## Next Steps

### Immediate Actions (Week 1)
1. ✅ Set up Modal account and basic sandbox
2. ✅ Create GitHub App with required permissions
3. ✅ Install OpenCode locally and understand SDK
4. ✅ Set up Cloudflare Workers project
5. ✅ Create project repository structure

### Week 2-3 Goals
1. 🔄 Complete Block 1.1: Modal sandbox with snapshots
2. 🔄 Complete Block 1.2: GitHub App integration
3. 🔄 Start Block 1.3: OpenCode in sandboxes

### Monthly Check-ins
- Review progress against plan
- Adjust timeline based on learnings
- Celebrate wins and merged PRs
- Gather user feedback

---

## Conclusion

This plan provides a structured approach to building Harvest, with each block designed to be independently developed and tested. The phased approach allows for early validation of core concepts while building toward a comprehensive system.

The key to success is maintaining focus on the core value proposition: **enabling developers to ship more, faster, with AI as a true collaborative partner**.

Let's harvest some code! 🌾
