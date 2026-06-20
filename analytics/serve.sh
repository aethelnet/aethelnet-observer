#!/bin/bash
# Serve analytics dashboard on port 1424

PORT=1424
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "📊 Starting Performance Analytics Hub on port $PORT..."
echo "📂 Serving from: $DIR"
echo "🌐 Open: http://localhost:$PORT"
echo ""

# Check for Python 3
if command -v python3 &> /dev/null; then
    cd "$DIR"
    python3 -m http.server $PORT
# Check for PHP
elif command -v php &> /dev/null; then
    cd "$DIR"
    php -S localhost:$PORT
else
    echo "❌ Error: Neither Python 3 nor PHP found"
    exit 1
fi







