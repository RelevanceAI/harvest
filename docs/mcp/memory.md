# Memory MCP Server

Persistent knowledge graph for tracking context, errors, patterns, and procedures across sessions.

**Server:** `@modelcontextprotocol/server-memory`
**Storage:** `/root/.mcp-memory/memory.jsonl` (Modal volume, per-repo)
**Auth:** None required

## Memory Operations

You have persistent memory via the MCP memory server. Use it actively to learn and improve over time.

### When to Query Memory

**Before any task:**
- Use `search_nodes` to find relevant knowledge for your current task
- Focus on specific entity types based on task context:
  - Testing/debugging → `environment_knowledge`
  - Writing code → `codebase_knowledge`
  - Creating PRs/commits → `process_knowledge`
  - Fixing errors → `incident_knowledge`

**Query examples:**
```
search_nodes(entityType="environment_knowledge")
search_nodes(name="ErrorPatterns")
search_nodes(entityType="process_knowledge", pattern="git|PR")
search_nodes(pattern="playwright|browser")
```

**For related context:**
- Use `open_nodes(name="EntityName")` to see an entity and all its connections
- Follow relationships to traverse the knowledge graph
- Use `read_graph()` sparingly (returns everything, expensive for large graphs)

### When to Update Memory

**After fixing any error (CRITICAL - always do this):**
```
add_observations(
  name="ErrorPatterns",
  observations=["Problem: <describe issue> - Solution: <how you fixed it> [2026-01-14]"]
)
```

**After discovering tool limitations:**
```
add_observations(
  name="EnvironmentConfig",
  observations=["Tool X limitation: <what doesn't work and why>"]
)
```

**After learning project patterns:**
```
add_observations(
  name="LearnedPatterns",
  observations=["Pattern: <what to do> (NOT <anti-pattern>)"]
)
```

**After successful workflows:**
```
add_observations(
  name="WorkflowProcedures",
  observations=["Process for X: step 1, step 2, step 3 [2026-01-14]"]
)
```

**When creating relationships:**
```
create_relations(
  from="ErrorPatterns",
  to="EnvironmentConfig",
  relationType="informs"
)
```

### Memory Entity Reference

| Entity | Type | Purpose |
|--------|------|---------|
| HarvestSession | session_context | Sandbox state, session info |
| EnvironmentConfig | environment_knowledge | Modal, MCP, networking, persistence |
| GitWorkflow | process_knowledge | Git rules, Safe-Carry-Forward, checkpoints |
| WorkflowProcedures | process_knowledge | Testing, PRs, deployment |
| ErrorPatterns | incident_knowledge | Failures, fixes, workarounds |
| LearnedPatterns | codebase_knowledge | Repo-specific conventions discovered |

### Temporal Best Practices

- **Add timestamps** `[YYYY-MM-DD]` to observations when timeliness matters
- **Recent observations** take precedence over older ones
- **Mark superseded facts**: `"SUPERSEDED [2026-01-14]: <old fact> - Now: <new fact>"`
- **Query recent first**: When multiple observations exist, trust newest

### Query Pattern Examples

**Debugging an error:**
```
search_nodes(entityType="incident_knowledge", pattern="<error-keyword>")
→ Gets known error patterns and solutions
```

**Implementing new feature:**
```
search_nodes(entityType="codebase_knowledge")
open_nodes(name="LearnedPatterns")
→ Gets repo-specific conventions
```

**Creating PR:**
```
search_nodes(entityType="process_knowledge", pattern="PR|commit")
→ Gets workflow procedures
```

### Memory Maintenance

**Check memory at session start:**
```
read_graph()  // Once per session to understand full context
```

**After resolving errors, always update:**
```
add_observations(name="ErrorPatterns", observations=["..."])
```

**Monitor memory growth:**
- Memory persists in `/root/.mcp-memory/memory.jsonl`
- If an entity exceeds ~100 observations, consider consolidating
- Mark outdated observations as SUPERSEDED rather than removing

### Observation Format Guidelines

**EnvironmentConfig** - Add when discovering MCP capabilities/limitations, environment behavior:
```
"Tool X limitation: <constraint> (reason: <why it exists>)"
"Service Y accessible at: <URL> (NOT <wrong URL>)"
```

**LearnedPatterns** - Add when finding patterns in codebase, learning architectural decisions:
```
"Use X for Y (NOT Z): <clear directive with anti-pattern>"
"Pattern: <convention description>"
```

**ErrorPatterns** - Add after fixing ANY error (immediately):
```
"Problem: <brief description> - Solution: <specific fix> [YYYY-MM-DD]"
"Workaround for X: <describe hack and why needed>"
```

**WorkflowProcedures** - Add when learning workflows, testing procedures:
```
"Step: <concrete action with commands>"
"Requirement: <must-do before X>"
```

### Memory Persistence

Memory in Harvest persists **per-repository** across sessions:

- Volume name: `harvest-memory-{owner}-{repo}`
- Mount point: `/root/.mcp-memory/`
- First session: Seeded with base entities from `/app/memory-seed.json`
- Subsequent sessions: Continues from previous state

This means the agent learns and improves for each repository over time, accumulating:
- Error patterns specific to the codebase
- Discovered conventions and patterns
- Workflow procedures that work for this project
