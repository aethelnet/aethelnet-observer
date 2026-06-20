#!/bin/bash
# Safe cleanup script for backup directories
# Removes: venv, __pycache__, build artifacts, node_modules, .git (if you want)
# Keeps: source code, configs, important data

BACKUP_DIR="${1:-$HOME/Projects/Backup}"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Backup directory not found: $BACKUP_DIR"
    exit 1
fi

echo "🧹 Cleaning up backups in: $BACKUP_DIR"
echo "This will remove: venv, __pycache__, build artifacts, node_modules"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

TOTAL_FREED=0

# Function to clean a directory
clean_dir() {
    local dir="$1"
    local size_before=$(du -sb "$dir" 2>/dev/null | cut -f1)
    
    echo "Cleaning: $dir"
    
    # Remove Python virtual environments
    find "$dir" -type d -name "venv" -prune -exec rm -rf {} + 2>/dev/null
    
    # Remove Python cache
    find "$dir" -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null
    find "$dir" -type f -name "*.pyc" -delete 2>/dev/null
    find "$dir" -type f -name "*.pyo" -delete 2>/dev/null
    
    # Remove build artifacts (Rust/Cargo)
    find "$dir" -type d -name "target" -path "*/src-tauri/target/*" -prune -exec rm -rf {} + 2>/dev/null
    
    # Remove node_modules
    find "$dir" -type d -name "node_modules" -prune -exec rm -rf {} + 2>/dev/null
    
    # Remove compiled binaries (keep source)
    find "$dir" -type f -name "*.so" -delete 2>/dev/null
    find "$dir" -type f -name "*.dylib" -delete 2>/dev/null
    find "$dir" -type f -name "*.dll" -delete 2>/dev/null
    
    # Remove large database files (optional - be careful!)
    # Uncomment if you want to remove market_data.db from backups:
    # find "$dir" -type f -name "market_data.db" -delete 2>/dev/null
    
    local size_after=$(du -sb "$dir" 2>/dev/null | cut -f1)
    local freed=$((size_before - size_after))
    TOTAL_FREED=$((TOTAL_FREED + freed))
    
    if [ $freed -gt 0 ]; then
        echo "  ✅ Freed: $(numfmt --to=iec-i --suffix=B $freed)"
    fi
}

# Clean each auratic backup
for backup in "$BACKUP_DIR"/auratic-systems-prime*; do
    if [ -d "$backup" ]; then
        clean_dir "$backup"
    fi
done

echo ""
echo "🎉 Total freed: $(numfmt --to=iec-i --suffix=B $TOTAL_FREED)"
echo "✅ Cleanup complete!"







