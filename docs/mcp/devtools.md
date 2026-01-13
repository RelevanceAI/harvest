# Chrome DevTools MCP Server

Low-level browser debugging via Chrome DevTools Protocol for performance analysis, network inspection, and console debugging.

**Server:** `chrome-devtools-mcp`
**Connection:** In-sandbox Chromium (installed with Playwright)
**Auth:** None required

## Playwright vs DevTools: Tag Team Pattern

Both Playwright and DevTools work with the browser but serve different purposes:

| Playwright MCP | Chrome DevTools MCP |
|----------------|---------------------|
| High-level automation | Low-level debugging |
| Navigate, screenshot, evaluate | Network HAR, console logs, performance traces |
| Token-efficient for happy path | Comprehensive when things break |
| 3 tools | 26 tools |

**The Pattern:**
1. Start with **Playwright** for heavy lifting (navigation, interactions, screenshots)
2. Switch to **DevTools** when Playwright hits a wall ("can't find button", "page is blank")
3. Use DevTools to diagnose (check console, inspect network, trace performance)
4. Return to Playwright with the fix

## Available Tools

### Input Automation

| Tool | Description |
|------|-------------|
| `click` | Click an element on the page |
| `drag` | Drag from one element to another |
| `fill` | Fill a text input field |
| `fill_form` | Fill multiple form fields at once |
| `handle_dialog` | Accept or dismiss browser dialogs |
| `hover` | Hover over an element |
| `press_key` | Press a keyboard key |
| `upload_file` | Upload a file to an input |

### Navigation

| Tool | Description |
|------|-------------|
| `navigate_page` | Navigate to a URL |
| `new_page` | Open a new browser tab |
| `close_page` | Close a browser tab |
| `list_pages` | List all open tabs |
| `select_page` | Switch to a specific tab |
| `wait_for` | Wait for an element or condition |

### Emulation

| Tool | Description |
|------|-------------|
| `emulate` | Emulate a device (mobile, tablet) |
| `resize_page` | Resize the viewport |

### Performance

| Tool | Description |
|------|-------------|
| `performance_start_trace` | Start recording a performance trace |
| `performance_stop_trace` | Stop recording and get trace data |
| `performance_analyze_insight` | Analyze trace for performance insights |

### Network

| Tool | Description |
|------|-------------|
| `list_network_requests` | List all network requests made by the page |
| `get_network_request` | Get details of a specific request (headers, body, timing) |

### Debugging

| Tool | Description |
|------|-------------|
| `list_console_messages` | List all console messages (logs, errors, warnings) |
| `get_console_message` | Get details of a specific console message |
| `evaluate_script` | Execute JavaScript in the page context |
| `take_screenshot` | Capture a screenshot of the page |
| `take_snapshot` | Capture a DOM snapshot |

## Debugging Workflows

### "Page is Blank" Workflow

```
1. navigate_page(url="http://localhost:3000")
2. list_console_messages()  # Check for JS errors
3. list_network_requests()  # Check for failed requests (4xx, 5xx)
4. take_screenshot()        # Visual confirmation
```

### "Can't Find Element" Workflow

```
1. navigate_page(url="http://localhost:3000/target-page")
2. take_snapshot()          # Get full DOM structure
3. list_console_messages()  # Check if element is hidden due to error
4. evaluate_script(script="document.querySelector('.my-button')")  # Test selector
```

### Performance Investigation

```
1. performance_start_trace()
2. navigate_page(url="http://localhost:3000")
3. # Interact with the page...
4. performance_stop_trace()
5. performance_analyze_insight()  # Get actionable insights
```

### Network Debugging

```
1. navigate_page(url="http://localhost:3000")
2. list_network_requests()  # See all requests
3. get_network_request(id="request-id")  # Inspect specific request
   # Returns: headers, body, timing, status
```

## Example Prompts

**When Playwright fails to find an element:**
> "Use DevTools to navigate to http://localhost:3000/login and check the console for JavaScript errors. Also take a screenshot so I can see what's rendering."

**When page loads slowly:**
> "Use DevTools to start a performance trace, navigate to the homepage, then stop the trace and analyze for performance insights."

**When API calls are failing:**
> "Use DevTools to navigate to http://localhost:3000 and list all network requests. Show me any requests that returned 4xx or 5xx status codes."

**When debugging auth issues:**
> "Use DevTools to list network requests and find the login API call. Show me the request headers and response body."

## Connection Details

DevTools runs in-sandbox with Chromium (installed via Playwright):
- **Browser**: Chromium installed at image build time
- **Each connection creates a new browser instance**
- **Sessions don't persist between tool calls** (stateless debugging)

For persistent sessions, you'll need to navigate to the same URL in each session.

## Modal Sandbox Notes

In the Harvest Modal sandbox:
- Chromium is pre-installed via `npx playwright install chromium`
- No external browserless container needed
- Browser runs headless within the sandbox
- Screenshots and traces are available directly
