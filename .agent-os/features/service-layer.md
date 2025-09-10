# Service Layer Architecture

## Overview

RecomAMP follows a layered architecture with a robust service layer that provides business logic abstraction, data access patterns, error handling, and cross-cutting concerns. The service layer acts as an intermediary between API endpoints and database operations, ensuring consistency and reusability across the application.

## Service Layer Design Principles

### Core Principles
1. **Single Responsibility** - Each service handles one domain area
2. **Dependency Injection** - Services are loosely coupled and testable
3. **Error Handling** - Consistent error patterns across all services
4. **Database Abstraction** - Database-agnostic business logic
5. **Transaction Management** - Automatic transaction handling
6. **Connection Resilience** - Automatic retry and reconnection logic

## Base Service Classes

### DatabaseService Base Class
```python
# amc_manager/services/database_service.py
import asyncio
from functools import wraps
from supabase import create_client, Client
from amc_manager.core.config import settings
import logging

logger = logging.getLogger(__name__)

def with_connection_retry(max_retries=3, delay=1):
    """Decorator for automatic database connection retry"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(self, *args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Check if this is a connection-related error
                    if self._is_connection_error(e) and attempt < max_retries - 1:
                        logger.warning(f"Database connection error, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
                        continue
                    else:
                        # Re-raise if not connection error or max retries reached
                        raise
            
            raise last_exception
        return wrapper
    return decorator

class DatabaseService:
    """Base service class with database connection and common utilities"""
    
    def __init__(self):
        self.db: Client = self._initialize_database()
        self._connection_pool = None
    
    def _initialize_database(self) -> Client:
        """Initialize Supabase client with connection pooling"""
        return create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY,
            options={
                'auto_refresh_token': True,
                'persist_session': False,
                'detect_session_in_url': False
            }
        )
    
    def _is_connection_error(self, error: Exception) -> bool:
        """Check if error is connection-related"""
        error_msg = str(error).lower()
        connection_indicators = [
            'connection', 'timeout', 'network', 'unreachable',
            'could not connect', 'connection refused', 'connection reset'
        ]
        return any(indicator in error_msg for indicator in connection_indicators)
    
    @with_connection_retry()
    async def execute_query(self, query_func):
        """Execute database query with retry logic"""
        return query_func()
    
    def handle_database_error(self, error: Exception, context: str = ""):
        """Standardized database error handling"""
        logger.error(f"Database error in {context}: {str(error)}")
        
        # Map database errors to appropriate HTTP errors
        error_msg = str(error).lower()
        
        if 'unique constraint' in error_msg:
            raise HTTPException(status_code=409, detail="Resource already exists")
        elif 'foreign key constraint' in error_msg:
            raise HTTPException(status_code=400, detail="Referenced resource not found")
        elif 'not null constraint' in error_msg:
            raise HTTPException(status_code=400, detail="Required field missing")
        elif 'permission denied' in error_msg:
            raise HTTPException(status_code=403, detail="Access denied")
        else:
            raise HTTPException(status_code=500, detail="Internal database error")
    
    def paginate_query(self, query, page: int = 1, page_size: int = 50):
        """Add pagination to query"""
        offset = (page - 1) * page_size
        return query.range(offset, offset + page_size - 1)
    
    def filter_by_user(self, query, user_id: str, user_field: str = 'user_id'):
        """Add user filtering to query for data isolation"""
        return query.eq(user_field, user_id)
```

### Service Registration and Dependency Injection
```python
# amc_manager/services/service_registry.py
from typing import Dict, Type, Any
from abc import ABC, abstractmethod

class ServiceRegistry:
    """Service registry for dependency injection"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._service_classes: Dict[str, Type] = {}
    
    def register(self, service_name: str, service_class: Type):
        """Register service class"""
        self._service_classes[service_name] = service_class
    
    def get_service(self, service_name: str) -> Any:
        """Get service instance (singleton pattern)"""
        if service_name not in self._services:
            if service_name not in self._service_classes:
                raise ValueError(f"Service {service_name} not registered")
            
            service_class = self._service_classes[service_name]
            self._services[service_name] = service_class()
        
        return self._services[service_name]
    
    def clear(self):
        """Clear all service instances (for testing)"""
        self._services.clear()

# Global service registry
service_registry = ServiceRegistry()

# Service registration decorator
def service(name: str):
    """Decorator to register service"""
    def decorator(cls):
        service_registry.register(name, cls)
        return cls
    return decorator

# Dependency injection decorator
def inject_service(service_name: str):
    """Decorator to inject service dependency"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            service = service_registry.get_service(service_name)
            return await func(self, service, *args, **kwargs)
        return wrapper
    return decorator
```

## Core Service Implementations

### User Service
```python
# amc_manager/services/user_service.py
from amc_manager.services.database_service import DatabaseService, with_connection_retry
from amc_manager.services.token_service import TokenService
from datetime import datetime, timedelta

@service('user_service')
class UserService(DatabaseService):
    """User management and profile operations"""
    
    def __init__(self):
        super().__init__()
        self.token_service = TokenService()
    
    @with_connection_retry()
    async def create_user(self, user_data: dict) -> dict:
        """Create new user with encrypted tokens"""
        try:
            # Encrypt OAuth tokens
            encrypted_access_token = None
            encrypted_refresh_token = None
            
            if user_data.get('access_token'):
                encrypted_access_token = self.token_service.encrypt_token(
                    user_data['access_token']
                )
            
            if user_data.get('refresh_token'):
                encrypted_refresh_token = self.token_service.encrypt_token(
                    user_data['refresh_token']
                )
            
            # Create user record
            user = self.db.table('users').insert({
                'email': user_data['email'],
                'full_name': user_data.get('full_name'),
                'amazon_user_id': user_data.get('amazon_user_id'),
                'encrypted_access_token': encrypted_access_token,
                'encrypted_refresh_token': encrypted_refresh_token,
                'token_expires_at': user_data.get('token_expires_at'),
                'timezone': user_data.get('timezone', 'UTC'),
                'email_notifications': user_data.get('email_notifications', True),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'last_login_at': datetime.utcnow().isoformat(),
                'is_active': True
            }).execute()
            
            return user.data[0]
            
        except Exception as e:
            self.handle_database_error(e, "create_user")
    
    @with_connection_retry()
    async def get_user_by_id(self, user_id: str) -> dict:
        """Get user by ID with token decryption"""
        try:
            result = self.db.table('users')\
                .select('*')\
                .eq('id', user_id)\
                .eq('is_active', True)\
                .execute()
            
            if not result.data:
                raise HTTPException(status_code=404, detail="User not found")
            
            user = result.data[0]
            
            # Decrypt tokens if present (for internal use only)
            if user.get('encrypted_access_token'):
                try:
                    user['access_token'] = self.token_service.decrypt_token(
                        user['encrypted_access_token']
                    )
                except Exception as e:
                    logger.warning(f"Failed to decrypt access token for user {user_id}: {e}")
                    user['access_token'] = None
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            self.handle_database_error(e, "get_user_by_id")
    
    @with_connection_retry()
    async def update_user_tokens(self, user_id: str, token_data: dict) -> dict:
        """Update user OAuth tokens"""
        try:
            update_data = {
                'updated_at': datetime.utcnow().isoformat()
            }
            
            if 'access_token' in token_data:
                update_data['encrypted_access_token'] = self.token_service.encrypt_token(
                    token_data['access_token']
                )
            
            if 'refresh_token' in token_data:
                update_data['encrypted_refresh_token'] = self.token_service.encrypt_token(
                    token_data['refresh_token']
                )
            
            if 'expires_at' in token_data:
                update_data['token_expires_at'] = token_data['expires_at']
            
            result = self.db.table('users')\
                .update(update_data)\
                .eq('id', user_id)\
                .execute()
            
            return result.data[0]
            
        except Exception as e:
            self.handle_database_error(e, "update_user_tokens")
    
    @with_connection_retry()
    async def get_users_with_expiring_tokens(self, minutes_ahead: int = 10) -> List[dict]:
        """Get users whose tokens expire soon"""
        try:
            cutoff_time = datetime.utcnow() + timedelta(minutes=minutes_ahead)
            
            result = self.db.table('users')\
                .select('id, email, encrypted_refresh_token, token_expires_at')\
                .lte('token_expires_at', cutoff_time.isoformat())\
                .is_('encrypted_refresh_token', 'not.null')\
                .eq('is_active', True)\
                .execute()
            
            return result.data
            
        except Exception as e:
            self.handle_database_error(e, "get_users_with_expiring_tokens")
```

### Workflow Service
```python
# amc_manager/services/workflow_service.py
from amc_manager.services.database_service import DatabaseService, with_connection_retry

@service('workflow_service')
class WorkflowService(DatabaseService):
    """Workflow and query management"""
    
    def __init__(self):
        super().__init__()
        self.parameter_processor = ParameterProcessor()
        self.amc_client = None  # Injected via dependency
    
    @inject_service('amc_api_service')
    @with_connection_retry()
    async def create_workflow(self, amc_api_service, workflow_data: dict, 
                            user_id: str, instance_id: str) -> dict:
        """Create new workflow"""
        try:
            # Validate workflow data
            validation_errors = await self.validate_workflow_data(workflow_data)
            if validation_errors:
                raise HTTPException(status_code=400, detail=validation_errors)
            
            # Verify instance access
            await self.verify_instance_access(user_id, instance_id)
            
            # Create workflow record
            workflow = self.db.table('workflows').insert({
                'name': workflow_data['name'],
                'description': workflow_data.get('description'),
                'sql_query': workflow_data['sql_query'],
                'user_id': user_id,
                'instance_id': instance_id,
                'template_id': workflow_data.get('template_id'),
                'parameters': workflow_data.get('parameters', {}),
                'tags': workflow_data.get('tags', []),
                'is_public': workflow_data.get('is_public', False),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }).execute()
            
            return workflow.data[0]
            
        except HTTPException:
            raise
        except Exception as e:
            self.handle_database_error(e, "create_workflow")
    
    @with_connection_retry()
    async def execute_workflow(self, workflow_id: str, user_id: str, 
                             parameters: dict = None) -> dict:
        """Execute workflow and create execution record"""
        try:
            # Get workflow with instance info
            workflow = await self.get_workflow_with_instance(workflow_id, user_id)
            
            # Process parameters
            processed_sql = self.parameter_processor.substitute_parameters(
                workflow['sql_query'],
                parameters or workflow.get('parameters', {})
            )
            
            # Create execution record
            execution = self.db.table('workflow_executions').insert({
                'workflow_id': workflow_id,
                'user_id': user_id,
                'status': 'PENDING',
                'parameters': parameters or {},
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }).execute()
            
            execution_id = execution.data[0]['id']
            
            # Submit to AMC (via injected service)
            amc_result = await self.submit_to_amc(workflow, processed_sql, execution_id)
            
            # Update execution with AMC execution ID
            self.db.table('workflow_executions')\
                .update({
                    'amc_execution_id': amc_result['execution_id'],
                    'status': 'RUNNING',
                    'started_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                })\
                .eq('id', execution_id)\
                .execute()
            
            # Update workflow last executed time
            self.db.table('workflows')\
                .update({'last_executed_at': datetime.utcnow().isoformat()})\
                .eq('id', workflow_id)\
                .execute()
            
            return {
                **execution.data[0],
                'amc_execution_id': amc_result['execution_id'],
                'status': 'RUNNING'
            }
            
        except Exception as e:
            # Update execution status to failed if it was created
            if 'execution_id' in locals():
                self.db.table('workflow_executions')\
                    .update({
                        'status': 'FAILED',
                        'error_message': str(e),
                        'completed_at': datetime.utcnow().isoformat()
                    })\
                    .eq('id', execution_id)\
                    .execute()
            
            self.handle_database_error(e, "execute_workflow")
    
    async def validate_workflow_data(self, workflow_data: dict) -> List[str]:
        """Validate workflow data structure"""
        errors = []
        
        required_fields = ['name', 'sql_query']
        for field in required_fields:
            if not workflow_data.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Validate SQL query
        sql_query = workflow_data.get('sql_query', '')
        if sql_query and not sql_query.strip().lower().startswith('select'):
            errors.append("SQL query must start with SELECT")
        
        return errors
    
    @with_connection_retry()
    async def get_workflow_with_instance(self, workflow_id: str, user_id: str) -> dict:
        """Get workflow with AMC instance information"""
        try:
            result = self.db.table('workflows')\
                .select('*, amc_instances(*, amc_accounts(*))')\
                .eq('id', workflow_id)\
                .eq('user_id', user_id)\
                .execute()
            
            if not result.data:
                raise HTTPException(status_code=404, detail="Workflow not found")
            
            return result.data[0]
            
        except HTTPException:
            raise
        except Exception as e:
            self.handle_database_error(e, "get_workflow_with_instance")
```

## Service Layer Patterns

### Transaction Management
```python
# amc_manager/services/transaction_service.py
from contextlib import asynccontextmanager
import asyncio

class TransactionService(DatabaseService):
    """Service for managing database transactions"""
    
    @asynccontextmanager
    async def transaction(self):
        """Context manager for database transactions"""
        # Note: Supabase doesn't directly support transactions in Python client
        # This is a pattern for when using direct PostgreSQL connections
        
        connection = None
        try:
            connection = await self.get_connection()
            transaction = connection.transaction()
            await transaction.start()
            
            yield connection
            
            await transaction.commit()
            
        except Exception as e:
            if connection:
                await transaction.rollback()
            raise
        finally:
            if connection:
                await connection.close()
    
    async def execute_in_transaction(self, operations: List[callable]):
        """Execute multiple operations in a single transaction"""
        async with self.transaction() as conn:
            results = []
            for operation in operations:
                result = await operation(conn)
                results.append(result)
            return results
```

### Event-Driven Service Communication
```python
# amc_manager/services/event_service.py
from typing import Dict, List, Callable
import asyncio

class EventService:
    """Service for event-driven communication between services"""
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_name: str, handler: Callable):
        """Subscribe to event"""
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)
    
    async def publish(self, event_name: str, data: dict):
        """Publish event to all subscribers"""
        if event_name in self._handlers:
            tasks = []
            for handler in self._handlers[event_name]:
                if asyncio.iscoroutinefunction(handler):
                    tasks.append(handler(data))
                else:
                    # Run sync handlers in executor
                    tasks.append(asyncio.get_event_loop().run_in_executor(
                        None, handler, data
                    ))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

# Usage example
@service('notification_service')
class NotificationService(DatabaseService):
    def __init__(self):
        super().__init__()
        # Subscribe to workflow completion events
        event_service.subscribe('workflow_completed', self.send_completion_notification)
    
    async def send_completion_notification(self, event_data: dict):
        """Send notification when workflow completes"""
        # Implementation for sending notifications
        pass
```

### Service Caching Layer
```python
# amc_manager/services/cache_service.py
import redis
import json
from typing import Any, Optional
from datetime import timedelta

@service('cache_service')
class CacheService:
    """Centralized caching service"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.redis_client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL"""
        try:
            self.redis_client.setex(
                key, 
                ttl, 
                json.dumps(value, default=str)
            )
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
    
    async def delete(self, key: str):
        """Delete value from cache"""
        try:
            self.redis_client.delete(key)
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
    
    def cache_key(self, *parts) -> str:
        """Generate consistent cache key"""
        return ':'.join(str(part) for part in parts)

# Cache decorator for service methods
def cached(ttl: int = 300, key_generator: Callable = None):
    """Decorator for caching service method results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            cache_service = service_registry.get_service('cache_service')
            
            # Generate cache key
            if key_generator:
                cache_key = key_generator(self, *args, **kwargs)
            else:
                cache_key = cache_service.cache_key(
                    func.__name__, 
                    *args, 
                    *sorted(kwargs.items())
                )
            
            # Try cache first
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(self, *args, **kwargs)
            await cache_service.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator
```

## Service Layer Testing

### Service Test Base Class
```python
# tests/services/test_base.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from amc_manager.services.service_registry import service_registry

class ServiceTestBase:
    """Base class for service testing"""
    
    @pytest.fixture(autouse=True)
    def setup_test_services(self):
        """Setup test environment"""
        # Clear service registry
        service_registry.clear()
        
        # Mock database connections
        self.mock_db = MagicMock()
        self.mock_redis = AsyncMock()
        
        # Setup test data
        self.test_user_id = "test-user-123"
        self.test_instance_id = "test-instance-456"
        
        yield
        
        # Cleanup
        service_registry.clear()
    
    def mock_database_response(self, data: list, count: int = None):
        """Helper to mock database responses"""
        mock_result = MagicMock()
        mock_result.data = data
        mock_result.count = count or len(data)
        return mock_result
```

### Service Integration Testing
```python
# tests/services/test_workflow_service.py
import pytest
from amc_manager.services.workflow_service import WorkflowService
from tests.services.test_base import ServiceTestBase

class TestWorkflowService(ServiceTestBase):
    
    @pytest.fixture
    def workflow_service(self):
        """Create workflow service instance"""
        service = WorkflowService()
        service.db = self.mock_db
        return service
    
    @pytest.mark.asyncio
    async def test_create_workflow(self, workflow_service):
        """Test workflow creation"""
        # Setup mock response
        workflow_data = {
            'name': 'Test Workflow',
            'sql_query': 'SELECT * FROM campaigns',
            'description': 'Test description'
        }
        
        expected_result = {'id': 'workflow-123', **workflow_data}
        self.mock_db.table.return_value.insert.return_value.execute.return_value = \
            self.mock_database_response([expected_result])
        
        # Execute test
        result = await workflow_service.create_workflow(
            workflow_data, 
            self.test_user_id, 
            self.test_instance_id
        )
        
        # Assertions
        assert result['id'] == 'workflow-123'
        assert result['name'] == 'Test Workflow'
        self.mock_db.table.assert_called_with('workflows')
    
    @pytest.mark.asyncio
    async def test_workflow_validation_errors(self, workflow_service):
        """Test workflow validation"""
        # Test missing required fields
        invalid_data = {'description': 'Missing name and sql_query'}
        
        with pytest.raises(HTTPException) as exc_info:
            await workflow_service.create_workflow(
                invalid_data, 
                self.test_user_id, 
                self.test_instance_id
            )
        
        assert exc_info.value.status_code == 400
        assert 'Missing required field' in exc_info.value.detail
```

## Performance Monitoring

### Service Performance Metrics
```python
# amc_manager/services/metrics_service.py
import time
from functools import wraps
from typing import Dict
import asyncio

@service('metrics_service')
class MetricsService:
    """Service performance monitoring and metrics"""
    
    def __init__(self):
        self.metrics: Dict[str, list] = {}
        self.counters: Dict[str, int] = {}
    
    def record_duration(self, metric_name: str, duration: float):
        """Record execution duration"""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        
        self.metrics[metric_name].append(duration)
        
        # Keep only last 1000 measurements
        if len(self.metrics[metric_name]) > 1000:
            self.metrics[metric_name] = self.metrics[metric_name][-1000:]
    
    def increment_counter(self, counter_name: str, value: int = 1):
        """Increment counter metric"""
        if counter_name not in self.counters:
            self.counters[counter_name] = 0
        self.counters[counter_name] += value
    
    def get_metrics_summary(self, metric_name: str) -> dict:
        """Get metrics summary"""
        if metric_name not in self.metrics:
            return {}
        
        durations = self.metrics[metric_name]
        if not durations:
            return {}
        
        return {
            'count': len(durations),
            'avg': sum(durations) / len(durations),
            'min': min(durations),
            'max': max(durations),
            'recent_avg': sum(durations[-100:]) / min(len(durations), 100)
        }

def monitor_performance(metric_name: str = None):
    """Decorator to monitor service method performance"""
    def decorator(func):
        nonlocal metric_name
        if not metric_name:
            metric_name = f"{func.__module__}.{func.__name__}"
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            metrics_service = service_registry.get_service('metrics_service')
            
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                metrics_service.increment_counter(f"{metric_name}.success")
                return result
            except Exception as e:
                metrics_service.increment_counter(f"{metric_name}.error")
                raise
            finally:
                duration = time.time() - start_time
                metrics_service.record_duration(metric_name, duration)
        
        return wrapper
    return decorator
```

## Service Layer Best Practices

### Error Handling Standards
```python
class ServiceError(Exception):
    """Base service error"""
    pass

class ValidationError(ServiceError):
    """Data validation error"""
    pass

class BusinessLogicError(ServiceError):
    """Business rule violation"""
    pass

class ExternalServiceError(ServiceError):
    """External service communication error"""
    pass

def handle_service_errors(func):
    """Standard error handling for service methods"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except BusinessLogicError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except ExternalServiceError as e:
            raise HTTPException(status_code=503, detail=str(e))
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
    return wrapper
```

### Service Documentation Standards
```python
class ExampleService(DatabaseService):
    """
    Example service demonstrating documentation standards.
    
    This service handles example domain operations including:
    - Data validation and processing
    - Business logic enforcement
    - External service integration
    
    Attributes:
        external_client: Client for external API
        cache_duration: Default cache duration in seconds
    """
    
    def __init__(self):
        super().__init__()
        self.external_client = ExternalAPIClient()
        self.cache_duration = 300
    
    @monitor_performance()
    @cached(ttl=300)
    @handle_service_errors
    async def process_data(self, data: dict, user_id: str) -> dict:
        """
        Process data with validation and business logic.
        
        Args:
            data: Input data dictionary
            user_id: User identifier for access control
            
        Returns:
            dict: Processed data with additional metadata
            
        Raises:
            ValidationError: If input data is invalid
            BusinessLogicError: If business rules are violated
            ExternalServiceError: If external service calls fail
            
        Example:
            >>> service = ExampleService()
            >>> result = await service.process_data(
            ...     {'name': 'test'}, 
            ...     'user-123'
            ... )
            >>> print(result['status'])
            'processed'
        """
        # Implementation details...
        pass
```

This service layer architecture provides a robust, scalable, and maintainable foundation for RecomAMP's business logic, ensuring consistency across all application domains while maintaining flexibility for future enhancements.