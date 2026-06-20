#!/bin/bash
# Launch unified frontend application
# All views are now accessible via hash routing on port 1420
# Usage: ./launch-all.sh [--stop]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.frontend_pids"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Stop function
stop_all() {
    if [ -f "$PID_FILE" ]; then
        echo -e "${YELLOW}🛑 Stopping all frontend servers...${NC}"
        while read pid; do
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid" 2>/dev/null
                echo -e "  ${GREEN}✓${NC} Stopped process $pid"
            fi
        done < "$PID_FILE"
        rm -f "$PID_FILE"
        echo -e "${GREEN}✅ All frontend servers stopped${NC}"
    else
        echo -e "${YELLOW}No running servers found${NC}"
    fi
    exit 0
}

# Check for stop flag
if [ "$1" = "--stop" ] || [ "$1" = "-s" ]; then
    stop_all
fi

# Check if servers are already running
if [ -f "$PID_FILE" ]; then
    echo -e "${YELLOW}⚠️  Frontend servers may already be running${NC}"
    echo -e "  Run ${BLUE}./launch-all.sh --stop${NC} to stop them first"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    stop_all
fi

# Check for Python 3 or PHP
if ! command -v python3 &> /dev/null && ! command -v php &> /dev/null; then
    echo -e "${RED}❌ Error: Neither Python 3 nor PHP found${NC}"
    echo "Please install Python 3 or PHP to run the frontend servers"
    exit 1
fi

# Determine server command
if command -v python3 &> /dev/null; then
    SERVER_CMD="python3 -m http.server"
else
    SERVER_CMD="php -S localhost"
fi

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}     ${GREEN}🚀 Launching Unified Frontend Application${NC}            ${BLUE}║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Unified app runs on port 1420 with hash-based routing
PORT=1420
DIR_PATH="$SCRIPT_DIR"

if [ ! -d "$DIR_PATH" ]; then
    echo -e "${RED}❌${NC} Directory not found: $DIR_PATH"
    exit 1
fi

# Start server in background
cd "$DIR_PATH"
if command -v npm &> /dev/null && [ -d "node_modules" ]; then
    # Start Vite dev server in background
    npm run dev -- --port "$PORT" > /dev/null 2>&1 &
    PID=$!
else
    # Build if needed and serve dist
    if [ ! -d "dist" ] && command -v npm &> /dev/null; then
        npm run build > /dev/null 2>&1
    fi
    if [ -d "dist" ]; then
        cd dist
        if [[ "$SERVER_CMD" == *"python3"* ]]; then
            python3 -m http.server "$PORT" > /dev/null 2>&1 &
        else
            php -S "localhost:$PORT" > /dev/null 2>&1 &
        fi
        PID=$!
        cd ..
    else
        echo -e "${RED}❌ Error: No 'dist' folder and no 'node_modules' to run Vite dev server.${NC}"
        exit 1
    fi
fi
PIDS=($PID)

# Wait a moment to check if it started successfully
sleep 0.5
if kill -0 $PID 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Port ${BLUE}$PORT${NC} - Unified Trading Application"
else
    echo -e "${RED}✗${NC} Port ${BLUE}$PORT${NC} - ${RED}(failed to start)${NC}"
    exit 1
fi

# OLD MULTI-PORT CODE (kept for reference, commented out)
# declare -A VIEWS=(
#     ["1420"]="MVP Dashboard"
#     ["1421"]="Creative View (3D Market Connections)"
#     ["1422"]="Creative View v2 (3D Network + Chart)"
#     ["1423"]="Trading Chart View (Control Deck)"
#     ["1424"]="Performance Analytics Hub"
#     ["1425"]="Risk Management Dashboard"
#     ["1426"]="Trade Execution Monitor"
#     ["1427"]="Trade Opportunities"
#     ["1428"]="PROPHECY Alert Center"
#     ["1429"]="Market Scanner"
# )
# for port in "${!VIEWS[@]}"; do
#     ... (old multi-port logic)
# done

# Save PIDs to file
printf '%s\n' "${PIDS[@]}" > "$PID_FILE"

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}                    ${GREEN}✅ Application Running${NC}                    ${BLUE}║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}📋 Unified Trading Application:${NC}"
echo ""
echo -e "  ${GREEN}Port 1420:${NC} http://localhost:1420"
echo ""
echo -e "${YELLOW}📑 Available Views (hash routing):${NC}"
echo -e "  • ${BLUE}#dashboard${NC}     - Main dashboard with metrics"
echo -e "  • ${BLUE}#chartview${NC}     - Interactive trading chart with Control Deck"
echo -e "  • ${BLUE}#opportunities${NC} - Upcoming trade opportunities"
echo -e "  • ${BLUE}#scanner${NC}       - Market Scanner (Multi-Symbol Command Center)"
echo -e "  • ${BLUE}#analytics${NC}     - Performance analytics and metrics"
echo -e "  • ${BLUE}#prophecy${NC}      - PROPHECY Alert Center (Major Move Predictions)"
echo -e "  • ${BLUE}#risk${NC}          - Risk Management Dashboard"
echo -e "  • ${BLUE}#execution${NC}     - Real-time trade execution monitor"
echo -e "  • ${BLUE}#creative${NC}      - 3D market connections visualization"
echo ""
echo -e "${YELLOW}💡 Tips:${NC}"
echo -e "  • All views are accessible via hash routing (e.g., http://localhost:1420#chartview)"
echo -e "  • Navigation links in the header switch between views"
echo -e "  • Make sure the backend is running on port 8000"
echo -e "  • Run ${BLUE}./launch-all.sh --stop${NC} to stop the server"
echo ""
echo -e "${GREEN}🎉 Ready to use!${NC}"


