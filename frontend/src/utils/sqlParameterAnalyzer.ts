/**
 * SQL Parameter Analyzer - Detects parameter context and determines formatting
 */

export interface ParameterContext {
  name: string;
  type: 'text' | 'number' | 'date' | 'date_range' | 'list' | 'pattern';
  sqlContext: 'LIKE' | 'IN' | 'VALUES' | 'BETWEEN' | 'EQUALS' | 'COMPARISON';
  formatHint?: string;
  exampleValue?: string;
}

export interface ParameterDefinition {
  name: string;
  type: 'text' | 'number' | 'date' | 'date_range' | 'asin_list' | 'campaign_list' | 'pattern' | 'boolean';
  required: boolean;
  defaultValue?: any;
  description?: string;
  sqlContext?: 'LIKE' | 'IN' | 'VALUES' | 'BETWEEN' | 'EQUALS' | 'COMPARISON';
  formatPattern?: string;
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    enum?: string[];
  };
}

/**
 * Analyzes SQL query to detect parameter context
 */
export function analyzeParameterContext(sql: string, paramName: string): ParameterContext {
  const paramPattern = new RegExp(`\\{\\{${paramName}\\}\\}`, 'gi');
  const matches = Array.from(sql.matchAll(paramPattern));
  
  if (matches.length === 0) {
    return {
      name: paramName,
      type: 'text',
      sqlContext: 'EQUALS',
    };
  }

  // Analyze context around each parameter occurrence
  for (const match of matches) {
    const position = match.index!;
    const beforeContext = sql.substring(Math.max(0, position - 50), position);
    const afterContext = sql.substring(position + match[0].length, Math.min(sql.length, position + match[0].length + 50));
    
    // Check for IN context (must be immediately before parameter)
    if (beforeContext.match(/\sIN\s*$/i)) {
      return {
        name: paramName,
        type: 'list',
        sqlContext: 'IN',
        formatHint: 'Comma-separated values will be formatted as (\'value1\', \'value2\')',
        exampleValue: "('item1', 'item2', 'item3')",
      };
    }
    
    // Check for LIKE context (can have quotes and % wildcards between LIKE and parameter)
    if (beforeContext.match(/\sLIKE\s*['"]?%?$/i)) {
      return {
        name: paramName,
        type: 'pattern',
        sqlContext: 'LIKE',
        formatHint: 'Will be formatted as %value% for pattern matching',
        exampleValue: '%Supergoop%',
      };
    }
    
    // Check for VALUES context
    if (beforeContext.toUpperCase().includes('VALUES') || afterContext.toUpperCase().includes('VALUES')) {
      return {
        name: paramName,
        type: 'list',
        sqlContext: 'VALUES',
        formatHint: 'Will be formatted as VALUES clause',
        exampleValue: "VALUES ('item1'), ('item2'), ('item3')",
      };
    }
    
    // Check for BETWEEN context - only for the first parameter after BETWEEN
    if (beforeContext.match(/\sBETWEEN\s*$/i)) {
      return {
        name: paramName,
        type: 'date',
        sqlContext: 'BETWEEN',
        formatHint: 'Start date for BETWEEN clause',
        exampleValue: "'2024-01-01'",
      };
    }
    
    // Check if this is the second parameter in BETWEEN (after AND)
    if (beforeContext.match(/\sAND\s*$/i) && sql.toUpperCase().includes('BETWEEN')) {
      // Look backwards to see if BETWEEN is before the AND
      const fullBefore = sql.substring(0, position).toUpperCase();
      if (fullBefore.lastIndexOf('BETWEEN') > fullBefore.lastIndexOf('WHERE')) {
        return {
          name: paramName,
          type: 'date',
          sqlContext: 'BETWEEN',
          formatHint: 'End date for BETWEEN clause',
          exampleValue: "'2024-01-31'",
        };
      }
    }
    
    // Check for comparison operators
    const comparisonMatch = beforeContext.match(/(\w+)\s*([><=!]+)\s*$/);
    if (comparisonMatch) {
      const columnName = comparisonMatch[1].toLowerCase();
      const operator = comparisonMatch[2];
      
      // Try to infer type from column name
      if (columnName.includes('date') || columnName.includes('time')) {
        return {
          name: paramName,
          type: 'date',
          sqlContext: operator === '=' ? 'EQUALS' : 'COMPARISON',
          exampleValue: '2024-01-15',
        };
      }
      if (columnName.includes('count') || columnName.includes('amount') || 
          columnName.includes('price') || columnName.includes('quantity') || 
          columnName.includes('spend') || columnName.includes('clicks') ||
          columnName.includes('impressions') || columnName.includes('cost')) {
        return {
          name: paramName,
          type: 'number',
          sqlContext: operator === '=' ? 'EQUALS' : 'COMPARISON',
          exampleValue: '100',
        };
      }
      
      return {
        name: paramName,
        type: 'text',
        sqlContext: operator === '=' ? 'EQUALS' : 'COMPARISON',
      };
    }
  }
  
  // Default context
  return {
    name: paramName,
    type: guessTypeFromName(paramName),
    sqlContext: 'EQUALS',
  };
}

/**
 * Guess parameter type from its name
 */
export function guessTypeFromName(name: string): ParameterContext['type'] {
  const lowerName = name.toLowerCase();
  
  if (lowerName.includes('date') || lowerName.includes('time')) return 'date';
  if (lowerName.includes('start') && lowerName.includes('end')) return 'date_range';
  if (lowerName.includes('count') || lowerName.includes('number') || lowerName.includes('limit') || 
      lowerName.includes('amount') || lowerName.includes('price')) return 'number';
  if (lowerName.includes('pattern') || lowerName.includes('like') || lowerName.includes('search')) return 'pattern';
  if (lowerName.includes('list') || lowerName.includes('ids') || lowerName.endsWith('s')) return 'list';
  
  return 'text';
}

/**
 * Format parameter value based on its context
 */
export function formatParameterValue(value: any, context: ParameterContext): string {
  if (value === null || value === undefined || value === '') {
    return "''";
  }

  switch (context.sqlContext) {
    case 'LIKE':
      // Format for LIKE pattern matching
      if (typeof value === 'string') {
        // Remove any existing quotes and wildcards from the value
        const cleanValue = value.replace(/^['"%]+|['"%]+$/g, '');
        // Don't add wildcards if the SQL template already has them
        // This will be handled by the isPlaceholderInQuotes check
        return `'%${cleanValue}%'`;
      }
      return `'%${value}%'`;
    
    case 'IN':
      // Format list for IN clause
      if (Array.isArray(value)) {
        return `(${value.map(v => `'${v}'`).join(', ')})`;
      }
      if (typeof value === 'string' && value.includes(',')) {
        const items = value.split(',').map(s => s.trim());
        return `(${items.map(v => `'${v}'`).join(', ')})`;
      }
      return `('${value}')`;
    
    case 'VALUES':
      // Format for VALUES clause
      if (Array.isArray(value)) {
        return value.map(v => `('${v}')`).join(',\n    ');
      }
      if (typeof value === 'string' && value.includes(',')) {
        const items = value.split(',').map(s => s.trim());
        return items.map(v => `('${v}')`).join(',\n    ');
      }
      return `('${value}')`;
    
    case 'BETWEEN':
      // Format for BETWEEN clause (expecting object with start and end)
      if (typeof value === 'object' && value.start && value.end) {
        return `'${value.start}' AND '${value.end}'`;
      }
      return `'${value}' AND '${value}'`;
    
    case 'COMPARISON':
      // Format based on type
      if (context.type === 'number') {
        return String(value);
      }
      if (context.type === 'date') {
        return `'${value}'`;
      }
      return `'${value}'`;
    
    case 'EQUALS':
    default:
      // Standard formatting
      if (context.type === 'number') {
        return String(value);
      }
      if (typeof value === 'boolean') {
        return value ? 'true' : 'false';
      }
      if (Array.isArray(value)) {
        return `(${value.map(v => `'${v}'`).join(', ')})`;
      }
      return `'${value}'`;
  }
}

/**
 * Detect all parameters in SQL and analyze their contexts
 */
export function detectParametersWithContext(sql: string): ParameterDefinition[] {
  const paramPattern = /\{\{(\w+)\}\}/g;
  const matches = sql.matchAll(paramPattern);
  const params = Array.from(new Set(Array.from(matches, m => m[1])));
  
  return params.map(paramName => {
    const context = analyzeParameterContext(sql, paramName);
    const lowerName = paramName.toLowerCase();
    
    // Determine specific type based on context and name
    let type: ParameterDefinition['type'] = 'text';

    // LIKE context should always take precedence for pattern matching
    if (context.sqlContext === 'LIKE') {
      type = 'pattern';
    } else if (lowerName.includes('asin')) {
      type = 'asin_list';
    } else if (lowerName.includes('campaign')) {
      // Only set to campaign_list if NOT using LIKE (already checked above)
      type = 'campaign_list';
    } else if (context.type === 'date') {
      type = 'date';
    } else if (context.type === 'date_range') {
      type = 'date_range';
    } else if (context.type === 'number') {
      type = 'number';
    } else if (lowerName.includes('enabled') || lowerName.includes('active') || lowerName.includes('is_')) {
      type = 'boolean';
    }
    
    return {
      name: paramName,
      type,
      required: true,
      description: '',
      sqlContext: context.sqlContext,
      formatPattern: context.formatHint,
    };
  });
}

/**
 * Replace parameters in SQL with formatted values
 */
export function replaceParametersInSQL(sql: string, parameters: Record<string, any>): string {
  let result = sql;

  for (const [paramName, value] of Object.entries(parameters)) {
    const context = analyzeParameterContext(sql, paramName);

    // Check if the placeholder is already within quotes in the template (with or without wildcards)
    const quotedPlaceholderPattern = new RegExp(`'[%\\s]*\\{\\{${paramName}\\}\\}[%\\s]*'`, 'g');
    const isPlaceholderInQuotes = quotedPlaceholderPattern.test(sql);

    let formattedValue = formatParameterValue(value, context);

    // If placeholder is already in quotes with wildcards (like '%{{param}}%')
    if (isPlaceholderInQuotes && context.sqlContext === 'LIKE') {
      // Just return the plain value without quotes or wildcards
      // since the template already has '%{{param}}%'
      formattedValue = value.toString().replace(/^['"%]+|['"%]+$/g, '');
    } else if (isPlaceholderInQuotes && formattedValue.startsWith("'") && formattedValue.endsWith("'")) {
      // Remove the quotes we would have added since the template already has them
      formattedValue = formattedValue.slice(1, -1);
    }

    const paramPattern = new RegExp(`\\{\\{${paramName}\\}\\}`, 'g');
    result = result.replace(paramPattern, formattedValue);
  }

  return result;
}

/**
 * Generate preview SQL with sample values
 */
export function generatePreviewSQL(sql: string, parameters: ParameterDefinition[]): string {
  let previewSQL = sql;

  parameters.forEach(param => {
    const context = analyzeParameterContext(sql, param.name);
    let sampleValue = getSampleValue(param, context);

    // Check if the placeholder is already within quotes in the template (with or without wildcards)
    const quotedPlaceholderPattern = new RegExp(`'[%\\s]*\\{\\{${param.name}\\}\\}[%\\s]*'`, 'g');
    const isPlaceholderInQuotes = quotedPlaceholderPattern.test(sql);

    // If placeholder is already in quotes with wildcards (like '%{{param}}%')
    if (isPlaceholderInQuotes && context.sqlContext === 'LIKE') {
      // Just use a plain sample value without quotes or wildcards
      sampleValue = 'sample_pattern';
    } else if (isPlaceholderInQuotes && sampleValue.startsWith("'") && sampleValue.endsWith("'")) {
      // Remove the outer quotes since template already has them
      sampleValue = sampleValue.slice(1, -1);
    }

    const paramPattern = new RegExp(`\\{\\{${param.name}\\}\\}`, 'g');
    previewSQL = previewSQL.replace(paramPattern, sampleValue);
  });
  
  return previewSQL;
}

/**
 * Get sample value for parameter based on type and context
 */
function getSampleValue(param: ParameterDefinition, context: ParameterContext): string {
  // Use example value from context if available
  if (context.exampleValue) {
    return context.exampleValue;
  }
  
  // Generate based on type
  switch (param.type) {
    case 'pattern':
      return "'%sample_pattern%'";
    case 'date':
      return "'2024-01-15'";
    case 'date_range':
      return "'2024-01-01' AND '2024-01-31'";
    case 'asin_list':
      return "('B001234567', 'B002345678', 'B003456789')";
    case 'campaign_list':
      return "('Campaign 1', 'Campaign 2')";
    case 'number':
      return '100';
    case 'boolean':
      return 'true';
    default:
      return "'sample_value'";
  }
}