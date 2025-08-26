# Agent OS Documentation - RecomAMP Project

> Last Updated: 2025-08-26
> Version: 1.0.0

## Overview

This Agent OS system maintains automated documentation and institutional memory for the RecomAMP project. It tracks development progress, fixes, and commits to ensure AI agents have continuous context of what has been built and solved.

## Directory Structure

```
.agent-os/
├── README.md                          # This file - main documentation
├── instructions/                      # Agent instructions and guidelines
│   └── commit-documentation.md        # Commit documentation workflow
├── memory/                           # Persistent memory logs
│   ├── fixes-log.md                 # Solved problems and fixes
│   └── development-log.md           # Ongoing development tracking
└── workflows/                       # Standard workflows
    └── git-commit.md               # Git commit with documentation workflow
```

## Purpose

**Memory Persistence**: Ensures agents don't lose track of:
- Previously solved problems and their solutions
- Development milestones and decisions
- Bug fixes and their root causes
- Performance optimizations and their impact

**Documentation Automation**: Automatically captures:
- Commit summaries with context
- Problem-solution pairs
- Development progress
- Technical decisions and rationale

## Project Context: RecomAMP

**RecomAMP** is an Amazon Marketing Cloud (AMC) platform featuring:
- Multi-instance AMC management
- SQL query builder with visual editor
- Workflow scheduling and automation
- Query library with templates
- Execution history and error tracking
- Build Guides for tactical AMC guidance

**Tech Stack**: FastAPI + React 19 + Supabase + Python 3.11

## Key Memory Categories

### 1. Critical Fixes Log
- Token encryption/decryption issues
- AMC API authentication failures
- Database connection problems
- Schedule execution bugs
- Monaco Editor integration issues

### 2. Development Milestones
- Feature completions
- Architecture changes
- Performance improvements
- New integrations
- Breaking changes

### 3. Technical Decisions
- Why specific technologies were chosen
- Architecture patterns adopted
- Performance optimizations implemented
- Security measures added

## Agent Responsibilities

### Before Commits
1. Document what was changed and why
2. Record any problems solved
3. Note any new patterns or conventions
4. Update relevant memory logs

### After Commits
1. Update development log with progress
2. Add to fixes log if bugs were resolved
3. Note any technical debt created/resolved
4. Document any new dependencies or changes

## Memory Maintenance

- **Daily**: Update development log with progress
- **Weekly**: Review and organize memory logs
- **Monthly**: Archive completed features and major fixes
- **Per Release**: Comprehensive documentation update

## Usage Guidelines

1. **Always check memory logs** before starting work on similar problems
2. **Update logs immediately** after solving complex issues
3. **Reference previous solutions** when encountering known problems
4. **Cross-reference** related fixes and improvements
5. **Maintain chronological order** in all logs

## Integration with Development

This Agent OS system integrates with:
- Git commit workflow
- Issue tracking
- Code review process
- Release documentation
- Knowledge sharing

The goal is seamless documentation that captures institutional knowledge without disrupting development flow.