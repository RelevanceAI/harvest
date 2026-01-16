# Complexity Decision Heuristic

## When to Use Brainstorming

Before starting any task, evaluate against these criteria:

### Invoke `/superpowers:brainstorming` if ANY:

- ✅ **Architectural changes**: New modules, design patterns, infrastructure
- ✅ **Multi-module impact**: Changes span 3+ files across different subsystems
- ✅ **New feature**: Not a bug fix, refactor, or docs update
- ✅ **Uncertain approach**: Multiple valid solutions, unclear best path
- ✅ **User signals design**: Mentions "design", "architecture", "how should we"
- ✅ **High-risk areas**: Security, performance, data handling, payments, auth
- ✅ **Memory suggests**: Query memory for similar tasks that needed brainstorming

### Skip Brainstorming if ALL:

- ❌ Bug fix in single file with clear root cause
- ❌ Documentation/README/config changes only
- ❌ Simple refactor (rename, extract function, format)
- ❌ Clear, unambiguous task with obvious implementation
- ❌ Similar successful tasks skipped brainstorming (per memory)

### When Uncertain

Ask user directly:
"This task seems [simple/moderately complex]. Should I brainstorm the design approach, or proceed directly to planning?"

### Memory Integration

Before deciding:
```
memory_query("Similar tasks to [current task description]")
→ Check ComplexityDecisions entity
→ Did similar tasks need brainstorming?
→ What were outcomes?
```

After task completes:
```
memory_add_observation(
  entity="ComplexityDecisions",
  observation="[DATE] Task '[description]' → [brainstormed/skipped] → Plan [approved first try/needed revisions/rejected] → ASSESS: [GOOD CALL/SHOULD HAVE BRAINSTORMED/OVER-ENGINEERED]"
)
```
