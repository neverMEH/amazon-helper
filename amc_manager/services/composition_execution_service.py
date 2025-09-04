"""Service for executing flow compositions with orchestration and parameter mapping"""

from typing import Optional, Dict, Any, List, Set, Tuple
from datetime import datetime
import uuid
import json
import asyncio
import networkx as nx
from collections import defaultdict

from ..services.db_service import DatabaseService, with_connection_retry
from ..services.template_execution_service import TemplateExecutionService
from ..services.flow_composition_service import FlowCompositionService
from ..services.parameter_engine import ParameterEngine
from ..core.logger_simple import get_logger

logger = get_logger(__name__)


class CompositionExecutionService(DatabaseService):
    """Service for executing flow compositions by orchestrating multiple template executions"""
    
    def __init__(self):
        super().__init__()
        self.template_service = TemplateExecutionService()
        self.composition_service = FlowCompositionService()
        self.parameter_engine = ParameterEngine()
    
    @with_connection_retry
    async def execute_composition(
        self,
        composition_id: str,
        instance_id: str,
        user_id: str,
        parameters: Dict[str, Any],
        schedule_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a flow composition by running nodes in dependency order
        
        Args:
            composition_id: Composition ID to execute
            instance_id: AMC instance ID for execution
            user_id: User executing the composition
            parameters: Flow-level parameters
            schedule_id: Optional schedule ID if executed from schedule
            
        Returns:
            Composition execution record with status
        """
        try:
            # Get composition with all details
            composition = self.composition_service.get_composition_by_id(
                composition_id=composition_id,
                user_id=user_id,
                include_nodes=True,
                include_connections=True
            )
            
            if not composition:
                raise Exception(f"Composition not found: {composition_id}")
            
            # Validate DAG structure
            nodes = composition.get('nodes', [])
            connections = composition.get('connections', [])
            
            if not self.composition_service.validate_dag(nodes, connections):
                raise Exception("Composition contains circular dependencies")
            
            # Calculate execution order
            execution_order = self.composition_service.calculate_execution_order(nodes, connections)
            if not execution_order:
                raise Exception("Failed to calculate execution order")
            
            # Create master composition execution record
            execution_id = f"comp_exec_{uuid.uuid4().hex[:8]}"
            
            composition_execution = {
                'id': str(uuid.uuid4()),
                'execution_id': execution_id,
                'composition_id': composition['id'],
                'user_id': user_id,
                'instance_id': instance_id,
                'status': 'running',
                'started_at': datetime.utcnow().isoformat(),
                'total_nodes': len(nodes),
                'completed_nodes': 0,
                'failed_nodes': 0,
                'parameters': parameters,
                'execution_summary': {}
            }
            
            # Insert composition execution record
            exec_result = self.client.table('template_flow_composition_executions')\
                .insert(composition_execution)\
                .execute()
            
            if not exec_result.data:
                raise Exception("Failed to create composition execution record")
            
            comp_exec_record = exec_result.data[0]
            comp_exec_id = comp_exec_record['id']
            
            # Build dependency graph and parameter mappings
            node_dependencies = self._build_dependencies(nodes, connections)
            node_results = {}  # Store results from each node execution
            
            # Get execution config from composition
            config = composition.get('config', {})
            execution_mode = config.get('execution_mode', 'sequential')
            error_handling = config.get('error_handling', 'fail_fast')
            max_parallel = config.get('max_parallel', 3)
            
            # Execute nodes in dependency order
            if execution_mode == 'sequential':
                node_execution_results = await self._execute_sequential(
                    nodes=nodes,
                    connections=connections,
                    execution_order=execution_order,
                    instance_id=instance_id,
                    user_id=user_id,
                    flow_parameters=parameters,
                    comp_exec_id=comp_exec_id,
                    error_handling=error_handling
                )
            else:
                # Parallel execution with dependency resolution
                node_execution_results = await self._execute_parallel(
                    nodes=nodes,
                    connections=connections,
                    node_dependencies=node_dependencies,
                    instance_id=instance_id,
                    user_id=user_id,
                    flow_parameters=parameters,
                    comp_exec_id=comp_exec_id,
                    error_handling=error_handling,
                    max_parallel=max_parallel
                )
            
            # Calculate summary statistics
            completed_count = sum(1 for r in node_execution_results.values() 
                                if r.get('status') == 'completed')
            failed_count = sum(1 for r in node_execution_results.values() 
                             if r.get('status') == 'failed')
            
            # Update composition execution with results
            final_status = 'completed' if failed_count == 0 else 'failed'
            
            update_data = {
                'status': final_status,
                'completed_at': datetime.utcnow().isoformat(),
                'completed_nodes': completed_count,
                'failed_nodes': failed_count,
                'execution_summary': node_execution_results,
                'result_summary': self._aggregate_results(node_execution_results)
            }
            
            self.client.table('template_flow_composition_executions')\
                .update(update_data)\
                .eq('id', comp_exec_id)\
                .execute()
            
            return {
                'composition_execution_id': execution_id,
                'composition_id': composition['composition_id'],
                'status': final_status,
                'total_nodes': len(nodes),
                'completed_nodes': completed_count,
                'failed_nodes': failed_count,
                'started_at': composition_execution['started_at'],
                'completed_at': update_data['completed_at'],
                'nodes': [
                    {
                        'node_id': node_id,
                        'status': result.get('status', 'pending'),
                        'execution_id': result.get('execution_id'),
                        'error': result.get('error')
                    }
                    for node_id, result in node_execution_results.items()
                ]
            }
            
        except Exception as e:
            logger.error(f"Error executing composition {composition_id}: {e}")
            raise
    
    async def _execute_sequential(
        self,
        nodes: List[Dict[str, Any]],
        connections: List[Dict[str, Any]],
        execution_order: Dict[str, int],
        instance_id: str,
        user_id: str,
        flow_parameters: Dict[str, Any],
        comp_exec_id: str,
        error_handling: str
    ) -> Dict[str, Any]:
        """Execute nodes sequentially in dependency order"""
        
        node_results = {}
        node_by_id = {node['node_id']: node for node in nodes}
        
        # Sort nodes by execution order
        sorted_nodes = sorted(nodes, key=lambda n: execution_order.get(n['node_id'], 999))
        
        for node in sorted_nodes:
            node_id = node['node_id']
            
            try:
                # Get node parameters
                node_params = await self._prepare_node_parameters(
                    node=node,
                    connections=connections,
                    flow_parameters=flow_parameters,
                    node_results=node_results
                )
                
                # Execute node template
                logger.info(f"Executing node {node_id} with template {node['template_id']}")
                
                result = await self.template_service.execute_template(
                    template_id=node['template_id'],
                    instance_id=instance_id,
                    user_id=user_id,
                    parameters=node_params,
                    composition_execution_id=comp_exec_id,
                    composition_node_id=node_id
                )
                
                node_results[node_id] = {
                    'status': 'completed',
                    'execution_id': result.get('execution_id'),
                    'workflow_id': result.get('workflow_id'),
                    'result': result
                }
                
            except Exception as e:
                logger.error(f"Error executing node {node_id}: {e}")
                
                node_results[node_id] = {
                    'status': 'failed',
                    'error': str(e)
                }
                
                # Handle error based on strategy
                if error_handling == 'fail_fast':
                    # Stop execution on first error
                    break
                elif error_handling == 'continue':
                    # Continue with other nodes
                    continue
        
        return node_results
    
    async def _execute_parallel(
        self,
        nodes: List[Dict[str, Any]],
        connections: List[Dict[str, Any]],
        node_dependencies: Dict[str, Set[str]],
        instance_id: str,
        user_id: str,
        flow_parameters: Dict[str, Any],
        comp_exec_id: str,
        error_handling: str,
        max_parallel: int
    ) -> Dict[str, Any]:
        """Execute nodes in parallel with dependency resolution"""
        
        node_results = {}
        node_by_id = {node['node_id']: node for node in nodes}
        pending_nodes = set(node['node_id'] for node in nodes)
        running_tasks = {}
        
        async def execute_node(node_id: str):
            """Execute a single node"""
            node = node_by_id[node_id]
            
            try:
                # Get node parameters
                node_params = await self._prepare_node_parameters(
                    node=node,
                    connections=connections,
                    flow_parameters=flow_parameters,
                    node_results=node_results
                )
                
                # Execute node template
                logger.info(f"Executing node {node_id} with template {node['template_id']}")
                
                result = await self.template_service.execute_template(
                    template_id=node['template_id'],
                    instance_id=instance_id,
                    user_id=user_id,
                    parameters=node_params,
                    composition_execution_id=comp_exec_id,
                    composition_node_id=node_id
                )
                
                return {
                    'status': 'completed',
                    'execution_id': result.get('execution_id'),
                    'workflow_id': result.get('workflow_id'),
                    'result': result
                }
                
            except Exception as e:
                logger.error(f"Error executing node {node_id}: {e}")
                return {
                    'status': 'failed',
                    'error': str(e)
                }
        
        # Execute nodes with dependency resolution
        while pending_nodes or running_tasks:
            # Find nodes ready to execute (all dependencies completed)
            ready_nodes = []
            for node_id in pending_nodes:
                deps = node_dependencies.get(node_id, set())
                if all(dep in node_results for dep in deps):
                    # Check if all dependencies succeeded
                    failed_deps = [dep for dep in deps 
                                 if node_results.get(dep, {}).get('status') == 'failed']
                    
                    if failed_deps and error_handling == 'fail_fast':
                        # Skip this node if dependencies failed
                        node_results[node_id] = {
                            'status': 'skipped',
                            'error': f"Dependencies failed: {failed_deps}"
                        }
                        pending_nodes.remove(node_id)
                    else:
                        ready_nodes.append(node_id)
            
            # Start execution for ready nodes (respecting parallel limit)
            for node_id in ready_nodes[:max(0, max_parallel - len(running_tasks))]:
                pending_nodes.remove(node_id)
                task = asyncio.create_task(execute_node(node_id))
                running_tasks[node_id] = task
            
            # Wait for at least one task to complete
            if running_tasks:
                done, pending = await asyncio.wait(
                    running_tasks.values(),
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Process completed tasks
                for task in done:
                    # Find which node this task belongs to
                    for node_id, node_task in list(running_tasks.items()):
                        if node_task == task:
                            result = await task
                            node_results[node_id] = result
                            del running_tasks[node_id]
                            
                            # Check for fail_fast
                            if error_handling == 'fail_fast' and result['status'] == 'failed':
                                # Cancel remaining tasks
                                for remaining_task in running_tasks.values():
                                    remaining_task.cancel()
                                # Mark pending nodes as skipped
                                for pending_node_id in pending_nodes:
                                    node_results[pending_node_id] = {
                                        'status': 'skipped',
                                        'error': 'Execution stopped due to failure'
                                    }
                                return node_results
            
            # Small delay to prevent busy waiting
            if not ready_nodes and running_tasks:
                await asyncio.sleep(0.1)
        
        return node_results
    
    async def _prepare_node_parameters(
        self,
        node: Dict[str, Any],
        connections: List[Dict[str, Any]],
        flow_parameters: Dict[str, Any],
        node_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare parameters for a node execution by combining flow parameters
        and mapped parameters from upstream nodes
        """
        
        # Start with node's configured parameters
        node_config = node.get('config', {})
        node_params = node_config.get('parameters', {}).copy()
        
        # Override with flow-level parameters
        node_params.update(flow_parameters)
        
        # Find connections targeting this node
        incoming_connections = [
            conn for conn in connections
            if conn['target_node_id'] == node['node_id']
        ]
        
        # Process parameter mappings from connections
        for connection in incoming_connections:
            source_node_id = connection['source_node_id']
            mapping_config = connection.get('mapping_config', {})
            
            # Get source node's results
            source_result = node_results.get(source_node_id, {})
            if source_result.get('status') != 'completed':
                continue
            
            # Apply field mappings
            field_mappings = mapping_config.get('field_mappings', [])
            for mapping in field_mappings:
                source_field = mapping.get('source')
                target_field = mapping.get('target')
                transform = mapping.get('transform', 'direct')
                
                # Get value from source node results
                # This would need to fetch actual query results from S3/storage
                source_value = self._extract_field_value(
                    source_result.get('result', {}),
                    source_field
                )
                
                if source_value is not None:
                    # Apply transformation
                    transformed_value = self._apply_transform(
                        source_value,
                        transform
                    )
                    
                    # Set in target parameters
                    node_params[target_field] = transformed_value
        
        # Handle special "mapped_from_node" parameter type
        mapped_params = node_config.get('mapped_parameters', {})
        for param_name, mapping_info in mapped_params.items():
            from_node = mapping_info.get('from_node')
            field = mapping_info.get('field')
            transform = mapping_info.get('transform', 'direct')
            
            if from_node in node_results:
                source_result = node_results[from_node]
                if source_result.get('status') == 'completed':
                    source_value = self._extract_field_value(
                        source_result.get('result', {}),
                        field
                    )
                    
                    if source_value is not None:
                        node_params[param_name] = self._apply_transform(
                            source_value,
                            transform
                        )
        
        return node_params
    
    def _build_dependencies(
        self,
        nodes: List[Dict[str, Any]],
        connections: List[Dict[str, Any]]
    ) -> Dict[str, Set[str]]:
        """Build dependency map from connections"""
        
        dependencies = defaultdict(set)
        
        for connection in connections:
            source = connection['source_node_id']
            target = connection['target_node_id']
            dependencies[target].add(source)
        
        # Ensure all nodes are in the map
        for node in nodes:
            if node['node_id'] not in dependencies:
                dependencies[node['node_id']] = set()
        
        return dict(dependencies)
    
    def _extract_field_value(self, result: Dict[str, Any], field_path: str) -> Any:
        """Extract value from result using field path (supports dot notation)"""
        
        # For now, return a placeholder
        # In production, this would fetch actual query results from S3
        # and extract the specified field
        return result.get(field_path)
    
    def _apply_transform(self, value: Any, transform: str) -> Any:
        """Apply transformation to a value"""
        
        if transform == 'direct':
            return value
        elif transform == 'to_array':
            if isinstance(value, list):
                return value
            return [value] if value is not None else []
        elif transform == 'to_string':
            return str(value) if value is not None else ''
        elif transform == 'to_number':
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0
        elif transform == 'to_object':
            if isinstance(value, dict):
                return value
            return {'value': value}
        else:
            return value
    
    def _aggregate_results(self, node_results: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate results from all nodes into a summary"""
        
        summary = {
            'total_nodes': len(node_results),
            'successful_nodes': [],
            'failed_nodes': [],
            'skipped_nodes': []
        }
        
        for node_id, result in node_results.items():
            status = result.get('status')
            if status == 'completed':
                summary['successful_nodes'].append({
                    'node_id': node_id,
                    'execution_id': result.get('execution_id')
                })
            elif status == 'failed':
                summary['failed_nodes'].append({
                    'node_id': node_id,
                    'error': result.get('error')
                })
            elif status == 'skipped':
                summary['skipped_nodes'].append({
                    'node_id': node_id,
                    'reason': result.get('error')
                })
        
        return summary
    
    @with_connection_retry
    def get_composition_execution_status(
        self,
        execution_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get the status of a composition execution"""
        
        try:
            result = self.client.table('template_flow_composition_executions')\
                .select('*')\
                .eq('execution_id', execution_id)\
                .eq('user_id', user_id)\
                .single()\
                .execute()
            
            return result.data if result.data else None
            
        except Exception as e:
            logger.error(f"Error getting composition execution status: {e}")
            return None
    
    @with_connection_retry
    def cancel_composition_execution(
        self,
        execution_id: str,
        user_id: str
    ) -> bool:
        """Cancel a running composition execution"""
        
        try:
            # Update status to cancelled
            result = self.client.table('template_flow_composition_executions')\
                .update({
                    'status': 'cancelled',
                    'completed_at': datetime.utcnow().isoformat()
                })\
                .eq('execution_id', execution_id)\
                .eq('user_id', user_id)\
                .eq('status', 'running')\
                .execute()
            
            if result.data:
                # TODO: Cancel individual node executions
                # This would need to interact with AMC API to cancel running queries
                logger.info(f"Cancelled composition execution: {execution_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling composition execution: {e}")
            return False


# Global instance
composition_execution_service = CompositionExecutionService()