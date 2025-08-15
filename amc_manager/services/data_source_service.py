"""
AMC Data Source Service
Handles operations for AMC schema documentation and field definitions
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from .db_service import DatabaseService as SupabaseService

logger = logging.getLogger(__name__)


class DataSourceService(SupabaseService):
    """Service for managing AMC data source schemas"""
    
    def list_data_sources(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List AMC data sources with optional filtering
        
        Args:
            category: Filter by category
            search: Search term for full-text search
            tags: Filter by tags
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            List of data sources with enhanced metadata for AMC
        """
        try:
            query = self.client.table('amc_data_sources').select('*')
            
            if category:
                query = query.eq('category', category)
            
            if tags:
                # Filter by tags using JSONB containment
                query = query.contains('tags', json.dumps(tags))
            
            if search:
                # Use the search function for full-text search
                result = self.client.rpc('search_amc_schemas', {'search_query': search}).execute()
                if result.data:
                    schema_ids = [r['schema_id'] for r in result.data]
                    query = query.in_('schema_id', schema_ids)
            
            query = query.order('category').order('name')
            query = query.range(offset, offset + limit - 1)
            
            result = query.execute()
            
            # Get field and example counts for each data source
            for item in result.data:
                # Parse JSON fields
                if item.get('data_sources'):
                    item['data_sources'] = json.loads(item['data_sources']) if isinstance(item['data_sources'], str) else item['data_sources']
                if item.get('tags'):
                    item['tags'] = json.loads(item['tags']) if isinstance(item['tags'], str) else item['tags']
                if item.get('availability'):
                    item['availability'] = json.loads(item['availability']) if isinstance(item['availability'], str) else item['availability']
                
            # Batch fetch counts and metadata for all data sources to avoid N+1 queries
            if result.data:
                data_source_ids = [item['id'] for item in result.data]
                
                # Get detailed field information including dimension/metric split
                try:
                    fields_result = self.client.table('amc_schema_fields')\
                        .select('data_source_id, dimension_or_metric, field_name')\
                        .in_('data_source_id', data_source_ids)\
                        .execute()
                    
                    # Count dimensions and metrics per data source
                    dimension_count_map = {}
                    metric_count_map = {}
                    audience_capabilities_map = {}
                    
                    if fields_result.data:
                        for field in fields_result.data:
                            ds_id = field['data_source_id']
                            
                            # Count by type
                            if field['dimension_or_metric'] == 'Dimension':
                                dimension_count_map[ds_id] = dimension_count_map.get(ds_id, 0) + 1
                            else:  # Metric
                                metric_count_map[ds_id] = metric_count_map.get(ds_id, 0) + 1
                            
                            # Determine audience capabilities based on field names
                            if ds_id not in audience_capabilities_map:
                                audience_capabilities_map[ds_id] = set()
                            
                            field_lower = field['field_name'].lower()
                            if 'user_id' in field_lower or 'customer' in field_lower:
                                audience_capabilities_map[ds_id].add('User Targeting')
                            if 'conversion' in field_lower or 'purchase' in field_lower:
                                audience_capabilities_map[ds_id].add('Purchase Behavior')
                            if 'impression' in field_lower or 'view' in field_lower:
                                audience_capabilities_map[ds_id].add('Ad Engagement')
                            if 'cart' in field_lower or 'basket' in field_lower:
                                audience_capabilities_map[ds_id].add('Cart Analysis')
                            if 'click' in field_lower:
                                audience_capabilities_map[ds_id].add('Click Behavior')
                            if 'campaign' in field_lower:
                                audience_capabilities_map[ds_id].add('Campaign Targeting')
                                
                except Exception as e:
                    logger.warning(f"Failed to get field details: {e}")
                    dimension_count_map = {}
                    metric_count_map = {}
                    audience_capabilities_map = {}
                
                # Get relationships to determine joinable sources
                try:
                    relationships_result = self.client.table('amc_schema_relationships')\
                        .select('source_schema_id, target_schema_id, relationship_type, target:amc_data_sources!target_schema_id(schema_id, name)')\
                        .in_('source_schema_id', data_source_ids)\
                        .eq('relationship_type', 'joins_with')\
                        .execute()
                    
                    joinable_sources_map = {}
                    relationship_count_map = {}
                    
                    if relationships_result.data:
                        for rel in relationships_result.data:
                            source_id = rel['source_schema_id']
                            
                            # Count relationships
                            relationship_count_map[source_id] = relationship_count_map.get(source_id, 0) + 1
                            
                            # Track joinable sources
                            if source_id not in joinable_sources_map:
                                joinable_sources_map[source_id] = []
                            
                            if rel.get('target') and len(joinable_sources_map[source_id]) < 5:
                                joinable_sources_map[source_id].append({
                                    'schema_id': rel['target']['schema_id'],
                                    'name': rel['target']['name']
                                })
                                
                except Exception as e:
                    logger.warning(f"Failed to get relationships: {e}")
                    joinable_sources_map = {}
                    relationship_count_map = {}
                
                # Single query for all example counts
                try:
                    example_counts_result = self.client.table('amc_query_examples')\
                        .select('data_source_id, id')\
                        .in_('data_source_id', data_source_ids)\
                        .execute()
                    
                    # Count examples per data source
                    example_count_map = {}
                    if example_counts_result.data:
                        for example in example_counts_result.data:
                            ds_id = example['data_source_id']
                            example_count_map[ds_id] = example_count_map.get(ds_id, 0) + 1
                except Exception as e:
                    logger.warning(f"Failed to get example counts: {e}")
                    example_count_map = {}
                
                # Apply all metadata to each data source
                for item in result.data:
                    data_source_id = item['id']
                    
                    # Set dimension and metric counts
                    item['dimension_count'] = dimension_count_map.get(data_source_id, 0)
                    item['metric_count'] = metric_count_map.get(data_source_id, 0)
                    item['field_count'] = item['dimension_count'] + item['metric_count']
                    
                    # Set audience capabilities
                    capabilities = audience_capabilities_map.get(data_source_id, set())
                    item['audience_capabilities'] = list(capabilities)[:4]  # Limit to 4 for display
                    
                    # Set joinable sources
                    item['joinable_sources'] = joinable_sources_map.get(data_source_id, [])
                    item['relationship_count'] = relationship_count_map.get(data_source_id, 0)
                    
                    # Set example count with fallback
                    item['example_count'] = example_count_map.get(data_source_id, 0)
                    
                    # Determine data freshness based on category
                    # These are typical AMC data lags
                    if 'real-time' in item.get('name', '').lower():
                        item['data_lag_days'] = 0
                        item['update_frequency'] = 'Real-time'
                    elif item.get('category') == 'Conversion':
                        item['data_lag_days'] = 14
                        item['update_frequency'] = 'Daily'
                    elif item.get('category') == 'Attribution':
                        item['data_lag_days'] = 7
                        item['update_frequency'] = 'Daily'
                    else:
                        item['data_lag_days'] = 14
                        item['update_frequency'] = 'Daily'
                    
                    # Calculate complexity based on field count
                    field_count = item['field_count']
                    if field_count < 20:
                        item['complexity'] = 'simple'
                    elif field_count < 50:
                        item['complexity'] = 'medium'
                    else:
                        item['complexity'] = 'complex'
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error listing data sources: {str(e)}")
            raise
    
    def get_data_source(self, schema_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single data source by schema ID
        
        Args:
            schema_id: The schema identifier
            
        Returns:
            Data source details or None
        """
        try:
            result = self.client.table('amc_data_sources').select('*').eq('schema_id', schema_id).single().execute()
            
            if result.data:
                # Parse JSON fields
                if result.data.get('data_sources'):
                    result.data['data_sources'] = json.loads(result.data['data_sources']) if isinstance(result.data['data_sources'], str) else result.data['data_sources']
                if result.data.get('tags'):
                    result.data['tags'] = json.loads(result.data['tags']) if isinstance(result.data['tags'], str) else result.data['tags']
                if result.data.get('availability'):
                    result.data['availability'] = json.loads(result.data['availability']) if isinstance(result.data['availability'], str) else result.data['availability']
                
                return result.data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting data source {schema_id}: {str(e)}")
            return None
    
    def get_schema_fields(
        self,
        schema_id: str,
        dimension_or_metric: Optional[str] = None,
        aggregation_threshold: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get fields for a data source
        
        Args:
            schema_id: The schema identifier
            dimension_or_metric: Filter by type (Dimension/Metric)
            aggregation_threshold: Filter by aggregation threshold
            
        Returns:
            List of fields
        """
        try:
            # First get the data source ID
            ds_result = self.client.table('amc_data_sources').select('id').eq('schema_id', schema_id).single().execute()
            
            if not ds_result.data:
                return []
            
            data_source_id = ds_result.data['id']
            
            # Query fields
            query = self.client.table('amc_schema_fields').select('*').eq('data_source_id', data_source_id)
            
            if dimension_or_metric:
                query = query.eq('dimension_or_metric', dimension_or_metric)
            
            if aggregation_threshold:
                query = query.eq('aggregation_threshold', aggregation_threshold)
            
            query = query.order('field_order').order('field_name')
            
            result = query.execute()
            
            # Parse JSON examples
            for field in result.data:
                if field.get('examples'):
                    field['examples'] = json.loads(field['examples']) if isinstance(field['examples'], str) else field['examples']
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error getting fields for {schema_id}: {str(e)}")
            return []
    
    def get_query_examples(
        self,
        schema_id: str,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get query examples for a data source
        
        Args:
            schema_id: The schema identifier
            category: Filter by example category
            
        Returns:
            List of query examples
        """
        try:
            # First get the data source ID
            ds_result = self.client.table('amc_data_sources').select('id').eq('schema_id', schema_id).single().execute()
            
            if not ds_result.data:
                return []
            
            data_source_id = ds_result.data['id']
            
            # Query examples
            query = self.client.table('amc_query_examples').select('*').eq('data_source_id', data_source_id)
            
            if category:
                query = query.eq('category', category)
            
            query = query.order('example_order').order('title')
            
            result = query.execute()
            
            # Parse JSON parameters if present
            for example in result.data:
                if example.get('parameters'):
                    example['parameters'] = json.loads(example['parameters']) if isinstance(example['parameters'], str) else example['parameters']
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error getting examples for {schema_id}: {str(e)}")
            return []
    
    def get_schema_sections(self, schema_id: str) -> List[Dict[str, Any]]:
        """
        Get documentation sections for a data source
        
        Args:
            schema_id: The schema identifier
            
        Returns:
            List of sections
        """
        try:
            # First get the data source ID
            ds_result = self.client.table('amc_data_sources').select('id').eq('schema_id', schema_id).single().execute()
            
            if not ds_result.data:
                return []
            
            data_source_id = ds_result.data['id']
            
            # Query sections
            result = self.client.table('amc_schema_sections')\
                .select('*')\
                .eq('data_source_id', data_source_id)\
                .order('section_order')\
                .execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error getting sections for {schema_id}: {str(e)}")
            return []
    
    def get_schema_relationships(self, schema_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get relationships for a data source (both as source and target)
        
        Args:
            schema_id: The schema identifier
            
        Returns:
            Dictionary with 'from' and 'to' relationships
        """
        try:
            # First get the data source ID
            ds_result = self.client.table('amc_data_sources').select('id').eq('schema_id', schema_id).single().execute()
            
            if not ds_result.data:
                return {'from': [], 'to': []}
            
            data_source_id = ds_result.data['id']
            
            # Get relationships where this schema is the source
            from_result = self.client.table('amc_schema_relationships')\
                .select('*, target:amc_data_sources!target_schema_id(schema_id, name)')\
                .eq('source_schema_id', data_source_id)\
                .execute()
            
            # Get relationships where this schema is the target
            to_result = self.client.table('amc_schema_relationships')\
                .select('*, source:amc_data_sources!source_schema_id(schema_id, name)')\
                .eq('target_schema_id', data_source_id)\
                .execute()
            
            return {
                'from': from_result.data,
                'to': to_result.data
            }
            
        except Exception as e:
            logger.error(f"Error getting relationships for {schema_id}: {str(e)}")
            return {'from': [], 'to': []}
    
    def get_complete_schema(self, schema_id: str) -> Optional[Dict[str, Any]]:
        """
        Get complete schema details including all related data
        
        Args:
            schema_id: The schema identifier
            
        Returns:
            Complete schema data or None
        """
        try:
            # Try to use the database function for efficiency
            try:
                result = self.client.rpc('get_amc_schema_details', {'p_schema_id': schema_id}).execute()
                
                if result.data:
                    # Parse JSON fields in the schema object if they're strings
                    if 'schema' in result.data and result.data['schema']:
                        schema_data = result.data['schema']
                        if isinstance(schema_data.get('data_sources'), str):
                            schema_data['data_sources'] = json.loads(schema_data['data_sources']) if schema_data['data_sources'] else []
                        if isinstance(schema_data.get('tags'), str):
                            schema_data['tags'] = json.loads(schema_data['tags']) if schema_data['tags'] else []
                        if isinstance(schema_data.get('availability'), str):
                            schema_data['availability'] = json.loads(schema_data['availability']) if schema_data['availability'] else None
                    return result.data
            except Exception as rpc_error:
                logger.debug(f"RPC function not available, falling back to manual assembly: {rpc_error}")
            
            # Fallback to manual assembly if function doesn't exist
            schema = self.get_data_source(schema_id)
            if not schema:
                return None
            
            # Ensure all fields return arrays even if empty
            return {
                'schema': schema,
                'fields': self.get_schema_fields(schema_id) or [],
                'examples': self.get_query_examples(schema_id) or [],
                'sections': self.get_schema_sections(schema_id) or [],
                'relationships': self.get_schema_relationships(schema_id) or {'from': [], 'to': []}
            }
            
        except Exception as e:
            logger.error(f"Error getting complete schema for {schema_id}: {str(e)}")
            # Return minimal valid structure instead of None
            schema = self.get_data_source(schema_id)
            if schema:
                return {
                    'schema': schema,
                    'fields': [],
                    'examples': [],
                    'sections': [],
                    'relationships': {'from': [], 'to': []}
                }
            return None
    
    def search_fields(
        self,
        search_term: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search for fields across all data sources
        
        Args:
            search_term: Term to search for
            limit: Maximum results
            
        Returns:
            List of matching fields with their data source info
        """
        try:
            # Search fields
            result = self.client.table('amc_schema_fields')\
                .select('*, data_source:amc_data_sources(schema_id, name, category)')\
                .or_(f"field_name.ilike.%{search_term}%,description.ilike.%{search_term}%")\
                .limit(limit)\
                .execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error searching fields: {str(e)}")
            return []
    
    def get_categories(self) -> List[str]:
        """
        Get all unique categories
        
        Returns:
            List of category names
        """
        try:
            result = self.client.table('amc_data_sources')\
                .select('category')\
                .execute()
            
            categories = list(set(item['category'] for item in result.data if item.get('category')))
            return sorted(categories)
            
        except Exception as e:
            logger.error(f"Error getting categories: {str(e)}")
            return []
    
    def get_popular_tags(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get most commonly used tags
        
        Args:
            limit: Maximum number of tags
            
        Returns:
            List of tags with usage counts
        """
        try:
            result = self.client.table('amc_data_sources').select('tags').execute()
            
            tag_counts = {}
            for item in result.data:
                if item.get('tags'):
                    tags = json.loads(item['tags']) if isinstance(item['tags'], str) else item['tags']
                    for tag in tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            # Sort by count and return top tags
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
            return [{'tag': tag, 'count': count} for tag, count in sorted_tags[:limit]]
            
        except Exception as e:
            logger.error(f"Error getting popular tags: {str(e)}")
            return []
    
    def export_for_ai(self) -> Dict[str, Any]:
        """
        Export all schemas in a format optimized for AI/LLM consumption
        
        Returns:
            Dictionary with all schema data structured for AI
        """
        try:
            schemas = self.list_data_sources(limit=1000)
            
            ai_export = {
                'version': '1.0',
                'generated_at': datetime.utcnow().isoformat(),
                'total_schemas': len(schemas),
                'schemas': []
            }
            
            for schema in schemas:
                schema_data = self.get_complete_schema(schema['schema_id'])
                if schema_data:
                    # Structure for AI understanding
                    ai_schema = {
                        'id': schema['schema_id'],
                        'name': schema['name'],
                        'category': schema['category'],
                        'description': schema['description'],
                        'tables': schema.get('data_sources', []),
                        'tags': schema.get('tags', []),
                        'key_fields': [],
                        'metrics': [],
                        'dimensions': [],
                        'example_queries': [],
                        'use_cases': [],
                        'relationships': []
                    }
                    
                    # Categorize fields
                    if schema_data.get('fields'):
                        for field in schema_data['fields']:
                            field_info = {
                                'name': field['field_name'],
                                'type': field['data_type'],
                                'description': field.get('description', '')
                            }
                            
                            if field['dimension_or_metric'] == 'Metric':
                                ai_schema['metrics'].append(field_info)
                            else:
                                ai_schema['dimensions'].append(field_info)
                            
                            # Identify key fields
                            if any(key in field['field_name'].lower() for key in ['id', 'key', 'name']):
                                ai_schema['key_fields'].append(field['field_name'])
                    
                    # Add examples
                    if schema_data.get('examples'):
                        for example in schema_data['examples']:
                            ai_schema['example_queries'].append({
                                'title': example['title'],
                                'sql': example['sql_query'],
                                'category': example.get('category', 'General')
                            })
                    
                    # Add relationships
                    if schema_data.get('relationships'):
                        for rel in schema_data['relationships'].get('from', []):
                            ai_schema['relationships'].append({
                                'type': rel['relationship_type'],
                                'target': rel['target']['schema_id'],
                                'direction': 'outgoing'
                            })
                    
                    ai_export['schemas'].append(ai_schema)
            
            return ai_export
            
        except Exception as e:
            logger.error(f"Error exporting for AI: {str(e)}")
            return {}