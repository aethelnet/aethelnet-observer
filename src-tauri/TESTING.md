# Tauri App Testing Guide

This document describes how to test the Tauri application after installation of system dependencies.

## Prerequisites

1. **System Libraries** (install in toolbox with dnf):
   ```bash
   toolbox enter
   dnf install libsoup3-devel javascriptcoregtk4.1-devel webkit2gtk4.1-devel
   ```

2. **Backend Running**: The Python FastAPI backend should be running at `http://localhost:8000`

3. **Environment Variables** (optional):
   - `AURATIC_API_URL` - Backend API URL (default: `http://localhost:8000`)
   - `AURATIC_LOG_PATH` - Path to backend log file
   - `AURATIC_VAULT_PATH` - Path to vault directory
   - `AURATIC_REQUEST_TIMEOUT` - HTTP request timeout in seconds (default: 10)

## Testing HTTP Client

### 1. Test HTTP Client Initialization

The HTTP client should initialize automatically when the app starts. Check logs for:
```
[APP] HTTP client initialized successfully
```

If initialization fails, check:
- Configuration values are correct
- Network connectivity
- Backend is accessible

### 2. Test GET Requests

All fetch commands use GET requests. Test with backend running:

```bash
# Check backend is responding
curl http://localhost:8000/api/dashboard/status
```

Then test in app:
- `fetch_backend_status()` - Should return system status
- `fetch_trading_metrics()` - Should return trading metrics
- `fetch_market_data()` - Should return market data array
- `fetch_positions()` - Should return positions array
- `fetch_recent_trades()` - Should return trades array

### 3. Test POST Requests

Test with backend running:
- `emergency_stop()` - Should call `/api/failsafe/panic`
- `restart_trading()` - Should call `/api/failsafe/resume`
- `start_week_test()` - Should call `/api/dashboard/start-week-test`

### 4. Test Error Handling

#### Test with Backend Not Running:
1. Stop the backend
2. Try any fetch command
3. Should see error message: "Connection failed - unable to reach the backend server..."

#### Test Timeout:
1. Set `AURATIC_REQUEST_TIMEOUT=1` (1 second)
2. Make a request to a slow endpoint
3. Should see: "Request timeout - the server took too long to respond..."

#### Test Invalid Response:
1. Mock backend returns invalid JSON
2. Should see: "Failed to parse JSON: ..."

## Testing Commands

### Fetch Commands

All fetch commands follow the same pattern:
1. Log command invocation
2. Get HTTP client
3. Make request
4. Log success/failure
5. Return result or error

**Expected Log Output:**
```
[CMD] fetch_backend_status called
[HTTP] GET request to: http://localhost:8000/api/dashboard/status
[HTTP] GET http://localhost:8000/api/dashboard/status - Response received in 50ms
[HTTP] GET http://localhost:8000/api/dashboard/status - Status: 200 OK
[HTTP] GET http://localhost:8000/api/dashboard/status - Successfully parsed JSON response
[CMD] fetch_backend_status - Success
```

### Action Commands

Action commands (emergency_stop, restart_trading, start_week_test):
- Should log with appropriate level (warn for emergency_stop, info for others)
- Should return success message on completion

### Path Opening Commands

`open_logs()` and `open_vault()`:
- Should log path being opened
- Should spawn appropriate system command (xdg-open on Linux)
- Should handle errors gracefully

## Testing Configuration

### Default Configuration

Without environment variables, should use:
- API URL: `http://localhost:8000`
- Log path: `~/Projects/Backup/auratic-systems-prime/backend.log`
- Vault path: `~/Projects/Cursor`
- Timeout: 10 seconds

### Environment Variable Overrides

Set environment variables and verify they're used:
```bash
export AURATIC_API_URL=http://localhost:9000
export AURATIC_REQUEST_TIMEOUT=5
```

Check logs for:
```
[CONFIG] API URL: http://localhost:9000
[CONFIG] Request timeout: 5s
```

## Testing Cross-Platform Path Opening

### Linux
- Should use `xdg-open`
- Should handle missing `xdg-open` gracefully

### macOS
- Should use `open` command
- Should handle errors

### Windows
- Should use `cmd /C start`
- Should handle errors

## Debug Logging

Enable debug logging by setting log level in `lib.rs`:
```rust
.level(log::LevelFilter::Debug)
```

This will show:
- All HTTP requests/responses
- Configuration loading
- Command invocations
- Error details

## Common Issues

### 1. "Failed to initialize HTTP client"
- Check configuration values
- Verify network stack is working
- Check for conflicting dependencies

### 2. "Connection failed"
- Backend not running
- Wrong API URL
- Firewall blocking connection

### 3. "Request timeout"
- Backend is slow
- Network issues
- Timeout too short

### 4. "Failed to parse JSON"
- Backend returned invalid JSON
- Response format changed
- Encoding issues

## Manual Testing Checklist

- [ ] App compiles without errors
- [ ] App launches successfully
- [ ] HTTP client initializes
- [ ] Configuration loads correctly
- [ ] All fetch commands work with backend running
- [ ] All fetch commands handle backend not running gracefully
- [ ] All POST commands work
- [ ] Error messages are user-friendly
- [ ] Logs provide useful debugging information
- [ ] Path opening works on current platform
- [ ] Environment variables override defaults correctly


