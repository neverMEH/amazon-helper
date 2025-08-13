#!/usr/bin/env python3
"""
Comprehensive SQL escaping fix
Properly escapes all single quotes in field descriptions
"""

import re

def fix_sql_file(input_file, output_file):
    """Fix SQL escaping issues comprehensively"""
    
    with open(input_file, 'r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    
    for line in lines:
        # Check if this is an INSERT INTO amc_schema_fields line
        if 'INSERT INTO amc_schema_fields' in line or 'id, ' in line:
            # This is a field insert statement - need to carefully handle it
            if line.strip().startswith("id, '"):
                # This is a field data line that needs fixing
                # Pattern: id, 'field_name', 'data_type', 'dimension_or_metric', 'description', 'threshold', order
                
                # Split the line carefully
                parts = []
                current_part = []
                in_quotes = False
                quote_count = 0
                i = 0
                
                while i < len(line):
                    char = line[i]
                    
                    if char == "'" and (i == 0 or line[i-1] != '\\'):
                        if not in_quotes:
                            in_quotes = True
                            quote_count += 1
                            current_part.append(char)
                        elif i + 1 < len(line) and line[i+1] == "'":
                            # This is an escaped quote
                            current_part.append("''")
                            i += 1  # Skip the next quote
                        else:
                            # End of quoted string
                            in_quotes = False
                            current_part.append(char)
                            
                            # Check if this is followed by a comma (end of field)
                            if i + 1 < len(line) and line[i+1:i+3] == ', ':
                                parts.append(''.join(current_part))
                                current_part = []
                                i += 2  # Skip the comma and space
                                continue
                    else:
                        current_part.append(char)
                    
                    i += 1
                
                # Add the last part
                if current_part:
                    parts.append(''.join(current_part))
                
                # Now fix the description field (usually the 4th quoted field)
                if len(parts) >= 5:
                    # The pattern is typically: id, 'field_name', 'type', 'dim/metric', 'description', 'threshold', number
                    # We need to fix the description part
                    
                    # Find the description part (the longest one, usually)
                    for i, part in enumerate(parts):
                        if i >= 3 and len(part) > 50 and part.startswith("'") and part.endswith("'"):
                            # This is likely the description
                            # Remove outer quotes
                            desc = part[1:-1] if part.startswith("'") and part.endswith("'") else part
                            
                            # Escape all internal single quotes
                            desc = desc.replace("''", "<<<TEMP>>>")  # Temporarily replace already escaped quotes
                            desc = desc.replace("'", "''")  # Escape all single quotes
                            desc = desc.replace("<<<TEMP>>>", "''")  # Put back the already escaped ones
                            
                            # Put the quotes back
                            parts[i] = f"'{desc}'"
                
                # Reconstruct the line
                fixed_line = ', '.join(parts)
                if not fixed_line.endswith('\n'):
                    fixed_line += '\n'
                fixed_lines.append(fixed_line)
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    # Write the fixed content
    with open(output_file, 'w') as f:
        f.writelines(fixed_lines)
    
    print(f"Fixed SQL written to {output_file}")

# Alternative approach - use regex to fix specific problematic patterns
def fix_sql_patterns(input_file, output_file):
    """Fix known problematic patterns in SQL"""
    
    with open(input_file, 'r') as f:
        content = f.read()
    
    # List of patterns that need fixing
    patterns_to_fix = [
        # Fix POSSIBLE VALUES patterns
        (r"POSSIBLE VALUES INCLUDE: '([^']+)', '([^']+)', '([^']+)', AND NULL\.",
         r"POSSIBLE VALUES INCLUDE: ''\1'', ''\2'', ''\3'', AND NULL."),
        
        (r"POSSIBLE VALUES FOR THIS FIELD ARE: '([^']+)', '([^']+)'",
         r"POSSIBLE VALUES FOR THIS FIELD ARE: ''\1'', ''\2''"),
         
        (r"Possible values: '([^']+)' and '([^']+)'",
         r"Possible values: ''\1'' and ''\2''"),
         
        (r"Possible values include: '([^']+)', '([^']+)', '([^']+)', '([^']+)'",
         r"Possible values include: ''\1'', ''\2'', ''\3'', ''\4''"),
         
        (r"Possible values for this field are: '([^']+)', '([^']+)'",
         r"Possible values for this field are: ''\1'', ''\2''"),
         
        # Fix TRUE/FALSE patterns
        (r"VALUES FOR THIS FIELD ARE: '(TRUE|FALSE)', '(TRUE|FALSE)'",
         r"VALUES FOR THIS FIELD ARE: ''\1'', ''\2''"),
         
        (r"Possible values for this field are: '(true|false)', '(true|false)'",
         r"Possible values for this field are: ''\1'', ''\2''"),
         
        # Fix specific enum patterns
        (r"'(Y|N)' \(([^)]+)\)",
         r"''\1'' (\2)"),
         
        # Fix date format examples
        (r"Example value: '([^']+)'",
         r"Example value: ''\1''"),
         
        (r"Example values: '([^']+)', '([^']+)', '([^']+)'",
         r"Example values: ''\1'', ''\2'', ''\3''"),
         
        # Fix any remaining patterns with quotes
        (r"values include: '([^']+)', '([^']+)', and '([^']+)'",
         r"values include: ''\1'', ''\2'', and ''\3''"),
    ]
    
    # Apply all pattern fixes
    for pattern, replacement in patterns_to_fix:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
    
    # Additional manual fixes for complex cases
    # Fix the specific TRUE/FALSE case
    content = content.replace(
        "POSSIBLE VALUES FOR THIS FIELD ARE: 'TRUE', 'FALSE'.",
        "POSSIBLE VALUES FOR THIS FIELD ARE: ''TRUE'', ''FALSE''."
    )
    content = content.replace(
        "Possible values for this field are: 'true', 'false'",
        "Possible values for this field are: ''true'', ''false''"
    )
    
    # Write the fixed content
    with open(output_file, 'w') as f:
        f.write(content)
    
    print(f"Fixed SQL written to {output_file}")

if __name__ == "__main__":
    # Use the pattern-based approach which is more reliable
    fix_sql_patterns('scripts/import_amc_schemas_final.sql', 'scripts/import_amc_schemas_corrected.sql')