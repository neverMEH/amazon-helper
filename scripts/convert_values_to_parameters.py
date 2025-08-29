#!/usr/bin/env python3
"""
Convert SQL queries with hardcoded VALUES placeholders to use parameter syntax.

This script detects patterns like:
  VALUES
    ('SP_campaign_name1'),
    ('SP_campaign_name2')
    
And converts them to parameter placeholders like:
  {{sp_campaign_names}}

It also handles display campaign IDs and other common patterns.
"""

import re
import sys
from typing import Tuple, Optional

def detect_and_convert_values_patterns(sql: str) -> Tuple[str, list]:
    """
    Detect VALUES patterns in SQL and convert them to parameter placeholders.
    
    Returns:
        Tuple of (converted_sql, list_of_detected_parameters)
    """
    detected_params = []
    converted_sql = sql
    
    # Pattern 1: Sponsored Products campaign names in CTE
    # Matches: SP (campaign) AS (VALUES ('name1'), ('name2'))
    sp_pattern = r'(SP\s*\([^)]+\)\s*AS\s*\(\s*VALUES\s*\([^\)]+\)(?:\s*,\s*\([^\)]+\))*\s*\))'
    sp_replacement = r'SP (campaign) AS (\n  {{sp_campaign_names}}\n)'
    
    if re.search(sp_pattern, converted_sql, re.IGNORECASE | re.DOTALL):
        converted_sql = re.sub(sp_pattern, sp_replacement, converted_sql, flags=re.IGNORECASE | re.DOTALL)
        detected_params.append('sp_campaign_names')
        print("✓ Converted Sponsored Products campaign VALUES to {{sp_campaign_names}}")
    
    # Pattern 2: Display campaign IDs in CTE
    # Matches: Display (campaign_id) AS (VALUES (123), (456))
    display_pattern = r'(Display\s*\([^)]+\)\s*AS\s*\(\s*VALUES\s*\([^\)]+\)(?:\s*,\s*\([^\)]+\))*\s*\))'
    display_replacement = r'Display (campaign_id) AS (\n  {{display_campaign_ids}}\n)'
    
    if re.search(display_pattern, converted_sql, re.IGNORECASE | re.DOTALL):
        converted_sql = re.sub(display_pattern, display_replacement, converted_sql, flags=re.IGNORECASE | re.DOTALL)
        detected_params.append('display_campaign_ids')
        print("✓ Converted Display campaign VALUES to {{display_campaign_ids}}")
    
    # Pattern 3: Sponsored Brands campaign names
    sb_pattern = r'(SB\s*\([^)]+\)\s*AS\s*\(\s*VALUES\s*\([^\)]+\)(?:\s*,\s*\([^\)]+\))*\s*\))'
    sb_replacement = r'SB (campaign) AS (\n  {{sb_campaign_names}}\n)'
    
    if re.search(sb_pattern, converted_sql, re.IGNORECASE | re.DOTALL):
        converted_sql = re.sub(sb_pattern, sb_replacement, converted_sql, flags=re.IGNORECASE | re.DOTALL)
        detected_params.append('sb_campaign_names')
        print("✓ Converted Sponsored Brands campaign VALUES to {{sb_campaign_names}}")
    
    # Pattern 4: ASIN lists
    asin_pattern = r'(asins?\s*\([^)]+\)\s*AS\s*\(\s*VALUES\s*\([^\)]+\)(?:\s*,\s*\([^\)]+\))*\s*\))'
    asin_replacement = r'asins (asin) AS (\n  {{tracked_asins}}\n)'
    
    if re.search(asin_pattern, converted_sql, re.IGNORECASE | re.DOTALL):
        converted_sql = re.sub(asin_pattern, asin_replacement, converted_sql, flags=re.IGNORECASE | re.DOTALL)
        detected_params.append('tracked_asins')
        print("✓ Converted ASIN VALUES to {{tracked_asins}}")
    
    # Pattern 5: Generic VALUES in WHERE IN clause
    # Matches: WHERE campaign IN (VALUES ('name1'), ('name2'))
    where_in_pattern = r'(WHERE\s+\w+\s+IN\s*\(\s*VALUES\s*\([^\)]+\)(?:\s*,\s*\([^\)]+\))*\s*\))'
    
    # This is more complex - we need to detect the field name to create appropriate parameter
    matches = re.finditer(r'WHERE\s+(\w+)\s+IN\s*\(\s*VALUES\s*\([^\)]+\)(?:\s*,\s*\([^\)]+\))*\s*\)', 
                         converted_sql, re.IGNORECASE | re.DOTALL)
    
    for match in matches:
        field_name = match.group(1).lower()
        if 'campaign' in field_name:
            if 'id' in field_name:
                param_name = 'campaign_ids'
            else:
                param_name = 'campaign_names'
        elif 'asin' in field_name:
            param_name = 'asin_list'
        else:
            param_name = f'{field_name}_list'
        
        replacement = f'WHERE {match.group(1)} IN ({{{{{param_name}}}}})'
        converted_sql = converted_sql.replace(match.group(0), replacement)
        detected_params.append(param_name)
        print(f"✓ Converted WHERE {match.group(1)} IN VALUES to {{{{{param_name}}}}}")
    
    return converted_sql, detected_params

def process_sql_file(input_file: str, output_file: Optional[str] = None) -> None:
    """
    Process a SQL file and convert VALUES patterns to parameters.
    
    Args:
        input_file: Path to input SQL file
        output_file: Path to output file (if None, will create .converted.sql)
    """
    try:
        with open(input_file, 'r') as f:
            original_sql = f.read()
        
        print(f"\n📄 Processing: {input_file}")
        print("=" * 60)
        
        converted_sql, params = detect_and_convert_values_patterns(original_sql)
        
        if not params:
            print("ℹ️  No VALUES patterns found to convert")
            return
        
        # Determine output file
        if output_file is None:
            output_file = input_file.replace('.sql', '.converted.sql')
        
        # Write converted SQL
        with open(output_file, 'w') as f:
            f.write(converted_sql)
        
        print(f"\n✅ Converted SQL saved to: {output_file}")
        print(f"📊 Parameters detected: {', '.join([f'{{{{{p}}}}}' for p in params])}")
        
        # Show a sample of the changes
        print("\n🔍 Sample changes:")
        print("-" * 40)
        
        # Find first VALUES pattern in original
        values_match = re.search(r'VALUES\s*\([^\)]+\)(?:\s*,\s*\([^\)]+\))*', original_sql, re.DOTALL)
        if values_match:
            print("Original:")
            print(values_match.group(0)[:200] + '...' if len(values_match.group(0)) > 200 else values_match.group(0))
            print("\nConverted to parameter placeholder")
        
    except FileNotFoundError:
        print(f"❌ Error: File '{input_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error processing file: {e}")
        sys.exit(1)

def process_sql_string(sql: str) -> str:
    """
    Process a SQL string and return the converted version.
    
    Args:
        sql: SQL query string
        
    Returns:
        Converted SQL string with parameter placeholders
    """
    converted_sql, params = detect_and_convert_values_patterns(sql)
    
    if params:
        print(f"\n✅ Conversion complete!")
        print(f"📊 Parameters created: {', '.join([f'{{{{{p}}}}}' for p in params])}")
    else:
        print("ℹ️  No VALUES patterns found to convert")
    
    return converted_sql

def main():
    """Main entry point for the script."""
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║     SQL VALUES to Parameter Placeholder Converter           ║
║                                                              ║
║  Converts hardcoded VALUES clauses to parameter syntax      ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python convert_values_to_parameters.py <input.sql> [output.sql]")
        print("\nExample:")
        print("  python convert_values_to_parameters.py overlap_query.sql")
        print("  python convert_values_to_parameters.py query.sql query_converted.sql")
        
        # Demo mode with example
        print("\n" + "=" * 60)
        print("DEMO MODE - Processing example query")
        print("=" * 60)
        
        example_sql = """
WITH Display (campaign_id) AS (
  VALUES
    (11111111111),
    (2222222222)
),
SP (campaign) AS (
  VALUES
    ('SP_campaign_name1'),
    ('SP_campaign_name2')
)
SELECT * FROM campaigns
        """
        
        print("\nOriginal SQL:")
        print(example_sql)
        
        converted = process_sql_string(example_sql)
        
        print("\nConverted SQL:")
        print(converted)
        
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        process_sql_file(input_file, output_file)

if __name__ == "__main__":
    main()