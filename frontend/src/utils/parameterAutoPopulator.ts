import type { InstanceMappings } from '../services/instanceMappingService';

export interface AutoPopulatedParameter {
  value: string | string[];
  isAutoPopulated: boolean;
  source?: 'instance-mapping' | 'manual';
}

export interface ParameterMap {
  [key: string]: AutoPopulatedParameter;
}

/**
 * Auto-populates query parameters from instance mappings
 * Preserves manually set values over auto-populated ones
 *
 * @param mappings - Instance mappings containing brands, ASINs, and campaigns
 * @param currentParams - Current parameter values (if any)
 * @param parameterNames - Map of parameter names to auto-populate (e.g., { brand: 'brand_name', asins: 'asin_list' })
 * @returns Merged parameters with auto-populate metadata
 */
export function autoPopulateParameters(
  mappings: InstanceMappings | null,
  currentParams: Record<string, any> = {},
  parameterNames: {
    brands?: string;
    asins?: string;
    campaigns?: string;
  } = {}
): ParameterMap {
  const result: ParameterMap = {};

  // Process brands
  if (parameterNames.brands && mappings?.brands && mappings.brands.length > 0) {
    const paramName = parameterNames.brands;
    const manualValue = currentParams[paramName];

    if (manualValue !== undefined && manualValue !== null) {
      // Manual value exists - preserve it
      result[paramName] = {
        value: manualValue,
        isAutoPopulated: false,
        source: 'manual',
      };
    } else {
      // Auto-populate from mappings
      result[paramName] = {
        value: mappings.brands,
        isAutoPopulated: true,
        source: 'instance-mapping',
      };
    }
  }

  // Process ASINs
  if (parameterNames.asins && mappings?.asins_by_brand) {
    const paramName = parameterNames.asins;
    const manualValue = currentParams[paramName];

    console.log('[autoPopulateParameters] Processing ASINs:', {
      paramName,
      manualValue,
      asins_by_brand: mappings.asins_by_brand,
    });

    if (manualValue !== undefined && manualValue !== null && manualValue !== '' &&
        !(Array.isArray(manualValue) && manualValue.length === 0)) {
      // Manual value exists - preserve it
      console.log('[autoPopulateParameters] Preserving manual ASIN value');
      result[paramName] = {
        value: manualValue,
        isAutoPopulated: false,
        source: 'manual',
      };
    } else {
      // Auto-populate from mappings - collect all ASINs across all brands
      const allAsins: string[] = [];
      Object.values(mappings.asins_by_brand).forEach((asins: string[]) => {
        allAsins.push(...asins);
      });

      // Remove duplicates
      const uniqueAsins = Array.from(new Set(allAsins));

      console.log('[autoPopulateParameters] Auto-populating ASINs:', uniqueAsins.length);

      result[paramName] = {
        value: uniqueAsins,
        isAutoPopulated: true,
        source: 'instance-mapping',
      };
    }
  }

  // Process campaigns
  if (parameterNames.campaigns && mappings?.campaigns_by_brand) {
    const paramName = parameterNames.campaigns;
    const manualValue = currentParams[paramName];

    if (manualValue !== undefined && manualValue !== null) {
      // Manual value exists - preserve it
      result[paramName] = {
        value: manualValue,
        isAutoPopulated: false,
        source: 'manual',
      };
    } else {
      // Auto-populate from mappings - collect all campaigns across all brands
      const allCampaigns: (string | number)[] = [];
      Object.values(mappings.campaigns_by_brand).forEach((campaigns: (string | number)[]) => {
        allCampaigns.push(...campaigns);
      });

      // Remove duplicates and convert to strings
      const uniqueCampaigns = Array.from(new Set(allCampaigns)).map(c => String(c));

      result[paramName] = {
        value: uniqueCampaigns,
        isAutoPopulated: true,
        source: 'instance-mapping',
      };
    }
  }

  return result;
}

/**
 * Extracts plain parameter values from auto-populated parameter map
 * Used when submitting to API or rendering in forms
 *
 * @param parameterMap - Auto-populated parameter map
 * @returns Plain object with parameter values
 */
export function extractParameterValues(parameterMap: ParameterMap): Record<string, any> {
  const result: Record<string, any> = {};

  Object.entries(parameterMap).forEach(([key, param]) => {
    result[key] = param.value;
  });

  return result;
}

/**
 * Checks if a parameter is auto-populated
 *
 * @param parameterMap - Auto-populated parameter map
 * @param paramName - Parameter name to check
 * @returns True if the parameter is auto-populated
 */
export function isParameterAutoPopulated(parameterMap: ParameterMap, paramName: string): boolean {
  return parameterMap[paramName]?.isAutoPopulated ?? false;
}

/**
 * Marks a parameter as manually set (removes auto-populate flag)
 * Used when user manually changes a parameter value
 *
 * @param parameterMap - Auto-populated parameter map
 * @param paramName - Parameter name to mark as manual
 * @param value - New manual value
 * @returns Updated parameter map
 */
export function markParameterAsManual(
  parameterMap: ParameterMap,
  paramName: string,
  value: any
): ParameterMap {
  return {
    ...parameterMap,
    [paramName]: {
      value,
      isAutoPopulated: false,
      source: 'manual',
    },
  };
}
