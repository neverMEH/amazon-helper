import { describe, it, expect } from 'vitest';
import {
  analyzeParameterContext,
  detectParametersWithContext,
  formatParameterValue,
  replaceParametersInSQL,
  generatePreviewSQL,
  guessTypeFromName,
} from '../sqlParameterAnalyzer';

describe('sqlParameterAnalyzer', () => {
  describe('analyzeParameterContext', () => {
    it('detects IN context correctly', () => {
      const sql = 'SELECT * FROM campaigns WHERE campaign_id IN {{campaign_ids}}';
      const context = analyzeParameterContext(sql, 'campaign_ids');

      expect(context.sqlContext).toBe('IN');
      expect(context.type).toBe('list');
      expect(context.formatHint).toContain('Comma-separated values');
    });

    it('detects LIKE context correctly', () => {
      const sql = 'SELECT * FROM products WHERE name LIKE {{search_pattern}}';
      const context = analyzeParameterContext(sql, 'search_pattern');

      expect(context.sqlContext).toBe('LIKE');
      expect(context.type).toBe('pattern');
      expect(context.formatHint).toContain('pattern matching');
    });

    it('detects VALUES context correctly', () => {
      const sql = 'INSERT INTO temp_asins VALUES {{asin_list}}';
      const context = analyzeParameterContext(sql, 'asin_list');

      expect(context.sqlContext).toBe('VALUES');
      expect(context.type).toBe('list');
      expect(context.formatHint).toContain('VALUES clause');
    });

    it('detects BETWEEN context for start date', () => {
      const sql = 'SELECT * FROM orders WHERE date BETWEEN {{start_date}} AND {{end_date}}';
      const context = analyzeParameterContext(sql, 'start_date');

      expect(context.sqlContext).toBe('BETWEEN');
      expect(context.type).toBe('date');
      expect(context.formatHint).toContain('Start date');
    });

    it('detects BETWEEN context for end date', () => {
      const sql = 'SELECT * FROM orders WHERE date BETWEEN {{start_date}} AND {{end_date}}';
      const context = analyzeParameterContext(sql, 'end_date');

      expect(context.sqlContext).toBe('BETWEEN');
      expect(context.type).toBe('date');
      expect(context.formatHint).toContain('End date');
    });

    it('detects EQUALS context for simple comparisons', () => {
      const sql = 'SELECT * FROM users WHERE user_id = {{user_id}}';
      const context = analyzeParameterContext(sql, 'user_id');

      expect(context.sqlContext).toBe('EQUALS');
    });

    it('detects COMPARISON context for inequality operators', () => {
      const sql = 'SELECT * FROM metrics WHERE impressions > {{min_impressions}}';
      const context = analyzeParameterContext(sql, 'min_impressions');

      expect(context.sqlContext).toBe('COMPARISON');
      expect(context.type).toBe('number');
    });

    it('infers date type from column name', () => {
      const sql = 'SELECT * FROM events WHERE event_date = {{target_date}}';
      const context = analyzeParameterContext(sql, 'target_date');

      expect(context.type).toBe('date');
    });

    it('infers number type from metric column names', () => {
      const sql = 'SELECT * FROM campaigns WHERE spend > {{max_spend}}';
      const context = analyzeParameterContext(sql, 'max_spend');

      expect(context.type).toBe('number');
    });

    it('handles case-insensitive SQL keywords', () => {
      const sql = 'SELECT * FROM products WHERE name like {{pattern}}';
      const context = analyzeParameterContext(sql, 'pattern');

      expect(context.sqlContext).toBe('LIKE');
    });

    it('handles multiple parameter occurrences', () => {
      const sql = 'SELECT * FROM orders WHERE user_id = {{user_id}} OR manager_id = {{user_id}}';
      const context = analyzeParameterContext(sql, 'user_id');

      expect(context.sqlContext).toBe('EQUALS');
    });
  });

  describe('guessTypeFromName', () => {
    it('guesses date type from parameter names', () => {
      expect(guessTypeFromName('start_date')).toBe('date');
      expect(guessTypeFromName('end_time')).toBe('date');
      expect(guessTypeFromName('created_date')).toBe('date');
    });

    it('guesses number type from parameter names', () => {
      expect(guessTypeFromName('count')).toBe('number');
      expect(guessTypeFromName('total_amount')).toBe('number');
      expect(guessTypeFromName('price')).toBe('number');
      expect(guessTypeFromName('limit')).toBe('number');
    });

    it('guesses pattern type from parameter names', () => {
      expect(guessTypeFromName('search_pattern')).toBe('pattern');
      expect(guessTypeFromName('like_query')).toBe('pattern');
    });

    it('guesses list type from plural names', () => {
      expect(guessTypeFromName('campaign_ids')).toBe('list');
      expect(guessTypeFromName('asins')).toBe('list');
      expect(guessTypeFromName('products')).toBe('list');
    });

    it('returns text as default type', () => {
      expect(guessTypeFromName('random_param')).toBe('text');
      expect(guessTypeFromName('value')).toBe('text');
    });
  });

  describe('formatParameterValue', () => {
    it('formats values for LIKE context', () => {
      const context = { name: 'pattern', type: 'pattern' as const, sqlContext: 'LIKE' as const };

      expect(formatParameterValue('test', context)).toBe("'%test%'");
      expect(formatParameterValue('"test"', context)).toBe("'%test%'");
      expect(formatParameterValue('%test%', context)).toBe("'%test%'");
    });

    it('formats arrays for IN context', () => {
      const context = { name: 'ids', type: 'list' as const, sqlContext: 'IN' as const };

      expect(formatParameterValue(['a', 'b', 'c'], context)).toBe("('a', 'b', 'c')");
      expect(formatParameterValue('a,b,c', context)).toBe("('a', 'b', 'c')");
      expect(formatParameterValue('a, b, c', context)).toBe("('a', 'b', 'c')");
    });

    it('formats arrays for VALUES context', () => {
      const context = { name: 'items', type: 'list' as const, sqlContext: 'VALUES' as const };

      expect(formatParameterValue(['a', 'b', 'c'], context)).toBe("('a'),\n    ('b'),\n    ('c')");
      expect(formatParameterValue('a,b,c', context)).toBe("('a'),\n    ('b'),\n    ('c')");
    });

    it('formats date ranges for BETWEEN context', () => {
      const context = { name: 'date_range', type: 'date' as const, sqlContext: 'BETWEEN' as const };

      expect(formatParameterValue({ start: '2024-01-01', end: '2024-01-31' }, context))
        .toBe("'2024-01-01' AND '2024-01-31'");
    });

    it('formats numbers without quotes', () => {
      const context = { name: 'count', type: 'number' as const, sqlContext: 'EQUALS' as const };

      expect(formatParameterValue(100, context)).toBe('100');
      expect(formatParameterValue('100', context)).toBe('100');
    });

    it('formats booleans', () => {
      const context = { name: 'active', type: 'text' as const, sqlContext: 'EQUALS' as const };

      expect(formatParameterValue(true, context)).toBe('true');
      expect(formatParameterValue(false, context)).toBe('false');
    });

    it('handles null and undefined values', () => {
      const context = { name: 'param', type: 'text' as const, sqlContext: 'EQUALS' as const };

      expect(formatParameterValue(null, context)).toBe("''");
      expect(formatParameterValue(undefined, context)).toBe("''");
      expect(formatParameterValue('', context)).toBe("''");
    });

    it('formats dates with quotes', () => {
      const context = { name: 'date', type: 'date' as const, sqlContext: 'EQUALS' as const };

      expect(formatParameterValue('2024-01-15', context)).toBe("'2024-01-15'");
    });
  });

  describe('detectParametersWithContext', () => {
    it('detects multiple parameters with their contexts', () => {
      const sql = `
        SELECT * FROM campaigns
        WHERE campaign_id IN {{campaign_ids}}
        AND name LIKE {{search_pattern}}
        AND date BETWEEN {{start_date}} AND {{end_date}}
        AND impressions > {{min_impressions}}
      `;

      const params = detectParametersWithContext(sql);

      expect(params).toHaveLength(5);

      const campaignIds = params.find(p => p.name === 'campaign_ids');
      expect(campaignIds?.type).toBe('campaign_list');
      expect(campaignIds?.sqlContext).toBe('IN');

      const searchPattern = params.find(p => p.name === 'search_pattern');
      expect(searchPattern?.type).toBe('pattern');
      expect(searchPattern?.sqlContext).toBe('LIKE');

      const startDate = params.find(p => p.name === 'start_date');
      expect(startDate?.type).toBe('date');
      expect(startDate?.sqlContext).toBe('BETWEEN');

      const minImpressions = params.find(p => p.name === 'min_impressions');
      expect(minImpressions?.type).toBe('number');
      expect(minImpressions?.sqlContext).toBe('COMPARISON');
    });

    it('detects ASIN parameters', () => {
      const sql = 'SELECT * FROM products WHERE asin IN {{asin_list}}';
      const params = detectParametersWithContext(sql);

      expect(params[0].name).toBe('asin_list');
      expect(params[0].type).toBe('asin_list');
    });

    it('detects campaign parameters', () => {
      const sql = 'SELECT * FROM campaigns WHERE campaign_name IN {{campaign_names}}';
      const params = detectParametersWithContext(sql);

      expect(params[0].name).toBe('campaign_names');
      expect(params[0].type).toBe('campaign_list');
    });

    it('detects boolean parameters', () => {
      const sql = 'SELECT * FROM features WHERE is_enabled = {{is_enabled}}';
      const params = detectParametersWithContext(sql);

      expect(params[0].name).toBe('is_enabled');
      expect(params[0].type).toBe('boolean');
    });

    it('removes duplicate parameters', () => {
      const sql = `
        SELECT * FROM orders
        WHERE user_id = {{user_id}}
        OR manager_id = {{user_id}}
      `;

      const params = detectParametersWithContext(sql);

      expect(params).toHaveLength(1);
      expect(params[0].name).toBe('user_id');
    });

    it('marks all parameters as required', () => {
      const sql = 'SELECT * FROM users WHERE id = {{user_id}} AND name = {{user_name}}';
      const params = detectParametersWithContext(sql);

      expect(params.every(p => p.required)).toBe(true);
    });
  });

  describe('replaceParametersInSQL', () => {
    it('replaces all parameters with formatted values', () => {
      const sql = `
        SELECT * FROM campaigns
        WHERE campaign_id IN {{campaign_ids}}
        AND name LIKE {{search}}
        AND impressions > {{min_impressions}}
      `;

      const parameters = {
        campaign_ids: ['CAMP001', 'CAMP002'],
        search: 'summer',
        min_impressions: 1000
      };

      const result = replaceParametersInSQL(sql, parameters);

      expect(result).toContain("('CAMP001', 'CAMP002')");
      expect(result).toContain("'%summer%'");
      expect(result).toContain('1000');
      expect(result).not.toContain('{{');
    });

    it('handles missing parameters gracefully', () => {
      const sql = 'SELECT * FROM users WHERE id = {{user_id}}';
      const parameters = {};

      const result = replaceParametersInSQL(sql, parameters);

      expect(result).toContain("''");
    });

    it('preserves SQL structure and formatting', () => {
      const sql = `SELECT *
FROM table
WHERE col = {{param}}`;

      const parameters = { param: 'value' };
      const result = replaceParametersInSQL(sql, parameters);

      expect(result).toBe(`SELECT *
FROM table
WHERE col = 'value'`);
    });

    it('handles complex nested queries', () => {
      const sql = `
        WITH temp AS (
          SELECT * FROM products WHERE asin IN {{asins}}
        )
        SELECT * FROM temp WHERE name LIKE {{pattern}}
      `;

      const parameters = {
        asins: ['B001', 'B002'],
        pattern: 'Pro'
      };

      const result = replaceParametersInSQL(sql, parameters);

      expect(result).toContain("('B001', 'B002')");
      expect(result).toContain("'%Pro%'");
    });
  });

  describe('generatePreviewSQL', () => {
    it('generates preview with sample values', () => {
      const sql = 'SELECT * FROM campaigns WHERE campaign_id IN {{campaign_ids}}';
      const params = [{
        name: 'campaign_ids',
        type: 'campaign_list' as const,
        required: true,
        sqlContext: 'IN' as const
      }];

      const preview = generatePreviewSQL(sql, params);

      expect(preview).toContain("('Campaign 1', 'Campaign 2')");
      expect(preview).not.toContain('{{campaign_ids}}');
    });

    it('uses context example values when available', () => {
      const sql = 'SELECT * FROM products WHERE name LIKE {{pattern}}';
      const params = detectParametersWithContext(sql);

      const preview = generatePreviewSQL(sql, params);

      expect(preview).toContain('%sample_pattern%');
    });

    it('generates appropriate sample values for each type', () => {
      const sql = `
        SELECT * FROM orders
        WHERE date = {{order_date}}
        AND asin IN {{asin_list}}
        AND amount > {{min_amount}}
        AND active = {{is_active}}
      `;

      const params = detectParametersWithContext(sql);
      const preview = generatePreviewSQL(sql, params);

      expect(preview).toMatch(/'2024-\d{2}-\d{2}'/); // Date format
      expect(preview).toContain("('B001234567'"); // ASIN format
      expect(preview).toMatch(/\d+/); // Number without quotes
      expect(preview).toMatch(/true|false/); // Boolean value
    });
  });

  describe('Edge cases and error handling', () => {
    it('handles empty SQL string', () => {
      const params = detectParametersWithContext('');
      expect(params).toEqual([]);
    });

    it('handles SQL without parameters', () => {
      const sql = 'SELECT * FROM users';
      const params = detectParametersWithContext(sql);
      expect(params).toEqual([]);
    });

    it('handles malformed parameter syntax', () => {
      const sql = 'SELECT * FROM users WHERE id = {user_id}'; // Single braces
      const params = detectParametersWithContext(sql);
      expect(params).toEqual([]);
    });

    it('handles parameters with special characters', () => {
      const sql = 'SELECT * FROM data WHERE field = {{param_with_underscore}}';
      const params = detectParametersWithContext(sql);

      expect(params).toHaveLength(1);
      expect(params[0].name).toBe('param_with_underscore');
    });

    it('handles very long parameter names', () => {
      const longName = 'very_long_parameter_name_that_exceeds_normal_length';
      const sql = `SELECT * FROM table WHERE col = {{${longName}}}`;
      const params = detectParametersWithContext(sql);

      expect(params[0].name).toBe(longName);
    });

    it('handles SQL comments', () => {
      const sql = `
        -- This is a comment with {{fake_param}}
        SELECT * FROM users WHERE id = {{real_param}}
        /* Another comment {{another_fake}} */
      `;

      const params = detectParametersWithContext(sql);

      // Should detect parameters even in comments (as they might be meaningful)
      expect(params.length).toBeGreaterThan(0);
      expect(params.some(p => p.name === 'real_param')).toBe(true);
    });
  });

  describe('Performance scenarios', () => {
    it('handles large SQL queries efficiently', () => {
      const largeSql = Array(100).fill(null).map((_, i) =>
        `SELECT * FROM table${i} WHERE col = {{param${i}}}`
      ).join('\n UNION ALL \n');

      const startTime = performance.now();
      const params = detectParametersWithContext(largeSql);
      const endTime = performance.now();

      expect(params).toHaveLength(100);
      expect(endTime - startTime).toBeLessThan(100); // Should complete within 100ms
    });

    it('handles many parameter replacements efficiently', () => {
      const sql = Array(50).fill(null).map((_, i) =>
        `{{param${i}}}`
      ).join(' AND col = ');

      const parameters = Object.fromEntries(
        Array(50).fill(null).map((_, i) => [`param${i}`, `value${i}`])
      );

      const startTime = performance.now();
      const result = replaceParametersInSQL('SELECT * WHERE col = ' + sql, parameters);
      const endTime = performance.now();

      expect(result).not.toContain('{{');
      expect(endTime - startTime).toBeLessThan(50); // Should complete within 50ms
    });
  });
});