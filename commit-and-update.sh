#!/bin/bash

# Script to commit changes, push to repository, and update CLAUDE.md with recent changes
# Usage: ./commit-and-update.sh "commit message"

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if commit message is provided
if [ $# -eq 0 ]; then
    echo -e "${RED}Error: Please provide a commit message${NC}"
    echo "Usage: ./commit-and-update.sh \"commit message\""
    exit 1
fi

COMMIT_MESSAGE="$1"
CURRENT_DATE=$(date +"%Y-%m-%d")

echo -e "${BLUE}Starting commit and update process...${NC}\n"

# 1. Check git status
echo -e "${YELLOW}1. Checking git status...${NC}"
git status --short

# Check if there are changes to commit
if [ -z "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}No changes to commit${NC}"
    exit 0
fi

# 2. Show diff
echo -e "\n${YELLOW}2. Changes to be committed:${NC}"
git diff --stat

# 3. Ask for confirmation
echo -e "\n${YELLOW}Do you want to continue? (y/n)${NC}"
read -r response
if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo -e "${RED}Aborted${NC}"
    exit 1
fi

# 4. Stage all changes
echo -e "\n${YELLOW}3. Staging all changes...${NC}"
git add -A

# 5. Get list of modified files and changes summary
echo -e "\n${YELLOW}4. Generating change summary...${NC}"
CHANGED_FILES=$(git diff --cached --name-status)
DIFF_SUMMARY=$(git diff --cached --stat)

# 6. Update CLAUDE.md with recent changes
echo -e "\n${YELLOW}5. Updating CLAUDE.md...${NC}"

# Create a temporary file for the update
TEMP_UPDATE=$(mktemp)

# Generate the update entry
cat > "$TEMP_UPDATE" << EOF

### ${CURRENT_DATE}
**Commit**: ${COMMIT_MESSAGE}

**Files Changed**:
\`\`\`
${CHANGED_FILES}
\`\`\`

**Summary**:
${COMMIT_MESSAGE}

EOF

# Check if CLAUDE.md exists
CLAUDE_FILE="/root/amazon-helper/CLAUDE.md"
if [ ! -f "$CLAUDE_FILE" ]; then
    echo -e "${RED}CLAUDE.md not found at $CLAUDE_FILE${NC}"
    rm "$TEMP_UPDATE"
    exit 1
fi

# Find the line with "## Recent Critical Fixes" or create section if it doesn't exist
if grep -q "## Recent Critical Fixes" "$CLAUDE_FILE"; then
    # Insert the new entry after the "## Recent Critical Fixes" line
    awk '/## Recent Critical Fixes/ {
        print
        print ""
        while ((getline line < "'$TEMP_UPDATE'") > 0) {
            print line
        }
        close("'$TEMP_UPDATE'")
        next
    }
    {print}' "$CLAUDE_FILE" > "${CLAUDE_FILE}.tmp" && mv "${CLAUDE_FILE}.tmp" "$CLAUDE_FILE"
    echo -e "${GREEN}✓ Updated existing 'Recent Critical Fixes' section${NC}"
else
    # Add the section before the last closing section or at the end
    echo -e "\n## Recent Critical Fixes" >> "$CLAUDE_FILE"
    cat "$TEMP_UPDATE" >> "$CLAUDE_FILE"
    echo -e "${GREEN}✓ Created new 'Recent Critical Fixes' section${NC}"
fi

# Clean up temp file
rm "$TEMP_UPDATE"

# Stage the CLAUDE.md update
git add "$CLAUDE_FILE"

# 7. Commit with full message including Claude attribution
echo -e "\n${YELLOW}6. Committing changes...${NC}"
FULL_COMMIT_MESSAGE="${COMMIT_MESSAGE}

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git commit -m "$FULL_COMMIT_MESSAGE"

# 8. Push to origin
echo -e "\n${YELLOW}7. Pushing to remote repository...${NC}"
git push origin main

# 9. Show final status
echo -e "\n${GREEN}✅ Successfully completed!${NC}"
echo -e "${GREEN}✓ Changes committed with message: ${COMMIT_MESSAGE}${NC}"
echo -e "${GREEN}✓ CLAUDE.md updated with recent changes${NC}"
echo -e "${GREEN}✓ Pushed to origin/main${NC}"

# Show the latest commit
echo -e "\n${BLUE}Latest commit:${NC}"
git log --oneline -1