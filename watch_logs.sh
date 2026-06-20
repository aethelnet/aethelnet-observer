#!/bin/bash
# Smart log viewer with filtering options
# Usage: ./watch_logs.sh [filter] [logfile]

LOG_FILE="${BACKEND_LOG:-backend.log}"
FILTER="${1:-all}"

# Check if log file exists (try common locations)
if [ ! -f "$LOG_FILE" ]; then
    # Try to find it
    if [ -f "../backend/backend.log" ]; then
        LOG_FILE="../backend/backend.log"
    elif [ -f "input/backups/*/backend.log" ]; then
        LOG_FILE=$(find input/backups -name "backend.log" | head -1)
    else
        echo "❌ Log file not found: $LOG_FILE"
        echo "Set BACKEND_LOG environment variable or pass log file path"
        echo "Example: BACKEND_LOG=/path/to/backend.log ./watch_logs.sh errors"
        exit 1
    fi
fi

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Log file not found: $LOG_FILE"
    echo "Available options:"
    echo "  1. Set BACKEND_LOG environment variable"
    echo "  2. Pass log file as second argument: ./watch_logs.sh errors /path/to/log"
    exit 1
fi

case "$FILTER" in
    errors|error|err)
        echo "🔴 Watching for ERRORS in: $LOG_FILE"
        echo "Press Ctrl+C to stop"
        echo ""
        tail -f "$LOG_FILE" | grep --color=always -E "(ERROR|Exception|Traceback|Failed|FAIL)" | sed 's/^/🔴 /'
        ;;
    trades|trade|exec)
        echo "💰 Watching for TRADES in: $LOG_FILE"
        echo "Press Ctrl+C to stop"
        echo ""
        tail -f "$LOG_FILE" | grep --color=always -E "(TRADE|EXECUTE|FILL|ORDER|LONG|SHORT|BUY|SELL)" | sed 's/^/💰 /'
        ;;
    api|http|request)
        echo "🌐 Watching for API REQUESTS in: $LOG_FILE"
        echo "Press Ctrl+C to stop"
        echo ""
        tail -f "$LOG_FILE" | grep --color=always -E "(GET|POST|PUT|DELETE|/api|HTTP)" | sed 's/^/🌐 /'
        ;;
    websocket|ws)
        echo "🔌 Watching for WEBSOCKET in: $LOG_FILE"
        echo "Press Ctrl+C to stop"
        echo ""
        tail -f "$LOG_FILE" | grep --color=always -E "(WebSocket|ws:|/ws|connected|disconnected)" | sed 's/^/🔌 /'
        ;;
    metrics|pnl|performance)
        echo "📊 Watching for METRICS in: $LOG_FILE"
        echo "Press Ctrl+C to stop"
        echo ""
        tail -f "$LOG_FILE" | grep --color=always -E "(P&L|pnl|metrics|win_rate|drawdown|equity)" | sed 's/^/📊 /'
        ;;
    market|price|signal)
        echo "📈 Watching for MARKET DATA in: $LOG_FILE"
        echo "Press Ctrl+C to stop"
        echo ""
        tail -f "$LOG_FILE" | grep --color=always -E "(price|signal|market|ticker|symbol)" | sed 's/^/📈 /'
        ;;
    all|*)
        echo "📋 Watching ALL logs in: $LOG_FILE"
        echo "Press Ctrl+C to stop"
        echo ""
        tail -f "$LOG_FILE"
        ;;
esac







