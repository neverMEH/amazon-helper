/**
 * Parameter Processing Utility for AMC SQL Queries
 * Matches backend ParameterProcessor logic for consistent handling
 */

interface ParameterInfo {
  isLike: boolean;
  isCampaign: boolean;
  isAsin: boolean;
  context: 'LIKE' | 'EQUALS' | 'IN';
  expectedType: 'string' | 'array' | 'number' | 'boolean';
}

export class ParameterProcessor {
  // Dangerous SQL keywords to check for injection prevention
  private static DANGEROUS_KEYWORDS = [
    'DROP', 'DELETE FROM', 'INSERT INTO', 'UPDATE', 'ALTER',
    'CREATE', 'EXEC', 'EXECUTE', 'TRUNCATE', 'GRANT', 'REVOKE'
  ];

  // Keywords that indicate campaign parameters
  private static CAMPAIGN_KEYWORDS = [
    'campaign', 'campaign_id', 'campaign_name', 'campaigns',
    'campaign_ids', 'campaign_list', 'campaign_brand'
  ];

  // Keywords that indicate ASIN parameters
  private static ASIN_KEYWORDS = [
    'asin', 'product_asin', 'parent_asin', 'child_asin', 'asins',
    'asin_list', 'tracked_asins', 'target_asins', 'promoted_asins',
    'competitor_asins', 'purchased_asins', 'viewed_asins'
  ];

  /**
   * Process SQL template with parameter substitution
   * @param sqlTemplate SQL query with parameter placeholders
   * @param parameters Parameter values to substitute
   * @returns SQL query with substituted values
   */
  static processParameters(sqlTemplate: string, parameters: Record<string, any>): string {
    // Find all required parameters
    const requiredParams = this.findRequiredParameters(sqlTemplate);

    // Validate required parameters are present
    this.validateParameters(requiredParams, parameters);

    // Substitute parameters
    return this.substituteParameters(sqlTemplate, parameters);
  }

  /**
   * Extract all parameter names from SQL template
   */
  private static findRequiredParameters(sqlTemplate: string): string[] {
    const params = new Set<string>();

    // Pattern for {{parameter}} format
    const mustacheMatches = sqlTemplate.match(/\{\{(\w+)\}\}/g);
    if (mustacheMatches) {
      mustacheMatches.forEach(match => {
        const paramName = match.replace(/\{\{|\}\}/g, '');
        params.add(paramName);
      });
    }

    // Pattern for :parameter format
    const colonMatches = sqlTemplate.match(/:(\w+)\b/g);
    if (colonMatches) {
      colonMatches.forEach(match => {
        const paramName = match.substring(1);
        params.add(paramName);
      });
    }

    // Pattern for $parameter format
    const dollarMatches = sqlTemplate.match(/\$(\w+)\b/g);
    if (dollarMatches) {
      dollarMatches.forEach(match => {
        const paramName = match.substring(1);
        params.add(paramName);
      });
    }

    return Array.from(params);
  }

  /**
   * Validate that all required parameters are provided
   */
  private static validateParameters(requiredParams: string[], providedParams: Record<string, any>): void {
    const missingParams = requiredParams.filter(param => !(param in providedParams));

    if (missingParams.length > 0) {
      console.error('Missing required parameters:', missingParams);
      console.error('Available parameters:', Object.keys(providedParams));
      throw new Error(`Missing required parameters: ${missingParams.join(', ')}`);
    }
  }

  /**
   * Substitute all parameters in SQL template
   */
  private static substituteParameters(sqlTemplate: string, parameters: Record<string, any>): string {
    let query = sqlTemplate;

    for (const [paramName, value] of Object.entries(parameters)) {
      // Format the value based on its type and context
      const formattedValue = this.formatParameterValue(paramName, value, sqlTemplate);

      // Replace all parameter formats
      query = this.replaceParameterFormats(query, paramName, formattedValue);
    }

    return query;
  }

  /**
   * Format parameter value based on type and context
   */
  private static formatParameterValue(paramName: string, value: any, sqlTemplate: string): string {
    // Handle null or undefined
    if (value === null || value === undefined) {
      return 'NULL';
    }

    // Handle arrays/lists
    if (Array.isArray(value)) {
      return this.formatArrayParameter(paramName, value);
    }

    // Handle booleans
    if (typeof value === 'boolean') {
      return value ? 'TRUE' : 'FALSE';
    }

    // Handle numbers
    if (typeof value === 'number') {
      return value.toString();
    }

    // Handle strings
    if (typeof value === 'string') {
      return this.formatStringParameter(paramName, value, sqlTemplate);
    }

    // Default: convert to string
    return String(value);
  }

  /**
   * Format array parameter as SQL IN clause
   */
  private static formatArrayParameter(paramName: string, values: any[]): string {
    const escapedValues = values.map(val => {
      if (typeof val === 'string') {
        // Escape single quotes and check for injection
        const escaped = this.escapeStringValue(val, paramName);
        return `'${escaped}'`;
      }
      return String(val);
    });

    // Return formatted as SQL array
    return `(${escapedValues.join(',')})`;
  }

  /**
   * Format string parameter with proper escaping and wildcard detection
   */
  private static formatStringParameter(paramName: string, value: string, sqlTemplate: string): string {
    // Escape the value first
    const escapedValue = this.escapeStringValue(value, paramName);

    // Check if this parameter is used in a LIKE context
    if (this.isLikeParameter(paramName, sqlTemplate)) {
      // Add wildcards for LIKE pattern matching
      console.log(`✓ Parameter '${paramName}' formatted with wildcards for LIKE clause`);
      return `'%${escapedValue}%'`;
    }

    return `'${escapedValue}'`;
  }

  /**
   * Escape string value and check for SQL injection
   */
  private static escapeStringValue(value: string, paramName: string): string {
    // Escape single quotes
    const escaped = value.replace(/'/g, "''");

    // Check for dangerous SQL keywords
    for (const keyword of this.DANGEROUS_KEYWORDS) {
      if (escaped.toUpperCase().includes(keyword)) {
        throw new Error(`Dangerous SQL keyword '${keyword}' detected in parameter '${paramName}'`);
      }
    }

    return escaped;
  }

  /**
   * Detect if parameter is used in a LIKE context
   */
  private static isLikeParameter(paramName: string, sqlTemplate: string): boolean {
    const paramLower = paramName.toLowerCase();

    // Check if parameter name suggests it's a pattern
    if (paramLower.includes('pattern') || paramLower.includes('like')) {
      console.log(`Parameter '${paramName}' identified as LIKE pattern by name`);
      return true;
    }

    // Check for campaign brand parameters (often used with LIKE)
    if (paramLower.includes('campaign_brand') || paramLower.includes('brand')) {
      console.log(`Parameter '${paramName}' identified as brand pattern`);
      return true;
    }

    // Check for LIKE keyword near parameter in various formats
    const patterns = [
      // Direct LIKE patterns
      new RegExp(`\\bLIKE\\s+['"]?\\s*\\{\\{${paramName}\\}\\}`, 'i'),
      new RegExp(`\\bLIKE\\s+['"]?\\s*:${paramName}\\b`, 'i'),
      new RegExp(`\\bLIKE\\s+['"]?\\s*\\$${paramName}\\b`, 'i'),

      // LIKE anywhere near parameter (within 50 chars)
      new RegExp(`\\bLIKE\\s+.{0,50}\\{\\{${paramName}\\}\\}`, 'i'),
      new RegExp(`\\bLIKE\\s+.{0,50}:${paramName}\\b`, 'i'),
      new RegExp(`\\bLIKE\\s+.{0,50}\\$${paramName}\\b`, 'i'),
    ];

    for (const pattern of patterns) {
      if (pattern.test(sqlTemplate)) {
        console.log(`Parameter '${paramName}' found in LIKE context by regex`);
        return true;
      }
    }

    return false;
  }

  /**
   * Replace all parameter format variations with the formatted value
   */
  private static replaceParameterFormats(query: string, paramName: string, formattedValue: string): string {
    // Replace {{param}} format
    query = query.replace(new RegExp(`\\{\\{${paramName}\\}\\}`, 'g'), formattedValue);

    // Replace :param format
    query = query.replace(new RegExp(`:${paramName}\\b`, 'g'), formattedValue);

    // Replace $param format
    query = query.replace(new RegExp(`\\$${paramName}\\b`, 'g'), formattedValue);

    return query;
  }

  /**
   * Check if parameter name indicates it's a campaign parameter
   */
  static isCampaignParameter(paramName: string): boolean {
    const paramLower = paramName.toLowerCase();
    return this.CAMPAIGN_KEYWORDS.some(keyword => paramLower.includes(keyword));
  }

  /**
   * Check if parameter name indicates it's an ASIN parameter
   */
  static isAsinParameter(paramName: string): boolean {
    const paramLower = paramName.toLowerCase();
    return this.ASIN_KEYWORDS.some(keyword => paramLower.includes(keyword));
  }

  /**
   * Analyze SQL template and return information about each parameter
   */
  static getParameterInfo(sqlTemplate: string): Record<string, ParameterInfo> {
    const params = this.findRequiredParameters(sqlTemplate);
    const paramInfo: Record<string, ParameterInfo> = {};

    for (const param of params) {
      const isLike = this.isLikeParameter(param, sqlTemplate);
      const isCampaign = this.isCampaignParameter(param);
      const isAsin = this.isAsinParameter(param);

      paramInfo[param] = {
        isLike,
        isCampaign,
        isAsin,
        context: isLike ? 'LIKE' : (isCampaign || isAsin) ? 'IN' : 'EQUALS',
        expectedType: (isCampaign || isAsin) ? 'array' : 'string'
      };
    }

    return paramInfo;
  }

  /**
   * Validate and convert parameter types
   * Returns warnings for any issues found
   */
  static validateParameterTypes(parameters: Record<string, any>): Record<string, string> {
    const warnings: Record<string, string> = {};

    for (const [paramName, value] of Object.entries(parameters)) {
      // Check for null values
      if (value === null || value === undefined) {
        warnings[paramName] = `Parameter '${paramName}' has null value`;
      }
      // Check for empty arrays
      else if (Array.isArray(value) && value.length === 0) {
        warnings[paramName] = `Parameter '${paramName}' is an empty list`;
      }
      // Check for extremely long strings (potential issues)
      else if (typeof value === 'string' && value.length > 1000) {
        warnings[paramName] = `Parameter '${paramName}' is very long (${value.length} chars)`;
      }
    }

    return warnings;
  }
}