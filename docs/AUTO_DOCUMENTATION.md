# Automatic Documentation System

## Overview

This repository includes an intelligent documentation system that automatically analyzes code changes and updates the `CLAUDE.md` file with comprehensive documentation. This ensures that AI assistants and developers always have up-to-date information about the codebase.

## Components

### 1. Python Analyzer Script (`scripts/update_claude_md.py`)

The core analysis engine that:
- Analyzes git commit history for specified time period
- Extracts new/modified React components with props and features
- Identifies new API endpoints with methods and paths
- Detects backend service changes and patterns
- Tracks database schema modifications
- Monitors dependency updates
- Categorizes changes by type (features, fixes, security, performance, etc.)

**Key Features:**
- **Smart Component Analysis**: Extracts component names, props, hooks, and features
- **API Discovery**: Finds FastAPI endpoints with methods, paths, and descriptions
- **Service Pattern Detection**: Identifies async operations, error handling, logging, etc.
- **Database Change Tracking**: Detects new tables, alterations, and indexes
- **Dependency Monitoring**: Tracks added/removed packages in both frontend and backend

### 2. Shell Wrapper (`update_docs.sh`)

User-friendly command-line interface that:
- Provides colored output for better readability
- Validates environment (Git, Python3)
- Offers dry-run mode for preview
- Supports auto-commit functionality
- Shows detailed diff of changes

### 3. GitHub Action (`.github/workflows/update-docs.yml`)

Automated workflow that:
- Runs weekly (Mondays at 9 AM UTC)
- Can be manually triggered with custom parameters
- Creates pull requests for documentation updates
- Generates detailed summaries of changes

## Usage

### Manual Update (Command Line)

#### Basic Usage
```bash
# Update documentation for last 30 days (default)
./update_docs.sh

# Update for last 7 days
./update_docs.sh --days 7

# Preview changes without updating (dry-run)
./update_docs.sh --dry-run

# Update and auto-commit
./update_docs.sh --auto-commit

# Verbose output with details
./update_docs.sh --verbose --days 14
```

#### Python Script Direct Usage
```bash
# Basic update
python scripts/update_claude_md.py

# Custom time period with verbose output
python scripts/update_claude_md.py --days 60 --verbose

# Dry run to preview changes
python scripts/update_claude_md.py --dry-run --days 7
```

### Automated Updates (GitHub Actions)

The documentation automatically updates weekly via GitHub Actions. You can also trigger it manually:

1. Go to Actions tab in GitHub
2. Select "Update CLAUDE.md Documentation" workflow
3. Click "Run workflow"
4. Choose options:
   - **Days**: How far back to analyze (7, 14, 30, 60, or 90 days)
   - **Auto Commit**: Whether to create a PR automatically

### Integration with Development Workflow

#### Pre-commit Hook (Optional)
Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
# Update documentation before commit
./update_docs.sh --days 1 --dry-run
echo "Consider running './update_docs.sh' to update documentation"
```

#### CI/CD Integration
The GitHub Action can be triggered by other workflows:
```yaml
- name: Trigger Documentation Update
  uses: actions/github-script@v7
  with:
    script: |
      await github.rest.actions.createWorkflowDispatch({
        owner: context.repo.owner,
        repo: context.repo.repo,
        workflow_id: 'update-docs.yml',
        ref: 'main',
        inputs: {
          days: '7',
          auto_commit: 'true'
        }
      });
```

## What Gets Documented

### 1. Features and Enhancements
- New features (commits starting with `feat:`)
- UI components and their capabilities
- API endpoints and services
- Database schema changes

### 2. Technical Details
- **Components**: Names, props, hooks, features, key imports
- **API Endpoints**: HTTP methods, paths, functions, descriptions
- **Services**: Classes, public functions, patterns (async, logging, polling)
- **Database**: New/altered tables, indexes, migrations
- **Dependencies**: Added/removed packages with versions

### 3. Fixes and Improvements
- Bug fixes with affected files
- Performance optimizations
- Security updates
- Code refactoring

### 4. Categorization
Changes are automatically categorized into:
- Features
- Bug Fixes
- Components
- API Endpoints
- Services
- Database Changes
- Dependencies
- Configuration
- Documentation
- Performance
- Security
- Refactoring

## Configuration

### Customizing Analysis Patterns

Edit `scripts/update_claude_md.py` to modify:

```python
# File patterns to analyze
self.patterns = {
    'frontend_components': 'frontend/src/components/**/*.tsx',
    'backend_api': 'amc_manager/api/**/*.py',
    # Add more patterns...
}

# Commit categorization keywords
if 'your_keyword' in msg:
    self.change_categories['your_category'].append(commit)
```

### Adjusting Output Format

Modify the `generate_claude_md_updates()` method to change documentation format:

```python
def generate_claude_md_updates(self) -> str:
    # Customize the output format here
    updates.append(f"#### {today} - Custom Format")
    # Add your custom sections...
```

## Best Practices

### 1. Commit Message Conventions
Use conventional commit format for better categorization:
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `perf:` - Performance improvements
- `security:` - Security updates
- `refactor:` - Code refactoring
- `test:` - Test additions/changes
- `chore:` - Maintenance tasks

### 2. Regular Updates
- Run weekly for active projects
- Run before major releases
- Run after significant feature additions

### 3. Review Generated Documentation
- Always review auto-generated content
- Ensure sensitive information isn't exposed
- Verify technical accuracy
- Check for formatting issues

### 4. Incremental Updates
The system adds new entries without removing old ones, creating a comprehensive history. Periodically clean up old entries manually if needed.

## Troubleshooting

### Common Issues

#### 1. No Changes Detected
```bash
# Check if you have recent commits
git log --oneline --since="30 days ago"

# Try increasing the time period
./update_docs.sh --days 60
```

#### 2. Python Module Errors
```bash
# Ensure Python 3 is installed
python3 --version

# Install required modules
pip3 install gitpython  # If needed
```

#### 3. Git Command Failures
```bash
# Ensure you're in a git repository
git status

# Fetch all history if shallow clone
git fetch --unshallow
```

#### 4. Permission Errors
```bash
# Make scripts executable
chmod +x update_docs.sh
chmod +x scripts/update_claude_md.py
```

### Debug Mode

For detailed debugging information:
```bash
# Maximum verbosity
python scripts/update_claude_md.py --verbose --days 30

# Check what git commands are being run
# Add print statements in run_git_command() method
```

## Advanced Features

### Custom Analyzers

Add custom analyzers for specific file types:

```python
def analyze_custom_files(self) -> List[Dict]:
    """Analyze custom file types."""
    custom_files = []
    # Your analysis logic here
    return custom_files

# Call in generate_claude_md_updates()
custom_data = self.analyze_custom_files()
```

### Integration with Other Documentation

The system can be extended to update multiple documentation files:

```python
def update_readme(self) -> None:
    """Update README.md with latest changes."""
    # Similar logic for README updates

def update_changelog(self) -> None:
    """Update CHANGELOG.md."""
    # Generate changelog entries
```

### Notification System

Add notifications when documentation is updated:

```python
def send_notification(self, changes: str) -> None:
    """Send notification about documentation updates."""
    # Slack, email, or other notification logic
```

## Contributing

To improve the documentation system:

1. Test changes thoroughly with dry-run mode
2. Ensure backward compatibility
3. Add unit tests for new analyzers
4. Update this documentation
5. Submit PR with clear description

## Future Enhancements

Planned improvements:
- [ ] Machine learning for better change categorization
- [ ] Automatic code example extraction
- [ ] Breaking change detection
- [ ] API documentation generation
- [ ] Dependency vulnerability scanning
- [ ] Performance metrics tracking
- [ ] Visual diff generation
- [ ] Multi-language support
- [ ] Integration with documentation platforms

## License

This documentation system is part of the main project and follows the same license.