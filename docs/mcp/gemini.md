# Gemini MCP Server

This document guides interactions between the Harvest agent and Gemini (AI reviewer) via the Model Context Protocol, specifically for adversarial plan reviews and web research.

**Server:** `@houtini/gemini-mcp`
**Required Secret:** `GEMINI_API_KEY`
**Auth:** API key from Google AI Studio

Provides access to Google's Gemini AI for:
1. **Adversarial plan review** - Cross-check plans before implementation
2. **Web research** - Google Search Grounding for up-to-date information

## When to Use

### Plan Review
Use for non-trivial implementation plans:
- Complex multi-step tasks
- Architecture decisions
- Changes affecting multiple components
- Security-sensitive changes
- Anything you're not 100% confident about

### Web Research
Use as an alternative to WebSearch when you need:
- Synthesised answers (not just links)
- Multi-iteration deep research
- Current best practices with context

## Common Mistakes to Avoid

When interacting with Gemini for plan reviews, avoid these common pitfalls:

- **Vague or high-level plans** - Provide specific details, file paths, and concrete changes instead of abstract descriptions
- **Missing the "why"** - Always explain the goal or problem being solved, not just what you're changing
- **Context overload** - Don't dump entire files or massive diffs; point to relevant sections and provide focused snippets
- **Insufficient context** - Don't provide isolated code snippets without explaining their role in the larger plan
- **Ignoring BLOCKER issues** - Address all BLOCKER concerns before implementing, or provide explicit justification for deferral
- **Expecting full implementation** - Gemini reviews plans and suggests fixes; the agent writes the actual code

## Available Tools

| Tool | Use Case | Quota Impact |
|------|----------|--------------|
| `gemini_chat` | Quick review or search (single-pass) | 1 request |
| `gemini_deep_research` | Thorough multi-iteration analysis | 5-10 requests |
| `gemini_list_models` | Check available models | 1 request |

**Quota Warning**: Free tier has ~60 requests/min, ~1500 requests/day. Use `gemini_chat` for 90% of reviews. Reserve `gemini_deep_research` for critical architectural decisions only (uses 5-10x quota).

**Model Selection**: Default is `gemini-2.5-flash` (fast, has free tier). **Important**: Not all Gemini models have free tier support. Stick with `gemini-2.5-flash` unless you have specific needs.

## Expected Review Style

When Gemini reviews your plans, expect this tone and approach:

- **Constructively critical** - Gemini will identify risks and flaws, not validate existing beliefs
- **Objective and direct** - Focuses on facts and technical concerns without sugar-coating
- **Risk-focused** - Prioritizes identifying what could go wrong over praising what's right
- **Actionable** - Provides specific suggestions and fixes, not just abstract concerns
- **Professional but not formal** - Clear technical communication without unnecessary ceremony

Gemini's role is to be an adversarial reviewer that helps you catch issues before implementation, not to provide encouragement or approval.

## Plan Review Workflow

### 1. Create Your Plan
Write out your implementation plan with specific detail expectations:

- **Primary goal/objective** (1-2 sentences) - What problem is being solved or feature is being added
- **Proposed changes** - What files you'll modify and what approach you're taking
- **Known constraints/trade-offs** (bullet list) - Any non-negotiables or deliberate compromises
- **Key assumptions** (bullet list) - What you're assuming to be true about the system or requirements
- **High-level system context** (brief) - Relevant architecture, tech stack, or components involved
- **Brief test strategy** (1-2 sentences) - How you'll verify the changes work correctly
- **Plan type** (for Deep Reviews) - Explicitly state the category (e.g., "Plan Type: UI Redesign", "Plan Type: Data Migration")

### 2. Choose Review Depth

**Quick Review (DEFAULT - 90% of reviews)**
Use `gemini_chat` for most reviews - quota-friendly, single request.

**Structure your message** using this template for consistency:

```markdown
# Objective
[Primary goal/problem being solved - CONCISE, 1-2 sentences]

## Proposed Changes
[What files, what approach - USE BULLET POINTS]
- File: path/to/file.ts - Brief description of change
- File: path/to/other.ts - Brief description

### Code Snippets
[Relevant snippets with fenced code blocks using language specifiers]
```typescript
// Example of what you're changing
```

## Assumptions
[Key assumptions - BULLET POINTS]
- Assumption 1
- Assumption 2

## Constraints
[Known limitations/trade-offs - BULLET POINTS]
- Constraint 1

## Test Strategy
[How changes will be tested - BRIEF, 1-2 sentences]
```

**Keep it concise**: For quick reviews, focus on the *most critical* proposed changes and assumptions. Use bullet points, avoid extensive prose. If you need deeper analysis, use Deep Review instead.

**Tool call:**
```
gemini_chat(
  message="[YOUR STRUCTURED PLAN using template above]",
  system_prompt="You are an adversarial code reviewer. Analyse this plan and identify concerns. Categorise each as:\n- BLOCKER: Must fix (security, data loss, breaking changes)\n- SHOULD: Should address (edge cases, error handling)\n- CONSIDER: Nice to have (minor improvements)\n\nFor each concern, explain WHY it matters and suggest a fix."
)
```

**Deep Review (SPARINGLY - critical architectural decisions only)**
Uses 5-10x more quota - reserve for major changes.

**Key requirements:**
- **Explicitly state Plan Type** in your request (e.g., "Plan Type: UI Redesign", "Plan Type: Data Migration") so Gemini can tailor its focus
- **Dynamic focus_areas** - Adjust based on your plan type:
  - UI plans → include "accessibility", "responsive design", "user experience"
  - Data migrations → include "data integrity", "rollback strategy", "migration validation"
  - API changes → include "backward compatibility", "API versioning", "breaking changes"
  - Security updates → include "attack vectors", "data exposure", "authentication flows"

**Tool call:**
```
gemini_deep_research(
  research_question="What could go wrong with this implementation plan? Plan Type: [YOUR TYPE]. [YOUR DETAILED PLAN]",
  focus_areas=["security vulnerabilities", "breaking changes", "edge cases", "performance", "maintainability"],
  max_iterations=3
)
```

### 3. Address Concerns by Priority

| Priority | Action Required |
|----------|-----------------|
| **BLOCKER** | Must address before implementing |
| **SHOULD** | Should address, or explicitly acknowledge the risk |
| **CONSIDER** | Optional - use your judgement |

### 4. Iterative Refinement

Good plan reviews often involve multiple rounds of feedback. When submitting follow-up requests to Gemini:

**Highlight what changed:**
- Use a clear heading like "## Context Update: Round 2"
- Explicitly list changes made since the last review
- Example: "Updated: Added file size validation (addresses BLOCKER #1)"

**Reference previous feedback:**
- State which feedback points you've addressed: "Regarding point 3 from your review..."
- For deferred concerns, use this format: `[DEFERRED] Concern: Image resizing (Reason: Not critical for MVP, will address in Phase 2)`

## Web Research Workflow

### Quick Research
For simple questions with grounding (Google Search):
```
gemini_chat(
  message="What are the best practices for React Query cache invalidation in 2025?"
)
```

### Deep Research
For complex topics requiring multiple iterations:
```
gemini_deep_research(
  research_question="How should I implement real-time collaboration in a React Native app?",
  focus_areas=["WebSocket vs SSE", "conflict resolution", "offline support", "React Native specific considerations"],
  max_iterations=5
)
```

## Troubleshooting

### Common Errors

**503 Service Unavailable / Model Overloaded**
- **Cause**: Gemini service is temporarily overloaded
- **Fix**: Transient issue - retry after a few seconds
- **Note**: More common during peak usage hours

**429 Quota Exceeded (with `limit: 0`)**
- **Cause**: The model you're using doesn't have free tier support
- **Fix**: Use `gemini-2.5-flash` (the default) which has free tier
- **Example**: `gemini-2.0-flash` has no free tier, but `gemini-2.5-flash` does

**429 Quota Exceeded (normal quota message)**
- **Cause**: You've hit the free tier rate limit (60/min or 1500/day)
- **Fix**: Wait for quota to reset (per-minute resets quickly, daily resets at midnight UTC)
- **Prevention**: Use `gemini_chat` for most reviews, save `gemini_deep_research` for critical decisions

**404 Not Found**
- **Cause**: Model doesn't exist or isn't available via the v1beta API
- **Fix**: Check available models with `gemini_list_models` tool

**403 Permission Denied**
- **Cause**: Invalid API key or key doesn't have proper permissions
- **Fix**: Create a new key at https://aistudio.google.com/app/apikey

### Quota Monitoring

- Check usage: https://ai.dev/rate-limit
- Free tier limits: ~60 requests/min, ~1500 requests/day
- Models with free tier: `gemini-2.5-flash`, `gemini-2.5-flash-lite` (others may not have it)

## Not For

- Writing code (the agent does that)
- Real-time debugging (use DevTools/Playwright)
- Simple, obvious changes that don't need review
- Tasks where you're already confident in the approach
