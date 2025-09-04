#!/bin/bash

# Smart commit script that commits, pushes, and updates appropriate CLAUDE.md files
# Usage: ./smart-commit.sh "commit message" [--type=fix|feat|chore|docs|style|refactor|test|build]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Default values
COMMIT_TYPE="fix"
COMMIT_MESSAGE=""
SKIP_CLAUDE_UPDATE=false
AUTO_CONFIRM=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --type=*)
            COMMIT_TYPE="${arg#*=}"
            shift
            ;;
        --skip-claude)
            SKIP_CLAUDE_UPDATE=true
            shift
            ;;
        --auto|-y)
            AUTO_CONFIRM=true
            shift
            ;;
        --help|-h)
            echo "Usage: ./smart-commit.sh \"commit message\" [options]"
            echo ""
            echo "Options:"
            echo "  --type=TYPE       Commit type (fix|feat|chore|docs|style|refactor|test|build)"
            echo "  --skip-claude     Skip updating CLAUDE.md files"
            echo "  --auto, -y        Auto-confirm (skip confirmation prompt)"
            echo "  --help, -h        Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./smart-commit.sh \"Add new feature\""
            echo "  ./smart-commit.sh \"Fix bug in schedule\" --type=fix"
            echo "  ./smart-commit.sh \"Update docs\" --type=docs --skip-claude"
            exit 0
            ;;
        *)
            if [ -z "$COMMIT_MESSAGE" ]; then
                COMMIT_MESSAGE="$arg"
            fi
            ;;
    esac
done

# Check if commit message is provided
if [ -z "$COMMIT_MESSAGE" ]; then
    echo -e "${RED}Error: Please provide a commit message${NC}"
    echo "Usage: ./smart-commit.sh \"commit message\" [--type=fix|feat|chore|docs]"
    exit 1
fi

CURRENT_DATE=$(date +"%Y-%m-%d")
CURRENT_TIME=$(date +"%H:%M:%S")

echo -e "${CYAN}═══════════════════════════════════════════${NC}"
echo -e "${CYAN}   Smart Commit & Update Tool${NC}"
echo -e "${CYAN}═══════════════════════════════════════════${NC}\n"

# 1. Check git status
echo -e "${YELLOW}📋 Checking git status...${NC}"
git status --short

# Check if there are changes to commit
if [ -z "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}No changes to commit${NC}"
    exit 0
fi

# 2. Analyze changed files to determine which CLAUDE.md to update
echo -e "\n${YELLOW}🔍 Analyzing changed files...${NC}"
FRONTEND_CHANGES=false
BACKEND_CHANGES=false
OTHER_CHANGES=false

while IFS= read -r line; do
    file=$(echo "$line" | awk '{print $2}')
    if [[ $file == frontend/* ]]; then
        FRONTEND_CHANGES=true
        echo -e "  ${BLUE}Frontend:${NC} $file"
    elif [[ $file == amc_manager/* ]] || [[ $file == scripts/* ]] || [[ $file == *.py ]]; then
        BACKEND_CHANGES=true
        echo -e "  ${GREEN}Backend:${NC} $file"
    else
        OTHER_CHANGES=true
        echo -e "  ${MAGENTA}Other:${NC} $file"
    fi
done < <(git status --porcelain)

# 3. Show diff summary
echo -e "\n${YELLOW}📊 Change summary:${NC}"
git diff --stat

# 4. Ask for confirmation if not auto-confirm
if [ "$AUTO_CONFIRM" = false ]; then
    echo -e "\n${YELLOW}Continue with commit? (y/n)${NC}"
    read -r response
    if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo -e "${RED}Aborted${NC}"
        exit 1
    fi
fi

# 5. Stage all changes
echo -e "\n${YELLOW}📦 Staging all changes...${NC}"
git add -A

# 6. Get detailed change information
CHANGED_FILES=$(git diff --cached --name-status)
DIFF_STATS=$(git diff --cached --shortstat)

# 7. Update CLAUDE.md files if not skipped
if [ "$SKIP_CLAUDE_UPDATE" = false ]; then
    echo -e "\n${YELLOW}📝 Updating CLAUDE.md files...${NC}"
    
    # Function to update a CLAUDE.md file
    update_claude_md() {
        local claude_file="$1"
        local context="$2"
        
        if [ ! -f "$claude_file" ]; then
            echo -e "  ${YELLOW}⚠ $claude_file not found, skipping${NC}"
            return
        fi
        
        # Create temporary update content
        local temp_update=$(mktemp)
        
        cat > "$temp_update" << EOF

### ${CURRENT_DATE} - ${CURRENT_TIME}
**${COMMIT_TYPE}**: ${COMMIT_MESSAGE}
**Context**: ${context} changes
**Stats**: ${DIFF_STATS}
EOF
        
        # Find and update the Recent Critical Fixes section
        if grep -q "## Recent Critical Fixes" "$claude_file"; then
            # Keep only the last 10 entries in Recent Critical Fixes
            awk '/## Recent Critical Fixes/ {
                print
                print ""
                # Print the new entry
                while ((getline line < "'$temp_update'") > 0) {
                    print line
                }
                close("'$temp_update'")
                # Track how many ### entries we have printed
                count = 0
                in_section = 1
                next
            }
            in_section && /^##[^#]/ {
                in_section = 0
            }
            in_section && /^### / {
                if (count < 10) {
                    count++
                    print
                    # Print until next ### or ##
                    while ((getline) > 0) {
                        if (/^###/ || /^##[^#]/) {
                            # Put the line back for reprocessing
                            if (/^##[^#]/) in_section = 0
                            if (/^###/ && count >= 10) next
                            break
                        }
                        print
                    }
                    if (/^###/ || /^##[^#]/) {
                        # Reprocess this line
                        if (/^##[^#]/) {
                            in_section = 0
                            print
                        } else if (count < 10) {
                            count++
                            print
                        }
                    }
                } else {
                    next
                }
                next
            }
            {print}' "$claude_file" > "${claude_file}.tmp" && mv "${claude_file}.tmp" "$claude_file"
            
            echo -e "  ${GREEN}✓ Updated $claude_file${NC}"
        else
            # Add new section at the end
            echo -e "\n## Recent Critical Fixes" >> "$claude_file"
            cat "$temp_update" >> "$claude_file"
            echo -e "  ${GREEN}✓ Added Recent Critical Fixes section to $claude_file${NC}"
        fi
        
        rm "$temp_update"
        git add "$claude_file"
    }
    
    # Update appropriate CLAUDE.md files based on changes
    if [ "$FRONTEND_CHANGES" = true ]; then
        update_claude_md "/root/amazon-helper/frontend/CLAUDE.md" "Frontend"
    fi
    
    if [ "$BACKEND_CHANGES" = true ] || [ "$OTHER_CHANGES" = true ]; then
        update_claude_md "/root/amazon-helper/CLAUDE.md" "Backend/Project"
    fi
else
    echo -e "\n${YELLOW}⏭ Skipping CLAUDE.md updates${NC}"
fi

# 8. Create the full commit message
echo -e "\n${YELLOW}💾 Committing changes...${NC}"
FULL_COMMIT_MESSAGE="${COMMIT_TYPE}: ${COMMIT_MESSAGE}

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git commit -m "$FULL_COMMIT_MESSAGE"

# 9. Push to remote
echo -e "\n${YELLOW}🚀 Pushing to remote repository...${NC}"
git push origin main

# 10. Show success summary
echo -e "\n${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Successfully completed!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Type: ${COMMIT_TYPE}${NC}"
echo -e "${GREEN}✓ Message: ${COMMIT_MESSAGE}${NC}"
if [ "$SKIP_CLAUDE_UPDATE" = false ]; then
    [ "$FRONTEND_CHANGES" = true ] && echo -e "${GREEN}✓ Updated frontend/CLAUDE.md${NC}"
    [ "$BACKEND_CHANGES" = true ] || [ "$OTHER_CHANGES" = true ] && echo -e "${GREEN}✓ Updated CLAUDE.md${NC}"
fi
echo -e "${GREEN}✓ Pushed to origin/main${NC}"

# Show the latest commit
echo -e "\n${BLUE}📌 Latest commit:${NC}"
git log --oneline --color=always -1

# Show quick stats
echo -e "\n${BLUE}📈 Quick stats:${NC}"
echo "  $DIFF_STATS"