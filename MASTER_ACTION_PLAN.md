# Harvest Master Action Plan

**Last Updated**: 2026-01-14
**Status**: In Progress - AI Rules Fixes Complete, Ready for Implementation Phase

---

## Current Status

### ✅ Completed
- **AI Rules Documentation** - Comprehensive rules for autonomous agent behavior
- **Audit & Integration Analysis** - Relevance AI integration approved
- **4 Critical Fixes Implemented** - Panic Button, Checkpoint Cleanup, Gemini Fallback, Squash Scope
- **Rules Ready for Implementation** - All documented in `/docs/ai/`

### 🔄 Next Immediate Actions (THIS WEEK)
1. **Get adversarial review feedback** on the 4 fixes
2. **Address review feedback** if any BLOCKERs/SHOULDs identified
3. **Start implementation phase** - Build Relevance AI agent + Modal executor

### 📋 Consolidated Plans
- **Technical Architecture**: `/docs/plans/IMPLEMENTATION_PLAN.md` (Phase 1-4, MVP scope)
- **Modal Infrastructure Details**: `/docs/plans/phase-1.1-modal-sandbox.md` (detailed Block 1.1)
- **AI Agent Rules**: `/docs/ai/ADVERSARIAL_REVIEW_PLAN.md` (behavioral rules)
- **Fixes Submitted**: `/GEMINI_REVIEW_REQUEST.md` (4 critical fixes)

---

## Phase 0: Rules & Architecture (Current Phase)

### ✅ Block 0.1: AI Rules Documentation
**Status**: COMPLETE
- `docs/ai/autonomous-agent.md` - Autonomous agent behavior
- `docs/ai/local-development.md` - Local dev + Claude rules
- `docs/ai/shared/git-workflow.md` - Safe-Carry-Forward, Checkpoint, Panic Button
- `docs/ai/shared/code-comments.md` - Code quality standards
- `docs/ai/shared/planning.md` - Planning & validation workflow
- `docs/ai/shared/pull-requests.md` - PR conventions

### ⚠️ Block 0.2: 4 Critical Fixes (Pending Review)
**Status**: IMPLEMENTED, AWAITING FEEDBACK

**Fixes Applied**:
1. **Panic Button Expansion** - Added 8 system/environment error criteria
2. **Checkpoint Cleanup Policy** - Auto-expiry, session termination cleanup
3. **Gemini Fallback Strategy** - Heuristic self-review checklist for offline planning
4. **Squash Scope Clarity** - WIP snapshots vs logical commits guideline

**Location**: `/GEMINI_REVIEW_REQUEST.md` (comprehensive review document)

**Next**:
- [ ] Submit to Gemini for adversarial review
- [ ] Collect feedback (BLOCKERs, SHOULDs, CONSIDERs)
- [ ] Iterate if needed
- [ ] Finalize and merge to docs

---

## Phase 1: Foundation (Starting ASAP)

### Block 1.1: Modal Sandbox Infrastructure
**Goal**: Core execution environment for coding sessions
**Effort**: 1-2 weeks
**Status**: READY TO BUILD

**Key Deliverables**:
- [ ] Modal account setup + authentication
- [ ] Base image builder script
- [ ] Scheduled job for 30-min image refresh
- [ ] Snapshot save/restore system
- [ ] Test harness for sandbox spin-up

**File Location**: `/docs/plans/phase-1.1-modal-sandbox.md` (detailed specs)

---

### Block 1.2: GitHub App Integration
**Goal**: Secure automated GitHub access
**Effort**: 1 week
**Status**: DESIGN READY

**Key Deliverables**:
- [ ] GitHub App registered (permissions defined in IMPLEMENTATION_PLAN.md)
- [ ] Installation token generation service
- [ ] Git operations wrapper (clone, commit, push)
- [ ] Branch management utilities
- [ ] User attribution system

---

### Block 1.3: OpenCode Server Integration
**Goal**: Deploy OpenCode as core coding agent
**Effort**: 1 week
**Status**: DESIGN READY

**Key Deliverables**:
- [ ] OpenCode installed in Modal images
- [ ] Config setup (pointing to `/app/docs/ai/` instructions)
- [ ] Custom tools scaffolding (test runner, Slack updates)
- [ ] Plugin system setup

---

## Phase 2: API Layer (Weeks 3-4)

### Block 2.1: Cloudflare Workers + Durable Objects
**Goal**: Scalable API with per-session state
**Effort**: 1-2 weeks
**Status**: DESIGN READY

### Block 2.2: REST & WebSocket Endpoints
**Goal**: Comprehensive API for all client types
**Effort**: 1 week
**Status**: DESIGN READY

**See**: `/docs/plans/IMPLEMENTATION_PLAN.md` Phase 2 section

---

## Phase 3: Slack Bot Client (Weeks 4-5)

### Block 3.1: Slack Bot Integration
**Goal**: Primary Slack-based interface
**Effort**: 1-2 weeks
**Status**: DESIGN READY

**Key Components**:
- Slack app configuration
- Repository classifier
- Block Kit message templates
- Status update handling

**See**: `/docs/plans/IMPLEMENTATION_PLAN.md` Phase 3 section

---

## Phase 4: Intelligence & Tools (Weeks 5-6)

### Block 4.1: Core Agent Tools
**Goal**: Essential tools for agent verification
**Effort**: 1 week
**Status**: DESIGN READY

**Tools**:
- Test runner integration
- Slack status updates from agent

### Block 4.2: Basic Metrics Tracking
**Goal**: Track agent effectiveness
**Effort**: 1 week
**Status**: DESIGN READY

---

## How to Use This Plan

### For Immediate Next Steps:
1. Read `/GEMINI_REVIEW_REQUEST.md` (what we just submitted)
2. Get feedback on the 4 fixes
3. Address any blockers/SHOULDs
4. Start Block 1.1 (Modal infrastructure)

### For Implementation Details:
- **Architecture Overview**: `/docs/plans/IMPLEMENTATION_PLAN.md`
- **Modal Specifics**: `/docs/plans/phase-1.1-modal-sandbox.md`
- **Agent Rules**: `/docs/ai/autonomous-agent.md`

### For Code Standards:
- **Git Workflow**: `/docs/ai/shared/git-workflow.md`
- **Code Comments**: `/docs/ai/shared/code-comments.md`
- **Planning Process**: `/docs/ai/shared/planning.md`
- **PR Format**: `/docs/ai/shared/pull-requests.md`

---

## Why This Architecture Works

**Problem**: Building autonomous agent is complex. Many moving parts.

**Solution**: Phased blocks that:
1. Are independently testable
2. Don't block each other
3. Have clear inputs/outputs
4. Can be deployed separately
5. Are isolated from failures

**Risk Mitigation**:
- Clear escalation criteria (Panic Button)
- Checkpoint pattern for recovery
- Safe-Carry-Forward for persistence
- Adversarial planning validation
- Human handoff when needed

---

## Files to Reference

| File | Purpose |
|------|---------|
| `AUDIT_FINDINGS_UPDATED.md` | Why Relevance AI architecture is better |
| `GEMINI_REVIEW_REQUEST.md` | The 4 fixes we just implemented |
| `/docs/plans/IMPLEMENTATION_PLAN.md` | Full technical plan (Phase 1-4) |
| `/docs/plans/phase-1.1-modal-sandbox.md` | Block 1.1 detailed specs |
| `/docs/ai/ADVERSARIAL_REVIEW_PLAN.md` | How AI rules are structured |
| `/docs/ai/autonomous-agent.md` | Agent behavior rules |
| `/docs/ai/shared/` | Shared conventions (git, code, planning, PRs) |

---

## Success Criteria

### Phase 0 (Rules) - THIS WEEK
- [ ] Get feedback on 4 fixes from adversarial review
- [ ] Address any BLOCKERs
- [ ] Finalize rules documentation

### Phase 1 (Foundation) - WEEKS 2-3
- [ ] Modal sandboxes spin up in <5s
- [ ] GitHub App creates PRs successfully
- [ ] OpenCode agent can read rules and execute tasks
- [ ] Basic test running works

### Phase 2 (API) - WEEKS 3-4
- [ ] API handles 10+ concurrent sessions
- [ ] WebSocket real-time updates working
- [ ] Session state persists correctly

### Phase 3 (Client) - WEEKS 4-5
- [ ] Slack bot responds to Slack mentions
- [ ] Classifier picks repo correctly
- [ ] Agent triggered on complex tasks

### Phase 4 (Intelligence) - WEEKS 5-6
- [ ] Agent can run tests autonomously
- [ ] Slack updates from within sandbox
- [ ] Basic metrics tracked

---

## Cleanup Notes

**Deprecated/Removed**:
- ❌ `AUDIT_FINDINGS.md` (old version, replaced by `AUDIT_FINDINGS_UPDATED.md`)
- ❌ `docs/ai/ADVERSARIAL_REVIEW.md` (old format, replaced by `ADVERSARIAL_REVIEW_PLAN.md`)
- ❌ `docs/ai/GEMINI_ADVERSARIAL_REVIEW.md` (old format, replaced by `GEMINI_REVIEW_REQUEST.md`)

**Current Source of Truth**:
- ✅ `MASTER_ACTION_PLAN.md` (THIS FILE - consolidated overview)
- ✅ `AUDIT_FINDINGS_UPDATED.md` (architecture & integration analysis)
- ✅ `GEMINI_REVIEW_REQUEST.md` (4 critical fixes pending review)
- ✅ `/docs/plans/IMPLEMENTATION_PLAN.md` (technical implementation details)
- ✅ `/docs/ai/*` (AI agent rules, shared conventions)

---

## Next Steps (Exact Order)

1. **This hour**: Get adversarial review feedback on the 4 fixes
2. **Today**: Address any BLOCKERs from feedback
3. **Tomorrow**: Finalize rules if feedback received
4. **This week**: Start Block 1.1 (Modal sandbox infrastructure)

---

**Ready to build! 🚀**
