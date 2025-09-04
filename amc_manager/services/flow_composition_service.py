"""Service for managing Flow Compositions with CRUD operations"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import uuid
import json
import networkx as nx
from ..services.db_service import DatabaseService, with_connection_retry
from ..core.logger_simple import get_logger

logger = get_logger(__name__)


class FlowCompositionService(DatabaseService):
    """Service for managing flow compositions extending existing DatabaseService patterns"""
    
    def __init__(self):
        super().__init__()
    
    @with_connection_retry
    def list_compositions(
        self,
        user_id: str,
        search: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_public: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List flow compositions with filtering and search
        
        Args:
            user_id: Current user ID for access control
            search: Search in name and description
            tags: Filter by tags
            is_public: Filter public/private compositions
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            Dict containing compositions and metadata
        """
        try:
            # Build base query - user can see public compositions or their own
            query = self.client.table('template_flow_compositions').select(
                '''
                id,
                composition_id,
                name,
                description,
                tags,
                is_public,
                is_active,
                created_by,
                created_at,
                updated_at,
                execution_count,
                last_executed_at
                ''',
                count='exact'
            )
            
            # Apply RLS-style filtering
            if is_public is True:
                query = query.eq('is_public', True)
            elif is_public is False:
                query = query.eq('created_by', user_id).eq('is_public', False)
            else:
                # Show both public and user's private compositions
                query = query.or_(f"is_public.eq.true,created_by.eq.{user_id}")
            
            # Active compositions only
            query = query.eq('is_active', True)
            
            if search:
                # Search in name and description
                query = query.or_(f"name.ilike.%{search}%,description.ilike.%{search}%")
            
            if tags:
                # Filter by tags (contains all specified tags)
                for tag in tags:
                    query = query.contains('tags', [tag])
            
            # Add pagination and ordering
            query = query.order('updated_at', desc=True)
            query = query.range(offset, offset + limit - 1)
            
            # Execute query
            result = query.execute()
            
            compositions = result.data or []
            total_count = result.count or 0
            
            # Enrich with node count and template info
            if compositions:
                composition_ids = [c['id'] for c in compositions]
                
                # Get node counts
                nodes_result = self.client.table('template_flow_nodes')\
                    .select('composition_id, template_id')\
                    .in_('composition_id', composition_ids)\
                    .execute()
                
                # Count nodes and collect template IDs per composition
                node_counts = {}
                template_ids_by_comp = {}
                
                for node in nodes_result.data or []:
                    comp_id = node['composition_id']
                    template_id = node['template_id']
                    
                    node_counts[comp_id] = node_counts.get(comp_id, 0) + 1
                    
                    if comp_id not in template_ids_by_comp:
                        template_ids_by_comp[comp_id] = set()
                    template_ids_by_comp[comp_id].add(template_id)
                
                # Add enriched data to compositions
                for comp in compositions:
                    comp_id = comp['id']
                    comp['node_count'] = node_counts.get(comp_id, 0)
                    comp['template_ids'] = list(template_ids_by_comp.get(comp_id, set()))
            
            return {
                'compositions': compositions,
                'total_count': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + limit) < total_count
            }
            
        except Exception as e:
            logger.error(f"Error listing compositions: {e}")
            raise
    
    @with_connection_retry
    def get_composition_by_id(
        self,
        composition_id: str,
        user_id: Optional[str] = None,
        include_nodes: bool = True,
        include_connections: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get a single composition with all details
        
        Args:
            composition_id: Composition ID (UUID or string identifier)
            user_id: Current user ID for access control
            include_nodes: Include node details with templates
            include_connections: Include connection details
            
        Returns:
            Composition with full details or None if not found/unauthorized
        """
        try:
            # Determine query based on ID format
            if self._is_valid_uuid(composition_id):
                query = self.client.table('template_flow_compositions')\
                    .select('*')\
                    .eq('id', composition_id)
            else:
                query = self.client.table('template_flow_compositions')\
                    .select('*')\
                    .eq('composition_id', composition_id)
            
            # Apply access control
            if user_id:
                query = query.or_(f"is_public.eq.true,created_by.eq.{user_id}")
            else:
                query = query.eq('is_public', True)
            
            query = query.eq('is_active', True).single()
            result = query.execute()
            
            if not result.data:
                return None
            
            composition = result.data
            
            # Get nodes with template details
            if include_nodes:
                nodes_result = self.client.table('template_flow_nodes')\
                    .select('*, query_flow_templates(*)')\
                    .eq('composition_id', composition['id'])\
                    .order('execution_order')\
                    .execute()
                
                composition['nodes'] = nodes_result.data or []
            
            # Get connections
            if include_connections:
                connections_result = self.client.table('template_flow_connections')\
                    .select('*')\
                    .eq('composition_id', composition['id'])\
                    .execute()
                
                composition['connections'] = connections_result.data or []
            
            return composition
            
        except Exception as e:
            logger.error(f"Error getting composition {composition_id}: {e}")
            return None
    
    @with_connection_retry
    def create_composition(
        self,
        composition_data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Create a new flow composition
        
        Args:
            composition_data: Composition metadata and configuration
            user_id: Creating user ID
            
        Returns:
            Created composition with ID
        """
        try:
            # Add creator and timestamps
            composition_data['created_by'] = user_id
            composition_data['created_at'] = datetime.utcnow().isoformat()
            composition_data['updated_at'] = datetime.utcnow().isoformat()
            composition_data['is_active'] = True
            
            # Ensure composition_id follows pattern
            if 'composition_id' not in composition_data:
                composition_data['composition_id'] = self._generate_composition_id(
                    composition_data.get('name', 'untitled')
                )
            elif not composition_data['composition_id'].startswith('comp_'):
                raise ValueError("composition_id must start with 'comp_' prefix")
            
            # Create composition
            composition_result = self.client.table('template_flow_compositions')\
                .insert(composition_data)\
                .execute()
            
            if not composition_result.data:
                raise Exception("Failed to create composition")
            
            return composition_result.data[0]
            
        except Exception as e:
            logger.error(f"Error creating composition: {e}")
            raise
    
    @with_connection_retry
    def update_composition(
        self,
        composition_id: str,
        updates: Dict[str, Any],
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing composition (only by creator)
        
        Args:
            composition_id: Composition ID to update
            updates: Fields to update
            user_id: User attempting update
            
        Returns:
            Updated composition
        """
        try:
            # Check ownership
            composition = self.get_composition_by_id(composition_id, user_id, 
                                                   include_nodes=False, include_connections=False)
            if not composition or composition['created_by'] != user_id:
                raise Exception("Composition not found or unauthorized")
            
            # Update timestamp
            updates['updated_at'] = datetime.utcnow().isoformat()
            
            # Protect certain fields
            protected_fields = ['id', 'composition_id', 'created_by', 'created_at']
            for field in protected_fields:
                updates.pop(field, None)
            
            # Update composition
            result = self.client.table('template_flow_compositions')\
                .update(updates)\
                .eq('id', composition['id'])\
                .execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Error updating composition {composition_id}: {e}")
            raise
    
    @with_connection_retry
    def delete_composition(
        self,
        composition_id: str,
        user_id: str
    ) -> bool:
        """
        Soft delete a composition (only by creator)
        
        Args:
            composition_id: Composition ID to delete
            user_id: User attempting deletion
            
        Returns:
            True if deleted successfully
        """
        try:
            # Check ownership
            composition = self.get_composition_by_id(composition_id, user_id,
                                                   include_nodes=False, include_connections=False)
            if not composition or composition['created_by'] != user_id:
                raise Exception("Composition not found or unauthorized")
            
            # Soft delete by setting is_active to false
            result = self.client.table('template_flow_compositions')\
                .update({'is_active': False, 'updated_at': datetime.utcnow().isoformat()})\
                .eq('id', composition['id'])\
                .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error deleting composition {composition_id}: {e}")
            return False
    
    @with_connection_retry
    def add_node_to_composition(
        self,
        composition_id: str,
        node_data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Add a node to a composition
        
        Args:
            composition_id: Composition UUID
            node_data: Node configuration data
            user_id: User adding the node
            
        Returns:
            Created node record
        """
        try:
            # Verify composition ownership
            composition = self.get_composition_by_id(composition_id, user_id,
                                                   include_nodes=False, include_connections=False)
            if not composition or composition['created_by'] != user_id:
                raise Exception("Composition not found or unauthorized")
            
            # Add composition reference and timestamps
            node_data['composition_id'] = composition['id']
            node_data['created_at'] = datetime.utcnow().isoformat()
            node_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Create node
            result = self.client.table('template_flow_nodes')\
                .insert(node_data)\
                .execute()
            
            if not result.data:
                raise Exception("Failed to create node")
            
            # Update composition timestamp
            self.client.table('template_flow_compositions')\
                .update({'updated_at': datetime.utcnow().isoformat()})\
                .eq('id', composition['id'])\
                .execute()
            
            return result.data[0]
            
        except Exception as e:
            logger.error(f"Error adding node to composition {composition_id}: {e}")
            raise
    
    @with_connection_retry
    def update_node(
        self,
        composition_id: str,
        node_id: str,
        updates: Dict[str, Any],
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Update a node in a composition
        
        Args:
            composition_id: Composition UUID
            node_id: Node ID to update
            updates: Fields to update
            user_id: User attempting update
            
        Returns:
            Updated node
        """
        try:
            # Verify composition ownership
            composition = self.get_composition_by_id(composition_id, user_id,
                                                   include_nodes=False, include_connections=False)
            if not composition or composition['created_by'] != user_id:
                raise Exception("Composition not found or unauthorized")
            
            # Add timestamp
            updates['updated_at'] = datetime.utcnow().isoformat()
            
            # Update node
            result = self.client.table('template_flow_nodes')\
                .update(updates)\
                .eq('composition_id', composition['id'])\
                .eq('node_id', node_id)\
                .execute()
            
            if result.data:
                # Update composition timestamp
                self.client.table('template_flow_compositions')\
                    .update({'updated_at': datetime.utcnow().isoformat()})\
                    .eq('id', composition['id'])\
                    .execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Error updating node {node_id} in composition {composition_id}: {e}")
            raise
    
    @with_connection_retry
    def remove_node_from_composition(
        self,
        composition_id: str,
        node_id: str,
        user_id: str
    ) -> bool:
        """
        Remove a node from a composition
        
        Args:
            composition_id: Composition UUID
            node_id: Node ID to remove
            user_id: User removing the node
            
        Returns:
            True if removed successfully
        """
        try:
            # Verify composition ownership
            composition = self.get_composition_by_id(composition_id, user_id,
                                                   include_nodes=False, include_connections=False)
            if not composition or composition['created_by'] != user_id:
                raise Exception("Composition not found or unauthorized")
            
            # Remove node (cascade will handle connections)
            result = self.client.table('template_flow_nodes')\
                .delete()\
                .eq('composition_id', composition['id'])\
                .eq('node_id', node_id)\
                .execute()
            
            # Update composition timestamp
            self.client.table('template_flow_compositions')\
                .update({'updated_at': datetime.utcnow().isoformat()})\
                .eq('id', composition['id'])\
                .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error removing node {node_id} from composition {composition_id}: {e}")
            return False
    
    @with_connection_retry
    def create_connection(
        self,
        composition_id: str,
        connection_data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Create a connection between nodes in a composition
        
        Args:
            composition_id: Composition UUID
            connection_data: Connection configuration data
            user_id: User creating the connection
            
        Returns:
            Created connection record
        """
        try:
            # Verify composition ownership
            composition = self.get_composition_by_id(composition_id, user_id,
                                                   include_nodes=False, include_connections=False)
            if not composition or composition['created_by'] != user_id:
                raise Exception("Composition not found or unauthorized")
            
            # Add composition reference and timestamp
            connection_data['composition_id'] = composition['id']
            connection_data['created_at'] = datetime.utcnow().isoformat()
            
            # Create connection
            result = self.client.table('template_flow_connections')\
                .insert(connection_data)\
                .execute()
            
            if not result.data:
                raise Exception("Failed to create connection")
            
            # Update composition timestamp
            self.client.table('template_flow_compositions')\
                .update({'updated_at': datetime.utcnow().isoformat()})\
                .eq('id', composition['id'])\
                .execute()
            
            return result.data[0]
            
        except Exception as e:
            logger.error(f"Error creating connection in composition {composition_id}: {e}")
            raise
    
    @with_connection_retry
    def remove_connection(
        self,
        composition_id: str,
        connection_id: str,
        user_id: str
    ) -> bool:
        """
        Remove a connection from a composition
        
        Args:
            composition_id: Composition UUID
            connection_id: Connection ID to remove
            user_id: User removing the connection
            
        Returns:
            True if removed successfully
        """
        try:
            # Verify composition ownership
            composition = self.get_composition_by_id(composition_id, user_id,
                                                   include_nodes=False, include_connections=False)
            if not composition or composition['created_by'] != user_id:
                raise Exception("Composition not found or unauthorized")
            
            # Remove connection
            result = self.client.table('template_flow_connections')\
                .delete()\
                .eq('composition_id', composition['id'])\
                .eq('connection_id', connection_id)\
                .execute()
            
            # Update composition timestamp
            self.client.table('template_flow_compositions')\
                .update({'updated_at': datetime.utcnow().isoformat()})\
                .eq('id', composition['id'])\
                .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error removing connection {connection_id} from composition {composition_id}: {e}")
            return False
    
    def validate_dag(
        self,
        nodes: List[Dict[str, Any]],
        connections: List[Dict[str, Any]]
    ) -> bool:
        """
        Validate that the composition forms a valid DAG (no cycles)
        
        Args:
            nodes: List of node configurations
            connections: List of connection configurations
            
        Returns:
            True if valid DAG, False if cycles detected
        """
        try:
            # Create directed graph
            graph = nx.DiGraph()
            
            # Add nodes
            for node in nodes:
                graph.add_node(node['node_id'])
            
            # Add edges
            for connection in connections:
                graph.add_edge(
                    connection['source_node_id'],
                    connection['target_node_id']
                )
            
            # Check for cycles
            return nx.is_directed_acyclic_graph(graph)
            
        except Exception as e:
            logger.error(f"Error validating DAG: {e}")
            return False
    
    def calculate_execution_order(
        self,
        nodes: List[Dict[str, Any]],
        connections: List[Dict[str, Any]]
    ) -> Optional[Dict[str, int]]:
        """
        Calculate execution order using topological sorting
        
        Args:
            nodes: List of node configurations
            connections: List of connection configurations
            
        Returns:
            Dict mapping node_id to execution order, or None if invalid
        """
        try:
            # Create directed graph
            graph = nx.DiGraph()
            
            # Add nodes
            for node in nodes:
                graph.add_node(node['node_id'])
            
            # Add edges
            for connection in connections:
                graph.add_edge(
                    connection['source_node_id'],
                    connection['target_node_id']
                )
            
            # Perform topological sort
            if nx.is_directed_acyclic_graph(graph):
                topo_order = list(nx.topological_sort(graph))
                return {node_id: i for i, node_id in enumerate(topo_order)}
            else:
                return None
            
        except Exception as e:
            logger.error(f"Error calculating execution order: {e}")
            return None
    
    @with_connection_retry
    def get_composition_execution_summary(
        self,
        composition_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get execution summary for a composition using the database view
        
        Args:
            composition_id: Composition UUID
            user_id: Current user ID for access control
            
        Returns:
            Execution summary or None if not found/unauthorized
        """
        try:
            # Verify access
            composition = self.get_composition_by_id(composition_id, user_id,
                                                   include_nodes=False, include_connections=False)
            if not composition:
                return None
            
            # Get summary from view
            result = self.client.table('composition_execution_summary')\
                .select('*')\
                .eq('composition_id', composition['id'])\
                .single()\
                .execute()
            
            return result.data if result.data else None
            
        except Exception as e:
            logger.error(f"Error getting execution summary for {composition_id}: {e}")
            return None
    
    # Helper methods
    def _is_valid_uuid(self, value: str) -> bool:
        """Check if a string is a valid UUID"""
        try:
            uuid.UUID(str(value))
            return True
        except ValueError:
            return False
    
    def _generate_composition_id(self, name: str) -> str:
        """Generate a composition_id from composition name"""
        import re
        # Convert to lowercase, replace spaces with underscores, remove special chars
        comp_id = name.lower()
        comp_id = re.sub(r'[^a-z0-9\s_-]', '', comp_id)
        comp_id = re.sub(r'\s+', '_', comp_id)
        comp_id = re.sub(r'[_-]+', '_', comp_id)
        comp_id = comp_id.strip('_')
        
        # Add timestamp suffix and comp_ prefix
        timestamp = datetime.utcnow().strftime('%Y%m%d')
        return f"comp_{comp_id}_{timestamp}"


# Global instance
flow_composition_service = FlowCompositionService()