#!/usr/bin/env python3
"""
Import AMC Schema Documentation from Markdown Files
Parses markdown files in amc_dataset/ and imports them into the database
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from supabase import create_client, Client
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class AMCSchemaImporter:
    """Import AMC schemas from markdown files to database"""
    
    def __init__(self):
        """Initialize the importer with Supabase client"""
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Use service role for admin operations
        )
        self.schema_dir = Path("amc_dataset")
        
        # Schema categories mapping
        self.categories = {
            "dsp": "DSP Tables",
            "attributed": "Attribution Tables",
            "conversions": "Conversion Tables",
            "sponsored": "Sponsored Ads Tables",
            "brand_store": "Brand Store Insights",
            "retail": "Retail Analytics",
            "audience": "Audience Tables",
            "pvc": "Premium Video Content",
            "your_garage": "Automotive Insights"
        }
        
    def parse_markdown_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse a markdown schema file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract schema ID from filename
        schema_id = file_path.stem.replace('_schema', '').replace('_', '-')
        
        # Parse sections
        sections = self._parse_sections(content)
        
        # Extract metadata
        metadata = self._extract_metadata(content, schema_id)
        
        # Parse fields from table
        fields = self._parse_fields(content)
        
        # Parse query examples
        examples = self._parse_examples(content)
        
        return {
            'metadata': metadata,
            'sections': sections,
            'fields': fields,
            'examples': examples
        }
    
    def _extract_metadata(self, content: str, schema_id: str) -> Dict[str, Any]:
        """Extract metadata from markdown content"""
        # Extract title
        title_match = re.search(r'^#\s+(.+?)(?:\s+Schema|\s+Data Source|\s+Tables?)?$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else schema_id.replace('-', ' ').title()
        
        # Extract data sources
        sources_match = re.search(r'\*\*Data Sources?:\*\*\s*\n-\s*`([^`]+)`(?:\s*(?:and|,)\s*`([^`]+)`)?', content)
        data_sources = []
        if sources_match:
            data_sources.append(sources_match.group(1))
            if sources_match.group(2):
                data_sources.append(sources_match.group(2))
        
        # Additional sources from bulleted list
        additional_sources = re.findall(r'^-\s*`([^`]+)`', content, re.MULTILINE)
        data_sources.extend([s for s in additional_sources if s not in data_sources])
        
        # Determine category
        category = self._determine_category(schema_id, title)
        
        # Check if it's a paid feature
        is_paid = "AMC Paid Features" in content or "subscription" in content.lower()
        
        # Extract geographic availability
        availability = self._extract_availability(content)
        
        # Extract description from overview
        overview_match = re.search(r'##\s+Overview\s*\n+(.*?)(?=\n##|\Z)', content, re.DOTALL)
        description = ""
        if overview_match:
            desc_lines = overview_match.group(1).strip().split('\n')
            # Get first paragraph that's not data sources
            for line in desc_lines:
                if line.strip() and not line.startswith('**Data Source') and not line.startswith('-'):
                    description = line.strip()
                    break
        
        # Generate tags
        tags = self._generate_tags(schema_id, title, content)
        
        return {
            'schema_id': schema_id,
            'name': title,
            'category': category,
            'description': description,
            'data_sources': data_sources,
            'is_paid_feature': is_paid,
            'availability': availability,
            'tags': tags,
            'version': '1.0.0'
        }
    
    def _determine_category(self, schema_id: str, title: str) -> str:
        """Determine the category for a schema"""
        schema_lower = schema_id.lower()
        title_lower = title.lower()
        
        for key, category in self.categories.items():
            if key in schema_lower or key in title_lower:
                return category
        
        return "Core Tables"  # Default
    
    def _extract_availability(self, content: str) -> Dict[str, Any]:
        """Extract availability information"""
        availability = {}
        
        # Check for geographic coverage
        geo_match = re.search(r'Geographic Coverage.*?(?=\n##|\Z)', content, re.DOTALL)
        if geo_match:
            markets = re.findall(r'\*\*([A-Z]{2})\*\*:\s*([^*\n]+)', geo_match.group(0))
            if markets:
                availability['marketplaces'] = {code: name.strip() for code, name in markets}
        
        # Check for requirements
        if "AMC Paid Features" in content:
            availability['requires_subscription'] = True
        
        # Check for historical data notes
        hist_match = re.search(r'Historical Data:?(.*?)(?=\n##|\n\n)', content, re.DOTALL)
        if hist_match:
            availability['historical_data_notes'] = hist_match.group(1).strip()
        
        return availability if availability else None
    
    def _generate_tags(self, schema_id: str, title: str, content: str) -> List[str]:
        """Generate tags for searchability"""
        tags = []
        
        # Add category-based tags
        if 'dsp' in schema_id.lower():
            tags.extend(['dsp', 'display', 'programmatic'])
        if 'attribution' in schema_id.lower() or 'attributed' in schema_id.lower():
            tags.extend(['attribution', 'conversion'])
        if 'conversion' in schema_id.lower():
            tags.extend(['conversion', 'purchase'])
        if 'brand_store' in schema_id.lower():
            tags.extend(['brand-store', 'storefront'])
        if 'audience' in schema_id.lower():
            tags.extend(['audience', 'segments', 'targeting'])
        if 'sponsored' in schema_id.lower():
            tags.extend(['sponsored-ads', 'search-ads'])
        if 'retail' in schema_id.lower():
            tags.extend(['retail', 'sales', 'inventory'])
        
        # Add feature-based tags
        if 'impression' in content.lower():
            tags.append('impressions')
        if 'click' in content.lower():
            tags.append('clicks')
        if 'video' in content.lower():
            tags.append('video')
        if 'pixel' in content.lower():
            tags.append('pixel-tracking')
        if 'new-to-brand' in content.lower() or 'new_to_brand' in content.lower():
            tags.append('new-to-brand')
        
        return list(set(tags))  # Remove duplicates
    
    def _parse_sections(self, content: str) -> List[Dict[str, Any]]:
        """Parse documentation sections from markdown"""
        sections = []
        
        # Common section patterns
        section_patterns = [
            (r'##\s+Overview\s*\n+(.*?)(?=\n##|\Z)', 'overview'),
            (r'##\s+(?:Critical\s+)?Table Differences.*?\n+(.*?)(?=\n##|\Z)', 'differences'),
            (r'##\s+(?:Key\s+)?Concepts.*?\n+(.*?)(?=\n##|\Z)', 'concepts'),
            (r'##\s+(?:Common\s+)?Query Patterns.*?\n+(.*?)(?=\n##|\Z)', 'query_patterns'),
            (r'##\s+Best Practices.*?\n+(.*?)(?=\n##|\Z)', 'best_practices'),
            (r'##\s+(?:Table\s+)?Selection Guidelines.*?\n+(.*?)(?=\n##|\Z)', 'selection_guidelines'),
            (r'##\s+Data Availability.*?\n+(.*?)(?=\n##|\Z)', 'data_availability'),
            (r'##\s+Usage.*?\n+(.*?)(?=\n##|\Z)', 'usage_guidelines'),
        ]
        
        for pattern, section_type in section_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                sections.append({
                    'section_type': section_type,
                    'content': match.group(1).strip()
                })
        
        return sections
    
    def _parse_fields(self, content: str) -> List[Dict[str, Any]]:
        """Parse field definitions from markdown table"""
        fields = []
        
        # Find table sections
        table_pattern = r'\|[^\n]+\|[^\n]+\|[^\n]+\|[^\n]+\|[^\n]+\|(?:[^\n]+\|)?\s*\n\|[-\s|]+\n((?:\|[^\n]+\n)+)'
        tables = re.findall(table_pattern, content)
        
        field_order = 0
        for table in tables:
            rows = table.strip().split('\n')
            for row in rows:
                if not row.strip() or '---' in row:
                    continue
                    
                parts = [p.strip() for p in row.split('|') if p.strip()]
                if len(parts) >= 5:  # Minimum required columns
                    field = {
                        'field_name': parts[0] if len(parts) > 0 else parts[0],
                        'data_type': parts[1] if len(parts) > 1 else 'STRING',
                        'dimension_or_metric': parts[2] if len(parts) > 2 else 'Dimension',
                        'description': parts[3] if len(parts) > 3 else '',
                        'aggregation_threshold': parts[4] if len(parts) > 4 else 'LOW',
                        'field_order': field_order
                    }
                    
                    # Extract field category if present
                    if len(parts) > 5:
                        field['field_category'] = parts[5]
                    
                    # Clean up values
                    field['data_type'] = field['data_type'].upper()
                    field['aggregation_threshold'] = field['aggregation_threshold'].upper()
                    
                    # Check if array type
                    if 'ARRAY' in field['data_type']:
                        field['is_array'] = True
                    
                    # Extract examples from description if present
                    example_match = re.search(r'Example(?:\s+values?)?:\s*([^.]+)', field['description'])
                    if example_match:
                        examples = [e.strip().strip("'\"") for e in example_match.group(1).split(',')]
                        field['examples'] = examples[:5]  # Limit to 5 examples
                    
                    fields.append(field)
                    field_order += 1
        
        return fields
    
    def _parse_examples(self, content: str) -> List[Dict[str, Any]]:
        """Parse SQL query examples from markdown"""
        examples = []
        
        # Find SQL code blocks
        sql_pattern = r'###?\s*([^\n]+)\n+```sql\n(.*?)\n```'
        matches = re.findall(sql_pattern, content, re.DOTALL)
        
        for idx, (title, sql) in enumerate(matches):
            # Clean up title
            title = re.sub(r'^[#\s]+', '', title).strip()
            
            # Determine category from title or content
            category = 'Basic'
            if any(word in title.lower() for word in ['advanced', 'complex', 'multi']):
                category = 'Advanced'
            elif any(word in title.lower() for word in ['performance', 'optimize']):
                category = 'Performance'
            elif 'attribution' in title.lower():
                category = 'Attribution'
            
            examples.append({
                'title': title,
                'sql_query': sql.strip(),
                'category': category,
                'example_order': idx
            })
        
        return examples
    
    def import_schema(self, file_path: Path) -> bool:
        """Import a single schema file to database"""
        try:
            logger.info(f"Processing {file_path.name}...")
            
            # Parse the markdown file
            parsed = self.parse_markdown_file(file_path)
            metadata = parsed['metadata']
            
            # Insert or update data source
            ds_result = self.supabase.table('amc_data_sources').upsert({
                'schema_id': metadata['schema_id'],
                'name': metadata['name'],
                'category': metadata['category'],
                'description': metadata['description'],
                'data_sources': json.dumps(metadata['data_sources']),
                'is_paid_feature': metadata['is_paid_feature'],
                'availability': json.dumps(metadata['availability']) if metadata['availability'] else None,
                'tags': json.dumps(metadata['tags']),
                'version': metadata['version']
            }, on_conflict='schema_id').execute()
            
            if not ds_result.data:
                logger.error(f"Failed to insert data source for {file_path.name}")
                return False
            
            data_source_id = ds_result.data[0]['id']
            
            # Delete existing fields for this data source (for re-import)
            self.supabase.table('amc_schema_fields').delete().eq('data_source_id', data_source_id).execute()
            
            # Insert fields
            if parsed['fields']:
                fields_data = []
                for field in parsed['fields']:
                    fields_data.append({
                        'data_source_id': data_source_id,
                        'field_name': field['field_name'],
                        'data_type': field['data_type'],
                        'dimension_or_metric': field['dimension_or_metric'],
                        'description': field['description'],
                        'aggregation_threshold': field['aggregation_threshold'],
                        'field_category': field.get('field_category'),
                        'examples': json.dumps(field.get('examples')) if field.get('examples') else None,
                        'field_order': field['field_order'],
                        'is_array': field.get('is_array', False)
                    })
                
                # Insert in batches of 100
                for i in range(0, len(fields_data), 100):
                    batch = fields_data[i:i+100]
                    self.supabase.table('amc_schema_fields').insert(batch).execute()
            
            # Delete existing sections and insert new ones
            self.supabase.table('amc_schema_sections').delete().eq('data_source_id', data_source_id).execute()
            
            # Insert sections
            if parsed['sections']:
                for idx, section in enumerate(parsed['sections']):
                    self.supabase.table('amc_schema_sections').insert({
                        'data_source_id': data_source_id,
                        'section_type': section['section_type'],
                        'content_markdown': section['content'],
                        'section_order': idx
                    }).execute()
            
            # Delete existing examples and insert new ones
            self.supabase.table('amc_query_examples').delete().eq('data_source_id', data_source_id).execute()
            
            # Insert query examples
            if parsed['examples']:
                for example in parsed['examples']:
                    self.supabase.table('amc_query_examples').insert({
                        'data_source_id': data_source_id,
                        'title': example['title'],
                        'sql_query': example['sql_query'],
                        'category': example['category'],
                        'example_order': example['example_order']
                    }).execute()
            
            logger.info(f"Successfully imported {metadata['name']} with {len(parsed['fields'])} fields and {len(parsed['examples'])} examples")
            return True
            
        except Exception as e:
            logger.error(f"Error importing {file_path.name}: {str(e)}")
            return False
    
    def create_relationships(self):
        """Create relationships between schemas after all are imported"""
        try:
            # Define known relationships
            relationships = [
                # Attribution tables variants
                ('amazon-attributed-events', 'amazon-attributed-events-by-traffic-time', 'variant', 
                 'Traffic-time variant of the same attribution data'),
                
                # DSP table relationships
                ('dsp-impressions', 'dsp-clicks', 'related', 
                 'Clicks are a subset of impressions'),
                ('dsp-impressions', 'dsp-views', 'related',
                 'Views are viewable impressions'),
                
                # Conversion relationships
                ('conversions', 'conversions-all', 'extends',
                 'All conversions including modeled data'),
                ('conversions', 'conversions-with-relevance', 'extends',
                 'Conversions with relevance scoring'),
            ]
            
            for source, target, rel_type, desc in relationships:
                # Get source and target IDs
                source_result = self.supabase.table('amc_data_sources').select('id').eq('schema_id', source).execute()
                target_result = self.supabase.table('amc_data_sources').select('id').eq('schema_id', target).execute()
                
                if source_result.data and target_result.data:
                    self.supabase.table('amc_schema_relationships').upsert({
                        'source_schema_id': source_result.data[0]['id'],
                        'target_schema_id': target_result.data[0]['id'],
                        'relationship_type': rel_type,
                        'description': desc
                    }, on_conflict='source_schema_id,target_schema_id,relationship_type').execute()
                    
            logger.info("Schema relationships created successfully")
            
        except Exception as e:
            logger.error(f"Error creating relationships: {str(e)}")
    
    def run(self):
        """Run the full import process"""
        logger.info("Starting AMC schema import...")
        
        # Get all markdown files
        schema_files = sorted(self.schema_dir.glob("*.md"))
        logger.info(f"Found {len(schema_files)} schema files")
        
        # Import each schema
        success_count = 0
        for file_path in schema_files:
            if self.import_schema(file_path):
                success_count += 1
        
        # Create relationships after all imports
        self.create_relationships()
        
        logger.info(f"Import complete: {success_count}/{len(schema_files)} schemas imported successfully")
        
        # Print summary
        result = self.supabase.table('amc_data_sources').select('category', count='exact').execute()
        if result.data:
            logger.info("\nSchema Summary by Category:")
            categories = {}
            for item in result.data:
                cat = item['category']
                categories[cat] = categories.get(cat, 0) + 1
            for cat, count in sorted(categories.items()):
                logger.info(f"  {cat}: {count} schemas")

if __name__ == "__main__":
    importer = AMCSchemaImporter()
    importer.run()