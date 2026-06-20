#!/bin/bash
# Git Workflow Helper Script
# Makes branch-based development easier

set -e

ACTION="${1:-help}"

case "$ACTION" in
    start)
        # Start new feature branch
        FEATURE_NAME="${2}"
        if [ -z "$FEATURE_NAME" ]; then
            echo "Usage: ./git-helper.sh start feature/port-142X-name"
            exit 1
        fi
        
        echo "🌿 Starting new feature branch..."
        git checkout mvp
        git checkout -b "$FEATURE_NAME"
        echo "✅ Created and switched to: $FEATURE_NAME"
        ;;
    
    commit)
        # Quick commit
        MESSAGE="${2}"
        if [ -z "$MESSAGE" ]; then
            echo "Usage: ./git-helper.sh commit 'Your commit message'"
            exit 1
        fi
        
        echo "📝 Committing changes..."
        git add .
        git commit -m "$MESSAGE"
        echo "✅ Committed: $MESSAGE"
        ;;
    
    merge)
        # Merge current branch to mvp
        CURRENT_BRANCH=$(git branch --show-current)
        if [ "$CURRENT_BRANCH" = "mvp" ] || [ "$CURRENT_BRANCH" = "main" ]; then
            echo "❌ Error: Don't merge from mvp or main!"
            exit 1
        fi
        
        echo "🔄 Merging $CURRENT_BRANCH to mvp..."
        git checkout mvp
        git merge "$CURRENT_BRANCH"
        echo "✅ Merged $CURRENT_BRANCH to mvp"
        echo "💡 Tip: Test on mvp, then merge to main if stable"
        ;;
    
    cleanup)
        # Delete merged branches
        echo "🧹 Cleaning up merged branches..."
        git checkout mvp
        MERGED=$(git branch --merged mvp | grep -v "^\*" | grep -v "mvp" | grep -v "main" | xargs)
        if [ -z "$MERGED" ]; then
            echo "✅ No merged branches to clean up"
        else
            echo "Deleting merged branches:"
            echo "$MERGED"
            echo "$MERGED" | xargs git branch -d
            echo "✅ Cleanup complete"
        fi
        ;;
    
    status)
        # Show current branch and status
        CURRENT_BRANCH=$(git branch --show-current)
        echo "📍 Current branch: $CURRENT_BRANCH"
        echo ""
        echo "📊 Status:"
        git status --short
        echo ""
        echo "🌿 Branches:"
        git branch
        ;;
    
    help|*)
        echo "Git Workflow Helper"
        echo ""
        echo "Usage: ./git-helper.sh <action> [args]"
        echo ""
        echo "Actions:"
        echo "  start <branch-name>    Create and switch to new feature branch"
        echo "  commit <message>      Quick commit (adds all, commits with message)"
        echo "  merge                  Merge current branch to mvp"
        echo "  cleanup                Delete merged branches"
        echo "  status                Show current branch and status"
        echo "  help                  Show this help"
        echo ""
        echo "Examples:"
        echo "  ./git-helper.sh start feature/port-1427-new-view"
        echo "  ./git-helper.sh commit 'Feature: Add new view'"
        echo "  ./git-helper.sh merge"
        echo "  ./git-helper.sh cleanup"
        ;;
esac







