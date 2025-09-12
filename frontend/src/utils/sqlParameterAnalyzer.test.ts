import { analyzeParameterContext, formatParameterValue, detectParametersWithContext } from './sqlParameterAnalyzer';

// Test SQL queries with different parameter contexts
const testQueries = {
  likePattern: `
    SELECT * FROM campaigns 
    WHERE campaign_name LIKE {{campaign_pattern}}
  `,
  
  inClause: `
    SELECT * FROM products
    WHERE asin IN {{asins}}
  `,
  
  valuesClause: `
    WITH tracked_asins AS (
      SELECT asin FROM (VALUES {{tracked_asins}}) AS t(asin)
    )
    SELECT * FROM tracked_asins
  `,
  
  betweenDates: `
    SELECT * FROM orders
    WHERE order_date BETWEEN {{date_range}}
  `,
  
  comparisonNumber: `
    SELECT * FROM products
    WHERE price >= {{min_price}}
    AND quantity <= {{max_quantity}}
  `,
  
  mixedQuery: `
    SELECT 
      campaign_name,
      SUM(impressions) as total_impressions
    FROM campaign_performance
    WHERE campaign_name LIKE {{campaign_pattern}}
      AND asin IN {{target_asins}}
      AND performance_date BETWEEN {{start_date}} AND {{end_date}}
      AND spend >= {{min_spend}}
    GROUP BY campaign_name
  `
};

// Test cases
console.log('=== SQL Parameter Analyzer Tests ===\n');

// Test 1: LIKE pattern detection
console.log('Test 1: LIKE Pattern Detection');
const likeContext = analyzeParameterContext(testQueries.likePattern, 'campaign_pattern');
console.log('Context:', likeContext);
console.log('Formatted value:', formatParameterValue('Supergoop', likeContext));
console.log('Expected: %Supergoop%\n');

// Test 2: IN clause detection
console.log('Test 2: IN Clause Detection');
const inContext = analyzeParameterContext(testQueries.inClause, 'asins');
console.log('Context:', inContext);
console.log('Formatted value:', formatParameterValue(['B001', 'B002', 'B003'], inContext));
console.log('Expected: (\'B001\', \'B002\', \'B003\')\n');

// Test 3: VALUES clause detection
console.log('Test 3: VALUES Clause Detection');
const valuesContext = analyzeParameterContext(testQueries.valuesClause, 'tracked_asins');
console.log('Context:', valuesContext);
console.log('Formatted value:', formatParameterValue(['B001', 'B002'], valuesContext));
console.log('Expected: (\'B001\'),\\n    (\'B002\')\n');

// Test 4: Mixed query with multiple contexts
console.log('Test 4: Mixed Query Detection');
const detectedParams = detectParametersWithContext(testQueries.mixedQuery);
console.log('Detected parameters:');
detectedParams.forEach(param => {
  console.log(`  - ${param.name}:`, {
    type: param.type,
    sqlContext: param.sqlContext,
    formatPattern: param.formatPattern
  });
});

// Test 5: Format various values
console.log('\nTest 5: Value Formatting');
const testValues = {
  pattern: { value: 'Sunscreen', context: { name: 'pattern', type: 'pattern' as const, sqlContext: 'LIKE' as const } },
  list: { value: 'item1,item2,item3', context: { name: 'list', type: 'list' as const, sqlContext: 'IN' as const } },
  number: { value: 100, context: { name: 'num', type: 'number' as const, sqlContext: 'COMPARISON' as const } },
  date: { value: '2024-01-15', context: { name: 'date', type: 'date' as const, sqlContext: 'EQUALS' as const } },
};

Object.entries(testValues).forEach(([key, test]) => {
  const formatted = formatParameterValue(test.value, test.context);
  console.log(`${key}: ${test.value} -> ${formatted}`);
});

console.log('\n=== Tests Complete ===');

export {};