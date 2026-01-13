# MCP Server Documentation

Detailed documentation for Model Context Protocol (MCP) servers available to the Harvest agent.

## Available MCP Servers

### Required (Always Available)

| Server | Documentation | Purpose |
|--------|---------------|---------|
| **memory** | [memory.md](./memory.md) | Persistent knowledge graph for tracking context, errors, patterns |
| **filesystem** | Built-in | File operations in /workspace |
| **playwright** | [playwright.md](./playwright.md) | Browser automation for testing |
| **devtools** | [devtools.md](./devtools.md) | Chrome DevTools Protocol for browser debugging |

### Optional (Loaded Based on Secrets)

| Server | Documentation | Required Secret | Purpose |
|--------|---------------|-----------------|---------|
| **gemini** | [gemini.md](./gemini.md) | `GEMINI_API_KEY` | Plan review and web research |
| **linear** | Quick reference below | `LINEAR_API_KEY` | Issue tracking |
| **posthog** | Quick reference below | `POSTHOG_API_KEY` | Analytics, feature flags |
| **sentry** | Quick reference below | `SENTRY_AUTH_TOKEN` | Error tracking |

## Quick Reference

For lightweight MCP servers, here's a quick guide:

### Linear
```
# Update an issue
linear_update_issue(issueId="ENG-123", status="In Progress")

# List issues assigned to you
linear_list_issues(assignee="me")
```

### PostHog
```
# Check feature flag
posthog_get_feature_flag(key="new-feature", distinctId="user-123")

# Track event
posthog_capture(event="task_completed", properties={"task_id": "..."})
```

### Sentry
```
# Get issue details
sentry_get_issue(issueId="12345")

# Note: search_events and search_issues require OPENAI_API_KEY (not available)
```

## Adding New MCP Server Documentation

**All servers need:**
1. Entry in MCP Tools Index (`docs/ai/harvest-mode.md`)
2. Entry in MCP servers list (`memory-seed.json` → EnvironmentConfig)

**Heavy servers (>50 lines of docs) also need:**
3. Dedicated doc file: `docs/mcp/{server-name}.md`
4. Entry in this README

### Decision Criteria

**Create separate doc when:**
- Server documentation exceeds ~50 lines
- Server has complex workflows or multi-step patterns
- Server requires extensive examples or query patterns

**Keep in quick reference when:**
- Server usage is straightforward (1-3 tools, obvious usage)
- Instructions fit in 1-2 bullet points
- Examples are simple one-liners
