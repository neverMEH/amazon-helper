# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-08-26-schedule-fix-complete/spec.md

> Created: 2025-08-26
> Version: 1.0.0

## Technical Requirements

### Atomic Schedule Claiming
- Implement database-level optimistic locking using `last_run_at` field
- Use `UPDATE ... WHERE last_run_at = old_value` pattern for atomic claims
- Reduce buffer window from 2 minutes to 30 seconds maximum
- Add double-check validation against `schedule_runs` table

### Test Run Handling
- Detect stuck schedules (overdue >5 minutes with recent runs)
- Implement automatic `next_run_at` reset for stuck schedules
- Properly restore cron-based schedule after test run completion
- Add `is_test_run` flag tracking (when column available)

### Execution Parameter Fix
- Ensure `instance_id` (AMC ID) is correctly passed to execution service
- Verify instance retrieval uses proper UUID to AMC ID mapping
- Match parameter format between scheduled and manual executions
- Fix date parameter formatting (no 'Z' suffix for AMC)

### Retry Logic Implementation
- Maximum 3 retry attempts for API/network errors only
- Exponential backoff: 10s, 20s, 40s (max 60s)
- No retry for data/configuration errors
- Update `next_run_at` even on failure to prevent infinite loops

### Monitoring and Logging
- Add structured logging for schedule claim attempts
- Log instance data retrieval and parameter formatting
- Track execution attempts and retry reasons
- Add metrics for schedule success/failure rates

## Approach

### Database Locking Strategy
Use optimistic locking with last_run_at timestamp comparison to prevent race conditions during schedule claiming. This approach avoids table locks while ensuring atomicity.

### Error Classification System
Implement smart retry logic that distinguishes between transient errors (network, API limits) and permanent errors (configuration, permissions) to avoid infinite retry loops.

### Parameter Standardization
Create a unified parameter processing pipeline that ensures scheduled executions use identical data structures as manual executions, particularly for AMC instance identification.

## Performance Criteria

- Schedule claim operation < 100ms
- Zero duplicate executions under concurrent polling
- 95% schedule execution success rate
- Maximum 5-minute delay for stuck schedule recovery

## External Dependencies

- Supabase database for atomic operations
- Amazon Marketing Cloud API for workflow execution
- Existing authentication and token refresh services