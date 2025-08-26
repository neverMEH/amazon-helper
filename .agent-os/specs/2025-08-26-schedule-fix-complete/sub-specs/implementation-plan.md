# Implementation Plan

This is the implementation plan for the spec detailed in @.agent-os/specs/2025-08-26-schedule-fix-complete/spec.md

> Created: 2025-08-26
> Version: 1.0.0

## Phase 1: Core Fixes (Immediate)

### Fix 1: Atomic Schedule Claiming
**Location**: `amc_manager/services/schedule_executor_service.py`
**Method**: `_atomic_claim_schedule()`
**Implementation**: 
- Already partially complete, needs verification
- Ensure UPDATE WHERE last_run_at = old_value pattern
- Reduce buffer window to 30 seconds

### Fix 2: Test Run Recovery
**Location**: `amc_manager/services/schedule_executor_service.py`
**Method**: `_reset_stuck_schedule()`
**Implementation**: 
- Detect overdue schedules with recent execution history
- Auto-reset next_run_at for stuck schedules
- Log recovery actions for monitoring

### Fix 3: Instance ID Passing
**Location**: `amc_manager/services/schedule_executor_service.py`
**Method**: `execute_workflow()`
**Implementation**:
- Ensure correct AMC instance_id is passed, not internal UUID
- Verify instance retrieval and mapping logic
- Match parameter structure with manual execution path

## Phase 2: Monitoring (Next)

### Enhanced Logging
**Implementation**:
- Add structured log entries for debugging
- Include correlation IDs for tracking execution flow
- Log all state transitions and parameter values
- Add timing metrics for each operation

### Metrics Collection
**Implementation**:
- Track schedule execution success rate
- Monitor duplicate attempt frequency
- Measure execution latency and recovery times
- Create dashboard for operations monitoring

## Phase 3: Testing & Validation

### Test Scenarios
1. **Single Schedule Execution**
   - Verify exact timing execution
   - Confirm no duplicates under load

2. **Concurrent Schedule Handling**
   - Multiple schedules at same time
   - Validate atomic claiming works

3. **Test Run Integration**
   - Execute test run
   - Verify schedule timing restoration
   - Confirm no stuck states

4. **Failure Recovery**
   - Simulate API failures
   - Verify retry logic and backoff
   - Confirm eventual success

5. **Load Testing**
   - Concurrent polling from multiple workers
   - High-frequency schedule execution
   - Resource usage monitoring

### Success Criteria
- **Zero duplicates** in 100 test executions
- **100% test run recovery** rate
- **<5% difference** between manual and scheduled success rates
- **Sub-minute** stuck schedule recovery time

## Implementation Priority

### High Priority (Week 1)
1. Fix atomic schedule claiming
2. Resolve instance ID parameter passing
3. Implement test run recovery

### Medium Priority (Week 2)
1. Enhanced logging and monitoring
2. Comprehensive testing suite
3. Performance optimization

### Low Priority (Week 3)
1. Metrics dashboard
2. Alert system for failures
3. Documentation updates

## Risk Mitigation

### Database Lock Contention
- Use optimistic locking instead of pessimistic
- Implement exponential backoff for claim attempts
- Monitor database performance metrics

### API Rate Limiting
- Respect AMC API limits in retry logic
- Implement circuit breaker pattern
- Queue executions during peak times

### Data Consistency
- Validate all state transitions
- Implement rollback for failed operations
- Add data integrity checks