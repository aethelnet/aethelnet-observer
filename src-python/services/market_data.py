"""
Minimal market data service used by the Telegram bot.

This module provides a tiny in-memory adapter that other backend components
can push simple market updates into (via update_from_feed). The Telegram bot
and other consumers can then call get_latest, get_candle, or get_summary to
produce human-readable messages. This avoids adding heavy new backend APIs —
feeds already produced elsewhere can call update_from_feed(feed) with a
small dict.

Developer guide (short):
- To publish an update into this service:
    from services.market_data import update_from_feed
    update_from_feed({
        "symbol": "XAUUSD",
        "price": 1946.23,
        "ts": datetime.datetime.utcnow(),
        "interval": "1h",              # optional
        "candle": {                    # optional: latest candle data
            "open": 1940.0,
            "high": 1950.0,
            "low": 1938.0,
            "close": 1946.23,
            "ts": datetime.datetime.utcnow()
        },
        "complete": True               # whether the candle is complete
    })

- Consumers:
    get_latest("XAUUSD") -> dict or None
    get_candle("XAUUSD", "1h") -> dict or None
    get_summary("XAUUSD", "1h") -> str ready for sending to Telegram

This module intentionally stays dependency-free and synchronous.
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional, Any
import threading
import copy
import logging

logger = logging.getLogger("market_data")

_lock = threading.RLock()

# In-memory store format:
# _LATEST: {
#   "SYMBOL": {
#       "price": float,
#       "ts": datetime,
#       "intervals": {
#           "1h": {"last_candle": {...}, "complete": bool}
#       }
#   }
# }
_LATEST: Dict[str, Dict[str, Any]] = {}

# Default list of symbols the bot supports/searches for even if no feed yet.
DEFAULT_TRACKED_SYMBOLS = [
    "AAPL",
    "NVDA",
    "MSFT",
    "TSLA",
    "GOOGL",
    "AMZN",
    "BTCUSDT",
    "ETHUSDT",
    "XAUUSD",
    "EURUSD",
    "GBPUSD",
    "USDJPY",
]


def normalize_symbol(symbol: str) -> str:
    """
    Normalize an incoming symbol into the repository's canonical internal key.

    Rules (conservative):
    - Uppercase and strip whitespace.
    - If symbol contains an exchange prefix like "OANDA:EURUSD" or "BINANCE:BTCUSDT",
      strip the prefix and keep the part after the colon.
    - Replace common separators "_" -> "" (e.g. "XAU_USD" -> "XAUUSD").
    - Prefer known tracked pairs when short base tokens or unusual quote tokens (XAU/XAG) are used.
    - Attempt to consult runtime settings.get_trading_symbols() when available to align with configured
      trading universe (safe, optional).
    - This is intentionally lightweight so adapters can continue to emit a variety of
      ticker formats while the bot uses a stable internal keyspace.
    """
    if not symbol:
        return ""
    s = str(symbol).strip().upper()

    # If contains colon (exchange prefix), take everything after the colon
    if ":" in s:
        s = s.split(":", 1)[1]

    # Remove common separators
    s = s.replace("_", "").replace("-", "")

    # If symbol uses a commodity-like quote (e.g. ends with XAU or XAG), try to map to a tracked pair.
    for cquote in ("XAU", "XAG"):
        if s.endswith(cquote) and len(s) > len(cquote):
            base = s[:-len(cquote)]
            # Candidate preference order: USD, USDC, USDT, EUR
            candidates = [f"{base}USD", f"{base}USDC", f"{base}USDT", f"{base}EUR"]
            # Prefer DEFAULT_TRACKED_SYMBOLS (fast, no external deps)
            for c in candidates:
                if c in DEFAULT_TRACKED_SYMBOLS:
                    logger.debug("normalize_symbol: mapped %s -> %s via DEFAULT_TRACKED_SYMBOLS", s, c)
                    return c
            # If settings are available, consult configured trading symbols
            try:
                from config.settings import get_settings, get_trading_symbols

                settings = get_settings()
                tracked = set(get_trading_symbols(settings))
                for c in candidates:
                    if c in tracked:
                        logger.debug("normalize_symbol: mapped %s -> %s via configured trading symbols", s, c)
                        return c
            except Exception:
                # settings may not be importable in some test contexts; ignore failures gracefully
                pass

            # If the input was actually the commodity itself (XAU/XAG), map to common USD pair
            if base in ("XAU", "XAG") or s in ("XAU", "XAG"):
                mapped = f"{base}USD"
                logger.debug("normalize_symbol: mapped commodity token %s -> %s", s, mapped)
                return mapped

            # Otherwise, leave as-is (caller/adapters may decide how to handle uncommon quotes)
            logger.debug("normalize_symbol: leaving uncommon quote token unchanged: %s", s)
            return s

    # If it's a short base like "XAU" and a tracked pair exists like XAUUSD/XAUUSDC, prefer that.
    if len(s) <= 4 and s.isalpha():
        candidates = [f"{s}USD", f"{s}USDC", f"{s}USDT", f"{s}EUR"]
        for c in candidates:
            if c in DEFAULT_TRACKED_SYMBOLS:
                logger.debug("normalize_symbol: short token %s -> %s via DEFAULT_TRACKED_SYMBOLS", s, c)
                return c
        # As a fallback, consult configured trading symbols if available
        try:
            from config.settings import get_settings, get_trading_symbols

            settings = get_settings()
            tracked = set(get_trading_symbols(settings))
            for c in candidates:
                if c in tracked:
                    logger.debug("normalize_symbol: short token %s -> %s via configured trading symbols", s, c)
                    return c
        except Exception:
            pass

    return s


def _now() -> datetime:
    return datetime.utcnow()


def update_from_feed(feed: Dict[str, Any]) -> None:
    """
    Push a lightweight market feed into the in-memory store.

    Expected keys:
      - symbol (str) REQUIRED
      - price (float) OPTIONAL
      - ts (datetime) OPTIONAL, will default to now()
      - interval (str) OPTIONAL, e.g. "1h"
      - candle (dict) OPTIONAL: {open, high, low, close, ts}
      - complete (bool) OPTIONAL: whether the candle is complete
    """
    raw_symbol = feed.get("symbol", "")
    symbol = normalize_symbol(str(raw_symbol)) if raw_symbol is not None else ""
    if not symbol:
        return

    with _lock:
        # keep predictions/opportunities fields on entries so consumers can push
        # lightweight ML forecasts and suggested opportunities into the same feed.
        # Persist the canonical key while keeping the original source symbol for debugging.
        entry = _LATEST.setdefault(
            symbol,
            {
                "price": None,
                "ts": None,
                "intervals": {},
                "predictions": [],
                "opportunities": [],
                "source_symbol": raw_symbol,
            },
        )
        if "price" in feed and feed["price"] is not None:
            entry["price"] = float(feed["price"])
            entry["ts"] = feed.get("ts", _now())
        interval = feed.get("interval")
        if interval:
            iv = entry["intervals"].setdefault(interval, {"last_candle": None, "complete": False})
            candle = feed.get("candle")
            if candle:
                # normalize candle fields if present
                iv["last_candle"] = {
                    "open": float(candle.get("open")) if candle.get("open") is not None else None,
                    "high": float(candle.get("high")) if candle.get("high") is not None else None,
                    "low": float(candle.get("low")) if candle.get("low") is not None else None,
                    "close": float(candle.get("close")) if candle.get("close") is not None else None,
                    "ts": candle.get("ts", _now()),
                }
            if "complete" in feed:
                iv["complete"] = bool(feed["complete"])

        # Optional: allow other backend components to push predictions/opportunities
        # in the same lightweight feed to avoid adding new APIs. These are shallow-copied.
        if "predictions" in feed and feed["predictions"] is not None:
            try:
                entry["predictions"] = list(feed["predictions"])
            except Exception:
                # defensive: ignore malformed predictions
                entry["predictions"] = []

        if "opportunities" in feed and feed["opportunities"] is not None:
            try:
                entry["opportunities"] = list(feed["opportunities"])
            except Exception:
                entry["opportunities"] = []


def get_latest(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Return a deep copy of the latest known data for symbol, or None if unknown.

    Returning a deep copy prevents callers from accidentally mutating the
    internal in-memory store.
    """
    key = normalize_symbol(symbol)
    with _lock:
        entry = _LATEST.get(key)
        if not entry:
            return None
        return copy.deepcopy(entry)


def get_candle(symbol: str, interval: str) -> Optional[Dict[str, Any]]:
    key = normalize_symbol(symbol)
    with _lock:
        entry = _LATEST.get(key)
        if not entry:
            return None
        # return a deep copy so callers cannot mutate the internal store
        return copy.deepcopy(entry.get("intervals", {}).get(interval))


def list_symbols() -> Dict[str, Dict[str, Any]]:
    """
    Return a dict of currently active symbols -> latest entry (deepcopied).

    Only include symbols that actually have data pushed into the in-memory
    store. A symbol is considered active if at least one of:
      - a non-null, non-zero price is present
      - interval/candle data exists
      - predictions or opportunities have been pushed

    This makes the bot dynamic: it will only display symbols for which the
    backend has produced data, avoiding showing default/untracked symbols.
    """
    with _lock:
        result: Dict[str, Dict[str, Any]] = {}
        for sym, entry in _LATEST.items():
            price = entry.get("price")
            has_intervals = bool(entry.get("intervals"))
            has_preds = bool(entry.get("predictions"))
            has_opps = bool(entry.get("opportunities"))
            # Skip entries that are effectively empty
            if (price is None or price == 0) and not (has_intervals or has_preds or has_opps):
                continue
            result[sym] = copy.deepcopy(entry)
        return result


def symbol_debug_report(symbol: str) -> Dict[str, Any]:
    """
    Return a small diagnostics dict for a given symbol to help debug why a
    symbol like XAUUSD may not be appearing in the active list.

    The report contains:
      - present: bool (is symbol known in the in-memory store)
      - price: latest price or None
      - ts: timestamp or None
      - has_intervals: whether any interval/candle data exists
      - has_predictions: boolean
      - has_opportunities: boolean
      - age_seconds: time since last price (if present) or None
      - default_tracked: whether symbol is in DEFAULT_TRACKED_SYMBOLS
    """
    key = normalize_symbol(symbol)
    with _lock:
        entry = _LATEST.get(key)
        now = _now()
        if not entry:
            return {
                "present": False,
                "price": None,
                "ts": None,
                "has_intervals": False,
                "has_predictions": False,
                "has_opportunities": False,
                "age_seconds": None,
                "default_tracked": key in DEFAULT_TRACKED_SYMBOLS,
            }
        price = entry.get("price")
        ts = entry.get("ts")
        age = (now - ts).total_seconds() if isinstance(ts, datetime) else None
        return {
            "present": True,
            "price": price,
            "ts": ts,
            "has_intervals": bool(entry.get("intervals")),
            "has_predictions": bool(entry.get("predictions")),
            "has_opportunities": bool(entry.get("opportunities")),
            "age_seconds": age,
            "default_tracked": key in DEFAULT_TRACKED_SYMBOLS,
        }


def list_all_known_keys() -> list:
    """
    Return all keys currently in the internal _LATEST store (useful for
    diagnosing naming mismatches between adapters and the bot).
    """
    with _lock:
        return sorted(list(_LATEST.keys()))


def _fmt_price(v: Optional[float]) -> str:
    if v is None:
        return "-"
    # choose reasonable decimal formatting, strip trailing zeros
    s = f"{v:.6f}"
    s = s.rstrip("0").rstrip(".")
    return s


def get_summary(symbol: str, interval: str = "1h") -> str:
    """
    Produce a concise summary string for the symbol and interval suitable for
    Telegram messages. Includes price/timestamp and a short candle summary when available.

    The summary is intentionally self-contained so the bot can send something
    useful even if link construction or other services are unavailable.
    """
    s = symbol.upper()
    latest = get_latest(s)
    lines = []
    lines.append(f"[SYMBOL] {s} - Market Summary")
    # Always include a timestamp for clarity
    now_ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines.append(f"[TIME] {now_ts}")

    if not latest:
        lines.append("")
        lines.append("No market data available for this symbol.")
        lines.append("")
        lines.append("Try these actions:")
        lines.append(f"* /symbol {s} 1h  — request again for a 1-hour snapshot")
        lines.append("* /daily [SYMBOL]  — daily overview")
        lines.append("* /news [SYMBOL]   — latest headlines")
        lines.append("")
        lines.append("Possible reasons: symbol not tracked, feed lag, or typo in the symbol.")
        return "\n".join(lines)

    price = latest.get("price")
    ts = latest.get("ts")
    if price is not None:
        ts_str = (
            ts.strftime("%Y-%m-%d %H:%M UTC") if isinstance(ts, datetime) else str(ts)
        )
        lines.append("")
        lines.append(f"Last price: { _fmt_price(price) } (as of {ts_str} UTC)")
    else:
        lines.append("")
        lines.append("No latest price recorded for this symbol.")

    # Candle summary
    candle = get_candle(s, interval)
    if candle and candle.get("last_candle"):
        lc = candle["last_candle"]
        lines.append("")
        complete_str = "Complete" if candle.get("complete") else "Incomplete"
        lines.append(f"[CANDLE {interval}] {complete_str}")
        oc = _fmt_price(lc.get("open"))
        hi = _fmt_price(lc.get("high"))
        lo = _fmt_price(lc.get("low"))
        cl = _fmt_price(lc.get("close"))
        lines.append(f"Open: {oc}  High: {hi}  Low: {lo}  Close: {cl}")
    else:
        lines.append("")
        lines.append(f"[CANDLE {interval}] No candle data available.")

    # Helpful footer so users know how to proceed; link building is handled by the bot.
    lines.append("")

    # Include any short predictions or opportunities pushed by upstream feeds.
    preds = latest.get("predictions") if latest else None
    if preds:
        try:
            # show the top simple prediction (shallow structure expected)
            top = preds[0]
            p_t = top.get("ts")
            p_ts = p_t.strftime("%Y-%m-%d %H:%M UTC") if isinstance(p_t, datetime) else str(p_t)
            lines.append("[PREDICTIONS] Latest forecast:")
            lines.append(f"- {top.get('horizon','?')} @ {top.get('price','?')} (confidence: {top.get('confidence','?')}) — {p_ts}")
            lines.append("")
        except Exception:
            pass

    opps = latest.get("opportunities") if latest else None
    if opps:
        try:
            lines.append("[OPPORTUNITIES] Suggested:")
            for o in opps[:3]:
                lines.append(f"- {o.get('action','?')} {o.get('symbol', symbol)} (conf: {o.get('confidence','?')}) — {o.get('note','')}")
            lines.append("")
        except Exception:
            pass

    lines.append("You can verify prices on external chart providers (links provided below).")
    return "\n".join(lines)
