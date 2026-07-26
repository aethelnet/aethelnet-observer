# Developer Guide Verification Report
Generated: 2025-12-31

Summary:
This document records a verification pass comparing the "Auratic Systems: Prime - Developer Guide"
with the currently provided code files. It lists features that appear implemented, and (critically)
places where the codebase and the guide diverge or contain likely runtime issues. Each discrepancy
includes suggested remediation and the file(s) involved.

I performed the check against the set of repository files you provided and the few live endpoints
you included (notably /api/dashboard/status). This is a best-effort static / light runtime check;
I did not run the full system.

---

1) HIGH-PRIORITY MISMATCHES (features that will break runtime behavior)

A. Brain <-> Broadcast integration mismatch
- Files:
  - backend/services/brain.py
  - backend/routers/stream.py (broadcast_loop + handshake)
- Problem:
  - broadcast_loop (backend/routers/stream.py) expects engine.compute_projection(...) to return an object containing keys like `times`, `prices`, and `resonance`, and also references `engine.history` (e.g. `engine.history[2][-1]`).
  - BrainEngine.compute_projection (backend/services/brain.py) returns a dict with keys: "signal", "confidence", "regime", "volatility", "phase" and does NOT return `times`/`prices`/`resonance`.
  - BrainEngine does not define `history` attribute; it has `price_history`, `z_score_history`, etc.
- Impact:
  - broadcast_loop will raise AttributeError / KeyError at runtime when it tries to access non-existent keys/attributes, causing telemetry/broadcast failures.
- Suggested remediation (choose one of):
  1. Update broadcast_loop to use engine.price_history / engine.z_score_history / engine.compute_projection() outputs (the simpler fix).
  2. Or extend BrainEngine.compute_projection to optionally produce `times`/`prices` projection arrays and `resonance` key to match broadcast_loop expectations.
- Minimal actionable fix recommendation: change broadcast_loop to use engine.compute_projection() safe fields (signal/confidence/regime) and avoid assuming times/prices. This keeps heavy projection math inside Brain and prevents KeyErrors.

B. stream.py/handshake uses engine.history
- Files:
  - backend/routers/stream.py
- Problem:
  - Handshake code uses `current_z = engine.history[2][-1] if engine.history[2] else 0.0` and later `current_z = engine.history[2][-1] if hasattr(engine, 'history') and engine.history[2] else 0.0`.
  - BrainEngine has no `history` attribute.
- Impact:
  - On new WebSocket client handshake, reference to `engine.history` will raise AttributeError, preventing initial FULL_STATE packet from being sent.
- Suggested remediation:
  - Replace `engine.history[2][-1]` with a safe access, e.g. `engine.z_score_history[-1] if engine.z_score_history else 0.0`.
  - Audit all occurrences of `engine.history` across codebase and replace appropriately.

C. Database API compatibility mismatches
- Files:
  - backend/services/database.py
  - callers: backend/services/brain.py, backend/services/trading_service.py, backend/arena/manager.py, etc.
- Problem:
  - Callers assume multiple variant signatures or helper names (e.g., `db.get_open_positions`, `db.get_positions`, `db.delete_position`, `db.insert_position`) while Database provides other names (`get_position`, `upsert_position`, `insert_trade`, etc.).
  - Many call sites already wrap calls in try/except and attempt fallback signatures — that's defensive — but missing wrappers will still cause missing persistence in practice.
- Impact:
  - Position / open-position reload on startup may not populate performance tracker, causing UI or trading logic to start without persisted positions.
- Suggested remediation:
  - Add compatibility wrapper methods in Database: `get_positions`, `get_open_positions`, `delete_position`, `insert_position` that delegate to existing functions. Alternatively, update callers to consistently use Database's canonical methods.
  - Given multiple callers, adding thin compatibility methods to Database is the least intrusive fix.

D. Duplicate atomic_write implementations & inconsistent APIs
- Files:
  - backend/core/failsafe.py (defines atomic_write contextmanager)
  - backend/core/utils.py (defines atomic_write function but with different signature)
- Problem:
  - Two distinct implementations with different signatures and usages exist. Some call sites pass file path + data (utils.atomic_write), others use context manager (failsafe.atomic_write).
- Impact:
  - Confusion and potential subtle bugs; e.g., callers expecting `atomic_write(filepath, data)` while other atomic_write is a context manager.
- Suggested remediation:
  - Consolidate to a single consistent atomic_write API and adapt callers. If both styles are used, provide both helpers (one that accepts data and one contextmanager) and harmonize names to avoid collision (e.g., `atomic_write_text()` and `atomic_write_ctx()` or keep one and alias the other).

E. Broker / Router behavior & error propagation
- Files:
  - backend/brokers/binance.py
  - backend/brokers/router.py
- Problems / Observations:
  - binance._probe_permissions uses synchronous ccxt client in __init__ which may block; it's wrapped in try/except but could be fragile.
  - Multiple `except Exception` duplicates in get_position contain repeated code blocks — minor maintainability issue.
  - Router._init_brokers unpacks SecretStr via hasattr(..., 'get_secret_value') which is good, but some keychain getter calls may return None / empty dicts; router includes logging but some fallback paths might leave no broker, causing runtime RuntimeError in place_order.
- Suggested remediation:
  - Ensure router.place_order raises clear RuntimeError (already does). Consider logging missing brokers at startup as critical and exposing a health check.
  - Add unit tests that simulate missing keys to verify safe startup.

---

2) MEDIUM-PRIORITY / BEHAVIORAL GAP FINDINGS (features described in guide but only partially implemented)

A. compute_projection vs broadcast expectations (behavioral)
- Files:
  - backend/services/brain.py
  - backend/routers/stream.py
- Observation:
  - Guide describes "Compute market projection for broadcast loop" with possibly times/prices; BrainEngine.compute_projection uses a simple oscillator phase and returns signal/confidence/regime/volatility/phase.
- Recommendation:
  - Update documentation or code to align on whether projections include predicted path ("times/prices"). If projections are not produced, broadcast_loop should not attempt to format path arrays.

B. WebSocket auth handshake
- Files:
  - backend/routers/stream.py
- Observation:
  - Developer guide talks about AUTH handshake; stream.py currently has the auth block commented out and "Authentication Bypassed".
- Impact:
  - This is likely intentional for local/dev usage; for production the guide says AUTH; recommend making auth conditional on settings flag (e.g., require ADMIN_TOKEN when ENV_MODE=production).
- Recommendation:
  - Use settings.ADMIN_TOKEN presence or ENV_MODE to enable strict handshake in production.

C. Settings & presets consistency
- Files:
  - backend/config/settings.py
  - backend/api/trading.py
  - ShadowEngine code uses its own ShadowConfig dataclass
- Observation:
  - The guide documents Coffee/Espresso presets (MIN_HOLD_TIME 45 vs 10) but Settings defaults use MIN_HOLD_TIME=90 in current file. The code has multiple places using different defaults. This is mostly a docs/config drift rather than runtime error.
- Recommendation:
  - Reconcile default constants in settings.py and the guide (pick canonical defaults), and ensure API endpoints that derive preset names match settings constants.

D. Logging system
- Files:
  - backend/config/logging_config.py
- Observation:
  - Logging uses a QueueListener to offload; configure_logging stores listener as attribute — good. However configure_logging clears root_logger.handlers after starting listener; but QueueListener.start() was started before adding the QueueHandler to root; listener.start() expects handlers to be present; current code adds QueueHandler after clearing handlers — works because listener created with console_handler & file_handler objects. This area is implemented but should be tested under load.
- Recommendation:
  - Add unit test to ensure logging continues after reconfiguration and on shutdown call to shutdown_logging().

E. WebSocketManager: `get_latest_buffer` returns internal buffer; stream.broadcast_loop mutates it; concurrency is okay but consider copying to avoid race conditions.
- Recommendation:
  - Change get_latest_buffer to return a shallow copy (`return dict(self.buffer)`) to avoid external mutation during iteration.

---

3) CONFIRMED FEATURES (guide sections that appear implemented in code)

The following features from the guide are present and appear implemented in code (either fully or with defensive fallbacks):

- FastAPI-based backend with endpoints (backend/main.py, many API modules present).
- BrainEngine with incremental statistics (IncrementalStats) and z_score calculation (backend/services/brain.py).
- Trading service loop present with PerformanceTracker (backend/services/trading_service.py).
- Database wrapper with WAL and tables for analyses/signals/trades/positions/metrics (backend/services/database.py).
- WebSocket manager for Binance with multiplex socket (backend/services/websocket_manager.py).
- OmniRouter pattern and Binance/Alpaca broker classes present (backend/brokers/*).
- TUI frontend artifacts: Zustand store, hooks, components (victory-bridge files included).
- Panic switch and atomic file write utilities (backend/core/failsafe.py and backend/core/utils.py) — though duplicated.
- Authentication endpoints with JWT token generation (backend/api/auth.py).
- Shadow engine implementation present (backend/services/shadow_engine.py) with stats & check_validation_criteria.
- Arena manager, gamemodes, simulation harness, and many strategies skeletons present (backend/arena/*).
- Configuration via pydantic BaseSettings and get_settings caching (backend/config/settings.py).
- Sentinels and watchdog-like process (backend/services/sentinel.py).
- Many of the dashboard API endpoints exist and return consistent structures.

---

4) PRIORITIZED ACTION ITEMS (recommended fixes, minimal patches)

I. Fix runtime exceptions in stream broadcast / handshake
- Replace references to `engine.history` with `engine.z_score_history` or safe-access code.
- Fix usage of compute_projection assumptions: adapt broadcast_loop to operate using compute_projection() outputs, or update BrainEngine.compute_projection to provide the projection shape broadcast expects.

II. Add Database compatibility wrapper methods
- Add thin wrappers in backend/services/database.py:
  - `get_open_positions()` -> returns list of upserted positions
  - `get_positions()` -> alias to return all positions
  - `delete_position(symbol)` -> delete a position row
  - `insert_position(...)` -> compatibility shim for older callers
This will reduce the many defensive try/except blocks in callers.

III. Consolidate atomic_write implementations
- Keep a single canonical atomic_write API and add the alternate convenience wrapper or rename to avoid collision.

IV. Make WebSocket auth conditional and configurable
- Re-enable the commented auth handshake in stream.py and gate it behind a setting (e.g., require AUTH when ENV_MODE == "production" or when ADMIN_TOKEN set).

V. Small/Medium improvements
- Make WebSocketManager.get_latest_buffer return a shallow copy.
- Add unit tests that cover broadcast_loop and compute_projection integration.
- Add minimal health-check logging for router initialization failures.

---

5) SUGGESTED NEXT STEPS & QUICK COMMANDS

Run the project's tests and basic startup checks:

Suggested commands (run from project root):
- `python -m pytest -q`  -- run test suite
- `uvicorn backend.main:app --reload` -- start backend for manual testing
- `python -c "from backend.services.database import Database; Database()._init_db(); print('DB OK')"` -- quick DB init check

(If you want, I can produce and apply focused code changes for any of the "PRIORITIZED ACTION ITEMS" above; tell me which ones and I will provide exact SEARCH/REPLACE edits.)

---

6) APPENDIX: DETECTED LOCATIONS OF SPECIFIC MISMATCHES

- `backend/routers/stream.py` lines referencing `engine.history` and expecting projection `times/prices` — must change to use `engine.z_score_history` and the actual compute_projection output.
- `backend/services/brain.py` compute_projection: returns {'signal','confidence','regime','volatility','phase'} — consider expanding or documenting.
- `backend/services/database.py` lacks `get_open_positions`, `get_positions`, `delete_position`, `insert_position` which are referenced by callers in defensive ways (see trading_service and manager).
- `backend/core/failsafe.py` and `backend/core/utils.py` both implement atomic write utilities with different signatures.
- `backend/brokers/binance.py` contains duplicated except blocks in get_position; consider deduping.
