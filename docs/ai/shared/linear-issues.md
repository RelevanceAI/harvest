# Linear Issues - AI Agent Guide

**Prerequisites:** Linear MCP server configured in Claude Code setup.

## Philosophy

Linear issues are team communication tools, not dumping grounds. Keep them clean, scannable, and useful for both humans and AI.

**Core Principles:**
- Update before creating
- Search before duplicating
- Ask before acting if uncertain
- Always prefix AI contributions with 🤖

**AI Boundaries:**
- Never close issues without approval (except confirmed duplicates)
- Never assign P0/P1 without validation
- Never delete anything
- Always provide clear reasoning

---

## When to Create vs Update

### Update When:
- Adding info to known bug (logs, repro steps)
- Linking PRs or branches
- Automated status updates
- Appending feedback to existing request
- You find a duplicate (link it, don't create)

### Create When:
- Truly novel problem with no counterpart
- Critical event (outage, security issue)
- Systemic issue from multiple reports

### Do Nothing When:
- Information is ambiguous or incomplete
- Similar issue exists and is active
- Request is outside your scope
- You lack confidence in the action

**Golden Rule:** Search first with `list_issues`. If unsure, ask.

---

## Issue Titles

**Format:** `<TYPE>: [Context] Clear, specific description`

**Types:** `BUG`, `FEAT`, `TASK`, `CHORE`, `DOCS`

**Good:**
- ✅ `BUG: [Mobile] Google SSO login fails on iOS 17`
- ✅ `FEAT: [Dashboard] CSV export for analytics`

**Bad:**
- ❌ `Fix bug` - what bug?
- ❌ `ENG-123` - use words

**Rules:** <60 chars, specific area, imperative mood, focus on WHAT not HOW

---

## Issue Descriptions

### Bug Template

```markdown
## Problem
[What's broken, impact - 2-3 sentences]

## Steps to Reproduce
1. Navigate to...
2. Click...
3. Observe...

## Expected vs Actual
Expected: [...]
Actual: [...]

## Environment
- Platform/Browser/OS
- Version/Build

## Impact
- Severity: P0-P3
- Affected: [users/segment]
```

### Feature Template

```markdown
## User Story
As a [user type], I want [goal] so that [benefit].

## Problem/Opportunity
[Why this matters - 2-3 sentences]

## Acceptance Criteria
- [ ] Testable criterion 1
- [ ] Testable criterion 2

## Out of Scope
[What this does NOT include]
```

### Task Template

```markdown
## Objective
[What needs doing]

## Context
[Why necessary, how it fits]

## Definition of Done
- [ ] Task complete
- [ ] Tests passing
```

**AI Tips:**
- Extract key info from unstructured data (logs, emails, chats)
- Summarize long logs instead of pasting raw output
- Link to monitoring/metrics when available
- Focus on user value for features, not implementation

---

## Labels and Metadata

### Standard Taxonomy

**Type:** `bug`, `feature`, `task`, `chore`, `docs`
**Priority:** `P0-blocker`, `P1-high`, `P2-medium`, `P3-low`
**Component:** `frontend`, `backend`, `mobile`, `api`, `auth`

### AI Labeling Strategy

```typescript
// Check available labels first
const labels = await list_issue_labels({ team: "ENG" })

// Apply based on content analysis
const suggestedLabels = analyzeIssueContent(description)
  .filter(label => teamLabels.includes(label))

// Create with labels
create_issue({
  labels: ["bug", "mobile", "auth"], // Don't create P0/P1 without validation
  ...
})
```

**Guidelines:**
- Use keyword matching and content analysis
- Check existing labels before creating new ones
- Let humans set P0/P1 unless explicitly instructed
- Assign to specific person when known

---

## Comments

### When to Comment

**Do:**
- Link related issues/PRs/duplicates
- Add technical info (logs, traces, metrics)
- Summarize long discussions
- Automated status updates

**Don't:**
- Update description instead if that's the right place
- Add conversational fluff ("thanks!", "LGTM")
- Comment when uncertain - ask instead

### Format

```markdown
🤖 [Action/Information]

[Details if needed]
```

**Examples:**
- ✅ `🤖 Linked duplicate: ENG-789 has same root cause`
- ✅ `🤖 Build failed on abc123. Timeout in health check`
- ❌ `Thanks for creating this!`

---

## Issue Relationships

**Duplicates:** Link and close newer one with explanation
**Blockers:** AI suggests, humans confirm
**Related:** Only link when genuinely relevant

### Finding Duplicates

```typescript
const existing = await list_issues({
  query: "login Google SSO",
  team: "ENG",
  state: "open"
})

// If found, link it
await create_comment({
  issueId: newId,
  body: "🤖 Duplicate of ENG-789. Both describe Google SSO failures on mobile."
})

await update_issue({
  id: newId,
  duplicateOf: "ENG-789"
})
```

---

## Common Workflows

### Creating a Bug

```typescript
// 1. Search first
const existing = await list_issues({
  query: "auth timeout",
  label: "bug",
  state: "open"
})

// 2. Create if no duplicate
await create_issue({
  team: "ENG",
  title: "BUG: [API] Auth timeout on mobile",
  description: `## Problem
30s timeout on login, then retry required.

## Steps to Reproduce
1. Open app (iOS 17.2)
2. Tap "Login"
3. Enter credentials
4. Observe timeout

## Expected vs Actual
Expected: Login in 2-3s
Actual: 30s timeout, error

## Environment
- iOS 17.2, App 2.4.1
- Backend: auth-service 1.3.2

## Impact
- Severity: P1-High
- Affected: ~15% iOS users`,
  labels: ["bug", "mobile", "api"],
  assignee: "backend-lead"
})
```

### Linking PR to Issue

```typescript
// In PR description
const prBody = `
## Context
🐛 Fixes auth timeout. Resolves ENG-456.
...
`

// Comment on issue
await create_comment({
  issueId: "ENG-456",
  body: "🤖 PR opened: https://github.com/org/repo/pull/789"
})
```

---

## MCP Tools Quick Reference

**Issues:** `list_issues`, `get_issue`, `create_issue`, `update_issue`
**Comments:** `list_comments`, `create_comment`
**Labels:** `list_issue_labels`, `create_issue_label`
**Projects:** `list_projects`, `get_project`
**Teams/Users:** `list_teams`, `get_team`, `list_users`, `get_user`

See function signatures in Claude Code for full parameters.

---

## Common Mistakes

❌ **Vague titles** - Be specific
❌ **Creating duplicates** - Search first
❌ **Missing repro steps** - Every bug needs them
❌ **No acceptance criteria** - Features need clear "done" definition
❌ **Chatty comments** - Be informative, not conversational
❌ **Wrong priority** - Don't mark everything urgent
❌ **Stale descriptions** - Update when context changes

### AI-Specific Pitfalls

❌ **Over-automation** - Don't create circular updates
❌ **Insufficient search** - Leads to duplicates
❌ **Acting on ambiguity** - Ask instead
❌ **Losing context** - Read full issue before commenting
❌ **Ignoring rate limits** - Batch operations when possible

---

## Decision Tree: Should I Act?

```
Is info complete and unambiguous?
  ├─ NO → Ask user or do nothing
  └─ YES → Does similar issue exist?
      ├─ YES → Update/link existing
      └─ NO → Is it within my scope?
          ├─ NO → Ask user
          └─ YES → Is priority/impact clear?
              ├─ NO → Create with P2/P3, let humans triage
              └─ YES → Create with confidence
```

**When in doubt: Ask, don't act.**
