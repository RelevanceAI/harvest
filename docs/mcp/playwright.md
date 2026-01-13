# Playwright MCP Server

High-level browser automation for testing UX changes and verifying visual output.

**Server:** `@anthropic-ai/mcp-server-playwright`
**Browser:** Chromium (pre-installed in sandbox)
**Auth:** None required

## When to Use

- Testing UX changes after implementation
- Verifying visual output of components
- Automating user flows (login, form submission, navigation)
- Taking screenshots for verification
- Extracting data from rendered pages

## Available Tools

| Tool | Description |
|------|-------------|
| `playwright_navigate` | Navigate to a URL |
| `playwright_screenshot` | Take a screenshot of the page |
| `playwright_evaluate` | Execute JavaScript and return results |

## Basic Workflow

```
1. playwright_navigate(url="http://localhost:3000")
2. playwright_screenshot()  # Verify page loaded correctly
3. playwright_evaluate(script="document.querySelector('.submit-btn').click()")
4. playwright_screenshot()  # Verify action result
```

## Common Patterns

### Testing a Form Submission

```
playwright_navigate(url="http://localhost:3000/contact")
playwright_evaluate(script=`
  document.querySelector('#name').value = 'Test User';
  document.querySelector('#email').value = 'test@example.com';
  document.querySelector('#submit').click();
`)
# Wait for response
playwright_evaluate(script="new Promise(r => setTimeout(r, 1000))")
playwright_screenshot()
```

### Checking Element Existence

```
playwright_navigate(url="http://localhost:3000/dashboard")
playwright_evaluate(script=`
  const element = document.querySelector('.user-avatar');
  element ? 'Found' : 'Not found'
`)
```

### Getting Page Content

```
playwright_navigate(url="http://localhost:3000/api/status")
playwright_evaluate(script="document.body.innerText")
```

## When to Switch to DevTools

Switch to [DevTools MCP](./devtools.md) when:

- Playwright can't find an element (use `take_snapshot()` to inspect DOM)
- Page is blank or broken (use `list_console_messages()` for JS errors)
- Network requests are failing (use `list_network_requests()`)
- Need performance analysis (use performance trace tools)

See [DevTools Tag Team Pattern](./devtools.md#playwright-vs-devtools-tag-team-pattern) for more details.

## Modal Sandbox Notes

In the Harvest Modal sandbox:
- Chromium is pre-installed at image build time
- Browser runs headless within the sandbox
- No external services or containers needed
- Screenshots return base64 encoded images

## Troubleshooting

**Page not loading:**
- Ensure the dev server is running
- Check the correct port (may vary by project)
- Use DevTools to check for network errors

**Element not found:**
- Use DevTools `take_snapshot()` to see actual DOM
- Check for dynamic loading (may need to wait)
- Verify selector is correct with `evaluate_script`

**JavaScript errors:**
- Use DevTools `list_console_messages()` to see errors
- Check for missing dependencies or failed API calls
