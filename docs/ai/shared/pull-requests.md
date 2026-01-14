## Pull Request Conventions

### PR Titles

**Format:** `<type>(<scope>): <description> [ID]`

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `refactor` - Code restructuring (behaviour unchanged)
- `docs` - Documentation only
- `test` - Test changes
- `chore` - Build, deps, config

**Examples:**
- ✅ `fix(auth): prevent session timeout during long operations [ENG-456]`
- ✅ `feat(checkout): add one-click payment support`
- ❌ `fix bug` - yeah nah, what bug?
- ❌ `updated files` - cheers for that, very helpful
- ❌ `ENG-123` - mate, use your words

**Breaking Changes:**
Use `!` after the type to flag breaking changes:
- `feat(api)!: change response format for user endpoint [ENG-789]`
- Alternatively, add `BREAKING CHANGE:` in the commit/PR body footer

**Rules:**
- Aim for 50 chars, hard ceiling at 72 (git tooling truncates beyond this)
- Imperative mood: "add", "fix", "prevent" (not "added", "fixes")
- Include Linear URL at the end if one exists, query it from a key if that is all you have
- Be specific about what changed

### PR Description Structure

Use emojis to make Context and Verification scannable at a glance.

```
## Context
[💡/🚀/🐛 + 2-3 sentences max. Link the ticket/ID here.]
Example: 🚀 Adding one-click checkout to reduce friction. Fixes [ENG-123].

## The Approach
[Only if it's complex. Explain the "why this way" for design choices. 🧠
If it's straightforward, skip this section entirely.]

## Verification
- 🧪 **Automated:** [e.g. Auth unit tests & type-check ✅]
- 📱 **Manual:** [e.g. Tested login flow on mobile]
- 🛡️ **Edge cases:** [e.g. Checked 404 handling & slow network]

[Screenshots/Videos for UI changes]

## Note
[Only if there are dependencies or ⚠️ Breaking Change warnings]
```

**Emoji Guide:**
- 🚀 New feature
- 🐛 Bug fix
- 🔧 Refactor/chore
- 📚 Docs
- 💡 Improvement/enhancement
- 🪦 Fixing something proper fucked

### The "Why" Matters

Reviewers need to understand the rationale, not just see code changes.

**Cooked:**
- "See JIRA-123" (makes reviewer hunt for context)
- "Bob asked for it" (not useful documentation)
- "To fix the issue" (what #$%&ing issue?)

**Heaps good:**
- "Profile endpoint was hitting 500ms+ latency at p95, causing poor UX. This caches user data in Redis."
- "React 19 changed Context API; updating our patterns to avoid memory leaks per migration guide."

### The "How" Means Design Decisions

For significant choices, explain why you picked that approach.

**Example:**
```
Implemented as Redis cache rather than query optimization because:
- Query optimization alone wouldn't help during traffic spikes
- Redis TTL (15 mins) fits data freshness requirements
- Alternative: browser caching, but data changes across devices
```

### Verification - Don't Be Vague

**Cooked:**
- "Test it yourself"
- "Works on my machine"
- No mention of what tests were run
- No mention of edge cases

**Heaps good:**
```
## Verification
- 🧪 **Automated:** `npm run check` ✅ (typecheck, lint, 4 tests passed)
- 📱 **Manual:** Toggled dark mode on/off, verified text readable
- 🛡️ **Edge cases:** Rapid toggles, system dark mode, scroll during toggle
```

### Scope - One Thing Per PR

Don't chuck a new feature, UI refactor, database tweak, and two bug fixes into one PR. That's cooked.

**Rule of thumb:** If you need "and" to describe the PR, it's probably two PRs.

- ✅ "feat: add login API endpoint"
- ✅ "feat: add login form UI" (separate PR)
- ❌ "feat: add login with form and API and also fix that other bug"

### For AI-Generated PRs

Since you don't have 6 months of codebase context, be explicit about:

1. **Why this approach over alternatives**
   - "Used TypeScript utility types over generics because caller sites are simpler"

2. **Assumptions made**
   - "Assumed [X] based on [Y] in codebase. Confirm this is correct."

3. **Codebase conventions followed**
   - "Followed pattern from src/hooks/useQuery.ts"
   - "Used BaseToast foundation per CLAUDE.md"

### PR Checklist

Before submitting, verify:

- [ ] Title follows `type(scope): description` format (50 chars aim, 72 max)
- [ ] Breaking changes flagged with `!` if applicable
- [ ] Context has relevant emoji (🚀/🐛/💡/🔧/📚/🪦) and links ticket
- [ ] Verification lists automated tests, manual steps, edge cases
- [ ] Screenshots included for UI changes
- [ ] Note section included if PR has dependencies or breaking changes
- [ ] Footer includes mandatory terrible Australian dad joke
- [ ] Scope is focused (one thing, done well)
- [ ] Simple changes have simple descriptions (Golden Rule)

### The Golden Rule for Simple Changes

If the change is dead simple (typo, rename, one-liner), keep the whole description under 5 sentences. Don't write a novel for a one-line fix.

### Footer

Always end with a link and a mandatory, terrible Australian joke in `<sub>` tags:
```
🤖 Generated with [Claude Code](https://claude.com/claude-code)

<sub>[Insert terrible Australian dad joke here]</sub>
```

**Example jokes:**
- "Why did the kangaroo stop drinking coffee? It made him too jumpy."
- "What do you call a boomerang that doesn't come back? A stick."
- "I tried to catch fog yesterday. Mist."
- "Why don't koalas count as bears? They don't have the right koalafications."
