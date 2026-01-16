# Verification Guidelines

## Core Principle

**Evidence before claims.** Cannot assert "complete", "fixed", or "passing" without fresh verification.

## Test Requirements (Context-Aware)

### Tests REQUIRED for:

- ✅ New functions/methods/classes with logic
- ✅ Bug fixes (regression test to prevent recurrence)
- ✅ API endpoints or integration points
- ✅ Business logic, algorithms, data transformations
- ✅ State management or complex control flow
- ✅ Security-sensitive code (auth, validation, sanitization)

### Tests NOT Required for:

- ❌ Documentation (*.md, comments, JSDoc/TSDoc)
- ❌ Configuration files (package.json, tsconfig.json, .env)
- ❌ Pure type definitions (*.d.ts, interfaces without logic)
- ❌ Pure refactoring where existing tests cover behavior
- ❌ Formatting/linting-only changes
- ❌ Build scripts or tooling configuration

## Verification Approaches

### For Logic Code (Tests Required)

1. **Write failing test first** (watch it fail for right reason - RED)
2. **Implement minimum code** to pass the test
3. **Verify test passes** (GREEN)
4. **Run full test suite** (ensure no regressions)
5. **Commit both test + implementation together**

### For Non-Logic Changes (Tests Not Required)

1. **Make changes**
2. **Run existing test suite** (ensure no regressions)
3. **Additional verification**:
   - Docs: Lint check, manual review
   - Config: Validate syntax (JSON.parse, YAML lint)
   - Types: Run type-checker (`tsc --noEmit`)
   - Build: Run build command
4. **Commit changes**

## Pre-Commit Advisory

### Advisory Warning (Non-Blocking)

For most code changes with logic but no new tests:
```
⚠️  WARNING: These files have logic changes but no new tests:
  - src/classifier.ts
  - src/api/sessions.ts

✅ Proceeding with warning (use --no-verify to suppress)
```

### Blocking Enforcement (High-Risk Only)

For high-risk paths without tests:
```
❌ BLOCKED: High-risk changes require tests:
  - src/auth/authenticate.ts (authentication)
  - src/api/payments.ts (payment processing)

Add tests or use --no-verify to bypass (not recommended)
```

**High-risk patterns**:
- `auth`, `authenticate`, `login`, `session`
- `payment`, `billing`, `charge`, `transaction`
- `security`, `encrypt`, `decrypt`, `sanitize`
- `database`, `migration`, `schema`
- `api/**/*.ts` (API endpoints)

### Exemption Patterns

Never warn/block:
- `*.md` (Markdown)
- `README*`
- `*.json`, `*.yaml`, `*.yml` (Config)
- `*.d.ts` (Type definitions)
- `docs/**/*`
- `.github/**/*`

## 5-Step Verification Gate

Before any completion claim:

1. **Identify** the verification command that proves your claim
2. **Run** it freshly in current session (not from memory)
3. **Read** complete output including exit codes and failure counts
4. **Verify** output actually supports your claim
5. **Only then** state completion with evidence

### Examples

❌ **Bad** (no evidence):
```
"I've fixed the issue, tests should pass now"
"The implementation is complete"
```

✅ **Good** (evidence-based):
```
"Tests passing (ran `npm test`, all 47 tests green, exit 0)"
"Implementation complete, verified with:
  - npm test: 12/12 passing ✅
  - npm run type-check: no errors ✅
  - npm run build: success ✅"
```

## Memory Integration

After verification success/failure:
```
memory_add_observation(
  entity="VerificationPatterns",
  observation="[file type/path pattern] changes → [verification approach] → [worked/revealed issues]"
)
```

Examples:
- "src/api/*.ts changes → Integration tests required, unit tests insufficient → Caught auth bug"
- "Config changes (package.json) → Build + type-check sufficient, no tests needed → Worked"
