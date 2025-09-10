# Execution Monitoring System

## Overview

The execution monitoring system provides real-time tracking of AMC workflow executions, from submission to completion. It handles status polling, result processing, error tracking, and user notifications through a sophisticated background service architecture.

## Key Components

### Backend Services
- `amc_manager/services/execution_poller.py` - Main polling service
- `amc_manager/services/amc_api_client_with_retry.py` - AMC status checking
- `amc_manager/services/workflow_service.py` - Execution management
- `amc_manager/api/supabase/executions.py` - Execution API endpoints

### Frontend Components
- `frontend/src/components/ExecutionStatus.tsx` - Real-time status display
- `frontend/src/components/ExecutionResults.tsx` - Results visualization
- `frontend/src/pages/ExecutionHistory.tsx` - Historical execution view
- `frontend/src/hooks/useExecutionStatus.ts` - Status polling hook

### Database Tables
- `workflow_executions` - Core execution records
- `workflows` - Parent workflow definitions
- `amc_instances` - Instance configurations for API calls

## Execution Lifecycle

### Status States
```python
# Execution status progression
EXECUTION_STATES = {
    'PENDING': 'Submitted to AMC, waiting to start',
    'RUNNING': 'Currently executing in AMC',
    'SUCCESS': 'Completed successfully with results',
    'FAILED': 'Failed with error message',
    'CANCELLED': 'Cancelled by user or system',
    'TIMEOUT': 'Exceeded maximum execution time'
}
```

### State Transitions
```python
# execution_poller.py - Status transition logic
class ExecutionStatusManager:
    VALID_TRANSITIONS = {
        'PENDING': ['RUNNING', 'FAILED', 'CANCELLED'],
        'RUNNING': ['SUCCESS', 'FAILED', 'TIMEOUT'],
        'SUCCESS': [],  # Terminal state
        'FAILED': [],   # Terminal state
        'CANCELLED': [], # Terminal state
        'TIMEOUT': []   # Terminal state
    }
    
    def validate_status_transition(self, current: str, new: str) -> bool:
        """Validate that status transition is allowed"""
        return new in self.VALID_TRANSITIONS.get(current, [])
    
    async def update_execution_status(self, execution_id: str, new_status: str, 
                                    response_data: dict = None):
        """Update execution status with validation"""
        current_execution = self.get_execution(execution_id)
        current_status = current_execution['status']
        
        if not self.validate_status_transition(current_status, new_status):
            logger.warning(f"Invalid status transition: {current_status} → {new_status}")
            return
        
        update_data = {
            'status': new_status,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Handle terminal states
        if new_status in ['SUCCESS', 'FAILED', 'CANCELLED', 'TIMEOUT']:
            update_data['completed_at'] = datetime.utcnow().isoformat()
            
            if new_status == 'SUCCESS':
                await self.process_success_completion(execution_id, response_data)
            else:
                await self.process_error_completion(execution_id, new_status, response_data)
        
        # Update database
        self.db.table('workflow_executions')\
            .update(update_data)\
            .eq('id', execution_id)\
            .execute()
```

## Background Polling System

### Execution Poller Implementation
```python
# execution_poller.py - Core monitoring service
class ExecutionPoller(DatabaseService):
    def __init__(self):
        super().__init__()
        self.poll_interval = 15  # 15 seconds
        self.max_concurrent_polls = 10
        self.amc_client = AMCAPIClientWithRetry()
    
    async def start(self):
        """Main polling loop"""
        logger.info("Starting Execution Poller Service")
        
        while True:
            try:
                await self.poll_all_pending_executions()
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Execution poller error: {e}")
                await asyncio.sleep(self.poll_interval)
    
    async def poll_all_pending_executions(self):
        """Poll status for all non-terminal executions"""
        # Get executions that need status updates
        active_executions = self.db.table('workflow_executions')\
            .select('*, workflows(*, amc_instances(*, amc_accounts(*)))')\
            .in_('status', ['PENDING', 'RUNNING'])\
            .order('created_at')\
            .execute()
        
        if not active_executions.data:
            return
        
        logger.info(f"Polling {len(active_executions.data)} active executions")
        
        # Use semaphore to control concurrent polls
        semaphore = asyncio.Semaphore(self.max_concurrent_polls)
        
        tasks = [
            self.poll_execution_with_semaphore(semaphore, execution)
            for execution in active_executions.data
        ]
        
        # Execute polls concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log any polling errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                execution_id = active_executions.data[i]['id']
                logger.error(f"Error polling execution {execution_id}: {result}")
    
    async def poll_execution_with_semaphore(self, semaphore: asyncio.Semaphore, execution: dict):
        """Poll single execution with concurrency control"""
        async with semaphore:
            return await self.poll_single_execution(execution)
    
    async def poll_single_execution(self, execution: dict):
        """Poll AMC for execution status"""
        try:
            # Extract AMC credentials
            workflow = execution['workflows']
            instance = workflow['amc_instances']
            account = instance['amc_accounts']
            
            # Validate required data
            if not execution.get('amc_execution_id'):
                raise ValueError(f"Execution {execution['id']} missing AMC execution ID")
            
            if not account:
                raise ValueError(f"Execution {execution['id']} missing account information")
            
            # Check status with AMC
            status_response = await self.amc_client.get_execution_status(
                execution_id=execution['amc_execution_id'],
                instance_id=instance['instance_id'],
                entity_id=account['account_id']
            )
            
            current_amc_status = status_response.get('status')
            current_db_status = execution['status']
            
            # Update status if changed
            if current_amc_status and current_amc_status != current_db_status:
                await self.update_execution_status(
                    execution['id'], 
                    current_amc_status, 
                    status_response
                )
                
                logger.info(f"Updated execution {execution['id']}: {current_db_status} → {current_amc_status}")
            
        except Exception as e:
            logger.error(f"Failed to poll execution {execution['id']}: {e}")
            
            # Consider marking as failed after repeated errors
            await self.handle_polling_error(execution, e)
    
    async def handle_polling_error(self, execution: dict, error: Exception):
        """Handle errors during status polling"""
        error_count = execution.get('error_count', 0) + 1
        
        # Update error tracking
        self.db.table('workflow_executions')\
            .update({
                'error_count': error_count,
                'last_error': str(error),
                'last_error_at': datetime.utcnow().isoformat()
            })\
            .eq('id', execution['id'])\
            .execute()
        
        # Mark as failed after too many errors
        if error_count >= 5:
            await self.update_execution_status(
                execution['id'], 
                'FAILED',
                {'error': f'Polling failed after {error_count} attempts: {str(error)}'}
            )
```

### Result Processing
```python
async def process_success_completion(self, execution_id: str, response_data: dict):
    """Process successful execution completion"""
    try:
        # Download results from AMC
        if 'result_url' in response_data:
            result_data = await self.download_execution_results(
                response_data['result_url']
            )
            
            # Store results in database
            self.db.table('workflow_executions')\
                .update({
                    'result_data': result_data,
                    'result_rows': len(result_data) if isinstance(result_data, list) else None,
                    'result_size_bytes': len(json.dumps(result_data)),
                    'execution_duration': response_data.get('duration_seconds')
                })\
                .eq('id', execution_id)\
                .execute()
            
            logger.info(f"Downloaded results for execution {execution_id}")
        
        # Update completion metrics
        await self.update_completion_metrics(execution_id, response_data)
        
    except Exception as e:
        logger.error(f"Error processing successful execution {execution_id}: {e}")
        # Don't change status, but log the error

async def download_execution_results(self, result_url: str) -> dict:
    """Download and parse execution results from AMC"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(result_url)
            response.raise_for_status()
            
            # Parse based on content type
            content_type = response.headers.get('content-type', '')
            
            if 'application/json' in content_type:
                return response.json()
            elif 'text/csv' in content_type:
                # Convert CSV to JSON format
                import csv
                import io
                
                csv_data = response.text
                reader = csv.DictReader(io.StringIO(csv_data))
                return list(reader)
            else:
                return {'raw_data': response.text}
                
    except Exception as e:
        logger.error(f"Failed to download results from {result_url}: {e}")
        return {'error': f'Failed to download results: {str(e)}'}
```

## Real-Time Status Updates

### Frontend Polling Hook
```typescript
// useExecutionStatus.ts - React hook for real-time updates
interface UseExecutionStatusOptions {
  executionId: string;
  enabled?: boolean;
  onStatusChange?: (status: string) => void;
  pollInterval?: number;
}

export const useExecutionStatus = ({
  executionId,
  enabled = true,
  onStatusChange,
  pollInterval = 5000
}: UseExecutionStatusOptions) => {
  const queryClient = useQueryClient();
  
  const query = useQuery({
    queryKey: ['execution-status', executionId],
    queryFn: () => executionService.getStatus(executionId),
    enabled: enabled && !!executionId,
    refetchInterval: (data) => {
      // Stop polling if execution is complete
      const terminalStates = ['SUCCESS', 'FAILED', 'CANCELLED', 'TIMEOUT'];
      return terminalStates.includes(data?.status) ? false : pollInterval;
    },
    refetchIntervalInBackground: true
  });
  
  // Callback for status changes
  useEffect(() => {
    if (query.data?.status && onStatusChange) {
      onStatusChange(query.data.status);
    }
  }, [query.data?.status, onStatusChange]);
  
  // Invalidate related queries when execution completes
  useEffect(() => {
    if (query.data?.status === 'SUCCESS') {
      queryClient.invalidateQueries(['execution-results', executionId]);
      queryClient.invalidateQueries(['workflow-executions']);
    }
  }, [query.data?.status, executionId, queryClient]);
  
  return {
    status: query.data?.status,
    isLoading: query.isLoading,
    error: query.error,
    execution: query.data,
    refetch: query.refetch
  };
};
```

### Status Display Component
```typescript
// ExecutionStatus.tsx - Visual status indicator
interface ExecutionStatusProps {
  execution: WorkflowExecution;
  showDetails?: boolean;
}

const ExecutionStatus: React.FC<ExecutionStatusProps> = ({ 
  execution, 
  showDetails = false 
}) => {
  const getStatusColor = (status: string) => {
    const colors = {
      'PENDING': 'yellow',
      'RUNNING': 'blue',
      'SUCCESS': 'green',
      'FAILED': 'red',
      'CANCELLED': 'gray',
      'TIMEOUT': 'orange'
    };
    return colors[status] || 'gray';
  };
  
  const getStatusIcon = (status: string) => {
    const icons = {
      'PENDING': '⏳',
      'RUNNING': '🔄',
      'SUCCESS': '✅',
      'FAILED': '❌',
      'CANCELLED': '⏹️',
      'TIMEOUT': '⏰'
    };
    return icons[status] || '❓';
  };
  
  const formatDuration = (startTime: string, endTime?: string) => {
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const duration = Math.floor((end.getTime() - start.getTime()) / 1000);
    
    const minutes = Math.floor(duration / 60);
    const seconds = duration % 60;
    
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };
  
  return (
    <div className="flex items-center space-x-2">
      <div className={`flex items-center space-x-1 px-2 py-1 rounded-full bg-${getStatusColor(execution.status)}-100 text-${getStatusColor(execution.status)}-800`}>
        <span>{getStatusIcon(execution.status)}</span>
        <span className="text-sm font-medium">{execution.status}</span>
      </div>
      
      {showDetails && (
        <div className="text-sm text-gray-600">
          {execution.status === 'RUNNING' && (
            <span>Running for {formatDuration(execution.created_at)}</span>
          )}
          
          {execution.status === 'SUCCESS' && execution.result_rows && (
            <span>{execution.result_rows.toLocaleString()} rows</span>
          )}
          
          {execution.status === 'FAILED' && execution.error_message && (
            <span title={execution.error_message}>Error occurred</span>
          )}
        </div>
      )}
    </div>
  );
};
```

## Error Handling and Recovery

### Error Classification
```python
class ExecutionErrorClassifier:
    ERROR_TYPES = {
        'AMC_API_ERROR': 'AMC API returned error response',
        'TIMEOUT_ERROR': 'Execution exceeded time limit',
        'AUTHENTICATION_ERROR': 'Invalid or expired tokens',
        'PERMISSION_ERROR': 'Insufficient permissions',
        'QUERY_ERROR': 'SQL query syntax or logic error',
        'RESOURCE_ERROR': 'AMC resource limits exceeded',
        'NETWORK_ERROR': 'Network connectivity issues',
        'UNKNOWN_ERROR': 'Unclassified error'
    }
    
    def classify_error(self, error_data: dict) -> str:
        """Classify error based on AMC response"""
        error_message = error_data.get('error', '').lower()
        
        if 'timeout' in error_message:
            return 'TIMEOUT_ERROR'
        elif 'authentication' in error_message or 'token' in error_message:
            return 'AUTHENTICATION_ERROR'
        elif 'permission' in error_message or 'forbidden' in error_message:
            return 'PERMISSION_ERROR'
        elif 'syntax' in error_message or 'query' in error_message:
            return 'QUERY_ERROR'
        elif 'rate limit' in error_message or 'quota' in error_message:
            return 'RESOURCE_ERROR'
        elif 'network' in error_message or 'connection' in error_message:
            return 'NETWORK_ERROR'
        else:
            return 'UNKNOWN_ERROR'
```

### Automatic Retry Logic
```python
async def handle_execution_error(self, execution: dict, error_data: dict):
    """Handle execution errors with retry logic"""
    error_type = self.error_classifier.classify_error(error_data)
    retry_count = execution.get('retry_count', 0)
    
    # Define retry strategies
    retryable_errors = ['NETWORK_ERROR', 'AMC_API_ERROR']
    max_retries = 3
    
    if error_type in retryable_errors and retry_count < max_retries:
        # Schedule retry with exponential backoff
        retry_delay = min(300, 60 * (2 ** retry_count))  # Max 5 minutes
        
        self.db.table('workflow_executions')\
            .update({
                'status': 'PENDING',
                'retry_count': retry_count + 1,
                'next_retry_at': (datetime.utcnow() + timedelta(seconds=retry_delay)).isoformat(),
                'last_error': error_data.get('error'),
                'error_type': error_type
            })\
            .eq('id', execution['id'])\
            .execute()
        
        logger.info(f"Scheduled retry {retry_count + 1} for execution {execution['id']}")
    else:
        # Mark as permanently failed
        self.db.table('workflow_executions')\
            .update({
                'status': 'FAILED',
                'error_message': error_data.get('error'),
                'error_type': error_type,
                'failed_at': datetime.utcnow().isoformat()
            })\
            .eq('id', execution['id'])\
            .execute()
```

## Performance Monitoring

### Execution Metrics
```python
class ExecutionMetrics:
    def __init__(self):
        self.metrics_buffer = []
    
    async def record_execution_metrics(self, execution_id: str, metrics: dict):
        """Record performance metrics for execution"""
        metric_data = {
            'execution_id': execution_id,
            'start_time': metrics.get('start_time'),
            'end_time': metrics.get('end_time'),
            'duration_seconds': metrics.get('duration'),
            'result_size_bytes': metrics.get('result_size'),
            'result_rows': metrics.get('result_rows'),
            'amc_processing_time': metrics.get('amc_time'),
            'network_time': metrics.get('network_time'),
            'recorded_at': datetime.utcnow().isoformat()
        }
        
        # Store in database or metrics system
        self.db.table('execution_metrics').insert(metric_data).execute()
    
    async def get_performance_stats(self, time_window: timedelta = timedelta(days=7)) -> dict:
        """Get execution performance statistics"""
        cutoff_time = datetime.utcnow() - time_window
        
        stats = self.db.rpc('get_execution_stats', {
            'start_time': cutoff_time.isoformat()
        }).execute()
        
        return stats.data[0] if stats.data else {}
```

### Health Monitoring
```python
async def check_monitoring_health(self) -> dict:
    """Check health of execution monitoring system"""
    health_data = {}
    
    # Check polling service health
    health_data['poller_status'] = await self.check_poller_health()
    
    # Check recent execution processing
    health_data['recent_activity'] = await self.check_recent_activity()
    
    # Check error rates
    health_data['error_rates'] = await self.check_error_rates()
    
    # Check AMC API connectivity
    health_data['amc_connectivity'] = await self.check_amc_connectivity()
    
    return health_data

async def check_poller_health(self) -> dict:
    """Check execution poller service health"""
    # Check if poller is processing executions
    last_poll = self.get_last_poll_time()
    poll_age = datetime.utcnow() - last_poll
    
    return {
        'status': 'healthy' if poll_age < timedelta(minutes=5) else 'unhealthy',
        'last_poll': last_poll.isoformat(),
        'poll_age_seconds': poll_age.total_seconds()
    }
```

## Testing and Debugging

### Execution Simulation
```python
# Test execution monitoring without AMC
class MockExecutionPoller(ExecutionPoller):
    def __init__(self, mock_responses: dict):
        super().__init__()
        self.mock_responses = mock_responses
    
    async def poll_single_execution(self, execution: dict):
        """Mock execution polling for testing"""
        execution_id = execution['id']
        
        if execution_id in self.mock_responses:
            mock_response = self.mock_responses[execution_id]
            await self.update_execution_status(
                execution_id,
                mock_response['status'],
                mock_response
            )
```

### Debug Tools
```python
# Debug execution monitoring issues
async def debug_execution_polling():
    """Debug tool for execution monitoring issues"""
    
    # Check stuck executions
    stuck_executions = await find_stuck_executions()
    
    # Check AMC API connectivity
    api_health = await test_amc_connectivity()
    
    # Check database connections
    db_health = await test_database_connectivity()
    
    return {
        'stuck_executions': stuck_executions,
        'amc_api_health': api_health,
        'database_health': db_health
    }

async def find_stuck_executions():
    """Find executions that may be stuck"""
    old_pending = datetime.utcnow() - timedelta(hours=1)
    old_running = datetime.utcnow() - timedelta(hours=2)
    
    stuck = self.db.table('workflow_executions')\
        .select('*')\
        .or_(
            f'and(status.eq.PENDING,created_at.lt.{old_pending.isoformat()})',
            f'and(status.eq.RUNNING,created_at.lt.{old_running.isoformat()})'
        )\
        .execute()
    
    return stuck.data
```