# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/specs/2025-08-26-schedule-fix-complete/spec.md

> Created: 2025-08-26
> Status: Ready for Implementation

## Tasks

### Phase 1: Immediate Diagnosis (Priority: CRITICAL)

#### Task 1.1: Analyze Current Debug Output ✅
**Files**: `server.log`, Railway deployment logs  
**Estimated Time**: 2 hours  
**Description**: Examine recent debug logs to identify:
- [x] Created diagnostic script: `scripts/diagnose_schedule_issues.py`
- [x] Identifies stuck schedules and overdue executions
- [x] Checks for duplicate runs and failure patterns
- [x] Verifies instance configuration
- [x] Ready to run when Railway logs available

#### Task 1.2: Database State Investigation ✅
**Files**: Database queries, manual verification  
**Estimated Time**: 1 hour  
**Description**: Verify database integrity:
- [x] Created verification script: `scripts/verify_database_state.py`
- [x] Checks `amc_instances.instance_id` for NULL values
- [x] Verifies workflow-instance relationships
- [x] Identifies orphaned records
- [x] Detects duplicate schedule runs

#### Task 1.3: Execution Path Comparison ✅
**Files**: `schedule_executor_service.py`, `workflows.py` API endpoints  
**Estimated Time**: 3 hours  
**Description**: Document execution flow differences:
- [x] Created comparison script: `scripts/compare_execution_paths.py`
- [x] Documented manual vs scheduled flow
- [x] Identified critical difference: instance_id resolution
- [x] Root cause likely: NULL instance_id in amc_instances table
- [x] Provided verification steps and fix

### Phase 2: Core Issue Resolution (Priority: HIGH)

#### Task 2.1: Fix Instance ID Resolution Logic
**Files**: `amc_manager/services/schedule_executor_service.py` (lines 218-246)  
**Estimated Time**: 4 hours  
**Description**: Ensure proper instance_id handling:
- [ ] Verify instance query returns correct `instance_id` field (not UUID)
- [ ] Add null/empty validation before AMC API calls
- [ ] Implement fallback instance resolution if needed
- [ ] Add detailed logging for instance resolution steps
- [ ] Test with known working AMC instances

#### Task 2.2: Strengthen Atomic Schedule Claiming
**Files**: `amc_manager/services/schedule_executor_service.py` (`_atomic_claim_schedule` method)  
**Estimated Time**: 3 hours  
**Description**: Prevent duplicate execution attempts:
- [ ] Verify optimistic locking using `updated_at` timestamp
- [ ] Add transaction isolation level if needed
- [ ] Implement retry logic for failed claims
- [ ] Test with concurrent service instances
- [ ] Add metrics for claim success/failure rates

#### Task 2.3: Improve Stuck Schedule Recovery
**Files**: `amc_manager/services/schedule_executor_service.py` (`_reset_stuck_schedule` method)  
**Estimated Time**: 2 hours  
**Description**: Handle stuck schedule cleanup:
- [ ] Test stuck schedule detection (5+ minutes in progress)
- [ ] Verify croniter-based next_run calculation is correct
- [ ] Add safeguards against infinite reset loops
- [ ] Log all recovery attempts with context
- [ ] Test with various CRON expressions

### Phase 3: Parameter and Authentication Fixes (Priority: HIGH)

#### Task 3.1: Fix Parameter Processing
**Files**: `amc_manager/services/schedule_executor_service.py` (`calculate_parameters` method)  
**Estimated Time**: 2 hours  
**Description**: Ensure correct parameter format for AMC API:
- [ ] Verify date format excludes 'Z' timezone suffix
- [ ] Check all required parameters are included
- [ ] Match exact parameter structure from manual execution
- [ ] Test with date ranges, relative dates, custom parameters
- [ ] Validate parameter substitution logic

#### Task 3.2: Token Management Verification
**Files**: `amc_manager/services/schedule_executor_service.py` (`ensure_fresh_token` method)  
**Estimated Time**: 2 hours  
**Description**: Ensure proper authentication:
- [ ] Verify token refresh happens before execution
- [ ] Check token encryption/decryption process
- [ ] Test expired token recovery scenario
- [ ] Ensure proper error handling for auth failures
- [ ] Add token validity logging

### Phase 4: Retry Logic and Error Handling (Priority: MEDIUM)

#### Task 4.1: Implement Intelligent Retry System
**Files**: `amc_manager/services/schedule_executor_service.py` (`execute_schedule` method)  
**Estimated Time**: 4 hours  
**Description**: Add smart retry mechanism:
- [ ] Identify retryable errors (network, auth) vs permanent failures
- [ ] Implement exponential backoff (1, 2, 4 minute delays)
- [ ] Limit to 3 retry attempts per schedule
- [ ] Log retry attempts with failure reasons
- [ ] Update schedule state appropriately after final failure

#### Task 4.2: Enhanced Error Classification
**Files**: `amc_manager/services/schedule_executor_service.py`  
**Estimated Time**: 2 hours  
**Description**: Improve error reporting and handling:
- [ ] Add specific error codes for different failure types
- [ ] Include execution context in error messages
- [ ] Log full stack traces for debugging
- [ ] Create error categorization (auth, network, validation, AMC)
- [ ] Update frontend to display meaningful error messages

### Phase 5: Testing and Validation (Priority: MEDIUM)

#### Task 5.1: Controlled Test Environment
**Files**: Test schedules, monitoring scripts  
**Estimated Time**: 3 hours  
**Description**: Set up comprehensive testing:
- [ ] Create simple test workflow with known parameters
- [ ] Schedule for frequent execution (every 5 minutes)
- [ ] Monitor for duplicate executions over 2-hour period
- [ ] Test with various parameter types and date ranges
- [ ] Verify proper cleanup after test completion

#### Task 5.2: Load and Concurrency Testing
**Files**: Test scripts, load simulation  
**Estimated Time**: 4 hours  
**Description**: Test under realistic conditions:
- [ ] Create 10+ concurrent schedules with different intervals
- [ ] Simulate high-frequency polling service restarts
- [ ] Test with intentionally failing workflows
- [ ] Verify no duplicates under concurrent execution
- [ ] Monitor database performance under load

#### Task 5.3: Test Run Feature Validation
**Files**: Test run execution, recovery verification  
**Estimated Time**: 2 hours  
**Description**: Ensure test runs work properly:
- [ ] Execute test run and verify it doesn't affect schedule state
- [ ] Confirm schedule recovers proper next_run_at value
- [ ] Test multiple consecutive test runs
- [ ] Verify test runs don't create duplicate schedule_runs records
- [ ] Test test run failure scenarios

### Phase 6: Monitoring and Observability (Priority: LOW)

#### Task 6.1: Metrics and Alerting
**Files**: New metrics module, monitoring configuration  
**Estimated Time**: 4 hours  
**Description**: Implement comprehensive monitoring:
- [ ] Track schedule execution success rate by instance
- [ ] Monitor duplicate execution attempts
- [ ] Measure execution latency and queue depth
- [ ] Create alerting for execution failures
- [ ] Add Grafana dashboard for schedule health

#### Task 6.2: Structured Logging Enhancement
**Files**: `amc_manager/services/schedule_executor_service.py`  
**Estimated Time**: 2 hours  
**Description**: Improve log quality:
- [ ] Add correlation IDs for tracking execution chains
- [ ] Use structured JSON logging format
- [ ] Include timing information for all operations
- [ ] Add configurable debug verbosity levels
- [ ] Implement log rotation and archival

#### Task 6.3: Debug and Maintenance Utilities
**Files**: `scripts/debug_schedules.py`, maintenance tools  
**Estimated Time**: 3 hours  
**Description**: Build operational tools:
- [ ] Script to identify and reset stuck schedules
- [ ] Tool to manually trigger schedule execution
- [ ] Query to detect and clean duplicate executions
- [ ] Utility to test atomic claiming logic
- [ ] Health check endpoint for schedule service

### Phase 7: Documentation and Deployment (Priority: LOW)

#### Task 7.1: Documentation Updates
**Files**: `CLAUDE.md`, troubleshooting guides  
**Estimated Time**: 2 hours  
**Description**: Update project documentation:
- [ ] Document new retry behavior and error codes
- [ ] Update troubleshooting guide with common issues
- [ ] Add monitoring and alerting guidelines
- [ ] Create runbook for schedule service operations
- [ ] Update API documentation for schedule endpoints

#### Task 7.2: Deployment Strategy
**Files**: Deployment scripts, rollback plans  
**Estimated Time**: 2 hours  
**Description**: Plan safe production rollout:
- [ ] Test all fixes in local development environment
- [ ] Create deployment checklist and rollback procedure
- [ ] Monitor schedule health during initial deployment
- [ ] Plan gradual enablement if blue-green deployment available
- [ ] Document post-deployment verification steps

#### Task 7.3: Post-Deployment Monitoring
**Files**: Monitoring scripts, validation queries  
**Estimated Time**: 4 hours (spread over 48 hours)  
**Description**: Verify fix effectiveness:
- [ ] Monitor for 48 hours for duplicate executions
- [ ] Track schedule success rate improvement
- [ ] Verify all existing schedules continue working
- [ ] Confirm new schedules work correctly
- [ ] Document any remaining issues for follow-up

## Implementation Priority

### CRITICAL (Immediate - Day 1)
1. Task 1.1: Debug log analysis
2. Task 1.2: Database state verification  
3. Task 1.3: Execution path comparison
4. Task 2.1: Instance ID resolution fix

### HIGH (Days 2-3)
5. Task 3.1: Parameter processing fix
6. Task 2.2: Atomic claiming improvement
7. Task 3.2: Token management verification
8. Task 5.1: Controlled testing setup

### MEDIUM (Days 4-5)
9. Task 4.1: Retry logic implementation
10. Task 4.2: Error classification enhancement
11. Task 5.2: Load testing
12. Task 2.3: Stuck schedule recovery

### LOW (Days 6-7)
13. Task 5.3: Test run validation
14. Task 6.1: Metrics implementation
15. Task 7.2: Deployment planning
16. Task 7.3: Post-deployment monitoring

## Success Metrics

### Primary Success Criteria
- **Zero duplicate executions** in 48-hour monitoring period
- **95%+ schedule execution success rate** for valid workflows
- **Test runs complete without affecting regular schedules**
- **Clear, actionable error messages** for all failure types

### Secondary Success Criteria  
- Schedule claim contention < 5% under normal load
- Average execution latency < 30 seconds from scheduled time
- Stuck schedule recovery within 10 minutes
- All existing schedules continue working without changes

## Risk Mitigation

### High Risk Items
- **Instance ID resolution changes** could break existing workflows
- **Atomic claiming modifications** could cause schedule lockout
- **Parameter format changes** could cause AMC API failures

### Mitigation Strategies
- Test all changes with known working schedules first
- Implement feature flags for gradual rollout
- Keep detailed logs of all changes for quick rollback
- Have manual schedule execution available as fallback

## Dependencies

### External Dependencies
- AMC API availability and consistency
- Database performance under increased load
- Token refresh service reliability

### Internal Dependencies  
- Workflow execution service stability
- User authentication token validity
- Background service coordination

## Notes

- Start with diagnostic tasks to understand current failure modes
- Focus on instance_id issue as most likely root cause
- Test each fix incrementally before moving to next phase  
- Maintain detailed change log for post-deployment analysis
- Consider implementing feature flags for gradual rollout