# Tests Specification

This is the tests coverage details for the spec detailed in @.agent-os/specs/2025-09-08-fix-workflow-execution-tracking/spec.md

> Created: 2025-09-08
> Version: 1.0.0

## Test Coverage

### Unit Tests

#### 1. HistoricalCollectionService Tests

**File**: `tests/test_historical_collection_service.py`

**Test Cases**:

```python
class TestHistoricalCollectionServiceExecutionTracking:
    
    @pytest.mark.asyncio
    async def test_collect_week_data_stores_execution_id(self):
        """Test that _collect_week_data extracts and stores execution_id"""
        # Arrange
        mock_execution_result = {
            'execution_id': 'exec-12345',
            'status': 'SUCCEEDED',
            'data': {'result': 'test_data'}
        }
        
        # Mock AMC API response
        with patch('amc_api_client_with_retry.create_workflow_execution') as mock_exec:
            mock_exec.return_value = mock_execution_result
            
            # Mock update_week_status to capture parameters
            with patch.object(service, 'update_week_status') as mock_update:
                # Act
                await service._collect_week_data(
                    collection_id='coll-123',
                    week_id='week-456',
                    workflow_data={'query': 'SELECT * FROM table'}
                )
                
                # Assert
                mock_update.assert_called_once_with(
                    collection_id='coll-123',
                    week_id='week-456',
                    status='completed',
                    data={'result': 'test_data'},
                    execution_id='exec-12345'  # Verify execution_id passed
                )
    
    @pytest.mark.asyncio
    async def test_collect_week_data_handles_missing_execution_id(self):
        """Test graceful handling when execution_id is missing from AMC response"""
        # Arrange
        mock_execution_result = {
            'status': 'SUCCEEDED',
            'data': {'result': 'test_data'}
            # execution_id is missing
        }
        
        with patch('amc_api_client_with_retry.create_workflow_execution') as mock_exec:
            mock_exec.return_value = mock_execution_result
            
            with patch.object(service, 'update_week_status') as mock_update:
                # Act
                await service._collect_week_data(
                    collection_id='coll-123',
                    week_id='week-456', 
                    workflow_data={'query': 'SELECT * FROM table'}
                )
                
                # Assert - should pass None for execution_id
                mock_update.assert_called_once_with(
                    collection_id='coll-123',
                    week_id='week-456',
                    status='completed',
                    data={'result': 'test_data'},
                    execution_id=None
                )
    
    @pytest.mark.asyncio
    async def test_collect_week_data_handles_null_execution_result(self):
        """Test handling when AMC API returns None/null"""
        with patch('amc_api_client_with_retry.create_workflow_execution') as mock_exec:
            mock_exec.return_value = None
            
            with patch.object(service, 'update_week_status') as mock_update:
                # Act
                await service._collect_week_data(
                    collection_id='coll-123',
                    week_id='week-456',
                    workflow_data={'query': 'SELECT * FROM table'}
                )
                
                # Assert - should handle gracefully
                mock_update.assert_called_once_with(
                    collection_id='coll-123', 
                    week_id='week-456',
                    status='completed',
                    data=None,
                    execution_id=None
                )
    
    @pytest.mark.asyncio 
    async def test_execution_tracking_failure_fallback(self):
        """Test fallback when execution tracking fails"""
        mock_execution_result = {'execution_id': 'exec-12345', 'data': {'result': 'test'}}
        
        with patch('amc_api_client_with_retry.create_workflow_execution') as mock_exec:
            mock_exec.return_value = mock_execution_result
            
            # Mock update_week_status to fail first time, succeed second time
            call_count = 0
            def mock_update_side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1 and 'execution_id' in kwargs:
                    raise Exception("Database error")
                return None
                
            with patch.object(service, 'update_week_status', side_effect=mock_update_side_effect) as mock_update:
                # Act
                await service._collect_week_data(
                    collection_id='coll-123',
                    week_id='week-456',
                    workflow_data={'query': 'SELECT * FROM table'}
                )
                
                # Assert - should attempt fallback without execution_id
                assert mock_update.call_count == 2
                # First call with execution_id (failed)
                # Second call without execution_id (fallback)
```

#### 2. DataCollectionService Tests

**File**: `tests/test_data_collection_service.py`

**Test Cases**:

```python
class TestDataCollectionServiceExecutionTracking:
    
    @pytest.mark.asyncio
    async def test_update_week_status_with_execution_id(self):
        """Test update_week_status properly stores execution_id"""
        # Arrange
        service = DataCollectionService()
        
        with patch.object(service, 'supabase') as mock_supabase:
            mock_table = Mock()
            mock_supabase.table.return_value = mock_table
            mock_table.update.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute.return_value = Mock()
            
            # Act
            await service.update_week_status(
                collection_id='coll-123',
                week_id='week-456',
                status='completed',
                data={'result': 'test'},
                execution_id='exec-789'
            )
            
            # Assert
            expected_update_data = {
                'status': 'completed',
                'updated_at': Any(str),
                'execution_id': 'exec-789',
                'data': {'result': 'test'}
            }
            mock_table.update.assert_called_once_with(expected_update_data)
    
    @pytest.mark.asyncio
    async def test_update_week_status_without_execution_id(self):
        """Test backward compatibility - update_week_status without execution_id"""
        service = DataCollectionService()
        
        with patch.object(service, 'supabase') as mock_supabase:
            mock_table = Mock()
            mock_supabase.table.return_value = mock_table
            mock_table.update.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute.return_value = Mock()
            
            # Act - call without execution_id parameter
            await service.update_week_status(
                collection_id='coll-123',
                week_id='week-456', 
                status='completed',
                data={'result': 'test'}
            )
            
            # Assert - execution_id should not be in update data
            call_args = mock_table.update.call_args[0][0]
            assert 'execution_id' not in call_args
            assert call_args['status'] == 'completed'
            assert call_args['data'] == {'result': 'test'}
    
    @pytest.mark.asyncio
    async def test_update_week_status_null_execution_id(self):
        """Test handling of explicit None execution_id"""
        service = DataCollectionService()
        
        with patch.object(service, 'supabase') as mock_supabase:
            mock_table = Mock()
            mock_supabase.table.return_value = mock_table
            mock_table.update.return_value = mock_table
            mock_table.eq.return_value = mock_table  
            mock_table.execute.return_value = Mock()
            
            # Act
            await service.update_week_status(
                collection_id='coll-123',
                week_id='week-456',
                status='completed', 
                execution_id=None
            )
            
            # Assert - None execution_id should not be included
            call_args = mock_table.update.call_args[0][0]
            assert 'execution_id' not in call_args
```

### Integration Tests

#### 3. End-to-End Data Collection Tests

**File**: `tests/integration/test_execution_tracking_flow.py`

**Test Cases**:

```python
class TestExecutionTrackingIntegration:
    
    @pytest.mark.asyncio
    async def test_full_collection_stores_execution_ids(self):
        """Test complete data collection flow stores execution_ids"""
        # Arrange - Create test collection
        collection_data = {
            'name': 'Test Collection',
            'workflow_id': 'workflow-123',
            'user_id': 'user-456'
        }
        
        # Act - Trigger data collection
        collection_id = await create_test_collection(collection_data)
        weeks = await generate_test_weeks(collection_id, 3)  # 3 weeks
        
        # Execute collection
        await execute_historical_collection(collection_id)
        
        # Assert - Check execution_ids are stored
        stored_weeks = await get_collection_weeks(collection_id)
        
        for week in stored_weeks:
            assert week['execution_id'] is not None
            assert week['status'] == 'completed'
            # Verify execution_id format (UUID)
            assert len(week['execution_id']) == 36
            assert week['execution_id'].count('-') == 4
    
    @pytest.mark.asyncio
    async def test_parallel_collections_maintain_separate_execution_ids(self):
        """Test multiple concurrent collections have different execution_ids"""
        # Arrange - Create multiple collections
        collections = []
        for i in range(3):
            collection_data = {'name': f'Collection {i}', 'workflow_id': f'workflow-{i}'}
            collection_id = await create_test_collection(collection_data)
            collections.append(collection_id)
        
        # Act - Execute collections concurrently
        await asyncio.gather(*[
            execute_historical_collection(coll_id) for coll_id in collections
        ])
        
        # Assert - Each collection has unique execution_ids
        all_execution_ids = []
        for collection_id in collections:
            weeks = await get_collection_weeks(collection_id)
            for week in weeks:
                assert week['execution_id'] is not None
                all_execution_ids.append(week['execution_id'])
        
        # Verify all execution_ids are unique
        assert len(all_execution_ids) == len(set(all_execution_ids))
    
    @pytest.mark.asyncio
    async def test_amc_api_failure_handling(self):
        """Test execution tracking when AMC API fails"""
        # Arrange
        collection_id = await create_test_collection({'name': 'Failure Test'})
        
        # Mock AMC API to fail
        with patch('amc_api_client_with_retry.create_workflow_execution') as mock_exec:
            mock_exec.side_effect = Exception("AMC API Error")
            
            # Act
            await execute_historical_collection(collection_id)
            
            # Assert - Weeks should be marked as failed, no execution_id
            weeks = await get_collection_weeks(collection_id)
            for week in weeks:
                assert week['status'] == 'failed'
                assert week['execution_id'] is None
                assert 'AMC API Error' in week.get('error_message', '')
```

### Database Tests

#### 4. Database Layer Tests

**File**: `tests/database/test_execution_id_storage.py`

**Test Cases**:

```python
class TestExecutionIdDatabaseStorage:
    
    async def test_execution_id_column_exists(self):
        """Verify execution_id column exists with correct properties"""
        query = """
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'report_data_weeks' 
        AND column_name = 'execution_id'
        """
        
        result = await execute_query(query)
        assert len(result) == 1
        column = result[0]
        assert column['column_name'] == 'execution_id'
        assert column['data_type'] == 'uuid'
        assert column['is_nullable'] == 'YES'
    
    async def test_execution_id_storage_and_retrieval(self):
        """Test storing and retrieving execution_id"""
        # Arrange
        test_execution_id = str(uuid.uuid4())
        week_data = {
            'collection_id': str(uuid.uuid4()),
            'week_start_date': '2025-01-01',
            'week_end_date': '2025-01-07', 
            'status': 'completed',
            'execution_id': test_execution_id
        }
        
        # Act - Insert week with execution_id
        week_id = await insert_week_data(week_data)
        retrieved_week = await get_week_by_id(week_id)
        
        # Assert
        assert retrieved_week['execution_id'] == test_execution_id
        assert isinstance(retrieved_week['execution_id'], str)
    
    async def test_null_execution_id_handling(self):
        """Test NULL execution_id values are handled properly"""
        week_data = {
            'collection_id': str(uuid.uuid4()),
            'week_start_date': '2025-01-01',
            'week_end_date': '2025-01-07',
            'status': 'completed',
            'execution_id': None
        }
        
        # Act
        week_id = await insert_week_data(week_data)
        retrieved_week = await get_week_by_id(week_id)
        
        # Assert
        assert retrieved_week['execution_id'] is None
    
    async def test_execution_id_foreign_key_relationship(self):
        """Test relationship between execution_id and workflow_executions"""
        # Create test workflow execution
        execution_data = {
            'workflow_id': str(uuid.uuid4()),
            'user_id': str(uuid.uuid4()),
            'status': 'SUCCEEDED'
        }
        execution_id = await create_test_execution(execution_data)
        
        # Create week referencing execution
        week_data = {
            'collection_id': str(uuid.uuid4()),
            'week_start_date': '2025-01-01',
            'week_end_date': '2025-01-07',
            'status': 'completed',
            'execution_id': execution_id
        }
        
        week_id = await insert_week_data(week_data)
        
        # Test JOIN query
        query = """
        SELECT rdw.id, rdw.execution_id, we.status as execution_status
        FROM report_data_weeks rdw
        JOIN workflow_executions we ON we.id = rdw.execution_id
        WHERE rdw.id = %s
        """
        
        result = await execute_query(query, [week_id])
        assert len(result) == 1
        assert result[0]['execution_id'] == execution_id
        assert result[0]['execution_status'] == 'SUCCEEDED'
```

## Mocking Requirements

### AMC API Mocking

```python
# Mock AMC API responses for testing
@pytest.fixture
def mock_amc_execution_response():
    return {
        'execution_id': 'exec-test-12345',
        'status': 'SUCCEEDED',
        'data': {
            'rows': [
                {'campaign_id': '123', 'impressions': 1000},
                {'campaign_id': '456', 'impressions': 2000}
            ]
        }
    }

@pytest.fixture
def mock_amc_execution_failure():
    return {
        'execution_id': 'exec-test-67890', 
        'status': 'FAILED',
        'error': 'Query syntax error'
    }
```

### Database Mocking

```python
# Mock Supabase responses
@pytest.fixture
def mock_supabase_update_response():
    return {
        'data': [{'id': 'week-123', 'status': 'completed'}],
        'error': None
    }

# Mock database connection
@pytest.fixture
def mock_database_service(monkeypatch):
    mock_db = AsyncMock()
    monkeypatch.setattr('amc_manager.services.database_service.DatabaseService.supabase', mock_db)
    return mock_db
```

### Service Layer Mocking

```python
# Mock service dependencies
@pytest.fixture
def mock_historical_collection_service():
    service = Mock()
    service._collect_week_data = AsyncMock()
    service.update_week_status = AsyncMock()
    return service

@pytest.fixture  
def mock_data_collection_service():
    service = Mock()
    service.update_week_status = AsyncMock()
    service.get_collection_weeks = AsyncMock()
    return service
```

## Performance Tests

### Load Testing

```python
class TestExecutionTrackingPerformance:
    
    @pytest.mark.performance
    async def test_batch_execution_id_updates(self):
        """Test performance of updating multiple weeks with execution_ids"""
        # Arrange - Create 100 weeks
        collection_id = str(uuid.uuid4())
        weeks = []
        for i in range(100):
            week_data = {'collection_id': collection_id, 'week_num': i}
            week_id = await create_test_week(week_data)
            weeks.append(week_id)
        
        # Act - Measure update performance
        start_time = time.time()
        
        tasks = []
        for week_id in weeks:
            task = update_week_status(
                collection_id, week_id, 'completed', 
                execution_id=str(uuid.uuid4())
            )
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Assert - Should complete within reasonable time
        assert execution_time < 10.0  # 10 seconds max for 100 updates
        assert execution_time / len(weeks) < 0.1  # < 100ms per update
```

## Test Data Setup

### Test Fixtures

```python
@pytest.fixture
async def test_collection():
    """Create a test data collection"""
    collection_data = {
        'name': 'Test Execution Tracking Collection',
        'workflow_id': str(uuid.uuid4()),
        'user_id': str(uuid.uuid4()),
        'instance_id': str(uuid.uuid4())
    }
    collection_id = await create_collection(collection_data)
    yield collection_id
    await cleanup_collection(collection_id)

@pytest.fixture
async def test_weeks(test_collection):
    """Create test weeks for collection"""
    weeks = []
    for i in range(5):
        week_data = {
            'collection_id': test_collection,
            'week_start_date': f'2025-01-{(i*7)+1:02d}',
            'week_end_date': f'2025-01-{(i*7)+7:02d}',
            'status': 'pending'
        }
        week_id = await create_week(week_data)
        weeks.append(week_id)
    return weeks
```

### Cleanup Procedures

```python
async def cleanup_test_data():
    """Clean up test data after execution tracking tests"""
    # Remove test collections
    await execute_query("DELETE FROM report_data_collections WHERE name LIKE 'Test%'")
    
    # Remove test workflow executions
    await execute_query("DELETE FROM workflow_executions WHERE id LIKE 'exec-test-%'")
    
    # Remove orphaned weeks
    await execute_query("""
        DELETE FROM report_data_weeks 
        WHERE collection_id NOT IN (
            SELECT id FROM report_data_collections
        )
    """)
```