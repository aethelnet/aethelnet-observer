#!/bin/bash
# Serve Market Scanner on port 1429

PORT=1429
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "📊 Starting Market Scanner on port $PORT"
echo "📁 Directory: $DIR"
echo "🌐 Open: http://localhost:$PORT"
echo ""
echo "Press Ctrl+C to stop"
echo ""

cd "$DIR"
python3 -m http.server $PORT



