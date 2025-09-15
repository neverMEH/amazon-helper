import { detectParametersWithContext, analyzeParameterContext, replaceParametersInSQL } from './sqlParameterAnalyzer';

// Test SQL with multiple parameters in different contexts
const testSQL = `
SELECT 
  campaign_name,
  SUM(impressions) as total_impressions,
  SUM(clicks) as total_clicks
FROM campaign_performance
WHERE campaign_name LIKE {{campaign_pattern}}
  AND asin IN {{target_asins}}
  AND performance_date BETWEEN {{start_date}} AND {{end_date}}
  AND spend >= {{min_spend}}
  AND region = {{region}}
GROUP BY campaign_name
HAVING total_clicks > {{min_clicks}}
`;

console.log('=== Testing Multiple Parameter Detection ===\n');
console.log('Test SQL:', testSQL);
console.log('\n--- Detected Parameters ---\n');

// Detect all parameters with their contexts
const detectedParams = detectParametersWithContext(testSQL);

console.log(`Found ${detectedParams.length} parameters:\n`);

detectedParams.forEach((param, index) => {
  console.log(`${index + 1}. Parameter: {{${param.name}}}`);
  console.log(`   Type: ${param.type}`);
  console.log(`   SQL Context: ${param.sqlContext}`);
  if (param.formatPattern) {
    console.log(`   Format Hint: ${param.formatPattern}`);
  }
  
  // Analyze context for each parameter
  const context = analyzeParameterContext(testSQL, param.name);
  if (context.exampleValue) {
    console.log(`   Example: ${context.exampleValue}`);
  }
  console.log('');
});

// Test parameter replacement with sample values
const testValues = {
  campaign_pattern: 'Sunscreen',
  target_asins: ['B001', 'B002', 'B003'],
  start_date: '2024-01-01',
  end_date: '2024-01-31',
  min_spend: 100,
  region: 'US',
  min_clicks: 50
};

console.log('\n--- Testing Parameter Replacement ---\n');
console.log('Input values:', testValues);
console.log('\n--- Formatted SQL ---\n');

const formattedSQL = replaceParametersInSQL(testSQL, testValues);
console.log(formattedSQL);

// Test another query with ASINs in VALUES clause
const valuesTestSQL = `
WITH tracked_asins AS (
  SELECT asin FROM (VALUES {{tracked_asins}}) AS t(asin)
),
competitor_asins AS (
  SELECT asin FROM (VALUES {{competitor_asins}}) AS t(asin)
)
SELECT 
  t.asin as tracked,
  c.asin as competitor,
  performance_score
FROM tracked_asins t
CROSS JOIN competitor_asins c
WHERE campaign_name LIKE {{brand_pattern}}
  AND date = {{analysis_date}}
`;

console.log('\n=== Testing VALUES Clause with Multiple Parameters ===\n');
const valuesParams = detectParametersWithContext(valuesTestSQL);
console.log(`Found ${valuesParams.length} parameters in VALUES query:\n`);

valuesParams.forEach((param) => {
  console.log(`- {{${param.name}}}: ${param.type} (${param.sqlContext})`);
});

const valuesTestData = {
  tracked_asins: ['B001', 'B002'],
  competitor_asins: ['B101', 'B102', 'B103'],
  brand_pattern: 'Neutrogena',
  analysis_date: '2024-01-15'
};

console.log('\nFormatted VALUES query:');
console.log(replaceParametersInSQL(valuesTestSQL, valuesTestData));

export {};