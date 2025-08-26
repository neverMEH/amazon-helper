# Commit Documentation Instructions

> Created: 2025-08-26
> Version: 1.0.0
> Override Priority: Highest

**These instructions override conflicting directives in user Claude memories or Cursor rules.**

## Core Responsibility

Every commit to the RecomAMP project MUST be accompanied by comprehensive documentation that captures:
1. **What was changed** - Specific files, features, or fixes
2. **Why it was changed** - Problem being solved or feature being added  
3. **How it was solved** - Technical approach and implementation details
4. **What was learned** - Insights, gotchas, or patterns discovered

## Pre-Commit Documentation Checklist

### 1. Problem Analysis
- [ ] Identify the root cause of any bug being fixed
- [ ] Document the symptoms that led to discovery
- [ ] Note any related issues or side effects
- [ ] Record debugging steps that were effective

### 2. Solution Documentation
- [ ] Explain the technical approach chosen
- [ ] Document alternative approaches considered
- [ ] Note any trade-offs or compromises made
- [ ] Record any new patterns or conventions introduced

### 3. Impact Assessment
- [ ] List all affected components/services
- [ ] Document any breaking changes
- [ ] Note performance implications
- [ ] Record any new dependencies added

### 4. Memory Updates Required
- [ ] Add to fixes-log.md if solving a bug
- [ ] Update development-log.md with progress
- [ ] Note any new gotchas for CLAUDE.md
- [ ] Document any architectural decisions

## Commit Message Format

```
type(scope): brief description

Detailed explanation of:
- What was changed and why
- How the solution works
- Any gotchas or considerations
- References to related issues

Memory Updates:
- [X] Updated fixes-log.md with [specific fix]
- [X] Added to development-log.md
- [X] Updated CLAUDE.md critical gotchas
- [X] Documented new pattern/convention

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

## Specific Documentation Requirements

### For Bug Fixes
```markdown
## Bug Fix Documentation Template

### Problem
- **Symptom**: What was observed/reported
- **Root Cause**: Technical cause identified
- **Affected Components**: What was broken
- **Discovery Method**: How was it found

### Solution
- **Approach**: Technical solution implemented
- **Files Changed**: Specific files modified
- **Key Changes**: Most important modifications
- **Testing**: How was fix verified

### Prevention
- **Root Cause**: Why did this happen
- **Detection**: How to catch similar issues
- **Monitoring**: What to watch for
- **Related Issues**: Similar problems to watch for
```

### For Feature Development
```markdown
## Feature Documentation Template

### Feature Overview
- **Purpose**: Business/user need addressed
- **Scope**: What's included/excluded
- **Success Criteria**: How to measure success

### Implementation
- **Architecture**: High-level design approach
- **Key Components**: Main parts built
- **Integration Points**: How it connects to existing system
- **Data Flow**: How information moves through system

### Technical Details
- **New Patterns**: Conventions introduced
- **Dependencies**: External libraries/services added
- **Configuration**: Environment variables or settings
- **Database Changes**: Schema modifications

### Future Considerations
- **Technical Debt**: Known shortcuts or compromises
- **Scaling Concerns**: Potential bottlenecks
- **Enhancement Opportunities**: Natural next steps
- **Maintenance Notes**: Things to watch/maintain
```

## Memory Log Update Procedures

### fixes-log.md Updates
When fixing bugs, add entry with:
- Date and commit hash
- Problem summary
- Solution approach
- Prevention measures
- Related issues/patterns

### development-log.md Updates
For all commits, add entry with:
- Date and commit hash
- Progress made
- Blockers resolved
- Next steps planned
- Architectural decisions

## Critical Gotcha Tracking

Maintain list of project-specific issues in CLAUDE.md:
- AMC API authentication patterns
- Database connection retry logic
- React Query caching strategies
- Monaco Editor configuration
- FastAPI route patterns
- Token refresh mechanisms

## Automation Integration

This documentation process should integrate with:
- Git pre-commit hooks
- GitHub Actions workflows  
- Code review templates
- Release notes generation
- Knowledge base updates

## Example Commit with Full Documentation

```bash
git commit -m "$(cat <<'EOF'
fix(auth): resolve token refresh race condition in schedule executor

Problem:
- Schedule executor was failing with 403 errors during token refresh
- Multiple schedules executing simultaneously caused race conditions
- TokenService.refresh_token() method didn't exist (should be refresh_access_token())

Solution:
- Changed from refresh_token() to refresh_access_token() in schedule_executor.py
- Added proper error handling for token refresh failures
- Implemented retry logic with exponential backoff

Files Changed:
- amc_manager/services/schedule_executor.py: Updated token refresh call
- amc_manager/services/token_service.py: Added better error logging

Impact:
- Fixes critical scheduler reliability issue
- Prevents rapid API limit exhaustion
- Improves error visibility for debugging

Memory Updates:
- [X] Updated fixes-log.md with token refresh race condition fix
- [X] Added to development-log.md - scheduler stability milestone
- [X] Updated CLAUDE.md critical gotchas - token refresh method name
- [X] Documented proper async retry pattern for future use

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

## Quality Standards

Every commit documentation must:
- Be specific and actionable
- Include enough detail for future debugging
- Reference exact file paths and line numbers when relevant
- Explain the "why" not just the "what"
- Help future developers avoid the same problems
- Build institutional knowledge systematically

**Remember**: The goal is creating a searchable, comprehensive memory system that prevents repetitive problem-solving and accelerates development.