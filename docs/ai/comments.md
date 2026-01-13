# Comment Policy: Explain WHY, not WHAT/HOW

- **CRITICAL: NEVER remove existing comments unless explicitly asked.** When modifying code, preserve all comments exactly as they are. Only add new comments or update existing ones if the change makes them incorrect.
- **Audience**: Other developers and future maintainers. Never the end user or the person who invoked the agent.
- **When to comment**: Only for non-obvious or complex code—document intent, invariants, constraints, trade-offs, and known pitfalls. Omit comments for straightforward code.
- **What to write**: Focus on the WHY: rationale, business/domain rules, performance/security considerations, external dependencies, and surprising behavior. When relevant, reference sources or tickets with links/IDs.
- **What not to write**: Do not narrate actions, restate code, or explain basic language/library features. Avoid conversational tone and avoid "we/I/you". Never use a comment to explain that you have moved or removed some code. Do not add comments like "NEW:", "CHANGED:", "UPDATED:", or similar prefixes that describe the development history of the code.
- **Placement**: Prefer comments above the relevant code or language-idiomatic docstrings. Avoid trailing inline comments except for very short clarifications.
- **Style**: Be concise and neutral. Use complete sentences when helpful. Keep comments up-to-date or remove them if they become stale.
- **TODOs**: Do not add TODO comments. Implement the change or create a tracked issue and reference it.

### Comment these:
- Coordinate transformations
- CORS workarounds
- Magic numbers with meaning
- Timing/sequence requirements

### TSDoc at type definitions
```typescript
type SlideAnnotation = {
  /** Unique ID for tracking annotations */
  id: string;

  /** Canvas coordinates - use convertToCanvasSpace() first */
  x: number;
  y: number;
}
```

### Test File Guidelines

- Test descriptions should be self-explanatory; avoid adding comments that merely categorize or label test groups.
- Do not add prefixes like "NEW:", "UPDATED:", or similar development history markers in test comments.
- Comments in tests should focus on explaining complex test setup, edge cases, or non-obvious assertions—not on what the test is doing.

## Examples

### Explain WHY, not what
```typescript
// ❌ Gets the pixel ratio
const ratio = window.devicePixelRatio;

// ✅ Need pixelRatio to convert DOM coords to canvas coords on high-DPI displays
const ratio = window.devicePixelRatio;
```

### Don't comment obvious code
```typescript
// ❌ Set the selected slide ID
setSelectedSlideId(slide.id);
```

### Good vs Bad
- Good (explains decision and constraints):
  ```
  // Why: We debounce to cap Supabase RPC calls under project rate limits; 300ms balances UX vs. quota (see ISSUE-1234).
  ```
- Bad (restates code or talks to the user):
  ```
  // We call debounce here because it's better :)
  ```
- Bad (development history markers):
  ```
  // NEW: Tests for image preset (text-only behavior)
  // UPDATED: Fixed validation logic
  ```
