/**
 * SQL Parameter Converter Utility
 * Detects hardcoded VALUES patterns and converts them to parameter placeholders
 */

export interface ConversionResult {
  converted: boolean;
  sql: string;
  detectedParameters: string[];
  suggestions: string[];
}

/**
 * Detect and convert hardcoded VALUES patterns to parameter placeholders
 * @param sql Original SQL query
 * @returns Conversion result with converted SQL and detected parameters
 */
export function convertValuesToParameters(sql: string): ConversionResult {
  const detectedParameters: string[] = [];
  const suggestions: string[] = [];
  let convertedSql = sql;
  let converted = false;

  // Pattern 1: Sponsored Products campaign names in CTE
  const spPattern = /SP\s*\([^)]+\)\s*AS\s*\(\s*VALUES\s*\([^)]+\)(?:\s*,\s*\([^)]+\))*\s*\)/gi;
  if (spPattern.test(sql)) {
    convertedSql = convertedSql.replace(spPattern, 'SP (campaign) AS (\n  {{sp_campaign_names}}\n)');
    detectedParameters.push('sp_campaign_names');
    suggestions.push('Converted Sponsored Products campaign VALUES to {{sp_campaign_names}}');
    converted = true;
  }

  // Pattern 2: Display campaign IDs in CTE
  const displayPattern = /Display\s*\([^)]+\)\s*AS\s*\(\s*VALUES\s*\([^)]+\)(?:\s*,\s*\([^)]+\))*\s*\)/gi;
  if (displayPattern.test(sql)) {
    convertedSql = convertedSql.replace(displayPattern, 'Display (campaign_id) AS (\n  {{display_campaign_ids}}\n)');
    detectedParameters.push('display_campaign_ids');
    suggestions.push('Converted Display campaign VALUES to {{display_campaign_ids}}');
    converted = true;
  }

  // Pattern 3: Sponsored Brands campaign names
  const sbPattern = /SB\s*\([^)]+\)\s*AS\s*\(\s*VALUES\s*\([^)]+\)(?:\s*,\s*\([^)]+\))*\s*\)/gi;
  if (sbPattern.test(sql)) {
    convertedSql = convertedSql.replace(sbPattern, 'SB (campaign) AS (\n  {{sb_campaign_names}}\n)');
    detectedParameters.push('sb_campaign_names');
    suggestions.push('Converted Sponsored Brands campaign VALUES to {{sb_campaign_names}}');
    converted = true;
  }

  // Pattern 4: ASIN lists
  const asinPattern = /asins?\s*\([^)]+\)\s*AS\s*\(\s*VALUES\s*\([^)]+\)(?:\s*,\s*\([^)]+\))*\s*\)/gi;
  if (asinPattern.test(sql)) {
    convertedSql = convertedSql.replace(asinPattern, 'asins (asin) AS (\n  {{tracked_asins}}\n)');
    detectedParameters.push('tracked_asins');
    suggestions.push('Converted ASIN VALUES to {{tracked_asins}}');
    converted = true;
  }

  return {
    converted,
    sql: convertedSql,
    detectedParameters,
    suggestions
  };
}

/**
 * Check if SQL contains hardcoded VALUES that should be parameters
 * @param sql SQL query to check
 * @returns true if hardcoded VALUES patterns are detected
 */
export function hasHardcodedValues(sql: string): boolean {
  const patterns = [
    /SP\s*\([^)]+\)\s*AS\s*\(\s*VALUES\s*\(/i,
    /Display\s*\([^)]+\)\s*AS\s*\(\s*VALUES\s*\(/i,
    /SB\s*\([^)]+\)\s*AS\s*\(\s*VALUES\s*\(/i,
    /asins?\s*\([^)]+\)\s*AS\s*\(\s*VALUES\s*\(/i,
    /VALUES\s*\(\s*['"][^'"]*_campaign[^'"]*['"]\s*\)/i,
    /VALUES\s*\(\s*\d{10,}\s*\)/i  // Likely campaign IDs
  ];

  return patterns.some(pattern => pattern.test(sql));
}

/**
 * Suggest parameter names based on SQL context
 * @param sql SQL query
 * @returns Suggested parameter names that might be useful
 */
export function suggestParameterNames(sql: string): string[] {
  const suggestions: string[] = [];
  
  // Check for common patterns and suggest appropriate parameters
  if (/sponsored_products|sp_campaign/i.test(sql)) {
    suggestions.push('sp_campaign_names');
  }
  
  if (/display|dsp|campaign_id/i.test(sql)) {
    suggestions.push('display_campaign_ids');
  }
  
  if (/sponsored_brands|sb_campaign/i.test(sql)) {
    suggestions.push('sb_campaign_names');
  }
  
  if (/asin|product/i.test(sql)) {
    suggestions.push('tracked_asins', 'target_asins', 'promoted_asins');
  }
  
  if (/date|time|period/i.test(sql)) {
    suggestions.push('date_range_start', 'date_range_end');
  }
  
  return [...new Set(suggestions)]; // Remove duplicates
}