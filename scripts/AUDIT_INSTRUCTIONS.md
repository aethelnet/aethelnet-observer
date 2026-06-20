# Frontend Live Audit — Instructions

This directory contains scripts to verify that all 7 frontend views (ports 1420-1426) are live, connected to the backend, and functioning correctly.

## Quick Start

### Option 1: Use the Wrapper Script (Recommended)

The easiest way to run the audit is using the unified wrapper script:

```bash
# Auto-detect and use available tool
./scripts/run_frontend_audit.sh

# Use Playwright specifically
./scripts/run_frontend_audit.sh --tool playwright

# Use Pyppeteer specifically
./scripts/run_frontend_audit.sh --tool pyppeteer

# Run both and compare results
./scripts/run_frontend_audit.sh --tool both

# Auto-install missing dependencies
./scripts/run_frontend_audit.sh --install-deps

# Verbose output
./scripts/run_frontend_audit.sh --verbose
```

### Option 2: Run Scripts Directly

#### Using Playwright (Recommended - More Modern)

```bash
# Install Playwright
pip3 install playwright
playwright install chromium

# Run audit
python3 scripts/frontend_live_audit_playwright.py
```

#### Using Pyppeteer (Alternative)

```bash
# Install Pyppeteer
pip3 install pyppeteer

# Run audit
python3 scripts/frontend_live_audit_pyppeteer.py
```

## What the Audit Does

Both scripts perform the same checks:

1. **File Structure Verification**
   - Checks that all 7 `index.html` files exist
   - Verifies `serve.sh` scripts are executable

2. **Page Loading**
   - Visits each frontend view (ports 1420-1426)
   - Waits for page load and network idle
   - Captures HTTP status codes

3. **API Integration**
   - Detects `API_BASE` configuration in code
   - Finds WebSocket URLs (`ws://localhost:8000/ws`)
   - Scans for endpoint usage in HTML/JS

4. **Network Monitoring**
   - Captures all network requests during page load
   - Identifies API calls to backend
   - Detects WebSocket connection attempts

5. **Library Detection**
   - Checks for Chart.js, TradingView Lightweight Charts, Three.js, GSAP
   - Verifies libraries are loaded in runtime

6. **Console Messages**
   - Captures console logs, warnings, and errors
   - Helps identify JavaScript issues

7. **Backend Status**
   - Attempts to read backend status indicators from DOM

## Output

Both scripts generate JSON reports:

- **Playwright:** `frontend_live_audit_playwright_report.json`
- **Pyppeteer:** `frontend_live_audit_pyppeteer_report.json`

The reports include:
- Per-port probe results (loaded, status, errors)
- API bases and WebSocket URLs found
- Endpoints detected in code
- Network requests observed
- Libraries detected
- Console messages
- Summary statistics

## Playwright vs Pyppeteer

### Playwright (Recommended)
- ✅ More modern and actively maintained
- ✅ Better error messages
- ✅ More reliable browser automation
- ✅ Better performance
- ⚠️ Requires separate `playwright install chromium` step

### Pyppeteer
- ✅ Auto-downloads Chromium on first run
- ✅ Simpler installation (just `pip install`)
- ⚠️ Older, less actively maintained
- ⚠️ May have compatibility issues on some systems

**Recommendation:** Use Playwright if possible. Both produce identical audit results.

## Prerequisites

1. **Python 3.8+** - Check with: `python3 --version`
2. **Backend Running** - The backend should be running on `http://localhost:8000`
3. **Frontend Views Running** - All 7 views should be served on ports 1420-1426

### Starting Frontend Views

If the views aren't running, start them:

```bash
# Root dashboard (1420)
./serve.sh

# Chart view (1423)
cd chartview && ./serve.sh &

# Analytics (1424)
cd analytics && ./serve.sh &

# Risk (1425)
cd risk && ./serve.sh &

# Execution (1426)
cd execution && ./serve.sh &

# Creative views (1421, 1422)
cd creative && ./serve.sh &
cd creative2 && ./serve.sh &
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'playwright'"
```bash
pip3 install playwright
playwright install chromium
```

### "ModuleNotFoundError: No module named 'pyppeteer'"
```bash
pip3 install pyppeteer
```

### "Failed to launch browser"
- **Playwright:** Make sure you ran `playwright install chromium`
- **Pyppeteer:** Check internet connection (Chromium auto-downloads)
- Try running with `--no-sandbox` flag (already included in scripts)

### "Navigation timeout" or "Connection refused"
- Make sure the frontend views are running on ports 1420-1426
- Check that the backend is running on port 8000
- Verify no firewall is blocking localhost connections

### "Address already in use"
- Another process is using one of the ports
- Find and kill the process: `lsof -i :1420` (or other port)
- Or use different ports and update the scripts

### Scripts run but show errors for all ports
- Frontend views may not be running
- Backend may not be running
- Check browser console for CORS errors
- Verify API_BASE is correctly set to `http://localhost:8000/api`

## Advanced Usage

### Custom Configuration

Edit the scripts to change:
- `HOST = "localhost"` - Backend host
- `PORTS = list(range(1420, 1427))` - Frontend ports
- `NAV_TIMEOUT = 15000` - Navigation timeout (ms)
- `OBSERVE_MS = 3000` - Network observation window (ms)

### Running in CI/CD

```bash
# Install dependencies
pip3 install -r scripts/requirements-audit.txt
playwright install chromium

# Run audit
./scripts/run_frontend_audit.sh --tool playwright

# Check exit code (0 = success, non-zero = failure)
if [ $? -eq 0 ]; then
    echo "Audit passed"
else
    echo "Audit failed"
    exit 1
fi
```

### Comparing Both Tools

Run both tools and compare results:

```bash
./scripts/run_frontend_audit.sh --tool both
```

This generates two JSON reports that can be compared to verify consistency.

## Requirements File

Install all dependencies at once:

```bash
pip3 install -r scripts/requirements-audit.txt
playwright install chromium
```

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Run with `--verbose` flag for detailed output
3. Check the generated JSON report for specific errors
4. Verify frontend views are accessible in a regular browser
