# Git Commit Workflow with Documentation

> Created: 2025-08-26
> Version: 1.0.0

This workflow ensures every commit to the RecomAMP project includes comprehensive documentation and memory updates for continuous institutional knowledge building.

## Pre-Commit Workflow

### Step 1: Code Review and Testing
```bash
# Ensure all changes are tested
npm run typecheck                    # Frontend type checking
pytest tests/ -v                     # Backend tests  
npm run lint                        # Code style validation

# Review changes
git status                          # See all modified files
git diff                           # Review specific changes
```

### Step 2: Documentation Analysis
Before committing, analyze your changes:

#### For Bug Fixes:
- [ ] What was the exact problem/symptom?
- [ ] What was the root cause discovered?
- [ ] How was the problem debugged/diagnosed?
- [ ] What is the technical solution implemented?
- [ ] How can this problem be prevented in the future?
- [ ] Are there related issues that might occur?

#### For Features:
- [ ] What user/business need does this address?
- [ ] What is the high-level technical approach?
- [ ] What are the key components/files involved?
- [ ] What patterns or conventions were established?
- [ ] What technical debt was created/resolved?
- [ ] What are the future enhancement opportunities?

#### For Refactoring:
- [ ] Why was the refactoring necessary?
- [ ] What was the previous approach and its limitations?
- [ ] How does the new approach improve the codebase?
- [ ] What risks were mitigated by this change?
- [ ] How does this affect other parts of the system?

### Step 3: Memory Log Updates
Update the appropriate memory logs BEFORE committing:

#### fixes-log.md Updates
```bash
# Open fixes log
nano .agent-os/memory/fixes-log.md

# Add entry following this template:
#### Fix ID: [CATEGORY-###]
**Date**: 2025-08-26
**Commit**: [will add hash after commit]
**Problem**: [Brief problem description]
**Symptoms**: [What users/developers experienced]
**Root Cause**: [Technical root cause discovered]
**Solution**: [Technical solution implemented]
**Files**: [Specific files modified]
**Pattern**: [Reusable pattern for future]
**Prevention**: [How to prevent similar issues]
```

#### development-log.md Updates
```bash
# Open development log
nano .agent-os/memory/development-log.md

# Update "Last Updated" date
# Add progress entry in appropriate section
# Update current status if milestone reached
# Note any architectural decisions made
```

## Commit Creation Workflow

### Step 4: Stage Changes
```bash
# Stage specific files (preferred)
git add path/to/specific/file.py
git add frontend/src/components/NewComponent.tsx

# Or stage all changes if appropriate
git add .

# Review staged changes
git diff --cached
```

### Step 5: Create Comprehensive Commit
```bash
git commit -m "$(cat <<'EOF'
type(scope): brief description of change

## Problem/Context
[Detailed explanation of what problem was being solved or feature being added]

## Solution  
[Explanation of the technical approach taken]

## Changes Made
- [Specific file/component changes]
- [Database schema modifications if any]
- [API endpoint changes if any]
- [Frontend component updates if any]

## Impact
- [Effect on users/system performance]
- [Breaking changes if any]
- [Dependencies added/removed]

## Testing
- [How was the change tested]
- [Edge cases considered]
- [Regression testing performed]

## Memory Updates
- [X] Updated fixes-log.md with [specific entry]
- [X] Updated development-log.md progress
- [X] Added to CLAUDE.md critical gotchas (if applicable)
- [X] Documented new patterns/conventions (if applicable)

## References
- Fixes #[issue-number] (if applicable)
- Related to [other-commit-hash] (if applicable)
- Addresses technical debt in [component]

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

### Step 6: Post-Commit Memory Updates
```bash
# Get the commit hash
COMMIT_HASH=$(git rev-parse HEAD)

# Update fixes-log.md with the actual commit hash
sed -i "s/**Commit**: \[will add hash after commit\]/**Commit**: \`$COMMIT_HASH\`/" .agent-os/memory/fixes-log.md

# Commit the memory updates
git add .agent-os/memory/
git commit -m "docs: update memory logs with commit $COMMIT_HASH documentation

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

## Commit Type Standards

Use conventional commit format:

### Primary Types
- **feat**: New feature for users
- **fix**: Bug fix for users  
- **docs**: Documentation changes
- **style**: Code style changes (formatting, semicolons, etc.)
- **refactor**: Code refactoring without feature/fix changes
- **perf**: Performance improvement
- **test**: Adding or updating tests
- **build**: Build system changes
- **ci**: CI/CD pipeline changes
- **chore**: Maintenance tasks

### Scope Examples
- **auth**: Authentication/authorization
- **api**: API endpoints
- **ui**: User interface components
- **db**: Database changes
- **schedule**: Scheduling system
- **workflow**: Workflow execution
- **guide**: Build guides feature
- **query**: Query building/execution

## Quality Checklist

Before finalizing commit:
- [ ] Commit message explains the "why" not just the "what"
- [ ] All affected files are included in staging
- [ ] No sensitive information (API keys, passwords) in commit
- [ ] Code follows established patterns and conventions
- [ ] Breaking changes are clearly documented
- [ ] Memory logs are updated with relevant information
- [ ] Related issues are referenced appropriately

## Push and Documentation Workflow

### Step 7: Push with Documentation
```bash
# Push to remote
git push origin [branch-name]

# If pushing to main, also update project documentation
git checkout main
git pull origin main

# Update CLAUDE.md if new critical patterns discovered
# Update README.md if major features added
# Update API documentation if endpoints changed

# Create documentation commit if needed
git add CLAUDE.md README.md [other-docs]
git commit -m "docs: update project documentation after [feature/fix]

Updated documentation to reflect:
- [New patterns or gotchas discovered]
- [API changes or new endpoints]
- [Critical fixes that affect future development]

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main
```

## Automation Opportunities

### Git Hooks
Consider implementing:
- **pre-commit**: Run tests, linting, type checking
- **prepare-commit-msg**: Template commit message with context
- **post-commit**: Automatic memory log updates

### GitHub Actions
Workflow triggers:
- **On push**: Update documentation, run full test suite
- **On PR**: Generate change summary, validate memory updates
- **Weekly**: Archive completed fixes, update project metrics

## Memory Integration Checklist

For every commit, ensure:
- [ ] Problem/solution is documented for future reference
- [ ] New patterns are captured in appropriate memory logs
- [ ] Related issues are cross-referenced for context
- [ ] Prevention strategies are documented
- [ ] Technical decisions are explained with rationale
- [ ] Impact on system architecture is noted
- [ ] Future considerations are recorded

## Example Complete Workflow

```bash
# 1. Make changes and test
npm run typecheck && pytest tests/ -v

# 2. Review changes
git status && git diff

# 3. Update memory logs
nano .agent-os/memory/fixes-log.md    # Add fix entry
nano .agent-os/memory/development-log.md  # Update progress

# 4. Stage and commit
git add src/components/NewFeature.tsx .agent-os/memory/
git commit -m "$(cat <<'EOF'
feat(ui): add advanced query filtering component

## Problem/Context
Users needed ability to filter query results by multiple criteria
simultaneously. Previous filtering was limited to single column.

## Solution
Implemented FilterPanel component with:
- Multi-column filter support
- Date range filtering  
- Text search with debouncing
- Filter state persistence in URL params

## Changes Made
- src/components/FilterPanel.tsx: New filtering component
- src/hooks/useQueryFilters.ts: Filter state management
- src/utils/filterUtils.ts: Filter logic utilities
- Updated QueryResults.tsx to integrate new filtering

## Impact
- Improved user query analysis workflow
- Better performance with debounced search
- Enhanced user experience with persistent filter state

## Testing
- Unit tests for filter logic
- E2E tests for user workflow
- Performance testing with large datasets

## Memory Updates
- [X] Updated development-log.md with filtering milestone
- [X] Added reusable filter pattern for future components
- [X] Documented URL state management pattern

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# 5. Update commit hash in memory logs
COMMIT_HASH=$(git rev-parse HEAD)
sed -i "s/**Commit**: \[will add hash after commit\]/**Commit**: \`$COMMIT_HASH\`/" .agent-os/memory/fixes-log.md

# 6. Commit memory updates  
git add .agent-os/memory/
git commit -m "docs: update memory logs with commit $COMMIT_HASH documentation"

# 7. Push with documentation
git push origin feature/advanced-filtering
```

## Continuous Improvement

This workflow should evolve based on:
- Team feedback and adoption
- Automation opportunities discovered  
- Documentation quality metrics
- Development velocity impact
- Knowledge retention effectiveness

**Goal**: Make comprehensive documentation a natural, efficient part of the development process that accelerates future development rather than slowing it down.