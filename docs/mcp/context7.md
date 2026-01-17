# Context7 MCP Server

Guidelines for using Context7 to access up-to-date, version-specific code documentation and examples.

Provides access to Context7 for:
1. **Up-to-date documentation** - Version-specific docs for frameworks and libraries
2. **Code examples** - Real-world usage examples from official sources
3. **API references** - Current API signatures and parameters

## When to Use

Use Context7 when you need:
- **Latest framework documentation** - React, Next.js, Vue, etc. with specific version support
- **Library API references** - Current method signatures, parameters, return types
- **Best practices** - Up-to-date patterns and recommendations from official sources
- **Migration guides** - Version-specific upgrade paths
- **Breaking changes** - What changed between versions

**Don't use for:**
- General programming questions (use WebSearch or Gemini)
- Historical information (use WebSearch)
- Custom/private codebases (use Grep/Read tools)
- Debugging runtime errors (use DevTools)

## Available Tools

Context7 integrates directly with Claude via the MCP protocol. When you need documentation, simply reference it naturally in your prompts:

```
"I need to implement authentication using the latest NextAuth.js v5 patterns"
"What's the current API for React Query's useQuery hook?"
"Show me how to use Tailwind's new container queries feature"
```

Context7 will automatically:
1. Detect the libraries/frameworks you mention
2. Fetch version-specific documentation
3. Inject relevant docs and examples into the context
4. Provide current, accurate information

## Usage Examples

### Framework Documentation

```
"I'm implementing a new feature using Next.js 15 App Router.
Show me the current patterns for server actions and form handling."
```

Context7 will inject:
- Next.js 15-specific App Router documentation
- Current server action patterns
- Form handling examples with progressive enhancement

### Library API Reference

```
"What's the correct way to configure React Query v5's
queryClient with custom defaults?"
```

Context7 will provide:
- React Query v5 API reference for QueryClient
- Configuration options and their types
- Default settings and best practices

### Version-Specific Migration

```
"I need to upgrade from Prisma 4 to Prisma 5.
What are the breaking changes and migration steps?"
```

Context7 will fetch:
- Prisma 5 migration guide
- Breaking changes between v4 and v5
- Code examples showing before/after patterns

## Supported Frameworks & Libraries

Context7 supports documentation for popular frameworks and libraries including:

- **Frontend:** React, Next.js, Vue, Nuxt, Svelte, SvelteKit, Angular
- **Backend:** Express, Fastify, NestJS, tRPC, GraphQL
- **Databases:** Prisma, Drizzle, TypeORM, Mongoose
- **State Management:** Redux, Zustand, Jotai, React Query, SWR
- **Styling:** Tailwind CSS, styled-components, Emotion
- **Testing:** Jest, Vitest, Playwright, Cypress
- **Build Tools:** Vite, webpack, Turbopack, esbuild

And many more. Context7 automatically detects framework references in prompts.

## Common Patterns

### Check Current API Before Implementation

```
Before implementing:
"What's the current API for Stripe's PaymentIntent creation in their latest SDK?"

Then implement with confidence using accurate, up-to-date patterns.
```

### Verify Best Practices

```
"What are the current React 19 best practices for data fetching in Server Components?"
```

Context7 ensures you're following current recommendations, not outdated patterns.

### Resolve Version Conflicts

```
"I'm using TypeScript 5.5 and ESLint 9. What's the current recommended config format?"
```

Context7 provides version-specific configuration examples that work together.

## Troubleshooting

### No Documentation Found

**Symptom:** Context7 can't find documentation for your library

**Possible causes:**
- Library not yet indexed by Context7
- Typo in library name
- Very new or niche library

**Fix:**
- Try alternative phrasing: "React Query" vs "@tanstack/react-query"
- Use WebSearch for niche libraries
- Check if library has official docs and reference them directly

### Outdated Information

**Symptom:** Context7 returns older documentation

**Possible causes:**
- Documentation cache hasn't refreshed yet
- Library very recently released new version

**Fix:**
- Verify version numbers in the response
- Cross-reference with official docs using WebFetch
- Report to Context7 team if consistently outdated

### Rate Limit Errors

**Symptom:** "Rate limit exceeded" errors

**Fix:**
- Add API key for higher limits
- Space out documentation requests
- Cache responses in conversation memory

## Integration with Other Tools

Context7 works well alongside:

- **Gemini**: Context7 for "what's the current API?", Gemini for "should I use this approach?"
- **WebSearch**: Context7 for framework docs, WebSearch for blog posts and discussions
- **Grep/Read**: Context7 for external libraries, Grep/Read for internal codebase patterns

## Not For

- Writing code (the agent does that)
- Searching your codebase (use Grep/Read)
- Debugging (use DevTools/logs)
- General web search (use WebSearch or Gemini)
- Historical "how things used to work" (use WebSearch)
