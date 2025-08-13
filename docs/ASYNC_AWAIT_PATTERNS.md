# Async/Await Patterns in FastAPI

## Overview
This document describes the correct async/await patterns for the RecomAMP backend, particularly for AMC execution services and database operations.

## Key Principles

### 1. No asyncio.run() in Async Context
When you're already in an async function (like a FastAPI endpoint), you cannot use `asyncio.run()`. This will cause the error:
```
RuntimeError: asyncio.run() cannot be called from a running event loop
```

### 2. Async All the Way Down
If a function calls async operations, it should be async itself:

**❌ WRONG:**
```python
def execute_workflow(self, ...):
    result = asyncio.run(self._execute_real_amc_query(...))  # ERROR!
    return result
```

**✅ CORRECT:**
```python
async def execute_workflow(self, ...):
    result = await self._execute_real_amc_query(...)
    return result
```

## Fixed Patterns (2025-08-13)

### AMC Execution Service
File: `amc_manager/services/amc_execution_service.py`

```python
class AMCExecutionService:
    async def execute_workflow(self, workflow_id: str, user_id: str, parameters: dict = None) -> dict:
        """Execute a workflow - now fully async"""
        # ... preparation code ...
        
        if use_real_api:
            # Call async method with await
            execution_response = await self._execute_real_amc_query(
                instance_id=instance_id,
                amc_workflow_id=amc_workflow_id,
                parameters=parameters,
                user_id=user_id
            )
        else:
            execution_response = self._execute_mock_query(...)
        
        return execution_response

    async def poll_and_update_execution(self, execution_id: str, user_id: str) -> dict:
        """Poll AMC for execution status - now async"""
        # ... fetch execution data ...
        
        if use_real_api:
            status = await self._poll_real_amc_status(
                instance_id=instance_id,
                amc_execution_id=amc_execution_id,
                user_id=user_id
            )
        else:
            status = self._poll_mock_status(...)
        
        return status

    async def _execute_real_amc_query(self, ...):
        """Actually execute query in AMC - now async"""
        # This method is now async to match the calling pattern
        # Even though it doesn't have await calls internally
        return response
```

### API Endpoints
File: `amc_manager/api/supabase/workflows.py`

```python
@router.post("/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    parameters: dict = Body({}),
    instance_id: str = Body(None),
    current_user: dict = Depends(get_current_user)
):
    """Execute a workflow - endpoint is async"""
    try:
        # Use await when calling async service methods
        result = await amc_execution_service.execute_workflow(
            workflow_id=workflow_id,
            user_id=current_user['id'],
            parameters=parameters,
            instance_id=instance_id
        )
        return result
    except Exception as e:
        logger.error(f"Error executing workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Background Polling Service
File: `amc_manager/services/execution_status_poller.py`

```python
class ExecutionStatusPoller:
    async def _poll_executions(self):
        """Poll all pending/running executions"""
        # ... fetch executions ...
        
        for execution in response.data:
            try:
                # The service method is now async, so we await it
                status = await amc_execution_service.poll_and_update_execution(
                    execution_id=execution_id,
                    user_id=user_id
                )
                
                if status:
                    logger.info(f"Updated status: {status}")
                    
            except Exception as e:
                logger.error(f"Error polling: {e}")
```

## Database Operations

### Supabase Client Usage
The Supabase client operations are synchronous, so they don't need await:

```python
# Synchronous Supabase operations
response = client.table('workflows').select('*').eq('id', workflow_id).single().execute()

# Can be used in async functions without await
async def get_workflow(workflow_id: str):
    response = client.table('workflows').select('*').eq('id', workflow_id).single().execute()
    return response.data
```

## Common Mistakes to Avoid

### 1. Mixing Sync and Async
```python
# ❌ WRONG: Sync function trying to call async
def process_data():
    result = await fetch_data()  # SyntaxError!

# ✅ CORRECT: Make the function async
async def process_data():
    result = await fetch_data()
```

### 2. Using asyncio.run() in FastAPI
```python
# ❌ WRONG: In a FastAPI endpoint
@router.get("/data")
async def get_data():
    result = asyncio.run(fetch_async_data())  # RuntimeError!

# ✅ CORRECT: Use await directly
@router.get("/data")
async def get_data():
    result = await fetch_async_data()
```

### 3. Forgetting await
```python
# ❌ WRONG: Calling async without await
async def process():
    data = fetch_async_data()  # Returns coroutine object!

# ✅ CORRECT: Use await
async def process():
    data = await fetch_async_data()
```

## Testing Async Code

When testing async functions, use pytest-asyncio:

```python
import pytest

@pytest.mark.asyncio
async def test_execute_workflow():
    result = await amc_execution_service.execute_workflow(
        workflow_id="test_id",
        user_id="user_123"
    )
    assert result is not None
```

## Summary

1. If a function uses `await`, it must be `async`
2. If calling an async function, use `await` (not `asyncio.run()`)
3. FastAPI endpoints can be async and should use `await` for async operations
4. Background tasks in FastAPI handle async automatically
5. Supabase client operations are synchronous (no await needed)

This pattern ensures proper async execution flow throughout the application without event loop conflicts.