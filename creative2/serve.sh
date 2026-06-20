#!/bin/bash
# Serve creative2 on port 1422

PORT=1422
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Starting server on port $PORT..."
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







