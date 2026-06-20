I reviewed the Developer Guide and the frontend files you added. Before I make any edits, please confirm exactly which of the following you want me to do next (pick one or more and reply):

1) Create missing support files (I will add these files and wire them into pages):
   - help-system.js (stub implementation for tooltips/help modal)
   - styles.css (skeleton stylesheet to replace broken/missing reference)
   - ws-client.js (robust WebSocket client with reconnect/backoff + event dispatch)
   - api-client.js (centralized fetch wrapper with retry/backoff)
   - app.js (MVP page behavioral logic: emergency stop, trading toggle, WS wiring)

2) Add a wrapper to run the audit locally:
   - scripts/run_frontend_audit.sh that installs deps (pyppeteer/playwright) and runs the audit scripts.

3) Run static edits now:
   - I will produce SEARCH/REPLACE blocks to add or modify the files you selected.

4) Do a runtime-focused change:
   - Implement ws-client.js and wire it into index.html and chartview/index.html to enable real-time updates (requires you to run the audit locally to verify).

Questions I need you to answer if you pick runtime or wiring changes:
- Do you want the WebSocket client to authenticate (send headers or a token)? If yes, provide the auth header name/value or a function to fetch it.
- Should help-system.js be a feature-rich helper (tooltips, modal, keyboard shortcuts) or a minimal stub so pages don't fail?

If you're not sure, reply:
- "create help-system.js and styles.css" — I will add safe skeletons for both and wire them into the pages.
- "go ahead" — I will create a minimal help-system.js, styles.css, and ws-client.js, and update index.html + chartview/index.html to load ws-client.js.

I will not modify any other files you marked read-only unless you explicitly add them to the chat.

Reply with your choice(s) or answer the questions above and I will produce the required SEARCH/REPLACE blocks.
