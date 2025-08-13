#!/usr/bin/env python3
"""
Standalone AMC Schema Importer
Imports schema documentation without external dependencies
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_import_sql():
    """Generate SQL statements to import all schemas"""
    
    schema_dir = Path("amc_dataset")
    
    # Schema categories mapping
    categories = {
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
    
    sql_statements = []
    
    # Process each schema file
    for file_path in sorted(schema_dir.glob("*.md")):
        logger.info(f"Processing {file_path.name}...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract schema ID from filename
        schema_id = file_path.stem.replace('_schema', '').replace('_', '-')
        
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
        category = "Core Tables"
        schema_lower = schema_id.lower()
        for key, cat_name in categories.items():
            if key in schema_lower:
                category = cat_name
                break
        
        # Check if it's a paid feature
        is_paid = "true" if ("AMC Paid Features" in content or "subscription" in content.lower()) else "false"
        
        # Extract description from overview
        overview_match = re.search(r'##\s+Overview\s*\n+(.*?)(?=\n##|\Z)', content, re.DOTALL)
        description = ""
        if overview_match:
            desc_lines = overview_match.group(1).strip().split('\n')
            for line in desc_lines:
                if line.strip() and not line.startswith('**Data Source') and not line.startswith('-'):
                    description = line.strip().replace("'", "''")  # Escape single quotes
                    break
        
        # Generate tags
        tags = []
        if 'dsp' in schema_lower:
            tags.extend(['dsp', 'display', 'programmatic'])
        if 'attribution' in schema_lower or 'attributed' in schema_lower:
            tags.extend(['attribution', 'conversion'])
        if 'conversion' in schema_lower:
            tags.extend(['conversion', 'purchase'])
        if 'brand_store' in schema_lower:
            tags.extend(['brand-store', 'storefront'])
        if 'audience' in schema_lower:
            tags.extend(['audience', 'segments', 'targeting'])
        if 'sponsored' in schema_lower:
            tags.extend(['sponsored-ads', 'search-ads'])
        if 'impression' in content.lower():
            tags.append('impressions')
        if 'click' in content.lower():
            tags.append('clicks')
        tags = list(set(tags))  # Remove duplicates
        
        # Create INSERT statement for data source
        sql = f"""
-- Insert schema: {title}
INSERT INTO amc_data_sources (
    schema_id, name, category, description, data_sources, 
    is_paid_feature, tags, version
) VALUES (
    '{schema_id}',
    '{title.replace("'", "''")}',
    '{category}',
    '{description}',
    '{json.dumps(data_sources)}',
    {is_paid},
    '{json.dumps(tags)}',
    '1.0.0'
) ON CONFLICT (schema_id) DO UPDATE SET
    name = EXCLUDED.name,
    category = EXCLUDED.category,
    description = EXCLUDED.description,
    data_sources = EXCLUDED.data_sources,
    tags = EXCLUDED.tags,
    updated_at = CURRENT_TIMESTAMP;
"""
        sql_statements.append(sql)
        
        # Parse and insert fields
        field_sql = parse_fields(content, schema_id)
        if field_sql:
            sql_statements.append(field_sql)
        
        # Parse and insert examples
        example_sql = parse_examples(content, schema_id)
        if example_sql:
            sql_statements.append(example_sql)
    
    # Add relationship statements
    relationship_sql = create_relationships()
    sql_statements.append(relationship_sql)
    
    return '\n'.join(sql_statements)


def parse_fields(content: str, schema_id: str) -> str:
    """Parse field definitions from markdown table"""
    sql_parts = []
    
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
                field_name = parts[0] if len(parts) > 0 else ''
                data_type = parts[1] if len(parts) > 1 else 'STRING'
                dimension_or_metric = parts[2] if len(parts) > 2 else 'Dimension'
                description = parts[3].replace("'", "''") if len(parts) > 3 else ''
                aggregation_threshold = parts[4] if len(parts) > 4 else 'LOW'
                
                if field_name and field_name not in ['Name', 'Field Category']:  # Skip header rows
                    sql = f"""
INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, '{field_name}', '{data_type.upper()}', '{dimension_or_metric}',
    '{description}', '{aggregation_threshold.upper()}', {field_order}
FROM amc_data_sources 
WHERE schema_id = '{schema_id}'
ON CONFLICT DO NOTHING;"""
                    sql_parts.append(sql)
                    field_order += 1
    
    return '\n'.join(sql_parts) if sql_parts else ''


def parse_examples(content: str, schema_id: str) -> str:
    """Parse SQL query examples from markdown"""
    sql_parts = []
    
    # Find SQL code blocks
    sql_pattern = r'###?\s*([^\n]+)\n+```sql\n(.*?)\n```'
    matches = re.findall(sql_pattern, content, re.DOTALL)
    
    for idx, (title, sql_query) in enumerate(matches):
        # Clean up title
        title = re.sub(r'^[#\s]+', '', title).strip().replace("'", "''")
        sql_query = sql_query.strip().replace("'", "''")
        
        # Determine category from title
        category = 'Basic'
        if any(word in title.lower() for word in ['advanced', 'complex', 'multi']):
            category = 'Advanced'
        elif any(word in title.lower() for word in ['performance', 'optimize']):
            category = 'Performance'
        elif 'attribution' in title.lower():
            category = 'Attribution'
        
        sql = f"""
INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, '{title}', '{sql_query}', '{category}', {idx}
FROM amc_data_sources 
WHERE schema_id = '{schema_id}'
ON CONFLICT DO NOTHING;"""
        sql_parts.append(sql)
    
    return '\n'.join(sql_parts) if sql_parts else ''


def create_relationships() -> str:
    """Create relationships between schemas"""
    relationships = [
        ('amazon-attributed-events', 'amazon-attributed-events-by-traffic-time', 'variant', 
         'Traffic-time variant of the same attribution data'),
        ('dsp-impressions', 'dsp-clicks', 'related', 
         'Clicks are a subset of impressions'),
        ('dsp-impressions', 'dsp-views', 'related',
         'Views are viewable impressions'),
        ('conversions', 'conversions-all', 'extends',
         'All conversions including modeled data'),
        ('conversions', 'conversions-with-relevance', 'extends',
         'Conversions with relevance scoring'),
    ]
    
    sql_parts = []
    for source, target, rel_type, desc in relationships:
        sql = f"""
INSERT INTO amc_schema_relationships (
    source_schema_id, target_schema_id, relationship_type, description
) SELECT 
    s.id, t.id, '{rel_type}', '{desc.replace("'", "''")}'
FROM amc_data_sources s, amc_data_sources t
WHERE s.schema_id = '{source}' AND t.schema_id = '{target}'
ON CONFLICT DO NOTHING;"""
        sql_parts.append(sql)
    
    return '\n-- Create schema relationships\n' + '\n'.join(sql_parts)


def main():
    """Main function"""
    logger.info("Starting AMC schema SQL generation...")
    
    # Check if schema directory exists
    schema_dir = Path("amc_dataset")
    if not schema_dir.exists():
        logger.error(f"Schema directory not found: {schema_dir}")
        return 1
    
    # Count schema files
    schema_files = list(schema_dir.glob("*.md"))
    logger.info(f"Found {len(schema_files)} schema files")
    
    # Generate SQL
    sql = generate_import_sql()
    
    # Write to file
    output_file = Path("scripts/import_amc_schemas.sql")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("-- AMC Schema Import SQL\n")
        f.write("-- Generated: " + datetime.now().isoformat() + "\n")
        f.write("-- Run this SQL in Supabase SQL Editor\n\n")
        f.write(sql)
    
    logger.info(f"✅ SQL import script generated: {output_file}")
    logger.info("\nNext steps:")
    logger.info("1. Open Supabase Dashboard")
    logger.info("2. Go to SQL Editor")
    logger.info("3. Create New Query")
    logger.info(f"4. Copy contents of {output_file}")
    logger.info("5. Run the query")
    
    # Also print summary
    logger.info(f"\nGenerated import SQL for {len(schema_files)} schemas")
    
    return 0


if __name__ == "__main__":
    exit(main())