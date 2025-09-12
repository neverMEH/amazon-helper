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
    const beforeContext = sql.substring(Math.max(0, position - 50), position).toUpperCase();
    const afterContext = sql.substring(position + match[0].length, Math.min(sql.length, position + match[0].length + 50)).toUpperCase();
    
    // Check for LIKE context
    if (beforeContext.includes('LIKE')) {
      return {
        name: paramName,
        type: 'pattern',
        sqlContext: 'LIKE',
        formatHint: 'Will be formatted as %value% for pattern matching',
        exampleValue: '%Supergoop%',
      };
    }
    
    // Check for IN context
    if (beforeContext.includes(' IN ') || beforeContext.includes(' IN(')) {
      return {
        name: paramName,
        type: 'list',
        sqlContext: 'IN',
        formatHint: 'Comma-separated values will be formatted as (\'value1\', \'value2\')',
        exampleValue: "('item1', 'item2', 'item3')",
      };
    }
    
    // Check for VALUES context
    if (beforeContext.includes('VALUES') || afterContext.includes('VALUES')) {
      return {
        name: paramName,
        type: 'list',
        sqlContext: 'VALUES',
        formatHint: 'Will be formatted as VALUES clause',
        exampleValue: "VALUES ('item1'), ('item2'), ('item3')",
      };
    }
    
    // Check for BETWEEN context
    if (beforeContext.includes('BETWEEN')) {
      return {
        name: paramName,
        type: 'date_range',
        sqlContext: 'BETWEEN',
        formatHint: 'Provide start and end values',
        exampleValue: "'2024-01-01' AND '2024-01-31'",
      };
    }
    
    // Check for comparison operators
    const comparisonOps = ['>=', '<=', '>', '<', '=', '!=', '<>'];
    for (const op of comparisonOps) {
      if (beforeContext.includes(` ${op} `) || beforeContext.endsWith(` ${op}`)) {
        // Try to infer type from column name
        const columnMatch = beforeContext.match(/(\w+)\s*[><=!]+\s*$/);
        if (columnMatch) {
          const columnName = columnMatch[1].toLowerCase();
          if (columnName.includes('date') || columnName.includes('time')) {
            return {
              name: paramName,
              type: 'date',
              sqlContext: 'COMPARISON',
              exampleValue: '2024-01-15',
            };
          }
          if (columnName.includes('count') || columnName.includes('amount') || columnName.includes('price') || columnName.includes('quantity')) {
            return {
              name: paramName,
              type: 'number',
              sqlContext: 'COMPARISON',
              exampleValue: '100',
            };
          }
        }
        
        return {
          name: paramName,
          type: 'text',
          sqlContext: op === '=' ? 'EQUALS' : 'COMPARISON',
        };
      }
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
        const cleanValue = value.replace(/^['"%]+|['"%]+$/g, '');
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
    
    if (context.sqlContext === 'LIKE') {
      type = 'pattern';
    } else if (lowerName.includes('asin')) {
      type = 'asin_list';
    } else if (lowerName.includes('campaign')) {
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
    const formattedValue = formatParameterValue(value, context);
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
    const sampleValue = getSampleValue(param, context);
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