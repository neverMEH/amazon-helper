# Background Services

## Overview

RecomAMP operates four critical background services that handle token management, execution monitoring, scheduled tasks, and data collection. These services run continuously to maintain system health and automate user workflows.

## Service Architecture

### Service Runner
- `amc_manager/services/service_runner.py` - Main service orchestrator
- Manages lifecycle of all background services
- Handles graceful shutdown and error recovery
- Provides service health monitoring

### Individual Services
1. **Token Refresh Service** - Maintains OAuth token validity
2. **Execution Poller** - Monitors AMC execution status
3. **Schedule Executor** - Executes scheduled workflows
4. **Collection Executor** - Manages data collection tasks

## Token Refresh Service

### Purpose
Automatically refresh OAuth access tokens before they expire to maintain uninterrupted API access.

### Implementation
```python
# token_refresh_service.py
class TokenRefreshService(DatabaseService):
    def __init__(self):
        super().__init__()
        self.token_service = TokenService()
        self.refresh_interval = 600  # 10 minutes
    
    async def start(self):
        """Start token refresh service"""
        logger.info("Starting Token Refresh Service")
        
        while True:
            try:
                await self.refresh_expiring_tokens()
                await asyncio.sleep(self.refresh_interval)
            except Exception as e:
                logger.error(f"Token refresh service error: {e}")
                await asyncio.sleep(60)  # Short retry interval on error
    
    async def refresh_expiring_tokens(self):
        """Refresh tokens expiring within 10 minutes"""
        cutoff_time = datetime.utcnow() + timedelta(minutes=10)
        
        # Find users with expiring tokens
        expiring_users = self.db.table('users')\
            .select('id, email, encrypted_refresh_token, token_expires_at')\
            .lte('token_expires_at', cutoff_time.isoformat())\
            .is_('encrypted_refresh_token', 'not.null')\
            .execute()
        
        logger.info(f"Found {len(expiring_users.data)} tokens to refresh")
        
        for user in expiring_users.data:
            try:
                # Use refresh_access_token method (not refresh_token!)
                await self.token_service.refresh_access_token(user['id'])
                logger.info(f"Refreshed token for user {user['id']}")
                
            except TokenRefreshError as e:
                logger.warning(f"Failed to refresh token for user {user['id']}: {e}")
                # Could send notification or disable user
                
            except TokenDecryptionError as e:
                logger.error(f"Token decryption failed for user {user['id']}: {e}")
                # User needs to re-authenticate
```

### Key Features
- **Proactive Refresh**: Refreshes tokens 10 minutes before expiry
- **Error Handling**: Graceful handling of refresh failures
- **User Notification**: Alerts when manual re-authentication needed
- **Batch Processing**: Handles multiple users efficiently

## Execution Poller Service

### Purpose
Monitor pending AMC workflow executions and update their status when complete.

### Implementation
```python
# execution_poller.py
class ExecutionPoller(DatabaseService):
    def __init__(self):
        super().__init__()
        self.amc_client = AMCAPIClientWithRetry()
        self.poll_interval = 15  # 15 seconds
    
    async def start(self):
        """Start execution polling service"""
        logger.info("Starting Execution Poller Service")
        
        while True:
            try:
                await self.poll_pending_executions()
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Execution poller error: {e}")
                await asyncio.sleep(self.poll_interval)
    
    async def poll_pending_executions(self):
        """Check status of all pending executions"""
        pending_executions = self.db.table('workflow_executions')\
            .select('*, workflows(*, amc_instances(*, amc_accounts(*)))')\
            .in_('status', ['PENDING', 'RUNNING'])\
            .execute()
        
        logger.info(f"Polling {len(pending_executions.data)} pending executions")
        
        # Process executions concurrently with limit
        semaphore = asyncio.Semaphore(10)  # Max 10 concurrent polls
        
        tasks = [
            self.poll_execution_with_semaphore(semaphore, execution)
            for execution in pending_executions.data
        ]
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log any exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    execution_id = pending_executions.data[i]['id']
                    logger.error(f"Error polling execution {execution_id}: {result}")
    
    async def poll_execution_with_semaphore(self, semaphore: asyncio.Semaphore, execution: dict):
        """Poll single execution with concurrency control"""
        async with semaphore:
            return await self.poll_single_execution(execution)
    
    async def poll_single_execution(self, execution: dict):
        """Poll status of single execution"""
        try:
            workflow = execution['workflows']
            instance = workflow['amc_instances']
            account = instance['amc_accounts']
            
            # Get current status from AMC
            status_response = await self.amc_client.get_execution_status(
                execution_id=execution['amc_execution_id'],
                instance_id=instance['instance_id'],
                entity_id=account['account_id']
            )
            
            current_status = status_response.get('status')
            
            # Update if status changed
            if current_status != execution['status']:
                await self.update_execution_status(execution, current_status, status_response)
                
        except Exception as e:
            logger.error(f"Failed to poll execution {execution['id']}: {e}")
            # Could mark execution as failed after repeated errors
    
    async def update_execution_status(self, execution: dict, new_status: str, response_data: dict):
        """Update execution status and handle completion"""
        update_data = {
            'status': new_status,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        if new_status in ['SUCCESS', 'FAILED']:
            # Execution completed
            update_data['completed_at'] = datetime.utcnow().isoformat()
            
            if new_status == 'SUCCESS':
                # Download results
                await self.download_execution_results(execution, response_data)
            else:
                # Record error details
                update_data['error_message'] = response_data.get('error', 'Execution failed')
        
        # Update database
        self.db.table('workflow_executions')\
            .update(update_data)\
            .eq('id', execution['id'])\
            .execute()
        
        logger.info(f"Updated execution {execution['id']} status: {new_status}")
```

### Key Features
- **Real-time Monitoring**: Checks every 15 seconds
- **Concurrent Polling**: Handles multiple executions simultaneously
- **Result Processing**: Downloads and stores results when complete
- **Error Resilience**: Continues polling despite individual failures

## Schedule Executor Service

### Purpose
Execute scheduled workflows at their designated times based on cron expressions.

### Implementation
```python
# schedule_executor.py
class ScheduleExecutor(DatabaseService):
    def __init__(self):
        super().__init__()
        self.workflow_service = WorkflowService()
        self.check_interval = 60  # 1 minute
    
    async def start(self):
        """Start schedule executor service"""
        logger.info("Starting Schedule Executor Service")
        
        while True:
            try:
                await self.execute_due_schedules()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Schedule executor error: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def execute_due_schedules(self):
        """Find and execute schedules that are due"""
        current_time = datetime.utcnow()
        
        # Find active schedules due for execution
        due_schedules = self.db.table('workflow_schedules')\
            .select('*, workflows(*, amc_instances(*, amc_accounts(*)))')\
            .eq('is_active', True)\
            .lte('next_run_at', current_time.isoformat())\
            .execute()
        
        logger.info(f"Found {len(due_schedules.data)} due schedules")
        
        for schedule in due_schedules.data:
            # Check for recent execution (deduplication)
            if not await self.has_recent_execution(schedule['id'], minutes=5):
                await self.execute_schedule(schedule)
            else:
                logger.info(f"Skipping schedule {schedule['id']} - recent execution detected")
    
    async def has_recent_execution(self, schedule_id: str, minutes: int = 5) -> bool:
        """Check if schedule executed recently (deduplication)"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        
        recent_runs = self.db.table('schedule_runs')\
            .select('id')\
            .eq('schedule_id', schedule_id)\
            .gte('created_at', cutoff_time.isoformat())\
            .execute()
        
        return len(recent_runs.data) > 0
    
    async def execute_schedule(self, schedule: dict):
        """Execute a scheduled workflow"""
        try:
            workflow = schedule['workflows']
            instance = workflow['amc_instances']
            account = instance['amc_accounts']
            
            # CRITICAL: Validate account association
            if not account:
                raise ValueError(f"Schedule {schedule['id']} missing AMC account information")
            
            # Execute workflow
            execution = await self.workflow_service.execute_workflow(
                workflow_id=workflow['id'],
                user_id=schedule['user_id'],
                instance_id=instance['instance_id'],  # AMC string ID
                entity_id=account['account_id'],
                parameters=schedule.get('parameters', {})
            )
            
            # Record successful schedule run
            await self.record_schedule_run(schedule['id'], execution['id'], 'SUCCESS')
            
            # Update next run time
            await self.update_next_run_time(schedule)
            
            logger.info(f"Executed schedule {schedule['id']}")
            
        except Exception as e:
            logger.error(f"Failed to execute schedule {schedule['id']}: {e}")
            
            # Record failed run
            await self.record_schedule_run(schedule['id'], None, 'FAILED', str(e))
            
            # Still update next run time to continue scheduling
            await self.update_next_run_time(schedule)
    
    async def update_next_run_time(self, schedule: dict):
        """Calculate and update next run time"""
        from croniter import croniter
        import pytz
        
        # Get timezone (default to UTC)
        tz = pytz.timezone(schedule.get('timezone', 'UTC'))
        local_now = datetime.now(tz)
        
        # Calculate next run
        cron = croniter(schedule['cron_expression'], local_now)
        next_local = cron.get_next(datetime)
        
        # Convert to UTC for storage
        next_utc = next_local.astimezone(pytz.UTC).replace(tzinfo=None)
        
        # Update schedule
        self.db.table('workflow_schedules')\
            .update({'next_run_at': next_utc.isoformat()})\
            .eq('id', schedule['id'])\
            .execute()
```

### Key Features
- **Cron Expression Support**: Full cron syntax with timezone handling
- **Deduplication Logic**: Prevents duplicate executions
- **Error Recovery**: Continues scheduling despite execution failures
- **Timezone Awareness**: Proper timezone conversion

## Collection Executor Service

### Purpose
Manage historical data collection by processing collections and their associated weeks.

### Implementation
```python
# collection_executor.py
class CollectionExecutor(DatabaseService):
    def __init__(self):
        super().__init__()
        self.workflow_service = WorkflowService()
        self.check_interval = 30  # 30 seconds
        self.max_concurrent_collections = 5
        self.max_concurrent_weeks = 10
    
    async def start(self):
        """Start collection executor service"""
        logger.info("Starting Collection Executor Service")
        
        while True:
            try:
                await self.process_active_collections()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Collection executor error: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def process_active_collections(self):
        """Process all active collections"""
        active_collections = self.db.table('report_data_collections')\
            .select('*, workflows(*, amc_instances(*, amc_accounts(*)))')\
            .eq('status', 'ACTIVE')\
            .execute()
        
        # Process up to max concurrent collections
        collections_to_process = active_collections.data[:self.max_concurrent_collections]
        
        if collections_to_process:
            logger.info(f"Processing {len(collections_to_process)} active collections")
            
            tasks = [
                self.process_collection(collection)
                for collection in collections_to_process
            ]
            
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def process_collection(self, collection: dict):
        """Process weeks for a single collection"""
        try:
            # Get pending weeks for this collection
            pending_weeks = self.db.table('report_data_weeks')\
                .select('*')\
                .eq('collection_id', collection['id'])\
                .eq('status', 'PENDING')\
                .order('week_start_date')\
                .limit(self.max_concurrent_weeks)\
                .execute()
            
            if not pending_weeks.data:
                # Check if collection is complete
                await self.check_collection_completion(collection['id'])
                return
            
            logger.info(f"Processing {len(pending_weeks.data)} weeks for collection {collection['id']}")
            
            # Process weeks concurrently
            semaphore = asyncio.Semaphore(self.max_concurrent_weeks)
            
            tasks = [
                self.execute_week_with_semaphore(semaphore, collection, week)
                for week in pending_weeks.data
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log any exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    week_id = pending_weeks.data[i]['id']
                    logger.error(f"Error executing week {week_id}: {result}")
                    
        except Exception as e:
            logger.error(f"Error processing collection {collection['id']}: {e}")
    
    async def execute_week_with_semaphore(self, semaphore: asyncio.Semaphore, collection: dict, week: dict):
        """Execute single week with concurrency control"""
        async with semaphore:
            return await self.execute_collection_week(collection, week)
    
    async def execute_collection_week(self, collection: dict, week: dict):
        """Execute workflow for specific week"""
        try:
            # Mark week as running
            self.db.table('report_data_weeks')\
                .update({
                    'status': 'RUNNING',
                    'started_at': datetime.utcnow().isoformat()
                })\
                .eq('id', week['id'])\
                .execute()
            
            workflow = collection['workflows']
            instance = workflow['amc_instances']
            account = instance['amc_accounts']
            
            # Build parameters for this week
            parameters = {
                'start_date': week['week_start_date'],
                'end_date': week['week_end_date'],
                **collection.get('parameters', {})
            }
            
            # Execute workflow
            execution = await self.workflow_service.execute_workflow(
                workflow_id=workflow['id'],
                user_id=collection['user_id'],
                instance_id=instance['instance_id'],
                entity_id=account['account_id'],
                parameters=parameters
            )
            
            # Update week with execution ID
            self.db.table('report_data_weeks')\
                .update({
                    'execution_id': execution['id'],
                    'status': 'SUCCESS',  # Will be updated by execution poller
                    'updated_at': datetime.utcnow().isoformat()
                })\
                .eq('id', week['id'])\
                .execute()
            
            logger.info(f"Executed week {week['id']} for collection {collection['id']}")
            
        except Exception as e:
            # Mark week as failed
            self.db.table('report_data_weeks')\
                .update({
                    'status': 'FAILED',
                    'error_message': str(e),
                    'updated_at': datetime.utcnow().isoformat()
                })\
                .eq('id', week['id'])\
                .execute()
            
            logger.error(f"Failed to execute week {week['id']}: {e}")
            raise
```

### Key Features
- **Parallel Processing**: Multiple collections and weeks concurrently
- **Progress Tracking**: Real-time status updates
- **Error Recovery**: Failed weeks can be retried individually
- **Completion Detection**: Automatic collection completion

## Service Management

### Service Runner Orchestration
```python
# service_runner.py - Main orchestrator
class ServiceRunner:
    def __init__(self):
        self.services = {}
        self.running = False
    
    async def start_all_services(self):
        """Start all background services"""
        self.services = {
            'token_refresh': TokenRefreshService(),
            'execution_poller': ExecutionPoller(),
            'schedule_executor': ScheduleExecutor(),
            'collection_executor': CollectionExecutor()
        }
        
        logger.info("Starting all background services")
        
        # Start all services concurrently
        tasks = [
            asyncio.create_task(service.start(), name=name)
            for name, service in self.services.items()
        ]
        
        self.running = True
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
            await self.stop_all_services()
        except Exception as e:
            logger.error(f"Service runner error: {e}")
            await self.stop_all_services()
    
    async def stop_all_services(self):
        """Gracefully stop all services"""
        logger.info("Stopping all background services")
        self.running = False
        
        # Cancel all service tasks
        for task in asyncio.all_tasks():
            if not task.done():
                task.cancel()
                
        # Wait for cleanup
        await asyncio.sleep(2)
        
        logger.info("All services stopped")

# Entry point
async def main():
    runner = ServiceRunner()
    await runner.start_all_services()

if __name__ == "__main__":
    asyncio.run(main())
```

### Health Monitoring
```python
class ServiceHealthMonitor:
    def __init__(self):
        self.service_stats = {}
    
    async def check_service_health(self):
        """Monitor service health and performance"""
        
        # Check token refresh success rate
        token_stats = await self.get_token_refresh_stats()
        
        # Check execution polling performance
        polling_stats = await self.get_polling_stats()
        
        # Check schedule execution success rate
        schedule_stats = await self.get_schedule_stats()
        
        # Check collection processing rate
        collection_stats = await self.get_collection_stats()
        
        return {
            'token_refresh': token_stats,
            'execution_polling': polling_stats,
            'schedule_execution': schedule_stats,
            'collection_processing': collection_stats,
            'overall_health': self.calculate_overall_health()
        }
```

## Error Handling and Recovery

### Service Resilience
- **Automatic Restart**: Services restart on critical failures
- **Connection Retry**: Database connection recovery
- **Graceful Degradation**: Continue operating with reduced functionality
- **Circuit Breaker**: Disable problematic services temporarily

### Monitoring and Alerting
- **Service Health Checks**: Regular health monitoring
- **Performance Metrics**: Track processing rates and errors
- **Error Notifications**: Alert on critical service failures
- **Dashboard Integration**: Real-time service status display

## Configuration and Deployment

### Environment Configuration
```python
# Service configuration
SERVICE_CONFIG = {
    'token_refresh': {
        'interval': int(os.getenv('TOKEN_REFRESH_INTERVAL', 600)),
        'buffer_minutes': int(os.getenv('TOKEN_BUFFER_MINUTES', 10))
    },
    'execution_poller': {
        'interval': int(os.getenv('POLL_INTERVAL', 15)),
        'max_concurrent': int(os.getenv('MAX_CONCURRENT_POLLS', 10))
    },
    'schedule_executor': {
        'interval': int(os.getenv('SCHEDULE_CHECK_INTERVAL', 60)),
        'deduplication_minutes': int(os.getenv('SCHEDULE_DEDUP_MINUTES', 5))
    },
    'collection_executor': {
        'interval': int(os.getenv('COLLECTION_CHECK_INTERVAL', 30)),
        'max_collections': int(os.getenv('MAX_CONCURRENT_COLLECTIONS', 5)),
        'max_weeks': int(os.getenv('MAX_CONCURRENT_WEEKS', 10))
    }
}
```

### Docker Deployment
```dockerfile
# Dockerfile for background services
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY amc_manager/ ./amc_manager/
COPY scripts/ ./scripts/

CMD ["python", "-m", "amc_manager.services.service_runner"]
```

## Testing Strategy

### Service Testing
```python
# Test service functionality in isolation
async def test_token_refresh_service():
    service = TokenRefreshService()
    # Mock database and external calls
    # Test refresh logic
    
async def test_execution_poller():
    poller = ExecutionPoller()
    # Mock AMC API responses
    # Test status update logic
```

### Integration Testing
```python
# Test service interactions
async def test_schedule_to_execution_flow():
    # Test complete flow from schedule to execution completion
```

### Load Testing
- Test service performance under high load
- Validate concurrency limits
- Monitor resource usage