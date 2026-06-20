Suggested additional frontend files to add to the chat (short rationale).  I will not edit anything until you add the files you want changed.

1) styles.css
   - Why: index.html links to "styles.css". Please add the real stylesheet so I can ensure styling is consistent and not broken by a missing file.
   - What I will do after you add it: either leave the link alone if the stylesheet is already good, or update styles.css to consolidate/override the large inline styles where appropriate.

2) app.js
   - Why: the inline <script> in index.html is currently minimal and missing handlers (handleEmergencyStop, handleTradingToggle) and WS handling. Moving logic to app.js makes it easier to review & test.
   - What I will do after you add it: wire button handlers, implement robust API calls, metrics/trades/market-data polling, and WebSocket client logic.

3) api-client.js (optional)
   - Why: centralize fetch wrappers, error handling, and endpoint paths (useful if endpoints are shared by multiple pages).
   - What I will do after you add it: use it from app.js to call backend endpoints and to provide consistent retries and error handling.

4) ws-client.js (optional)
   - Why: if you want live updates via WebSocket (index.html references WS_URL), a small module that decodes messages and emits events will keep the code tidy.
   - What I will do after you add it: integrate with app.js to update charts and trades in real time.

5) chart-config.js (optional)
   - Why: if you have multiple charts or custom chart settings, keeping Chart.js configuration separate helps reuse.
   - What I will do after you add it: move chart initialization there and expose simple functions to push new data points.

6) Any backend-API spec or README (recommended)
   - Why: I need to know which endpoints exist and their expected request/response shapes. Example endpoints my proposed UI wiring will call:
     - GET /api/dashboard/metrics  -> { main_pnl, shadow_pnl, win_rate, total_trades, open_positions, trading_enabled, timeseries? }
     - GET /api/dashboard/trades   -> [ {symbol, pnl, entry, exit, ...}, ... ]
     - GET /api/dashboard/market   -> market snapshot for the Market Data card
     - POST /api/control/emergency_stop  -> trigger emergency stop
     - POST /api/control/trading/toggle   -> toggle trading on/off
     - (WebSocket) ws://...  -> push messages of types: metrics, trade, market, control

If you want, I can:
- Edit index.html in-place (add missing handlers, WS, and more robust fetches).
- Or create the modular files above (styles.css, app.js, etc.) and update index.html to load them.

Next step:
- Add whichever of the files above you want me to create or edit (styles.css and/or app.js are the highest priority).
- Also confirm which backend endpoints (URLs + request shapes) actually exist, or give me a small samples/README so I wire the UI to them correctly.

When you add files, reply "go ahead" and I'll prepare exact SEARCH/REPLACE edits.
