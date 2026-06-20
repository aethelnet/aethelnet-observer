#!/bin/bash
# Creative interface HTTP server
# Usage: ./serve.sh [port]

PORT=${1:-1421}

echo "🎨 Starting Creative Interface on port $PORT..."
echo "🌌 Open http://localhost:$PORT in your browser"
echo "📊 MVP is on http://localhost:1420 (keep it open!)"
echo "🛑 Press Ctrl+C to stop"
echo ""

# Try different server options
if command -v python3 &> /dev/null; then
    python3 -m http.server $PORT
elif command -v python &> /dev/null; then
    python -m SimpleHTTPServer $PORT
elif command -v php &> /dev/null; then
    php -S localhost:$PORT
else
    echo "❌ No HTTP server found!"
    echo "Install Python 3 or PHP to use this script."
    exit 1
fi







