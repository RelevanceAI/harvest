# Documentation Standards

Keep documentation fresh and useful. These rules apply to all contributors (human and AI).

## Core Principles

### Update existing docs
If your changes affect READMEs or other docs, update them in the same commit.

**Examples**:
- Added a new environment variable? Update the setup section in README.md
- Changed an API endpoint? Update API documentation
- Modified a CLI command? Update the CLI usage guide

### Document new functionality
New features need documentation — don't leave them undiscovered.

**What to document**:
- Public APIs and their parameters
- Configuration options
- Setup steps for new features
- Usage examples

**Where to document**:
- User-facing features: README.md, user guides
- Developer features: Architecture docs, code comments
- Agent behavior: `docs/ai/` rules

### Capture gotchas
If you hit something non-obvious or learned something important, document it for future devs (and future you).

**Examples**:
- "Modal sandboxes must run as root for Claude CLI OAuth" → Document in architecture
- "Git credential helper must be configured BEFORE cloning" → Document in code comments
- "SQLite session state survives sandbox restarts" → Document in session state docs

**Where to capture gotchas**:
- Inline code comments (WHY this is needed)
- Architecture documentation (design decisions)
- Implementation notes in `.claude/plans/`

### Avoid values that rot
Don't hardcode counts or metrics that will become stale.

**Bad**:
```markdown
We have 47 API endpoints across 12 modules.
```

**Good**:
```markdown
API endpoints are organized by domain (see `src/api/` directory).
```

**Why**: Static numbers become outdated immediately and mislead readers.

**Acceptable exceptions**:
- Benchmarks with dates: "As of 2026-01-15, cold start time is 4.9s"
- Historical context: "Originally had 3 endpoints, now grown to domain-organized structure"

## Documentation Hierarchy

### 1. README.md (Evergreen)
- Current architecture and capabilities
- Getting started guide
- Prerequisites and setup
- Testing and deployment

**Avoid**: PR-specific migration details (put those in PR descriptions)

### 2. Architecture Docs (`docs/architecture/`)
- Design decisions and rationale
- System diagrams
- Component responsibilities
- Integration patterns

### 3. Implementation Plans (`docs/plans/`)
- Phase-based roadmap
- Technical specifications
- Success criteria

### 4. Planning Workflow (`.claude/plans/`)
- Research → Plan → Implementation workflow
- Timestamped versions per branch
- Audit trail of decisions

### 5. AI Agent Rules (`docs/ai/`)
- Agent behavior guidelines
- Shared conventions
- Context-specific rules

## When to Create New Docs

**Create a new doc when**:
- Introducing a major subsystem (needs architecture doc)
- Adding a multi-step workflow (needs guide)
- Defining new conventions (needs shared rule)

**Don't create a new doc when**:
- It duplicates existing docs (update the existing one)
- It's a one-time implementation detail (put in PR or code comments)
- It will go stale quickly (put in code, not docs)

## Maintenance

### Review docs when
- Starting new work (check if existing docs still accurate)
- Completing PRs (update any affected docs)
- Onboarding new team members (see what's confusing)

### Delete docs when
- Feature removed entirely
- Docs superseded by better documentation
- Content moved elsewhere (add redirect/note)

**Never**: Leave outdated docs without cleanup. Stale docs are worse than no docs.

### Maintaining llms.txt Index

When creating new documentation files, add them to `llms.txt` in the appropriate section.

**Trigger**: Adding or removing markdown documentation

**Steps**:
1. Create/update the source documentation file
2. Add entry to `llms.txt` under appropriate section header
3. Commit changes together (atomic update)

**Example**:
```bash
# Add new MCP server guide
echo "# Linear MCP Guide" > docs/mcp/linear.md

# Add to llms.txt under "MCP Server Guides" section
# (edit llms.txt and add line: - [Linear MCP](docs/mcp/linear.md): Linear issue tracking integration)

git add docs/mcp/linear.md llms.txt
git commit -m "docs(mcp): add Linear MCP guide"
```

**Detection**: Optional CI check warns if llms.txt appears outdated
```bash
# Count markdown files vs indexed entries
DOCS_COUNT=$(find docs -name "*.md" | wc -l)
INDEX_COUNT=$(grep -E '^\- \[' llms.txt | wc -l)
```

## Examples

### Good Documentation Flow

**Scenario**: Adding secure credential management

1. **During development**:
   - Add code comments explaining WHY (not WHAT):
     ```python
     # Use printf instead of echo to avoid shell interpretation of special chars
     await sandbox.exec("bash", "-c", f"printf '%s\\n' '{creds}' > ~/.git-credentials")
     ```

2. **In the PR**:
   - Update README.md security section
   - Document design decision in architecture docs
   - Add testing section for security tests

3. **After merge**:
   - Ensure README reflects new state (not migration)
   - Archive planning docs in `.claude/plans/`

### Bad Documentation Flow

**Scenario**: Adding feature without docs

1. Implements new session state management
2. Creates PR with code only
3. Merges without updating README
4. Future developers confused about where state is stored

**Result**: Team wastes time reverse-engineering from code

## Quick Checklist

Before submitting a PR:
- [ ] Updated README if user-facing changes
- [ ] Updated architecture docs if design changes
- [ ] Added code comments for non-obvious decisions
- [ ] Removed stale information (counts, old approaches)
- [ ] Documented gotchas discovered during implementation
- [ ] Checked that docs describe current state, not migration

---

**Remember**: Documentation is part of the feature. Incomplete documentation = incomplete feature.
