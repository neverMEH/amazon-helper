# System Interconnections

## Overview

RecomAMP is built as an interconnected ecosystem where each component relies on and enhances others. This document maps the relationships, data flows, and dependencies between all major system components.

## Core System Architecture

### Data Flow Diagram
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend UI   │◄──►│   FastAPI       │◄──►│   Supabase      │
│   (React)       │    │   Backend       │    │   Database      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  Background      │
                       │  Services        │
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  Amazon APIs     │
                       │  (AMC, SP-API)   │
                       └──────────────────┘
```

## Component Interaction Matrix

### Authentication System Connections
```yaml
Authentication System:
  Depends On:
    - Supabase Database (user storage)
    - Amazon OAuth (token acquisition)
    - Fernet encryption (token security)
  
  Provides To:
    - All API endpoints (user context)
    - Background services (user tokens)
    - Frontend (session management)
    - Instance management (access control)
```

### Instance Management Connections
```yaml
Instance Management:
  Depends On:
    - Authentication system (user context)
    - AMC API (connectivity validation)
    - Supabase Database (configuration storage)
  
  Provides To:
    - Workflow system (AMC credentials)
    - Scheduling system (execution context)
    - Data collections (instance targeting)
    - Campaign management (account filtering)
```

### Workflow Execution Connections
```yaml
Workflow Execution:
  Depends On:
    - Authentication system (user tokens)
    - Instance management (AMC credentials)
    - Query builder (SQL processing)
    - Background services (status monitoring)
  
  Provides To:
    - Scheduling system (execution capability)
    - Data collections (historical data)
    - Build guides (example results)
    - Dashboard system (data source)
```

## Critical Data Dependencies

### Instance ID Resolution Chain
```python
# The critical path for AMC operations
User Authentication → Instance Selection → AMC Credentials → API Execution

# Implementation chain:
1. user_id (from JWT token)
2. instance.id (UUID from database query)
3. instance.instance_id (AMC string ID for API)
4. amc_accounts.account_id (entity_id for API)
```

### Token Flow Architecture
```python
# Token lifecycle across components
OAuth Flow → Encrypted Storage → Background Refresh → API Usage

# Components involved:
AuthService.handle_callback() → TokenService.encrypt_token() → 
TokenRefreshService.refresh_expiring_tokens() → AMCAPIClient.make_request()
```

## Service Interdependencies

### Background Services Network
```yaml
Token Refresh Service:
  Triggers: Time-based (every 10 minutes)
  Affects: All other services (token validity)
  Dependencies: User authentication data

Execution Poller:
  Triggers: Time-based (every 15 seconds)
  Affects: Workflow system, UI status updates
  Dependencies: AMC API, workflow executions

Schedule Executor:
  Triggers: Cron expressions
  Affects: Workflow execution system
  Dependencies: User tokens, instance configs

Collection Executor:
  Triggers: Collection status
  Affects: Data collection progress
  Dependencies: Workflow system, schedule logic
```

### Service Communication Patterns
```python
# Direct service calls
schedule_executor → workflow_service.execute_workflow()
collection_executor → workflow_service.execute_workflow()
token_refresh_service → token_service.refresh_access_token()

# Indirect communication (via database)
execution_poller → updates workflow_executions table → UI polling
background_services → log errors → monitoring systems
```

## Database Relationship Map

### Primary Entity Relationships
```sql
-- Core entity relationships
users (1) ←→ (n) amc_instances
amc_instances (n) ←→ (1) amc_accounts
amc_instances (1) ←→ (n) workflows
workflows (1) ←→ (n) workflow_executions
workflows (1) ←→ (n) workflow_schedules

-- Data collection relationships
workflows (1) ←→ (n) report_data_collections
report_data_collections (1) ←→ (n) report_data_weeks
report_data_weeks (n) ←→ (1) workflow_executions

-- Template and guide relationships
query_templates (1) ←→ (n) workflows
build_guides (1) ←→ (n) build_guide_sections
build_guide_sections (n) ←→ (n) workflows
```

### Critical Join Patterns
```sql
-- CRITICAL: Always join amc_accounts when using instances
SELECT w.*, i.instance_id, a.account_id as entity_id
FROM workflows w
JOIN amc_instances i ON i.id = w.instance_id
JOIN amc_accounts a ON a.id = i.account_id
WHERE w.user_id = ?

-- Collection instance resolution
SELECT c.*, i.instance_id, a.account_id as entity_id
FROM report_data_collections c
JOIN amc_instances i ON i.id = c.instance_id
JOIN amc_accounts a ON a.id = i.account_id
WHERE c.id = ?
```

## Frontend-Backend Integration

### State Management Flow
```typescript
// Component hierarchy and data flow
App.tsx
├── AuthProvider (global auth state)
├── QueryClient (TanStack Query cache)
└── Router
    ├── WorkflowDetail (local workflow state)
    │   ├── SQLEditor (query state)
    │   ├── ParameterForm (parameter state)
    │   └── ExecutionResults (result state)
    └── DataCollections (collection state)
        ├── CollectionForm (creation state)
        └── CollectionProgress (progress state)
```

### API Communication Patterns
```typescript
// Service layer interactions
AuthService ←→ Backend /api/auth/*
WorkflowService ←→ Backend /api/workflows/*
InstanceService ←→ Backend /api/instances/*
DataCollectionService ←→ Backend /api/data-collections/*

// Real-time updates via polling
useQuery(['executions'], { refetchInterval: 5000 })
useQuery(['collections'], { refetchInterval: 10000 })
useQuery(['schedules'], { refetchInterval: 30000 })
```

## Error Propagation Chains

### Authentication Errors
```python
# Error flow for authentication failures
Amazon OAuth Error → AuthService → HTTP 401 → Frontend → Login Redirect

# Token expiry handling
AMC API 403 → Token Refresh → Retry Request OR Re-authentication Required
```

### Execution Errors
```python
# Workflow execution error chain
AMC API Error → ExecutionPoller → Database Update → Frontend Notification

# Background service errors
Service Exception → Logger → Health Monitor → Admin Alert (if configured)
```

### Data Consistency Patterns
```python
# Ensuring data consistency across services
1. Database transactions for multi-table updates
2. Retry logic with idempotency keys
3. Event-driven updates via database triggers
4. Eventual consistency for background processes
```

## Performance Optimization Interconnections

### Caching Strategy
```yaml
Frontend Caching:
  - TanStack Query cache (5-10 minutes)
  - Local storage for user preferences
  - Session storage for form data

Backend Caching:
  - Instance configuration cache
  - Schema metadata cache
  - User token cache (in-memory)

Database Optimization:
  - Indexes on join columns
  - Materialized views for complex queries
  - Connection pooling for services
```

### Load Balancing Considerations
```yaml
Service Distribution:
  - Background services can run on separate instances
  - Database read replicas for reporting
  - CDN for static frontend assets
  - API rate limiting per user/instance
```

## Security Interconnections

### Trust Boundaries
```yaml
External Trust Boundary:
  - Amazon OAuth servers
  - AMC API endpoints
  - Frontend client applications

Internal Trust Boundaries:
  - Database encryption at rest
  - Service-to-service authentication
  - Token encryption in memory
```

### Security Flow
```python
# Security validation chain
Frontend Request → JWT Validation → User Context → 
Instance Access Control → AMC Token Decryption → API Call
```

## Monitoring and Observability

### System Health Dependencies
```yaml
Component Health Checks:
  Database: Connection pools, query performance
  AMC API: Response times, error rates
  Background Services: Processing rates, error counts
  Frontend: Load times, error boundaries

Cross-Component Metrics:
  End-to-end execution time (Frontend → AMC → Results)
  User journey completion rates
  System throughput (workflows/hour)
```

### Logging Interconnections
```python
# Distributed logging strategy
Frontend Errors → Browser Console → Error Reporting Service
Backend Logs → Structured JSON → Log Aggregation
Database Logs → Performance Monitoring
AMC API Logs → Rate Limit Monitoring
```

## Deployment Interconnections

### Service Dependencies
```yaml
Deployment Order:
  1. Database (Supabase)
  2. Backend API server
  3. Background services
  4. Frontend static files

Environment Configuration:
  - Shared environment variables
  - Service discovery patterns
  - Health check endpoints
```

### Scaling Considerations
```yaml
Horizontal Scaling:
  - Multiple background service instances
  - Load-balanced API servers
  - Database connection pooling

Vertical Scaling:
  - Background service concurrency limits
  - Database connection limits
  - Memory management for large results
```

## Common Integration Patterns

### Event-Driven Updates
```python
# Database triggers for real-time updates
CREATE OR REPLACE FUNCTION notify_execution_update()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify('execution_updates', NEW.id::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER execution_status_trigger
    AFTER UPDATE ON workflow_executions
    FOR EACH ROW
    EXECUTE FUNCTION notify_execution_update();
```

### Circuit Breaker Pattern
```python
# Preventing cascade failures
class AMCAPICircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    async def call_with_breaker(self, func, *args, **kwargs):
        if self.state == 'OPEN':
            if time.time() - self.last_failure > self.timeout:
                self.state = 'HALF_OPEN'
            else:
                raise CircuitBreakerOpenError()
        
        try:
            result = await func(*args, **kwargs)
            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = 'OPEN'
                self.last_failure = time.time()
            raise
```

## Testing Interconnections

### Integration Test Patterns
```python
# Test service interactions
async def test_complete_workflow_execution():
    # 1. Create authenticated user
    user = await create_test_user()
    
    # 2. Create AMC instance
    instance = await create_test_instance(user.id)
    
    # 3. Create workflow
    workflow = await create_test_workflow(user.id, instance.id)
    
    # 4. Execute workflow
    execution = await workflow_service.execute_workflow(workflow.id)
    
    # 5. Verify all system interactions
    assert execution.status == 'PENDING'
    assert_amc_api_called_with(instance.instance_id)
    assert_database_updated(execution.id)
```

### End-to-End Test Flows
```python
# Test complete user journeys
async def test_user_journey_create_and_execute_workflow():
    # Login → Select Instance → Create Workflow → Execute → View Results
    pass

async def test_scheduled_workflow_execution():
    # Create Schedule → Wait for Execution → Verify Results
    pass
```

## Troubleshooting Interconnections

### Common Integration Issues
1. **Instance ID Confusion**: Using UUID instead of AMC instance string
2. **Missing Entity ID**: Forgetting to join amc_accounts table
3. **Token Expiry**: Not handling token refresh in background services
4. **Date Format Issues**: AMC requires specific date formats
5. **Parameter Injection**: SQL parameter substitution errors

### Debugging Flows
```python
# Systematic debugging approach
1. Verify user authentication
2. Check instance configuration
3. Validate AMC API connectivity
4. Test parameter substitution
5. Monitor background service logs
6. Trace database queries
```

This interconnected system design ensures that RecomAMP operates as a cohesive platform where each component enhances the functionality of others while maintaining clear separation of concerns and robust error handling.