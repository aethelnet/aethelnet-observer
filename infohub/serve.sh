#!/bin/bash
# Serve Info Hub View on port 1430

PORT=1430
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Starting Info Hub View on port $PORT"
echo "📁 Directory: $DIR"
echo "🌐 Open: http://localhost:$PORT"
echo ""
echo "Press Ctrl+C to stop"
echo ""

cd "$DIR"
python3 -m http.server $PORT



