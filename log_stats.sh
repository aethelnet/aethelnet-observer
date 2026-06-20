#!/bin/bash
# Show statistics about recent logs
# Usage: ./log_stats.sh [lines] [logfile]

LINES="${1:-1000}"
LOG_FILE="${2:-${BACKEND_LOG:-backend.log}}"

# Try to find log file if not specified
if [ ! -f "$LOG_FILE" ]; then
    if [ -f "../backend/backend.log" ]; then
        LOG_FILE="../backend/backend.log"
    elif [ -f "input/backups/*/backend.log" ]; then
        LOG_FILE=$(find input/backups -name "backend.log" | head -1)
    fi
fi

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Log file not found: $LOG_FILE"
    echo "Set BACKEND_LOG or pass log file path"
    exit 1
fi

echo "📊 Log Statistics (last $LINES lines from $LOG_FILE)"
echo "=================================================="
echo ""

echo "🔴 Errors:"
ERROR_COUNT=$(tail -n "$LINES" "$LOG_FILE" | grep -c "ERROR" || echo "0")
echo "   $ERROR_COUNT"

echo ""
echo "⚠️  Warnings:"
WARN_COUNT=$(tail -n "$LINES" "$LOG_FILE" | grep -c "WARN" || echo "0")
echo "   $WARN_COUNT"

echo ""
echo "💰 Trades:"
TRADE_COUNT=$(tail -n "$LINES" "$LOG_FILE" | grep -c -E "(TRADE|EXECUTE)" || echo "0")
echo "   $TRADE_COUNT"

echo ""
echo "🌐 API Requests:"
API_COUNT=$(tail -n "$LINES" "$LOG_FILE" | grep -c -E "(GET|POST|PUT|DELETE) /api" || echo "0")
echo "   $API_COUNT"

echo ""
echo "📊 Metrics Updates:"
METRICS_COUNT=$(tail -n "$LINES" "$LOG_FILE" | grep -c -E "(P&L|metrics)" || echo "0")
echo "   $METRICS_COUNT"

echo ""
echo "📈 Top Error Messages:"
tail -n "$LINES" "$LOG_FILE" | grep "ERROR" | sed 's/.*ERROR //' | sort | uniq -c | sort -rn | head -5 | sed 's/^/   /'

echo ""
echo "💰 Recent Trades:"
tail -n "$LINES" "$LOG_FILE" | grep -E "(TRADE|EXECUTE)" | tail -5 | sed 's/^/   /'

echo ""
echo "🔴 Recent Errors:"
tail -n "$LINES" "$LOG_FILE" | grep "ERROR" | tail -3 | sed 's/^/   /'







