#!/bin/bash
# Serve Trade Opportunities View on port 1427

PORT=1427
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Starting Trade Opportunities View on port $PORT"
echo "📁 Directory: $DIR"
echo "🌐 Open: http://localhost:$PORT"
echo ""
echo "Press Ctrl+C to stop"
echo ""

cd "$DIR"
python3 -m http.server $PORT



