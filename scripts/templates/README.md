# Build Guide Formatter Usage Guide

This directory contains templates and examples for creating build guides using the Build Guide Formatter tool.

## Quick Start

1. **Use the template**: Start with `build_guide_template.yaml` as your base
2. **Validate your guide**: Test it before uploading
3. **Preview the results**: See what will be created
4. **Upload to database**: Deploy your guide

## Files

- `build_guide_template.yaml` - Complete template with all available options
- `example_simple_guide.yaml` - Simple, beginner-friendly example
- `example_json_guide.json` - JSON format example
- `invalid_guide.yaml` - Example of validation errors (for testing)

## Command Examples

### Basic Usage
```bash
# Validate a guide file
python build_guide_formatter.py --file guide.yaml --validate-only

# Preview what will be created
python build_guide_formatter.py --file guide.yaml --preview

# Upload a new guide
python build_guide_formatter.py --file guide.yaml

# Update an existing guide
python build_guide_formatter.py --file guide.yaml --update
```

### Input Formats
```bash
# YAML file
python build_guide_formatter.py --file guide.yaml

# JSON file  
python build_guide_formatter.py --file guide.json

# Markdown with YAML frontmatter
python build_guide_formatter.py --file guide.md

# From stdin
cat guide.yaml | python build_guide_formatter.py --stdin --format yaml
```

### Advanced Options
```bash
# Verbose output
python build_guide_formatter.py --file guide.yaml --verbose

# Debug mode
python build_guide_formatter.py --file guide.yaml --debug

# Validation only with verbose errors
python build_guide_formatter.py --file guide.yaml --validate-only --verbose
```

## Guide Structure

### Required Fields

**Guide metadata:**
- `name`: Display name for the guide
- `category`: Category for organization 
- `short_description`: Brief summary

**Sections (optional):**
- `section_id`: Unique identifier
- `title`: Display title
- `display_order`: Order in the guide

**Queries (optional):**
- `title`: Query display name
- `sql_query`: The actual SQL
- `display_order`: Order in the guide

**Metrics (optional):**
- `metric_name`: Column/field name
- `display_name`: Human-readable name
- `definition`: Explanation of the metric
- `metric_type`: Either "metric" or "dimension"

### Optional Enhancements

- **Parameters**: Add dynamic parameters to SQL queries
- **Examples**: Include sample results and interpretations  
- **Prerequisites**: List requirements for using the guide
- **Tags**: Enable filtering and search
- **Difficulty levels**: "beginner", "intermediate", "advanced"

## Best Practices

1. **Start Simple**: Use the simple example as a starting point
2. **Validate Early**: Always validate before uploading
3. **Use Preview**: Check the formatted output before deployment
4. **Test Parameters**: Ensure SQL parameter substitution works correctly
5. **Clear Descriptions**: Write helpful descriptions for queries and metrics
6. **Logical Order**: Use display_order to control the flow
7. **Consistent Naming**: Use clear, consistent naming for IDs and fields

## Parameter Types

When defining query parameters, use these types:

- `string`: Text values
- `integer`: Numeric values  
- `boolean`: true/false values
- `array`: Lists of values (e.g., `["value1", "value2"]`)

## SQL Parameter Substitution

Use `{{parameter_name}}` in your SQL queries:

```sql
SELECT *
FROM campaigns
WHERE date_column >= DATE_ADD('day', -{{days_back}}, CURRENT_DATE)
  AND status IN ({{status_list}})
LIMIT {{max_results}}
```

## Common Issues

1. **Duplicate IDs**: Ensure section_id and metric_name values are unique within each guide
2. **Required Fields**: Check that all required fields are present
3. **Invalid Types**: Verify field types match the schema
4. **SQL Syntax**: Ensure SQL queries are valid (basic validation only)
5. **Parameter Mismatch**: Make sure default_parameters match parameters_schema

## Error Messages

The formatter provides detailed validation errors:

```bash
- guide.name: Field "name" is required
- sections[1].section_id: Duplicate section_id: "introduction"  
- queries[0].query_type: Query type must be one of: ['exploratory', 'main_analysis', 'validation']
- metrics[2].metric_type: Metric type must be one of: ['metric', 'dimension']
```

## Getting Help

Run the script with `--help` for full command-line options:

```bash
python build_guide_formatter.py --help
```