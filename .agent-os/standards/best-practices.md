# Development Best Practices

## Context

Development guidelines for the RecomAMP project (FastAPI + React/TypeScript).

<conditional-block context-check="core-principles">
IF this Core Principles section already read in current context:
  SKIP: Re-reading this section
  NOTE: "Using Core Principles already in context"
ELSE:
  READ: The following principles

## Core Principles

### Keep It Simple
- Implement code in the fewest lines possible while maintaining clarity
- Avoid over-engineering solutions
- Choose straightforward approaches over clever ones
- Follow YAGNI (You Aren't Gonna Need It) - don't build for hypothetical future needs

### Optimize for Readability
- Prioritize code clarity over micro-optimizations
- Write self-documenting code with clear variable names
- Add comments for "why" not "what"
- Use TypeScript types to make code intent clear
- Extract complex logic into well-named functions

### DRY (Don't Repeat Yourself)
- Extract repeated business logic to utility functions or services
- Extract repeated UI markup to reusable components
- Create shared types/interfaces for common data structures
- Use composition over duplication

### File Structure
- Keep files focused on a single responsibility
- Group related functionality together
- Use consistent naming conventions
- Organize imports by category
- Keep component files under 400 lines (extract sub-components if larger)
</conditional-block>

## Project-Specific Best Practices

### Backend (Python/FastAPI)

#### Service Layer Pattern
```python
# ALL services inherit from DatabaseService
from amc_manager.services.database_service import DatabaseService

class MyService(DatabaseService):
    def __init__(self):
        super().__init__()

    @with_connection_retry
    async def my_method(self):
        # Database operations auto-retry on disconnect
        pass
```

#### Error Handling
- Use try-except blocks for database operations
- Log errors with proper context
- Return appropriate HTTP status codes
- Use FastAPI's HTTPException for API errors

#### Async/Await
- Always await async methods
- Use async for I/O operations (DB, HTTP)
- Supabase client is synchronous (no await)

### Frontend (React/TypeScript)

#### Component Organization
- One component per file
- Use functional components (no class components)
- Keep useState/useEffect at top of component
- Define interfaces before component
- Export component as default

#### State Management
- Use TanStack Query for server state
- Use useState for local component state
- Avoid prop drilling (use React Context or lift state up)
- Keep query keys consistent: `['resource', id]`

#### Type Safety
- Use TypeScript strict mode
- Define interfaces for all props
- Use type-only imports (`import type`)
- Avoid `any` type (use `unknown` if necessary)
- Add explicit return types to functions

#### Performance
- Use useMemo for expensive computations
- Use useCallback for memoized callbacks
- Avoid inline function definitions in render loops
- Use React.memo for expensive components

### Database Operations

#### Instance ID Resolution
```python
# CRITICAL: Always join amc_accounts when fetching instances
instance = db.table('amc_instances')\
    .select('*, amc_accounts(*)')\
    .eq('instance_id', instance_id)\
    .execute()

# entity_id comes from amc_accounts.account_id
entity_id = instance['amc_accounts']['account_id']
```

#### Token Management
- Use retry client for AMC operations
- Always refresh tokens before API calls
- Use `refresh_access_token()` not `refresh_token()`

### API Integration

#### AMC API Critical Rules
1. Always use `instance_id` for AMC API calls (not internal UUID)
2. Entity ID required from `amc_accounts.account_id`
3. Date format: `2025-07-15T00:00:00` (no 'Z' suffix)
4. Handle 14-day data lag
5. Implement proper retry logic

### Testing

#### Backend Testing
```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest --cov=amc_manager tests/

# Specific test file
pytest tests/test_api_auth.py -v
```

#### Frontend Testing
```bash
# Unit tests
npm test

# E2E tests
npx playwright test

# Type checking
npx tsc --noEmit
```

<conditional-block context-check="dependencies" task-condition="choosing-external-library">
IF current task involves choosing an external library:
  IF Dependencies section already read in current context:
    SKIP: Re-reading this section
    NOTE: "Using Dependencies guidelines already in context"
  ELSE:
    READ: The following guidelines
ELSE:
  SKIP: Dependencies section not relevant to current task

## Dependencies

### Choose Libraries Wisely
When adding third-party dependencies:
- Select the most popular and actively maintained option
- Check the library's GitHub repository for:
  - Recent commits (within last 6 months)
  - Active issue resolution
  - Number of stars/downloads
  - Clear documentation
  - TypeScript support (for frontend)
  - Python type hints (for backend)

### Current Key Dependencies
- **Frontend**: React Query, React Router, Lucide React, Chart.js
- **Backend**: FastAPI, Supabase, httpx, tenacity
- **Upcoming**: shadcn/ui (component library)

### Avoid
- Unmaintained packages (no updates in 12+ months)
- Packages with known security vulnerabilities
- Packages with poor documentation
- Heavy dependencies for simple tasks
</conditional-block>

## Code Review Checklist

### Before Committing
- [ ] Code follows project style guides
- [ ] All TypeScript types are properly defined
- [ ] No console.log or print statements (use proper logging)
- [ ] Error handling is implemented
- [ ] Comments explain complex logic
- [ ] Tests pass locally
- [ ] No unused imports or variables
- [ ] Proper null/undefined checks

### Frontend Specific
- [ ] Components are properly typed
- [ ] Accessibility attributes (aria-label, htmlFor) are included
- [ ] Loading states are handled
- [ ] Error states are handled
- [ ] Keys are provided in list rendering
- [ ] API calls use React Query
- [ ] No inline styles (use Tailwind)

### Backend Specific
- [ ] Type hints on all function parameters/returns
- [ ] Proper error handling and logging
- [ ] Database queries use proper joins
- [ ] Async functions are awaited
- [ ] Services inherit from DatabaseService
- [ ] API endpoints return proper status codes
