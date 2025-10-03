/**
 * Utility functions for working with parameterized SQL queries
 */

/**
 * Replace parameter placeholders in SQL with actual values
 * @param sqlQuery The SQL query with {{parameter}} placeholders
 * @param parameters Object containing parameter values
 * @returns SQL query with parameters replaced by actual values
 */
export function replaceParametersInSQL(
  sqlQuery: string,
  parameters: Record<string, any> | null | undefined
): string {
  if (!sqlQuery || !parameters) {
    return sqlQuery || '';
  }

  let result = sqlQuery;

  // Replace each parameter in the SQL
  Object.entries(parameters).forEach(([key, value]) => {
    const placeholder = `{{${key}}}`;
    let replacement: string;

    // Handle different value types
    if (value === null || value === undefined) {
      replacement = 'NULL';
    } else if (typeof value === 'string') {
      // For string values, add quotes unless it's a special SQL keyword
      const upperValue = value.toUpperCase();
      if (upperValue === 'NULL' || upperValue === 'TRUE' || upperValue === 'FALSE') {
        replacement = upperValue;
      } else {
        // Escape single quotes in the string and wrap in quotes
        replacement = `'${value.replace(/'/g, "''")}'`;
      }
    } else if (typeof value === 'boolean') {
      replacement = value ? 'TRUE' : 'FALSE';
    } else if (Array.isArray(value)) {
      // Handle arrays (e.g., for IN clauses)
      if (value.length === 0) {
        replacement = '()';
      } else {
        const quotedValues = value.map(v => {
          if (typeof v === 'string') {
            return `'${v.replace(/'/g, "''")}'`;
          }
          return String(v);
        });
        replacement = `(${quotedValues.join(', ')})`;
      }
    } else if (typeof value === 'object') {
      // Handle objects (might be dates or other complex types)
      if (value instanceof Date) {
        replacement = `'${value.toISOString()}'`;
      } else {
        replacement = `'${JSON.stringify(value)}'`;
      }
    } else {
      // Numbers and other types
      replacement = String(value);
    }

    // Replace all occurrences of the placeholder
    const regex = new RegExp(placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g');
    result = result.replace(regex, replacement);
  });

  return result;
}

/**
 * Format SQL with parameter values shown as comments
 * @param sqlQuery The SQL query with {{parameter}} placeholders
 * @param parameters Object containing parameter values
 * @returns SQL query with parameter values shown as comments
 */
export function formatSQLWithParameterComments(
  sqlQuery: string,
  parameters: Record<string, any> | null | undefined
): string {
  if (!sqlQuery || !parameters || Object.keys(parameters).length === 0) {
    return sqlQuery || '';
  }

  // Build parameter comment block
  const paramLines = Object.entries(parameters)
    .map(([key, value]) => {
      let displayValue: string;

      if (value === null || value === undefined) {
        displayValue = 'NULL';
      } else if (typeof value === 'string') {
        displayValue = `'${value}'`;
      } else if (Array.isArray(value)) {
        if (value.length > 10) {
          displayValue = `[${value.slice(0, 10).join(', ')}, ... (${value.length} total)]`;
        } else {
          displayValue = `[${value.join(', ')}]`;
        }
      } else if (typeof value === 'object') {
        displayValue = JSON.stringify(value);
      } else {
        displayValue = String(value);
      }

      return `-- @${key} = ${displayValue}`;
    })
    .join('\n');

  // Add parameter comments at the top of the query
  return `-- Execution Parameters:\n${paramLines}\n\n${sqlQuery}`;
}

/**
 * Extract parameter names from a SQL query
 * @param sqlQuery The SQL query with {{parameter}} placeholders
 * @returns Array of parameter names found in the query
 */
export function extractParametersFromSQL(sqlQuery: string): string[] {
  if (!sqlQuery) {
    return [];
  }

  const parameterPattern = /\{\{(\w+)\}\}/g;
  const parameters = new Set<string>();
  let match;

  while ((match = parameterPattern.exec(sqlQuery)) !== null) {
    parameters.add(match[1]);
  }

  return Array.from(parameters);
}

/**
 * Check if a SQL query has parameters
 * @param sqlQuery The SQL query to check
 * @returns True if the query contains parameter placeholders
 */
export function hasParameters(sqlQuery: string): boolean {
  if (!sqlQuery) {
    return false;
  }

  const parameterPattern = /\{\{(\w+)\}\}/;
  return parameterPattern.test(sqlQuery);
}

/**
 * Validate that all required parameters have values
 * @param sqlQuery The SQL query with {{parameter}} placeholders
 * @param parameters Object containing parameter values
 * @returns Object with validation result and missing parameters
 */
export function validateParameters(
  sqlQuery: string,
  parameters: Record<string, any> | null | undefined
): { isValid: boolean; missingParameters: string[] } {
  const requiredParams = extractParametersFromSQL(sqlQuery);

  if (requiredParams.length === 0) {
    return { isValid: true, missingParameters: [] };
  }

  if (!parameters) {
    return { isValid: false, missingParameters: requiredParams };
  }

  const missingParameters = requiredParams.filter(param =>
    !(param in parameters) || parameters[param] === undefined
  );

  return {
    isValid: missingParameters.length === 0,
    missingParameters
  };
}