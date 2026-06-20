#!/bin/bash
# Serve script for the Auratic Frontend Vue + Vite App
# Usage: ./serve.sh [port] [mode: dev|prod]

PORT=${1:-1420}
MODE=${2:-dev}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ "$MODE" = "dev" ] && command -v npm &> /dev/null && [ -d "node_modules" ]; then
    echo "🚀 Starting Vite development server on port $PORT..."
    npm run dev -- --port $PORT
else
    # Production / static fallback
    if [ ! -d "dist" ] && command -v npm &> /dev/null; then
        echo "📦 Building frontend first..."
        npm run build
    fi
    
    if [ -d "dist" ]; then
        echo "🚀 Starting HTTP server on port $PORT serving compiled dist/..."
        echo "📊 Open http://localhost:$PORT in your browser"
        echo "🛑 Press Ctrl+C to stop"
        echo ""
        cd dist
        if command -v python3 &> /dev/null; then
            python3 -m http.server $PORT
        elif command -v php &> /dev/null; then
            php -S localhost:$PORT
        else
            echo "❌ No HTTP server found! Install Python 3 or PHP, or run npm run dev."
            exit 1
        fi
    else
        echo "❌ Error: compiled 'dist' directory not found and cannot run Vite dev server."
        echo "Please run: npm install && npm run build"
        exit 1
    fi
fi
