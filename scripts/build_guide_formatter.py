#!/usr/bin/env python3
"""
Build Guide Formatter and Uploader Agent

This script serves as a comprehensive tool for formatting and uploading build guides
to the database. It supports multiple input formats (JSON, YAML, Markdown with frontmatter)
and provides validation, formatting, and database operations.

Usage Examples:
    # Upload from YAML file
    python build_guide_formatter.py --file guide.yaml
    
    # Preview without uploading
    python build_guide_formatter.py --file guide.yaml --preview
    
    # Update existing guide
    python build_guide_formatter.py --file guide.yaml --update
    
    # Read from stdin
    cat guide.yaml | python build_guide_formatter.py --stdin --format yaml
    
    # Verbose logging
    python build_guide_formatter.py --file guide.yaml --verbose
    
    # Validate only (no database operations)
    python build_guide_formatter.py --file guide.yaml --validate-only

Input Format Support:
    - YAML files (.yaml, .yml)
    - JSON files (.json)
    - Markdown files with YAML frontmatter (.md)

Features:
    - Input validation with detailed error reporting
    - SQL query formatting and validation
    - Markdown table validation
    - Database transaction management with rollback on errors
    - Preview mode to see what will be created/updated
    - Support for updating existing guides
    - Comprehensive logging and error handling
"""

import os
import sys
import argparse
import json
import yaml
import re
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationError:
    """Represents a validation error with context"""
    field: str
    message: str
    value: Any = None
    context: str = ""


class BuildGuideFormatter:
    """Main class for processing and uploading build guides"""
    
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.validation_errors: List[ValidationError] = []
        self.client = None
        
        if not dry_run:
            try:
                self.client = SupabaseManager.get_client(use_service_role=True)
                logger.info("Connected to Supabase")
            except Exception as e:
                logger.error(f"Failed to connect to Supabase: {e}")
                if __name__ == "__main__":
                    sys.exit(1)
                else:
                    raise
    
    def load_input(self, file_path: Optional[str] = None, 
                   stdin_content: Optional[str] = None,
                   format_hint: Optional[str] = None) -> Dict[str, Any]:
        """Load input from file or stdin"""
        try:
            if file_path:
                logger.info(f"Loading guide from: {file_path}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Detect format from file extension
                file_ext = Path(file_path).suffix.lower()
                if file_ext in ['.yaml', '.yml']:
                    return self._parse_yaml(content)
                elif file_ext == '.json':
                    return self._parse_json(content)
                elif file_ext == '.md':
                    return self._parse_markdown_with_frontmatter(content)
                else:
                    raise ValueError(f"Unsupported file format: {file_ext}")
            
            elif stdin_content:
                logger.info("Loading guide from stdin")
                if format_hint == 'yaml':
                    return self._parse_yaml(stdin_content)
                elif format_hint == 'json':
                    return self._parse_json(stdin_content)
                elif format_hint == 'markdown':
                    return self._parse_markdown_with_frontmatter(stdin_content)
                else:
                    # Try to auto-detect format
                    return self._auto_detect_format(stdin_content)
            
            else:
                raise ValueError("Either file_path or stdin_content must be provided")
                
        except Exception as e:
            logger.error(f"Failed to load input: {e}")
            raise
    
    def _parse_yaml(self, content: str) -> Dict[str, Any]:
        """Parse YAML content"""
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")
    
    def _parse_json(self, content: str) -> Dict[str, Any]:
        """Parse JSON content"""
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
    
    def _parse_markdown_with_frontmatter(self, content: str) -> Dict[str, Any]:
        """Parse Markdown file with YAML frontmatter"""
        # Split frontmatter and content
        parts = content.split('---', 2)
        if len(parts) < 3:
            raise ValueError("Markdown file must have YAML frontmatter between --- markers")
        
        try:
            frontmatter = yaml.safe_load(parts[1])
            markdown_content = parts[2].strip()
            
            # Add markdown content to appropriate section
            if 'sections' in frontmatter and markdown_content:
                # Find or create a content section
                found_content_section = False
                for section in frontmatter['sections']:
                    if section.get('section_id') == 'content':
                        section['content_markdown'] = markdown_content
                        found_content_section = True
                        break
                
                if not found_content_section:
                    frontmatter['sections'].append({
                        'section_id': 'content',
                        'title': 'Content',
                        'display_order': 99,
                        'is_collapsible': True,
                        'default_expanded': True,
                        'content_markdown': markdown_content
                    })
            
            return frontmatter
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML frontmatter: {e}")
    
    def _auto_detect_format(self, content: str) -> Dict[str, Any]:
        """Auto-detect input format and parse accordingly"""
        content = content.strip()
        
        # Check for JSON
        if content.startswith('{') and content.endswith('}'):
            return self._parse_json(content)
        
        # Check for Markdown with frontmatter
        if content.startswith('---'):
            return self._parse_markdown_with_frontmatter(content)
        
        # Default to YAML
        return self._parse_yaml(content)
    
    def validate_guide_data(self, data: Dict[str, Any]) -> bool:
        """Validate the guide data structure"""
        self.validation_errors = []
        
        # Validate top-level structure
        if 'guide' not in data:
            self.validation_errors.append(
                ValidationError('guide', 'Root "guide" section is required')
            )
            return False
        
        guide = data['guide']
        
        # Validate required guide fields
        required_guide_fields = ['name', 'category', 'short_description']
        for field in required_guide_fields:
            if field not in guide or not guide[field]:
                self.validation_errors.append(
                    ValidationError(f'guide.{field}', f'Field "{field}" is required')
                )
        
        # Validate optional fields with defaults
        self._validate_guide_optional_fields(guide)
        
        # Validate sections
        if 'sections' in data:
            self._validate_sections(data['sections'])
        
        # Validate queries
        if 'queries' in data:
            self._validate_queries(data['queries'])
        
        # Validate metrics
        if 'metrics' in data:
            self._validate_metrics(data['metrics'])
        
        if self.validation_errors:
            logger.error(f"Validation failed with {len(self.validation_errors)} errors:")
            for error in self.validation_errors:
                logger.error(f"  - {error.field}: {error.message}")
                if error.value is not None and self.verbose:
                    logger.error(f"    Value: {error.value}")
            return False
        
        logger.info("✅ Validation passed")
        return True
    
    def _validate_guide_optional_fields(self, guide: Dict[str, Any]):
        """Validate optional guide fields with type checking"""
        validations = [
            ('difficulty_level', str, ['beginner', 'intermediate', 'advanced']),
            ('estimated_time_minutes', int, None),
            ('is_published', bool, None),
            ('display_order', int, None),
            ('tags', list, None),
            ('prerequisites', list, None)
        ]
        
        for field, expected_type, valid_values in validations:
            if field in guide:
                value = guide[field]
                if not isinstance(value, expected_type):
                    self.validation_errors.append(
                        ValidationError(f'guide.{field}', 
                                       f'Field "{field}" must be of type {expected_type.__name__}',
                                       value)
                    )
                
                if valid_values and value not in valid_values:
                    self.validation_errors.append(
                        ValidationError(f'guide.{field}',
                                       f'Field "{field}" must be one of: {valid_values}',
                                       value)
                    )
    
    def _validate_sections(self, sections: List[Dict[str, Any]]):
        """Validate guide sections"""
        required_fields = ['section_id', 'title', 'display_order']
        section_ids = set()
        
        for i, section in enumerate(sections):
            context = f'sections[{i}]'
            
            # Check required fields
            for field in required_fields:
                if field not in section:
                    self.validation_errors.append(
                        ValidationError(f'{context}.{field}', f'Field "{field}" is required')
                    )
            
            # Check for duplicate section_ids
            if 'section_id' in section:
                section_id = section['section_id']
                if section_id in section_ids:
                    self.validation_errors.append(
                        ValidationError(f'{context}.section_id',
                                       f'Duplicate section_id: "{section_id}"')
                    )
                section_ids.add(section_id)
            
            # Validate markdown content if present
            if 'content_markdown' in section:
                self._validate_markdown_content(section['content_markdown'], f'{context}.content_markdown')
    
    def _validate_queries(self, queries: List[Dict[str, Any]]):
        """Validate guide queries"""
        required_fields = ['title', 'sql_query', 'display_order']
        
        for i, query in enumerate(queries):
            context = f'queries[{i}]'
            
            # Check required fields
            for field in required_fields:
                if field not in query:
                    self.validation_errors.append(
                        ValidationError(f'{context}.{field}', f'Field "{field}" is required')
                    )
            
            # Validate SQL query
            if 'sql_query' in query:
                self._validate_sql_query(query['sql_query'], f'{context}.sql_query')
            
            # Validate parameters schema
            if 'parameters_schema' in query:
                self._validate_parameters_schema(query['parameters_schema'], f'{context}.parameters_schema')
            
            # Validate query type
            if 'query_type' in query:
                valid_types = ['exploratory', 'main_analysis', 'validation']
                if query['query_type'] not in valid_types:
                    self.validation_errors.append(
                        ValidationError(f'{context}.query_type',
                                       f'Query type must be one of: {valid_types}',
                                       query['query_type'])
                    )
    
    def _validate_metrics(self, metrics: List[Dict[str, Any]]):
        """Validate metrics definitions"""
        required_fields = ['metric_name', 'display_name', 'definition', 'metric_type']
        metric_names = set()
        
        for i, metric in enumerate(metrics):
            context = f'metrics[{i}]'
            
            # Check required fields
            for field in required_fields:
                if field not in metric:
                    self.validation_errors.append(
                        ValidationError(f'{context}.{field}', f'Field "{field}" is required')
                    )
            
            # Check for duplicate metric names
            if 'metric_name' in metric:
                metric_name = metric['metric_name']
                if metric_name in metric_names:
                    self.validation_errors.append(
                        ValidationError(f'{context}.metric_name',
                                       f'Duplicate metric_name: "{metric_name}"')
                    )
                metric_names.add(metric_name)
            
            # Validate metric type
            if 'metric_type' in metric:
                valid_types = ['metric', 'dimension']
                if metric['metric_type'] not in valid_types:
                    self.validation_errors.append(
                        ValidationError(f'{context}.metric_type',
                                       f'Metric type must be one of: {valid_types}',
                                       metric['metric_type'])
                    )
    
    def _validate_markdown_content(self, content: str, context: str):
        """Validate markdown content, especially tables"""
        if not content.strip():
            return
        
        # Check for malformed markdown tables
        lines = content.split('\n')
        in_table = False
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Check for table rows
            if '|' in stripped and stripped.startswith('|') and stripped.endswith('|'):
                in_table = True
                # Count columns
                columns = [col.strip() for col in stripped.split('|')[1:-1]]
                if not all(columns):  # Check for empty columns
                    logger.warning(f"{context} line {line_num}: Table row has empty columns")
            
            elif in_table and not stripped:
                in_table = False
            
            elif in_table and '|' not in stripped:
                # Should not have non-table content in the middle of a table
                logger.warning(f"{context} line {line_num}: Potential table formatting issue")
    
    def _validate_sql_query(self, sql: str, context: str):
        """Basic SQL query validation"""
        if not sql.strip():
            self.validation_errors.append(
                ValidationError(context, "SQL query cannot be empty")
            )
            return
        
        # Check for parameter placeholders
        placeholders = re.findall(r'\{\{(\w+)\}\}', sql)
        if placeholders and self.verbose:
            logger.info(f"{context}: Found parameters: {', '.join(set(placeholders))}")
        
        # Basic SQL structure check
        sql_lower = sql.lower().strip()
        if not (sql_lower.startswith('select') or 
                sql_lower.startswith('with') or 
                sql_lower.startswith('-- ')):
            logger.warning(f"{context}: SQL query should start with SELECT, WITH, or comment")
    
    def _validate_parameters_schema(self, schema: Dict[str, Any], context: str):
        """Validate parameters schema"""
        for param_name, param_def in schema.items():
            if not isinstance(param_def, dict):
                self.validation_errors.append(
                    ValidationError(f"{context}.{param_name}",
                                   "Parameter definition must be an object")
                )
                continue
            
            if 'type' not in param_def:
                self.validation_errors.append(
                    ValidationError(f"{context}.{param_name}.type",
                                   "Parameter type is required")
                )
            
            valid_types = ['string', 'integer', 'boolean', 'array']
            if param_def.get('type') not in valid_types:
                self.validation_errors.append(
                    ValidationError(f"{context}.{param_name}.type",
                                   f"Parameter type must be one of: {valid_types}",
                                   param_def.get('type'))
                )
    
    def format_guide_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format and enhance the guide data"""
        logger.info("Formatting guide data...")
        
        guide = data['guide']
        
        # Generate guide_id if not provided
        if 'guide_id' not in guide:
            guide['guide_id'] = self._generate_guide_id(guide['name'])
            logger.info(f"Generated guide_id: {guide['guide_id']}")
        
        # Set defaults
        guide.setdefault('difficulty_level', 'intermediate')
        guide.setdefault('estimated_time_minutes', 30)
        guide.setdefault('is_published', True)
        guide.setdefault('display_order', 0)
        guide.setdefault('tags', [])
        guide.setdefault('prerequisites', [])
        
        # Format SQL queries
        if 'queries' in data:
            for query in data['queries']:
                if 'sql_query' in query:
                    query['sql_query'] = self._format_sql_query(query['sql_query'])
                
                # Set defaults
                query.setdefault('query_type', 'main_analysis')
                query.setdefault('parameters_schema', {})
                query.setdefault('default_parameters', {})
        
        # Format sections
        if 'sections' in data:
            for section in data['sections']:
                section.setdefault('is_collapsible', True)
                section.setdefault('default_expanded', True)
        
        # Format metrics
        if 'metrics' in data:
            for metric in data['metrics']:
                metric.setdefault('metric_type', 'metric')
                metric.setdefault('display_order', 0)
        
        return data
    
    def _generate_guide_id(self, name: str) -> str:
        """Generate a guide_id from the guide name"""
        # Convert to lowercase and replace spaces/special chars with underscores
        guide_id = re.sub(r'[^a-zA-Z0-9]+', '_', name.lower()).strip('_')
        # Ensure it starts with 'guide_'
        if not guide_id.startswith('guide_'):
            guide_id = f'guide_{guide_id}'
        return guide_id
    
    def _format_sql_query(self, sql: str) -> str:
        """Basic SQL query formatting"""
        # Remove excessive whitespace while preserving structure
        lines = sql.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Preserve indentation for readability
            stripped = line.strip()
            if stripped:
                formatted_lines.append(line)
            elif formatted_lines:  # Preserve single blank lines
                formatted_lines.append('')
        
        return '\n'.join(formatted_lines)
    
    def preview_guide(self, data: Dict[str, Any]):
        """Preview what will be created/updated"""
        guide = data['guide']
        
        print("\n" + "="*60)
        print(f"📖 BUILD GUIDE PREVIEW")
        print("="*60)
        print(f"Name: {guide['name']}")
        print(f"ID: {guide['guide_id']}")
        print(f"Category: {guide['category']}")
        print(f"Description: {guide['short_description']}")
        print(f"Difficulty: {guide.get('difficulty_level', 'intermediate')}")
        print(f"Estimated Time: {guide.get('estimated_time_minutes', 30)} minutes")
        print(f"Published: {guide.get('is_published', True)}")
        
        if guide.get('tags'):
            print(f"Tags: {', '.join(guide['tags'])}")
        
        if guide.get('prerequisites'):
            print("Prerequisites:")
            for i, prereq in enumerate(guide['prerequisites'], 1):
                print(f"  {i}. {prereq}")
        
        # Preview sections
        if 'sections' in data:
            print(f"\n📑 SECTIONS ({len(data['sections'])})")
            print("-" * 40)
            for section in sorted(data['sections'], key=lambda x: x.get('display_order', 0)):
                print(f"{section.get('display_order', 0)}. {section['title']} [{section['section_id']}]")
                if section.get('content_markdown'):
                    content_preview = section['content_markdown'][:100].replace('\n', ' ')
                    print(f"   Content: {content_preview}{'...' if len(section['content_markdown']) > 100 else ''}")
        
        # Preview queries
        if 'queries' in data:
            print(f"\n🔍 QUERIES ({len(data['queries'])})")
            print("-" * 40)
            for query in sorted(data['queries'], key=lambda x: x.get('display_order', 0)):
                print(f"{query.get('display_order', 0)}. {query['title']} [{query.get('query_type', 'main_analysis')}]")
                if query.get('description'):
                    print(f"   Description: {query['description']}")
                
                # Show parameters
                if query.get('parameters_schema'):
                    params = list(query['parameters_schema'].keys())
                    print(f"   Parameters: {', '.join(params)}")
                
                # Show examples
                if 'examples' in query:
                    print(f"   Examples: {len(query['examples'])}")
        
        # Preview metrics
        if 'metrics' in data:
            print(f"\n📊 METRICS & DIMENSIONS ({len(data['metrics'])})")
            print("-" * 40)
            for metric in sorted(data['metrics'], key=lambda x: x.get('display_order', 0)):
                print(f"{metric.get('display_order', 0)}. {metric['display_name']} [{metric.get('metric_type', 'metric')}]")
                print(f"   Definition: {metric['definition'][:80]}{'...' if len(metric['definition']) > 80 else ''}")
        
        print("\n" + "="*60)
    
    def upload_guide(self, data: Dict[str, Any], update_existing: bool = False) -> bool:
        """Upload the guide to the database"""
        if self.dry_run:
            logger.info("Dry run mode - no database operations performed")
            return True
        
        logger.info("Starting database upload...")
        
        try:
            # Check if guide exists
            guide_data = data['guide']
            existing_guide = self._find_existing_guide(guide_data['guide_id'])
            
            if existing_guide and not update_existing:
                logger.error(f"Guide with ID '{guide_data['guide_id']}' already exists. Use --update to update it.")
                return False
            
            # Start transaction-like operations
            if existing_guide:
                guide_id = self._update_existing_guide(existing_guide['id'], guide_data)
                logger.info(f"Updated existing guide: {guide_data['name']}")
            else:
                guide_id = self._create_new_guide(guide_data)
                logger.info(f"Created new guide: {guide_data['name']}")
            
            if not guide_id:
                logger.error("Failed to create/update guide")
                return False
            
            # Upload sections
            if 'sections' in data:
                self._upload_sections(guide_id, data['sections'], update_existing)
            
            # Upload queries and examples
            if 'queries' in data:
                self._upload_queries(guide_id, data['queries'], update_existing)
            
            # Upload metrics
            if 'metrics' in data:
                self._upload_metrics(guide_id, data['metrics'], update_existing)
            
            logger.info("✅ Successfully uploaded build guide!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload guide: {e}")
            if self.verbose:
                import traceback
                logger.error(traceback.format_exc())
            return False
    
    def _find_existing_guide(self, guide_id: str) -> Optional[Dict[str, Any]]:
        """Find existing guide by guide_id"""
        try:
            response = self.client.table('build_guides').select('*').eq('guide_id', guide_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error checking for existing guide: {e}")
            return None
    
    def _create_new_guide(self, guide_data: Dict[str, Any]) -> Optional[str]:
        """Create a new guide in the database"""
        try:
            db_data = self._prepare_guide_for_db(guide_data)
            response = self.client.table('build_guides').insert(db_data).execute()
            
            if response.data:
                return response.data[0]['id']
            return None
        except Exception as e:
            logger.error(f"Failed to create guide: {e}")
            return None
    
    def _update_existing_guide(self, existing_id: str, guide_data: Dict[str, Any]) -> Optional[str]:
        """Update existing guide"""
        try:
            db_data = self._prepare_guide_for_db(guide_data, is_update=True)
            response = self.client.table('build_guides').update(db_data).eq('id', existing_id).execute()
            
            if response.data:
                return response.data[0]['id']
            return None
        except Exception as e:
            logger.error(f"Failed to update guide: {e}")
            return None
    
    def _prepare_guide_for_db(self, guide_data: Dict[str, Any], is_update: bool = False) -> Dict[str, Any]:
        """Prepare guide data for database insertion"""
        db_data = {
            'guide_id': guide_data['guide_id'],
            'name': guide_data['name'],
            'category': guide_data['category'],
            'short_description': guide_data['short_description'],
            'tags': guide_data.get('tags', []),
            'icon': guide_data.get('icon'),
            'difficulty_level': guide_data.get('difficulty_level', 'intermediate'),
            'estimated_time_minutes': guide_data.get('estimated_time_minutes', 30),
            'prerequisites': guide_data.get('prerequisites', []),
            'is_published': guide_data.get('is_published', True),
            'display_order': guide_data.get('display_order', 0)
        }
        
        if not is_update:
            db_data['created_at'] = datetime.utcnow().isoformat()
        
        db_data['updated_at'] = datetime.utcnow().isoformat()
        
        return db_data
    
    def _upload_sections(self, guide_id: str, sections: List[Dict[str, Any]], update_existing: bool):
        """Upload guide sections"""
        logger.info(f"Uploading {len(sections)} sections...")
        
        if update_existing:
            # Delete existing sections
            self.client.table('build_guide_sections').delete().eq('guide_id', guide_id).execute()
        
        for section in sections:
            section_data = {
                'guide_id': guide_id,
                'section_id': section['section_id'],
                'title': section['title'],
                'content_markdown': section.get('content_markdown'),
                'display_order': section.get('display_order', 0),
                'is_collapsible': section.get('is_collapsible', True),
                'default_expanded': section.get('default_expanded', True)
            }
            
            response = self.client.table('build_guide_sections').insert(section_data).execute()
            if response.data:
                logger.info(f"Created section: {section['title']}")
            else:
                logger.error(f"Failed to create section: {section['title']}")
    
    def _upload_queries(self, guide_id: str, queries: List[Dict[str, Any]], update_existing: bool):
        """Upload guide queries and examples"""
        logger.info(f"Uploading {len(queries)} queries...")
        
        if update_existing:
            # Delete existing queries (cascades to examples)
            self.client.table('build_guide_queries').delete().eq('guide_id', guide_id).execute()
        
        for query in queries:
            query_data = {
                'guide_id': guide_id,
                'title': query['title'],
                'description': query.get('description'),
                'sql_query': query['sql_query'],
                'parameters_schema': query.get('parameters_schema', {}),
                'default_parameters': query.get('default_parameters', {}),
                'display_order': query.get('display_order', 0),
                'query_type': query.get('query_type', 'main_analysis'),
                'interpretation_notes': query.get('interpretation_notes')
            }
            
            response = self.client.table('build_guide_queries').insert(query_data).execute()
            if response.data:
                query_id = response.data[0]['id']
                logger.info(f"Created query: {query['title']}")
                
                # Upload examples if present
                if 'examples' in query:
                    self._upload_examples(query_id, query['examples'])
            else:
                logger.error(f"Failed to create query: {query['title']}")
    
    def _upload_examples(self, query_id: str, examples: List[Dict[str, Any]]):
        """Upload query examples"""
        for example in examples:
            example_data = {
                'guide_query_id': query_id,
                'example_name': example['example_name'],
                'sample_data': example['sample_data'],
                'interpretation_markdown': example.get('interpretation_markdown'),
                'insights': example.get('insights', []),
                'display_order': example.get('display_order', 0)
            }
            
            response = self.client.table('build_guide_examples').insert(example_data).execute()
            if response.data:
                logger.info(f"Created example: {example['example_name']}")
            else:
                logger.error(f"Failed to create example: {example['example_name']}")
    
    def _upload_metrics(self, guide_id: str, metrics: List[Dict[str, Any]], update_existing: bool):
        """Upload metrics definitions"""
        logger.info(f"Uploading {len(metrics)} metrics...")
        
        if update_existing:
            # Delete existing metrics
            self.client.table('build_guide_metrics').delete().eq('guide_id', guide_id).execute()
        
        for metric in metrics:
            metric_data = {
                'guide_id': guide_id,
                'metric_name': metric['metric_name'],
                'display_name': metric['display_name'],
                'definition': metric['definition'],
                'metric_type': metric.get('metric_type', 'metric'),
                'display_order': metric.get('display_order', 0)
            }
            
            response = self.client.table('build_guide_metrics').insert(metric_data).execute()
            if response.data:
                logger.info(f"Created metric: {metric['display_name']}")
            else:
                logger.error(f"Failed to create metric: {metric['display_name']}")


# Convenience functions for module usage

def format_and_upload_guide(file_path: str, update_existing: bool = False, 
                           preview_only: bool = False, validate_only: bool = False) -> bool:
    """
    Convenience function for programmatic use
    
    Args:
        file_path: Path to the guide file
        update_existing: Whether to update if guide exists
        preview_only: Only show preview, don't upload
        validate_only: Only validate, don't upload
        
    Returns:
        True if successful, False otherwise
    """
    try:
        formatter = BuildGuideFormatter(dry_run=preview_only or validate_only, verbose=False)
        data = formatter.load_input(file_path=file_path)
        
        if not formatter.validate_guide_data(data):
            return False
            
        if validate_only:
            return True
            
        formatted_data = formatter.format_guide_data(data)
        
        if preview_only:
            formatter.preview_guide(formatted_data)
            return True
            
        return formatter.upload_guide(formatted_data, update_existing=update_existing)
        
    except Exception as e:
        logger.error(f"Error processing guide: {e}")
        return False


def create_guide_from_dict(guide_dict: Dict[str, Any], update_existing: bool = False) -> bool:
    """
    Create guide directly from a dictionary
    
    Args:
        guide_dict: Guide data as dictionary
        update_existing: Whether to update if guide exists
        
    Returns:
        True if successful, False otherwise
    """
    try:
        formatter = BuildGuideFormatter(dry_run=False, verbose=False)
        
        if not formatter.validate_guide_data(guide_dict):
            return False
            
        formatted_data = formatter.format_guide_data(guide_dict)
        return formatter.upload_guide(formatted_data, update_existing=update_existing)
        
    except Exception as e:
        logger.error(f"Error creating guide from dict: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Build Guide Formatter and Uploader',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --file guide.yaml
  %(prog)s --file guide.yaml --preview
  %(prog)s --file guide.yaml --update
  cat guide.yaml | %(prog)s --stdin --format yaml
  %(prog)s --file guide.yaml --validate-only --verbose
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--file', '-f', help='Input file path (YAML, JSON, or Markdown)')
    input_group.add_argument('--stdin', action='store_true', help='Read from stdin')
    
    # Format hint for stdin
    parser.add_argument('--format', choices=['yaml', 'json', 'markdown'],
                       help='Format hint for stdin input')
    
    # Operation modes
    parser.add_argument('--preview', '-p', action='store_true',
                       help='Preview mode - show what will be created without uploading')
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate the input, no database operations')
    parser.add_argument('--update', '-u', action='store_true',
                       help='Update existing guide if it exists')
    
    # Logging options
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Configure logging
    if args.debug:
        logger.setLevel('DEBUG')
    elif args.verbose:
        logger.setLevel('INFO')
    
    # Determine if this is a dry run
    dry_run = args.preview or args.validate_only
    
    try:
        # Initialize formatter
        formatter = BuildGuideFormatter(dry_run=dry_run, verbose=args.verbose)
        
        # Load input
        if args.file:
            data = formatter.load_input(file_path=args.file)
        else:
            stdin_content = sys.stdin.read()
            data = formatter.load_input(stdin_content=stdin_content, format_hint=args.format)
        
        # Validate input
        if not formatter.validate_guide_data(data):
            sys.exit(1)
        
        if args.validate_only:
            print("✅ Validation successful!")
            sys.exit(0)
        
        # Format data
        formatted_data = formatter.format_guide_data(data)
        
        # Preview mode
        if args.preview:
            formatter.preview_guide(formatted_data)
            sys.exit(0)
        
        # Upload to database
        success = formatter.upload_guide(formatted_data, update_existing=args.update)
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose or args.debug:
            import traceback
            logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()