# Playwright Browser Management Rules

## Browser Lifecycle Management

## Session Management

### One Workflow, One Session Rule
- **Don't mix different tasks** in the same browser session
- **Use separate contexts** for different user accounts or platforms
- **Close contexts explicitly** when switching between workflows
- **Restart browser** for major workflow changes

### Tab Management
- **Limit concurrent tabs** to prevent memory issues (max 5 active tabs)
- **Close unused tabs** immediately after operations complete
- **Use `browser_tab_list`** to monitor open tabs in MCP sessions
- **Switch tabs with `browser_tab_select`** rather than opening new ones

## Error Recovery Patterns

### Browser Session Conflicts
When encountering "Browser is already in use" errors:
1. **Run SELECTIVE cleanup script**: `python .claude/scripts/browser_cleanup.py` 
2. **CRITICAL**: Script kills ONLY Chrome browser processes, NOT Node.js Playwright server
3. **Wait 2-3 seconds** before retrying browser operations
4. **Restart Claude** if "Not connected" errors persist

### Selective Process Management Rule
**NEVER kill the Playwright Node.js server processes** - this breaks the MCP connection.

**Safe Process Killing:**
```bash
# Kill ONLY Chrome processes with mcp-chrome-profile
# PRESERVES Node.js processes running mcp-server-playwright
python .claude/scripts/browser_cleanup.py

# With options:
python .claude/scripts/browser_cleanup.py --verbose --dry-run
```

**Processes to Kill (Chrome only):**
- Chrome processes with `--user-data-dir=/Users/ranjit/Library/Caches/ms-playwright/mcp-chrome-profile`
- Chrome Helper processes (GPU, Renderer, Utility)

**Processes to PRESERVE (Node.js servers):**
- `node /Users/ranjit/.npm/_npx/.../mcp-server-playwright`
- `npm exec @playwright/mcp@latest`

**Manual Process Identification:**
```bash
# Find Chrome processes to kill (safe)
ps aux | grep "mcp-chrome-profile" | grep -v grep

# Find Node.js processes to PRESERVE (never kill these)
ps aux | grep "mcp-server-playwright" | grep -v grep
```

### Memory Management
- **Monitor Chrome memory usage** - restart if > 1GB per tab
- **Close browser contexts** when not actively needed
- **Use `browser.close()`** vs `context.close()` appropriately
- **Implement timeouts** for all browser operations (30s default)

## Navigation Best Practices

### Page Loading Strategy
- **Use `wait_until="networkidle"`** for dynamic content
- **Add explicit waits** after navigation (2-3 seconds minimum)
- **Check for loading indicators** before extracting content
- **Handle redirects gracefully** by checking final URL

### Element Interaction Timing
- **Wait for selectors** before interaction: `wait_for_selector(timeout=10000)`
- **Use `scroll_into_view_if_needed()`** before clicking elements
- **Add delays between actions** to appear more human-like (500ms-2s)
- **Verify element is visible** before interaction
- **Use `browser_press_key` instead of JavaScript eval** when interacting with web site UI elements to simulate human users better
  - Prefer `browser_press_key` for clicks, input, and navigation to mimic natural user interaction
  - Avoid direct JavaScript evaluation for UI interactions when possible
  - `browser_press_key` provides more human-like and reliable web element interaction

## Error Detection and Handling

### Common Browser Errors
- **Timeout Errors**: Increase timeout, retry once, then fail gracefully
- **Element Not Found**: Wait additional time, check page structure changes
- **Navigation Failures**: Check network connectivity, retry with fresh context
- **Profile Lock Errors**: Kill processes, clear locks, restart browser

### Page State Validation
```python
# Always verify successful navigation
def verify_page_loaded(page, expected_url_pattern):
    current_url = page.url
    page_title = page.title()
    
    # Check for error pages
    if "404" in page_title or "error" in current_url.lower():
        raise NavigationError(f"Error page detected: {current_url}")
    
    # Verify expected URL pattern
    if expected_url_pattern not in current_url:
        raise NavigationError(f"Unexpected URL: {current_url}")
    
    return True
```

## Performance Guidelines

### Resource Optimization
- **Disable images** for text-only scraping: `'--blink-settings=imagesEnabled=false'`
- **Block unnecessary resources** (ads, trackers) with request interception
- **Use single browser instance** for multiple operations when possible
- **Implement connection pooling** for database operations during scraping

### Concurrent Operations
- **Limit parallel browser instances** (max 3 on production VM)
- **Use semaphores** to control concurrent browser operations
- **Implement backoff strategies** for rate limiting
- **Monitor system resources** during intensive operations

## Windows-Specific Considerations

### Playwright MCP Server Protection (UPDATED)
**NEW SELECTIVE CLEANUP APPROACH:**
- Updated cleanup script kills ONLY Chrome browser processes with `mcp-chrome-profile`
- Node.js processes running `mcp-server-playwright` are NEVER terminated
- This prevents MCP server disconnection while resolving browser conflicts

**If MCP Server Still Disconnected:**
- Restart Claude to restore Playwright MCP server connections
- Verify Node.js processes are still running: `ps aux | grep mcp-server-playwright`
- If Node.js processes were accidentally killed, restart Claude to reinitialize

**Error Recovery Sequence:**
1. Run selective cleanup: `python .claude/scripts/browser_cleanup.py`
2. If "Not connected" errors persist, restart Claude
3. Verify Playwright connection restored

### MCP Server Configuration
- **Always use `cmd /c` wrapper** for npm commands on Windows
- **Ensure proper PATH** configuration for global npm packages
- **Handle Windows path separators** correctly in scripts
- **Use PowerShell** for advanced process management

### File System Access
- **Use forward slashes** in cross-platform code
- **Handle Windows file locks** properly (especially browser profiles)
- **Ensure proper permissions** for browser data directories
- **Use atomic file operations** for profile management

## Debug and Monitoring

### Logging Browser Operations
```python
logger.info(f"Browser launched with profile: {profile_path}")
logger.debug(f"Navigating to: {url}")
logger.info(f"Page loaded successfully: {page.title()}")
logger.warning(f"Slow page load detected: {load_time}ms")
logger.error(f"Browser operation failed: {error_message}")
```

### Performance Metrics to Track
- **Page load times** (target: <5 seconds)
- **Element interaction success rates** (target: >95%)
- **Memory usage per browser instance** (alert if >1GB)
- **Browser restart frequency** (should be <1 per hour)

## Emergency Procedures

### Complete Browser Reset
```python
# Use the standardized Python cleanup script
python .claude/scripts/browser_cleanup.py --verbose

# For emergencies, force cleanup and verify
python .claude/scripts/browser_cleanup.py && \
python .claude/scripts/browser_cleanup.py --verify-only
```

### Session Recovery
- **Save operation state** before critical browser operations
- **Implement checkpoint system** for long-running scraping tasks
- **Use database transactions** to maintain consistency during failures
- **Provide clear recovery instructions** in error messages