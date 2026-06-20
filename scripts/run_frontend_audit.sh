#!/bin/bash
# Unified wrapper script for frontend live audit
# Supports both Playwright and Pyppeteer

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default behavior
TOOL="auto"  # auto, playwright, pyppeteer, both
INSTALL_DEPS=false
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --tool)
            TOOL="$2"
            shift 2
            ;;
        --install-deps)
            INSTALL_DEPS=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --tool TOOL        Tool to use: auto, playwright, pyppeteer, or both (default: auto)"
            echo "  --install-deps      Automatically install missing dependencies"
            echo "  --verbose, -v       Verbose output"
            echo "  --help, -h          Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                          # Auto-detect and use available tool"
            echo "  $0 --tool playwright       # Use Playwright only"
            echo "  $0 --tool both             # Run both tools and compare"
            echo "  $0 --install-deps          # Install missing dependencies automatically"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check Python version
check_python() {
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}ERROR: python3 is not installed${NC}"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        echo -e "${RED}ERROR: Python 3.8+ is required (found $PYTHON_VERSION)${NC}"
        exit 1
    fi
    
    if [ "$VERBOSE" = true ]; then
        echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"
    fi
}

# Check if tool is available
check_tool() {
    local tool=$1
    case $tool in
        playwright)
            python3 -c "import playwright" 2>/dev/null && return 0 || return 1
            ;;
        pyppeteer)
            python3 -c "import pyppeteer" 2>/dev/null && return 0 || return 1
            ;;
        *)
            return 1
            ;;
    esac
}

# Install tool
install_tool() {
    local tool=$1
    echo -e "${YELLOW}Installing $tool...${NC}"
    
    case $tool in
        playwright)
            pip3 install playwright
            python3 -m playwright install chromium
            echo -e "${GREEN}✓${NC} Playwright installed"
            ;;
        pyppeteer)
            pip3 install pyppeteer
            echo -e "${GREEN}✓${NC} Pyppeteer installed (Chromium will be auto-downloaded on first run)"
            ;;
    esac
}

# Run audit with specific tool
run_audit() {
    local tool=$1
    local script=""
    
    case $tool in
        playwright)
            script="$SCRIPT_DIR/frontend_live_audit_playwright.py"
            ;;
        pyppeteer)
            script="$SCRIPT_DIR/frontend_live_audit_pyppeteer.py"
            ;;
        *)
            echo -e "${RED}ERROR: Unknown tool: $tool${NC}"
            return 1
            ;;
    esac
    
    if [ ! -f "$script" ]; then
        echo -e "${RED}ERROR: Script not found: $script${NC}"
        return 1
    fi
    
    echo -e "${BLUE}Running audit with $tool...${NC}"
    python3 "$script"
    return $?
}

# Main execution
main() {
    echo -e "${BLUE}=== Frontend Live Audit Wrapper ===${NC}"
    echo ""
    
    check_python
    
    # Detect available tools
    PLAYWRIGHT_AVAILABLE=false
    PYPPETEER_AVAILABLE=false
    
    if check_tool playwright; then
        PLAYWRIGHT_AVAILABLE=true
        if [ "$VERBOSE" = true ]; then
            echo -e "${GREEN}✓${NC} Playwright is available"
        fi
    else
        if [ "$VERBOSE" = true ]; then
            echo -e "${YELLOW}⚠${NC} Playwright is not installed"
        fi
    fi
    
    if check_tool pyppeteer; then
        PYPPETEER_AVAILABLE=true
        if [ "$VERBOSE" = true ]; then
            echo -e "${GREEN}✓${NC} Pyppeteer is available"
        fi
    else
        if [ "$VERBOSE" = true ]; then
            echo -e "${YELLOW}⚠${NC} Pyppeteer is not installed"
        fi
    fi
    
    # Determine which tool(s) to use
    if [ "$TOOL" = "auto" ]; then
        if [ "$PLAYWRIGHT_AVAILABLE" = true ]; then
            TOOL="playwright"
        elif [ "$PYPPETEER_AVAILABLE" = true ]; then
            TOOL="pyppeteer"
        else
            echo -e "${RED}ERROR: No audit tools available${NC}"
            echo ""
            echo "Install one of the following:"
            echo "  - Playwright: pip3 install playwright && playwright install chromium"
            echo "  - Pyppeteer: pip3 install pyppeteer"
            echo ""
            if [ "$INSTALL_DEPS" = true ]; then
                echo -e "${YELLOW}Auto-installing Playwright...${NC}"
                install_tool playwright
                TOOL="playwright"
            else
                echo "Or run with --install-deps to auto-install"
                exit 1
            fi
        fi
    fi
    
    # Handle tool installation if needed
    if [ "$TOOL" = "playwright" ] && [ "$PLAYWRIGHT_AVAILABLE" = false ]; then
        if [ "$INSTALL_DEPS" = true ]; then
            install_tool playwright
        else
            echo -e "${RED}ERROR: Playwright is not installed${NC}"
            echo "Install with: pip3 install playwright && playwright install chromium"
            echo "Or run with --install-deps"
            exit 1
        fi
    fi
    
    if [ "$TOOL" = "pyppeteer" ] && [ "$PYPPETEER_AVAILABLE" = false ]; then
        if [ "$INSTALL_DEPS" = true ]; then
            install_tool pyppeteer
        else
            echo -e "${RED}ERROR: Pyppeteer is not installed${NC}"
            echo "Install with: pip3 install pyppeteer"
            echo "Or run with --install-deps"
            exit 1
        fi
    fi
    
    # Run audit(s)
    if [ "$TOOL" = "both" ]; then
        echo ""
        echo -e "${BLUE}=== Running Playwright Audit ===${NC}"
        if [ "$PLAYWRIGHT_AVAILABLE" = false ] && [ "$INSTALL_DEPS" = true ]; then
            install_tool playwright
        fi
        if check_tool playwright; then
            run_audit playwright
            PLAYWRIGHT_EXIT=$?
        else
            echo -e "${RED}ERROR: Playwright not available${NC}"
            PLAYWRIGHT_EXIT=1
        fi
        
        echo ""
        echo -e "${BLUE}=== Running Pyppeteer Audit ===${NC}"
        if [ "$PYPPETEER_AVAILABLE" = false ] && [ "$INSTALL_DEPS" = true ]; then
            install_tool pyppeteer
        fi
        if check_tool pyppeteer; then
            run_audit pyppeteer
            PYPPETEER_EXIT=$?
        else
            echo -e "${RED}ERROR: Pyppeteer not available${NC}"
            PYPPETEER_EXIT=1
        fi
        
        echo ""
        echo -e "${BLUE}=== Summary ===${NC}"
        if [ $PLAYWRIGHT_EXIT -eq 0 ]; then
            echo -e "${GREEN}✓${NC} Playwright audit completed successfully"
        else
            echo -e "${RED}✗${NC} Playwright audit failed"
        fi
        if [ $PYPPETEER_EXIT -eq 0 ]; then
            echo -e "${GREEN}✓${NC} Pyppeteer audit completed successfully"
        else
            echo -e "${RED}✗${NC} Pyppeteer audit failed"
        fi
        
        if [ $PLAYWRIGHT_EXIT -eq 0 ] && [ $PYPPETEER_EXIT -eq 0 ]; then
            echo ""
            echo -e "${GREEN}Both audits completed successfully!${NC}"
            echo "Compare reports:"
            echo "  - frontend_live_audit_playwright_report.json"
            echo "  - frontend_live_audit_pyppeteer_report.json"
            exit 0
        else
            exit 1
        fi
    else
        # Run single tool
        run_audit "$TOOL"
        exit $?
    fi
}

main "$@"




