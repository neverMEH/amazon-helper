#!/bin/bash

# Script to set up useful git aliases for the project
# Run this once to add the aliases to your git config

echo "Setting up git aliases for smart commits..."

# Smart commit alias - commits with Claude attribution
git config alias.smart-commit '!f() { 
    if [ -z "$1" ]; then 
        echo "Error: Please provide a commit message"; 
        return 1; 
    fi; 
    git add -A && 
    git commit -m "$1

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>" && 
    git push origin main; 
}; f'

# Quick fix alias - for quick fixes
git config alias.qfix '!f() { 
    if [ -z "$1" ]; then 
        echo "Error: Please provide a commit message"; 
        return 1; 
    fi; 
    git add -A && 
    git commit -m "fix: $1

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>" && 
    git push origin main; 
}; f'

# Quick feature alias - for new features
git config alias.qfeat '!f() { 
    if [ -z "$1" ]; then 
        echo "Error: Please provide a commit message"; 
        return 1; 
    fi; 
    git add -A && 
    git commit -m "feat: $1

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>" && 
    git push origin main; 
}; f'

# Status and commit alias - shows status first, then commits
git config alias.scommit '!f() { 
    if [ -z "$1" ]; then 
        echo "Error: Please provide a commit message"; 
        return 1; 
    fi; 
    echo "Changes to be committed:"; 
    git status --short; 
    echo ""; 
    read -p "Continue? (y/n) " -n 1 -r; 
    echo ""; 
    if [[ $REPLY =~ ^[Yy]$ ]]; then 
        git add -A && 
        git commit -m "$1

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>" && 
        git push origin main; 
    fi; 
}; f'

echo "✅ Git aliases have been set up successfully!"
echo ""
echo "Available commands:"
echo "  git smart-commit \"message\"  - Commit and push with Claude attribution"
echo "  git qfix \"message\"         - Quick fix commit and push"
echo "  git qfeat \"message\"        - Quick feature commit and push"  
echo "  git scommit \"message\"      - Show status, confirm, then commit and push"
echo ""
echo "Examples:"
echo "  git smart-commit \"Update schedule configuration\""
echo "  git qfix \"Handle null values in schedule\""
echo "  git qfeat \"Add export functionality\""
echo "  git scommit \"Refactor authentication flow\""