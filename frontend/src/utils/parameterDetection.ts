/**
 * Parameter Detection Utility
 * Detects and classifies parameters in SQL queries
 */

export type ParameterType = 'asin' | 'date' | 'campaign' | 'unknown';

export interface DetectedParameter {
  name: string;
  type: ParameterType;
  placeholder: string;
  position: number;
}

export class ParameterDetector {
  // Parameter patterns for different placeholder formats
  private static readonly PLACEHOLDER_PATTERNS = [
    /\{\{([^}]+)\}\}/g,  // {{parameter}}
    /:(\w+)/g,           // :parameter
    /\$(\w+)/g,          // $parameter
  ];

  // Keywords that indicate parameter types (case-insensitive)
  private static readonly ASIN_KEYWORDS = [
    'asin', 'product_asin', 'parent_asin', 'child_asin', 'asins', 'asin_list'
  ];

  private static readonly DATE_KEYWORDS = [
    'date', 'start_date', 'end_date', 'date_from', 'date_to',
    'begin_date', 'finish_date', 'timestamp', 'start_time', 'end_time',
    'date_start', 'date_end', 'from_date', 'to_date'
  ];

  private static readonly CAMPAIGN_KEYWORDS = [
    'campaign', 'campaign_id', 'campaign_name', 'campaigns',
    'campaign_ids', 'campaign_list'
  ];

  /**
   * Detect and classify parameters in a SQL query
   */
  static detectParameters(query: string): DetectedParameter[] {
    const detectedParams: DetectedParameter[] = [];
    const seenParams = new Set<string>();

    // Process each placeholder pattern
    for (const pattern of this.PLACEHOLDER_PATTERNS) {
      // Reset the regex state
      pattern.lastIndex = 0;
      
      let match;
      while ((match = pattern.exec(query)) !== null) {
        const placeholder = match[0];
        const paramName = match[1];

        // Skip if we've already detected this parameter
        if (seenParams.has(paramName)) {
          continue;
        }

        // Skip if it's an escaped placeholder
        if (this.isEscaped(query, match.index)) {
          continue;
        }

        // Classify the parameter type
        const paramType = this.classifyParameter(paramName, query, match.index);

        detectedParams.push({
          name: paramName,
          type: paramType,
          placeholder: placeholder,
          position: match.index
        });
        seenParams.add(paramName);
      }
    }

    // Sort by position in query
    return detectedParams.sort((a, b) => a.position - b.position);
  }

  /**
   * Classify the type of a parameter based on its name and context
   */
  private static classifyParameter(
    paramName: string,
    query: string,
    position: number
  ): ParameterType {
    const paramLower = paramName.toLowerCase();

    // Check for ASIN parameters
    if (this.ASIN_KEYWORDS.some(keyword => paramLower.includes(keyword))) {
      return 'asin';
    }

    // Check for date parameters
    if (this.DATE_KEYWORDS.some(keyword => paramLower.includes(keyword))) {
      return 'date';
    }

    // Check for campaign parameters
    if (this.CAMPAIGN_KEYWORDS.some(keyword => paramLower.includes(keyword))) {
      return 'campaign';
    }

    // Try to infer from context around the parameter
    const context = this.getContext(query, position);
    const contextLower = context.toLowerCase();

    // Check context for ASIN indicators
    if (['asin', 'product'].some(keyword => contextLower.includes(keyword))) {
      return 'asin';
    }

    // Check context for date indicators
    if (['date', 'time', 'between', 'from', 'to'].some(keyword => contextLower.includes(keyword))) {
      return 'date';
    }

    // Check context for campaign indicators
    if (contextLower.includes('campaign')) {
      return 'campaign';
    }

    // Default to unknown if we can't classify
    return 'unknown';
  }

  /**
   * Get the context around a parameter position
   */
  private static getContext(query: string, position: number, contextSize: number = 30): string {
    const start = Math.max(0, position - contextSize);
    const end = Math.min(query.length, position + contextSize);
    return query.slice(start, end);
  }

  /**
   * Check if a placeholder is escaped (preceded by backslash)
   */
  private static isEscaped(query: string, position: number): boolean {
    if (position === 0) {
      return false;
    }
    return query[position - 1] === '\\';
  }

  /**
   * Format parameter values for SQL substitution
   */
  static formatParameterValue(value: any, type: ParameterType): string {
    if (type === 'date') {
      // Ensure no timezone suffix for AMC
      if (typeof value === 'string' && value.endsWith('Z')) {
        return value.slice(0, -1);
      }
      return value;
    }

    if (type === 'asin' || type === 'campaign') {
      // Handle arrays for multi-select
      if (Array.isArray(value)) {
        // Format for SQL IN clause
        return value.map(v => `'${v}'`).join(',');
      }
      return `'${value}'`;
    }

    return value;
  }
}

// Debounce utility for parameter detection
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout> | null = null;
  
  return (...args: Parameters<T>) => {
    if (timeout) {
      clearTimeout(timeout);
    }
    
    timeout = setTimeout(() => {
      func(...args);
    }, wait);
  };
}