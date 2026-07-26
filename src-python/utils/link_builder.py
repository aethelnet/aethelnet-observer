"""
Utilities to build external links to common chart/news pages (TradingView, Yahoo Finance, CoinGecko).

This module contains a small mapping table for common tickers (e.g. XAUUSD -> Yahoo's XAUUSD=X)
and returns multiple candidate links so the Telegram bot can present fallbacks.

Developer guide:
- If a symbol needs a special mapping, add it to _OVERRIDES with keys:
    "yahoo", "tradingview", "coingecko"
- The bot expects a dict with keys: "yahoo", "tradingview_chart", "tradingview_symbol", "coingecko"
"""
from __future__ import annotations

from typing import Dict, Optional
import urllib.parse
from config.settings import get_settings

_OVERRIDES: Dict[str, Dict[str, str]] = {
    # Common special cases (add more mappings here as needed)
    "XAUUSD": {
        # Yahoo uses XAUUSD=X for many FX/futures tickers
        "yahoo": "XAUUSD=X",
        # TradingView sometimes prefers a broker prefix; OANDA is common for FX quotes.
        "tradingview": "OANDA:XAUUSD",
        # CoinGecko has no canonical coin called XAUUSD, use search instead.
        "coingecko": "search:xauusd",
    },
    "BTCUSDT": {
        "yahoo": "BTC-USD",
        "tradingview": "BINANCE:BTCUSDT",
        "coingecko": "bitcoin",
    },
    "BTC": {
        "yahoo": "BTC-USD",
        "tradingview": "BINANCE:BTCUSDT",
        "coingecko": "bitcoin",
    },
    "BTCUSDC": {
        "yahoo": "BTC-USD",
        "tradingview": "BINANCE:BTCUSDC",
        "coingecko": "bitcoin",
    },
    "BTCEUR": {
        "yahoo": "BTC-EUR",
        "tradingview": "BINANCE:BTCEUR",
        "coingecko": "bitcoin",
    },
    "ETHUSDT": {
        "yahoo": "ETH-USD",
        "tradingview": "BINANCE:ETHUSDT",
        "coingecko": "ethereum",
    },
    "ETHUSDC": {
        "yahoo": "ETH-USD",
        "tradingview": "BINANCE:ETHUSDC",
        "coingecko": "ethereum",
    },
    # US equities
    "AAPL": {
        "yahoo": "AAPL",
        "tradingview": "NASDAQ:AAPL",
        # CoinGecko tokenized-stock page for Apple is "apple-xstock"
        "coingecko": "apple-xstock",
    },
    "NVDA": {
        "yahoo": "NVDA",
        "tradingview": "NASDAQ:NVDA",
        "coingecko": "search:nvda",
    },
    "MSFT": {
        "yahoo": "MSFT",
        "tradingview": "NASDAQ:MSFT",
        "coingecko": "search:msft",
    },
    "TSLA": {
        "yahoo": "TSLA",
        "tradingview": "NASDAQ:TSLA",
        "coingecko": "search:tsla",
    },
    "GOOGL": {
        "yahoo": "GOOGL",
        "tradingview": "NASDAQ:GOOGL",
        "coingecko": "search:googl",
    },
    "AMZN": {
        "yahoo": "AMZN",
        "tradingview": "NASDAQ:AMZN",
        "coingecko": "search:amzn",
    },
    # Major FX pairs
    "EURUSD": {
        "yahoo": "EURUSD=X",
        "tradingview": "FX:EURUSD",
        "coingecko": "search:eurusd",
    },
    "GBPUSD": {
        "yahoo": "GBPUSD=X",
        "tradingview": "FX:GBPUSD",
        "coingecko": "search:gbpusd",
    },
    "USDJPY": {
        "yahoo": "USDJPY=X",
        "tradingview": "FX:USDJPY",
        "coingecko": "search:usdjpy",
    },
}


def normalize_symbol(symbol: str) -> str:
    return (symbol or "").strip().upper()


def build_yahoo_url(symbol: str) -> str:
    s = normalize_symbol(symbol)
    override = _OVERRIDES.get(s, {})
    ticker = override.get("yahoo") or f"{s}"
    # Some tickers require URL escaping
    return f"https://finance.yahoo.com/quote/{urllib.parse.quote(ticker)}"


def build_tradingview_chart_url(symbol: str) -> str:
    """
    Return a TradingView chart URL. If we have an override like "OANDA:XAUUSD"
    we encode that into the URL's symbol param.
    """
    s = normalize_symbol(symbol)
    override = _OVERRIDES.get(s, {})
    tv_symbol = override.get("tradingview") or s
    # TradingView expects colon-separated exchange:symbol (encoded as needed)
    return f"https://www.tradingview.com/chart/?symbol={urllib.parse.quote(tv_symbol)}"


def build_mt5_webtrader_url(symbol: str, timeframe: Optional[str] = None, entry: Optional[float] = None, sl: Optional[float] = None, tp: Optional[float] = None) -> Optional[str]:
    """
    Build an MT5 broker webtrader URL for quick preset of a trade.

    Format used (example broker web terminal):
      https://webtrader.icmarkets.com/?symbol={symbol}&timeframe={tf}&entry={entry_price}&sl={stop_loss}&tp={take_profit}

    Behavior:
    - Reads MT5_WEBTRADER_URL and MT5_WEBTRADER_ENABLED from settings; returns None if disabled or unset.
    - Only generates links for non-crypto assets by default (heuristic).
      Cryptos are skipped unless the override explicitly provides a compatible trading symbol.
    - If entry/sl/tp are None, returns a base webtrader URL with symbol & timeframe if possible.
    """
    try:
        settings = get_settings()
        base = getattr(settings, "MT5_WEBTRADER_URL", None)
        enabled = getattr(settings, "MT5_WEBTRADER_ENABLED", True)
        if not base or not enabled:
            return None
    except Exception:
        return None

    s = normalize_symbol(symbol)

    # Heuristic: treat common crypto indicators as crypto and skip MT5 for them
    crypto_suffixes = ("USDT", "USDC", "BTC", "ETH", "BUSD", "BNB")
    is_crypto = any(s.endswith(suf) for suf in crypto_suffixes) and not s.startswith("FX:")
    # Also check overrides: if override tradingview explicitly references FX: or NASDAQ: treat as allowed
    override = _OVERRIDES.get(s, {})
    tv_override = override.get("tradingview", "") or ""
    if tv_override.startswith("FX:") or "NASDAQ:" in tv_override or "NYSE:" in tv_override or s in _OVERRIDES and (tv_override.startswith("NASDAQ:") or tv_override.startswith("FX:")):
        is_crypto = False

    if is_crypto:
        # Broker web terminals typically do not accept crypto tickers; skip by default.
        return None

    # Build base URL and append parameters if present
    url = base.rstrip("/")
    params = []
    # symbol parameter: prefer override tradingview symbol if it looks exchange-prefixed
    tv_symbol = override.get("tradingview") or s
    params.append(f"symbol={urllib.parse.quote(tv_symbol)}")
    if timeframe:
        params.append(f"timeframe={urllib.parse.quote(timeframe)}")
    if entry is not None:
        params.append(f"entry={entry}")
    if sl is not None:
        params.append(f"sl={sl}")
    if tp is not None:
        params.append(f"tp={tp}")

    if params:
        return f"{url}/?{'&'.join(params)}"
    return f"{url}/?symbol={urllib.parse.quote(tv_symbol)}"


def format_trade_links(symbol: str, timeframe: Optional[str] = None, entry: Optional[float] = None, sl: Optional[float] = None, tp: Optional[float] = None, side: Optional[str] = None) -> str:
    """
    Produce a combined, human-readable links line for a trade or prediction:

      "TradingView: <url> | Yahoo: <url> | MT5: <url>"

    Behavior:
    - Uses build_tradingview_chart_url and build_yahoo_url for TV/Yahoo links.
    - Attempts to generate an MT5 webtrader URL (with entry/sl/tp params) when available.
    - If entry/sl/tp are provided, they are used to parameterize the MT5 link and
      the TradingView fragment (position/entry/stop/target).
    - Returns a single string with available links separated by " | ".
    """
    tv_base = build_tradingview_chart_url(symbol)
    yahoo = build_yahoo_url(symbol)
    mt5 = None
    # Parameterized MT5 URL if possible
    try:
        mt5 = build_mt5_webtrader_url(symbol, timeframe, entry, sl, tp)
    except Exception:
        mt5 = None

    # Build a TradingView URL that encodes the proposed level(s) in a fragment
    tv_full = tv_base
    if any(v is not None for v in (entry, sl, tp, side)) and tv_base:
        frag_parts = []
        if side:
            frag_parts.append(f"position:{str(side).lower()}")
        if entry is not None:
            frag_parts.append(f"entry={entry}")
        if sl is not None:
            frag_parts.append(f"stop={sl}")
        if tp is not None:
            frag_parts.append(f"target={tp}")
        if frag_parts:
            tv_full = f"{tv_base}#{'&'.join(frag_parts)}"

    parts = []
    if tv_full:
        parts.append(f"TradingView: {tv_full}")
    if yahoo:
        parts.append(f"Yahoo: {yahoo}")
    if mt5:
        parts.append(f"MT5 Setup: {mt5}")
    # If no MT5 available, still return TV|Yahoo; caller can add paste instructions.
    return " | ".join(parts)


def build_tradingview_symbol_page(symbol: str) -> str:
    """
    Try to produce a /symbols/.../ page; TradingView uses underscores for page paths
    like 'FX_XAUUSD' for some forex pairs.
    """
    s = normalize_symbol(symbol)
    override = _OVERRIDES.get(s, {})
    tv_symbol = override.get("tradingview") or s
    # convert ":" to "_" for the symbols path
    path_symbol = tv_symbol.replace(":", "_")
    return f"https://www.tradingview.com/symbols/{urllib.parse.quote(path_symbol)}/"


def build_coingecko_url(symbol: str) -> str:
    """
    Prefer a direct coin page when we know the coingecko id, otherwise return a
    sensible coin page or search page. Uses simple heuristics for common crypto
    tickers (e.g. BTCUSDT -> bitcoin) and falls back to the search page for
    stocks/FX or unknown symbols.

    Overrides in _OVERRIDES take precedence. If the override value starts with
    "search:" the remainder is used as the search query; otherwise it's treated
    as the direct coingecko id.
    """
    s = normalize_symbol(symbol)
    override = _OVERRIDES.get(s, {})
    cg = override.get("coingecko")
    if cg:
        if isinstance(cg, str) and cg.startswith("search:"):
            q = cg.split("search:", 1)[1]
            return f"https://www.coingecko.com/en/search?query={urllib.parse.quote(q)}"
        return f"https://www.coingecko.com/en/coins/{urllib.parse.quote(cg)}"

    # Heuristic: common crypto pairs like BTCUSDT -> bitcoin
    # If symbol ends with a common quote currency like USDT, strip it.
    if s.endswith("USDT") and len(s) > 4:
        base = s[:-4].lower()
        return f"https://www.coingecko.com/en/coins/{urllib.parse.quote(base)}"

    # Known single-asset cryptos map to their lowercase id.
    common_crypto_ids = {"BTC", "ETH", "SOL", "LTC", "XRP", "ADA", "DOT", "BCH", "LINK"}
    if s in common_crypto_ids:
        return f"https://www.coingecko.com/en/coins/{urllib.parse.quote(s.lower())}"

    # For stocks and forex, CoinGecko does not have canonical coin pages. Use search.
    query = s.lower()
    return f"https://www.coingecko.com/en/search?query={urllib.parse.quote(query)}"


def build_all_links(symbol: str) -> Dict[str, str]:
    """
    Return a dict of useful external links. New keys:
      - mt5: MT5 broker webtrader URL (may be None if not supported/available)
      - dxcharts: fallback URL (same as tradingview_chart) when MT5 requires login

    Keep existing keys (yahoo, tradingview_chart, tradingview_symbol, coingecko) for backward compatibility.
    """
    tv = build_tradingview_chart_url(symbol)
    yahoo = build_yahoo_url(symbol)
    coingecko = build_coingecko_url(symbol)
    mt5 = build_mt5_webtrader_url(symbol)  # may be None (no support) or a base URL
    dxcharts = tv  # fallback to TradingView's chart if MT5 not available

    result: Dict[str, str] = {
        "yahoo": yahoo,
        "tradingview_chart": tv,
        "tradingview_symbol": build_tradingview_symbol_page(symbol),
        "coingecko": coingecko,
        "dxcharts": dxcharts,
    }
    if mt5:
        result["mt5"] = mt5
    return result
