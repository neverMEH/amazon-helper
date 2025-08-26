# Git Helper Scripts

This project includes several helper scripts, git aliases, and slash commands to streamline the commit and push workflow while maintaining proper documentation.

## Available Scripts

### 1. `smart-commit.sh` (Recommended)
The most feature-rich commit helper that automatically:
- Commits changes with proper formatting
- Updates relevant CLAUDE.md files based on what changed
- Pushes to remote repository
- Adds Claude attribution

**Usage:**
```bash
./smart-commit.sh "Your commit message"
./smart-commit.sh "Fix authentication bug" --type=fix
./smart-commit.sh "Add new feature" --type=feat --auto
```

**Options:**
- `--type=TYPE` - Specify commit type (fix|feat|chore|docs|style|refactor|test|build)
- `--skip-claude` - Skip updating CLAUDE.md files
- `--auto` or `-y` - Auto-confirm (skip confirmation prompt)

### 2. `commit-and-update.sh`
Basic script that commits, pushes, and updates the main CLAUDE.md file.

**Usage:**
```bash
./commit-and-update.sh "Your commit message"
```

### 3. Git Aliases
Quick git commands for common operations. Run `./setup-git-aliases.sh` once to install.

**Available aliases:**
- `git smart-commit "message"` - Commit and push with Claude attribution
- `git qfix "message"` - Quick fix commit and push
- `git qfeat "message"` - Quick feature commit and push
- `git scommit "message"` - Show status, confirm, then commit and push

**Examples:**
```bash
git qfix "Handle null values in schedule"
git qfeat "Add export functionality"
git scommit "Refactor authentication flow"
```

## Slash Commands (NEW!)

Claude Code slash commands for git operations. These work directly in your Claude Code session.

**Available slash commands:**
- `/commit [message]` - Smart commit with CLAUDE.md update and push
- `/qfix [description]` - Quick fix commit with "fix:" prefix
- `/qfeat [description]` - Quick feature commit with "feat:" prefix
- `/smart-commit [message] [options]` - Run smart-commit.sh with full options
- `/status-commit [message]` - Show detailed status before committing
- `/push` - Push current commits to origin/main
- `/git-help` - Show all available git slash commands

**Examples in Claude Code:**
```
/commit "Update authentication logic"
/qfix "Handle null values"
/qfeat "Add new dashboard"
/smart-commit "Refactor code" --type=refactor --auto
```

## Setup

1. Make scripts executable (already done):
```bash
chmod +x smart-commit.sh commit-and-update.sh setup-git-aliases.sh
```

2. Install git aliases (optional):
```bash
./setup-git-aliases.sh
```

3. Slash commands are automatically available in `.claude/commands/`

## Features

### Smart Change Detection
`smart-commit.sh` automatically detects whether changes are in:
- Frontend code → Updates `frontend/CLAUDE.md`
- Backend code → Updates main `CLAUDE.md`
- Both → Updates both files

### Automatic Claude Attribution
All scripts automatically add Claude co-authorship to commits:
```
🤖 Generated with [Claude Code](https://claude.ai/code)
Co-Authored-By: Claude <noreply@anthropic.com>
```

### CLAUDE.md Updates
Scripts maintain a "Recent Critical Fixes" section in CLAUDE.md files with:
- Date and time of change
- Commit type and message
- Files changed statistics
- Keeps only the last 10 entries to prevent file bloat

## Best Practices

1. **Use descriptive commit messages** - They'll be added to documentation
2. **Specify commit type** - Helps with changelog generation
3. **Review changes before confirming** - Scripts show diff before committing
4. **Use appropriate script** - `smart-commit.sh` for complex changes, aliases for quick fixes

## Troubleshooting

If you get "command not found" errors:
```bash
# Use bash directly
bash smart-commit.sh "message"

# Or make sure scripts are executable
chmod +x *.sh
```

If line ending issues occur (Windows/Unix):
```bash
dos2unix *.sh
# or
sed -i 's/\r$//' *.sh
```