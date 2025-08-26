# RecomAMP Product Overview

> Last Updated: 2025-08-26
> Version: 2.0.0
> Status: Production

## Product Description

RecomAMP is an internal agency platform for Amazon Marketing Cloud (AMC) that provides comprehensive query management, execution, and insights capabilities to agency team members. The platform streamlines AMC operations by offering a centralized interface for building, executing, and scheduling SQL queries against client Amazon advertising data.

## Target Users

- **Agency Analysts**: Create and execute AMC queries for client reporting
- **Account Managers**: Monitor campaign performance and generate insights
- **Data Scientists**: Build complex multi-step analytical workflows
- **Agency Leadership**: Access high-level dashboards and performance metrics

## Core Value Proposition

RecomAMP eliminates the complexity of working directly with Amazon Marketing Cloud by providing:

1. **Visual SQL Query Builder**: Intuitive interface with schema exploration and syntax highlighting
2. **Automated Execution Management**: Schedule recurring queries with smart retry and error handling
3. **Multi-Instance Support**: Manage queries across multiple client AMC instances from a single platform
4. **Rich Query Library**: Pre-built templates and examples for common use cases
5. **Comprehensive History**: Track all executions with detailed logs and performance metrics

## Current Platform Status

**Production System** serving active agency operations with:
- 15+ AMC instances under management
- 100+ active workflows and schedules
- Real-time execution monitoring and alerting
- OAuth-based secure authentication with Amazon
- Automated token refresh and session management

## Key Features (Live)

### Query Management
- Monaco-based SQL editor with AMC schema integration
- Parameter substitution for dynamic date ranges and filters
- Query validation and syntax highlighting
- Template library with categorized examples

### Execution Engine
- Asynchronous workflow execution with status polling
- Retry logic for failed executions with exponential backoff
- Cost tracking and execution time monitoring
- Export capabilities (CSV, JSON)

### Scheduling System
- Flexible scheduling: daily, weekly, monthly, custom CRON
- Timezone-aware execution with dynamic date parameters
- Auto-pause on consecutive failures
- Execution history and performance analytics

### Multi-Instance Architecture
- Centralized management of multiple AMC instances
- Instance-specific query execution and data isolation
- Bulk operations across selected instances
- Role-based access control per instance

## Current Technical Architecture

**Backend**: FastAPI with Supabase PostgreSQL, async/await patterns
**Frontend**: React 19 with TypeScript, TanStack Query for state management
**Database**: PostgreSQL with RLS policies and real-time subscriptions
**Authentication**: OAuth 2.0 with Amazon, encrypted token storage
**Background Services**: Token refresh, execution polling, schedule management

## Known Issues

1. **Schedule Executor Bug**: Multiple executions triggered for same schedule (fixed in latest deployment)
2. **Token Refresh Race Conditions**: Occasional authentication failures during concurrent operations
3. **Large Result Set Performance**: UI lag when displaying 10K+ row results

## Success Metrics

- **Query Execution Success Rate**: 94% (target: 96%)
- **Average Query Response Time**: 45 seconds (AMC-dependent)
- **Active Monthly Users**: 12 agency team members
- **Scheduled Query Reliability**: 91% successful auto-executions