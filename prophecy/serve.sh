#!/bin/bash
# Serve PROPHECY Alert Center on port 1428

PORT=1428
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "👁️ Starting PROPHECY Alert Center on port $PORT"
echo "📁 Directory: $DIR"
echo "🌐 Open: http://localhost:$PORT"
echo ""
echo "Press Ctrl+C to stop"
echo ""

cd "$DIR"
python3 -m http.server $PORT



