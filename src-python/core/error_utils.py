"""
Error utilities: categorize and consistently format broker and balance errors.

Provides helpers to:
- categorize_error(error_or_str) -> tag the likely root cause (insufficient_funds, network_error, etc.)
- format_order_error(...) -> produce a single standardized, human-readable log line for order failures
- format_balance_error(...) -> produce consistent balance-related error lines
- get_recovery_suggestion(...) -> return short actionable next steps

Centralizing formatting reduces duplication across trading_service and brokers and makes
logs easier to parse by humans and automated tooling.
"""
from typing import Dict, Optional
from enum import Enum


class ErrorCategory(Enum):
    """Error categories for appropriate handling"""
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
    API_PERMISSION = "API_PERMISSION"
    NETWORK_ERROR = "NETWORK_ERROR"
    INVALID_SYMBOL = "INVALID_SYMBOL"
    RATE_LIMIT = "RATE_LIMIT"
    INVALID_ORDER = "INVALID_ORDER"
    UNKNOWN = "UNKNOWN"


def categorize_error(error_msg: str) -> ErrorCategory:
    """
    Categorize error for appropriate handling.
    
    Args:
        error_msg: The error message string
        
    Returns:
        ErrorCategory enum value
    """
    error_lower = error_msg.lower()
    
    if "insufficient" in error_lower or "balance" in error_lower:
        return ErrorCategory.INSUFFICIENT_BALANCE
    elif "-2015" in error_msg or "permission" in error_lower or "unauthorized" in error_lower:
        return ErrorCategory.API_PERMISSION
    elif "network" in error_lower or "timeout" in error_lower or "connection" in error_lower:
        return ErrorCategory.NETWORK_ERROR
    elif "invalid symbol" in error_lower or "symbol" in error_lower and "not found" in error_lower:
        return ErrorCategory.INVALID_SYMBOL
    elif "rate limit" in error_lower or "429" in error_msg or "too many requests" in error_lower:
        return ErrorCategory.RATE_LIMIT
    elif "invalid order" in error_lower or "invalid" in error_lower and "order" in error_lower:
        return ErrorCategory.INVALID_ORDER
    
    return ErrorCategory.UNKNOWN


def format_order_error(*args, **kwargs) -> str:
    """
    Flexible order error formatter compatible with two call patterns:

    1) New-style:
        format_order_error(symbol: str, side: str, error: str, context: Optional[Dict] = None)

    2) Legacy-style (widely used in trading_service):
        format_order_error(error, symbol=..., size=..., price=..., signal=..., side=...)

    The function will detect the calling convention and normalize the output to a single,
    consistent log message including an actionable recovery suggestion.
    """
    # Normalize into (error, symbol, side, context_dict)
    error = None
    symbol = None
    side = None
    context = {}

    # Case A: keyword args explicitly contain new-style names
    if 'symbol' in kwargs and 'side' in kwargs and ('error' in kwargs or len(args) >= 3):
        symbol = kwargs.get('symbol')
        side = kwargs.get('side')
        error = kwargs.get('error') if 'error' in kwargs else (args[2] if len(args) >= 3 else None)
        context = kwargs.get('context', {})
    # Case B: positional new-style (symbol, side, error, [context])
    elif len(args) >= 3 and isinstance(args[0], str) and isinstance(args[1], str):
        symbol = args[0]
        side = args[1]
        error = args[2]
        if len(args) > 3:
            context = args[3] if isinstance(args[3], dict) else {}
        else:
            context = kwargs.get('context', {})
    else:
        # Legacy-style: (error, symbol, size, price, signal=None, side=None) or keyword equivalents
        error = args[0] if len(args) >= 1 else kwargs.get('error')
        symbol = kwargs.get('symbol') or (args[1] if len(args) >= 2 else None)
        size = kwargs.get('size', None) if ('size' in kwargs or len(args) < 3) else (args[2] if len(args) >= 3 else None)
        price = kwargs.get('price', None) if ('price' in kwargs or len(args) < 4) else (args[3] if len(args) >= 4 else None)
        signal = kwargs.get('signal', None) if ('signal' in kwargs or len(args) < 5) else (args[4] if len(args) >= 5 else None)
        side = kwargs.get('side', None) if ('side' in kwargs or len(args) < 6) else (args[5] if len(args) >= 6 else None)

        # Consolidate into context
        context = kwargs.get('context', {})
        if not isinstance(context, dict):
            context = {}
        if size is not None:
            context.setdefault('size', size)
        if 'qty' in kwargs:
            context.setdefault('qty', kwargs.get('qty'))
        if price is not None:
            context.setdefault('price', price)
        if signal is not None:
            context.setdefault('signal', signal)

    # Safe-stringify reason
    try:
        reason = str(error) if error is not None else "unknown error"
    except Exception:
        reason = "unknown error"

    # Derive category and suggestion if helpers available
    try:
        category = categorize_error(reason)
        suggestion = get_recovery_suggestion(category)
    except Exception:
        suggestion = "Check [BROKER] logs for details"

    side_label = (side or "ORDER").upper()

    # Build parts (size/qty/price/signal) with consistent formatting
    parts = [f"[ORDER] ❌ {side_label} failed: {reason}", f"symbol={symbol}"]
    if isinstance(context, dict):
        # size / qty
        if 'size' in context and context['size'] is not None:
            try:
                parts.append(f"size={float(context['size']):.8f}")
            except Exception:
                parts.append(f"size={context['size']}")
        if 'qty' in context and context['qty'] is not None:
            try:
                parts.append(f"qty={float(context['qty']):.8f}")
            except Exception:
                parts.append(f"qty={context['qty']}")
        # price
        if 'price' in context and context['price'] is not None:
            try:
                parts.append(f"price=${float(context['price']):.2f}")
            except Exception:
                parts.append(f"price={context['price']}")
        # signal
        if 'signal' in context and context['signal'] is not None:
            try:
                parts.append(f"signal={float(context['signal']):.4f}")
            except Exception:
                parts.append(f"signal={context['signal']}")

    parts.append(f"suggestion={suggestion}")

    return " | ".join(parts)


def format_balance_error(symbol: str, required: float, available: float, currency: str) -> str:
    """
    Format balance-related errors.
    
    Args:
        symbol: Trading symbol
        required: Required balance amount
        available: Available balance amount
        currency: Currency code (USDC, EUR, etc.)
        
    Returns:
        Formatted error string
    """
    return f"INSUFFICIENT BALANCE | symbol={symbol} | required={required:.8f} {currency} | available={available:.8f} {currency}"


def get_recovery_suggestion(category: ErrorCategory) -> str:
    """
    Get actionable recovery suggestion for error category.
    
    Args:
        category: ErrorCategory enum value
        
    Returns:
        Actionable suggestion string
    """
    suggestions = {
        ErrorCategory.INSUFFICIENT_BALANCE: "Check wallet balance or reduce position size",
        ErrorCategory.API_PERMISSION: "Verify Binance API permissions and IP whitelist",
        ErrorCategory.NETWORK_ERROR: "Check network connection and retry",
        ErrorCategory.INVALID_SYMBOL: "Verify symbol format and availability on exchange",
        ErrorCategory.RATE_LIMIT: "Wait before retrying - rate limit exceeded",
        ErrorCategory.INVALID_ORDER: "Check order parameters (quantity, price, symbol format)",
        ErrorCategory.UNKNOWN: "Check [BROKER] logs for detailed error information"
    }
    return suggestions.get(category, "Check logs for details")


