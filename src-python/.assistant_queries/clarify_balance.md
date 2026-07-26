Observed: logs show repeated "Insufficient balance ($0.00) - skipping BTCEUR" warnings every ~20s.
I can make code changes to reduce log spam and/or fix balance retrieval/fallbacks, but I need your decision which behavior you want.

Options (pick one or tell me a different approach):
1) Prefer stablecoin balances (recommended for crypto trading):
   - Change the wallet balance lookup to prefer "USDT" or "USDC" over "EUR".
   - Fallback order: USDT -> USDC -> EUR -> raw numeric return.

2) Improve robustness of wallet.get_balance handling:
   - Accept dict or numeric returns, handle None, and treat corrupt returns as 0 with a single warning.
   - Add a one-time warning per symbol instead of repeated logs (rate-limit).

3) Add a configurable minimum-balance threshold and early-exit:
   - If balance < MIN_TRADE_BALANCE (new setting, default 15.0), skip trading silently or log at DEBUG level.
   - Expose MIN_TRADE_BALANCE in settings.py.

4) Preserve simulated starting balance for testnet:
   - If in TESTNET/MOCK mode and wallet returns 0, use SETTINGS.starting_balance to allow simulated trades.
   - Safer: only enable when MOCK_TRADING=True.

5) Quick fix (local change):
   - Change call wallet.get_balance("EUR") -> wallet.get_balance("USDT") and rate-limit repeating warnings.

Tell me which option you'd like. If you want, I can implement a combination (e.g., 1 + 2 + 3).

Implementation notes (what I'll change in code):
- Edit backend/services/trading_service.py:
  - Replace the single-currency balance lookup with a helper that tries multiple currencies and normalizes return types.
  - Add a small in-memory set to track which symbols already warned to avoid log spam (e.g., warned_balance_symbols = set()).
  - Make MIN_TRADE_BALANCE configurable via settings (add setting if chosen).
- Optional: update backend/config/settings.py to add MIN_TRADE_BALANCE and MOCK_TRADING behavior.

If you approve one of the options, I'll produce SEARCH/REPLACE blocks that modify:
- backend/services/trading_service.py
- backend/config/settings.py (only if we add a new setting)

Suggested quick checks you can run now:
- tail -f backend.log | grep -i balance
- python backend/main.py

Reply with the option number you want (1-5), or "combine 1+2+3", or specify a different approach.
