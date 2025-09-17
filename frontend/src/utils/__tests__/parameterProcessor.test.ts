/**
 * Tests for frontend ParameterProcessor
 * Should match backend behavior exactly
 */
import { describe, it, expect } from 'vitest';
import { ParameterProcessor } from '../parameterProcessor';

describe('ParameterProcessor', () => {
  describe('Basic parameter replacement', () => {
    it('should replace string parameters', () => {
      const sql = 'SELECT * FROM table WHERE name = {{name}}';
      const params = { name: 'test' };

      const result = ParameterProcessor.processParameters(sql, params);

      expect(result).toBe("SELECT * FROM table WHERE name = 'test'");
    });

    it('should handle mustache format', () => {
      const sql = 'SELECT * WHERE id = {{user_id}} AND status = {{status}}';
      const params = { user_id: 123, status: 'active' };

      const result = ParameterProcessor.processParameters(sql, params);

      expect(result).toContain('id = 123');
      expect(result).toContain("status = 'active'");
    });

    it('should handle colon format', () => {
      const sql = 'SELECT * WHERE id = :user_id AND name = :name';
      const params = { user_id: 456, name: 'John' };

      const result = ParameterProcessor.processParameters(sql, params);

      expect(result).toContain('id = 456');
      expect(result).toContain("name = 'John'");
    });

    it('should handle dollar format', () => {
      const sql = 'SELECT * WHERE id = $id AND type = $type';
      const params = { id: 789, type: 'admin' };

      const result = ParameterProcessor.processParameters(sql, params);

      expect(result).toContain('id = 789');
      expect(result).toContain("type = 'admin'");
    });
  });

  describe('LIKE pattern detection', () => {
    it('should add wildcards for LIKE patterns by keyword', () => {
      const sql = 'SELECT * FROM campaigns WHERE name LIKE {{campaign_pattern}}';
      const params = { campaign_pattern: 'Nike' };

      const result = ParameterProcessor.processParameters(sql, params);

      expect(result).toContain("'%Nike%'");
    });

    it('should add wildcards for LIKE patterns by context', () => {
      const sql = 'SELECT * FROM campaigns WHERE campaign LIKE {{brand}}';
      const params = { brand: 'Adidas' };

      const result = ParameterProcessor.processParameters(sql, params);

      expect(result).toContain("'%Adidas%'");
    });

    it('should handle campaign_brand with LIKE', () => {
      const sql = 'SELECT * WHERE s.campaign LIKE {{campaign_brand}}';
      const params = { campaign_brand: 'Nike' };

      const result = ParameterProcessor.processParameters(sql, params);

      expect(result).toContain("'%Nike%'");
    });
  });

  describe('Array parameter handling', () => {
    it('should format arrays for IN clauses', () => {
      const sql = 'SELECT * FROM products WHERE asin IN {{asins}}';
      const params = { asins: ['B001', 'B002', 'B003'] };

      const result = ParameterProcessor.processParameters(sql, params);

      expect(result).toContain("('B001','B002','B003')");
    });

    it('should handle empty arrays', () => {
      const sql = 'SELECT * WHERE id IN {{ids}}';
      const params = { ids: [] };

      const result = ParameterProcessor.processParameters(sql, params);

      expect(result).toContain('()');
    });

    it('should format campaign arrays', () => {
      const sql = 'SELECT * WHERE campaign_id IN {{campaign_ids}}';
      const params = { campaign_ids: ['c1', 'c2', 'c3'] };

      const result = ParameterProcessor.processParameters(sql, params);

      expect(result).toContain("('c1','c2','c3')");
    });

    it('should format ASIN arrays', () => {
      const sql = 'SELECT * WHERE asin IN {{tracked_asins}}';
      const params = { tracked_asins: ['B08N5WRWNW', 'B07QR7Y8K3'] };

      const result = ParameterProcessor.processParameters(sql, params);

      expect(result).toContain("('B08N5WRWNW','B07QR7Y8K3')");
    });
  });

  describe('SQL injection prevention', () => {
    it('should prevent SQL injection attempts', () => {
      const sql = 'SELECT * WHERE name = {{name}}';
      const params = { name: "'; DROP TABLE users; --" };

      expect(() => {
        ParameterProcessor.processParameters(sql, params);
      }).toThrow('Dangerous SQL keyword');
    });

    it('should escape single quotes', () => {
      const sql = 'SELECT * WHERE name = {{name}}';
      const params = { name: "O'Brien" };

      const result = ParameterProcessor.processParameters(sql, params);

      expect(result).toContain("O''Brien");
    });
  });

  describe('Type handling', () => {
    it('should handle boolean values', () => {
      const sql = 'SELECT * WHERE active = {{is_active}}';
      const params = { is_active: true };

      const result = ParameterProcessor.processParameters(sql, params);

      expect(result).toContain('active = TRUE');
    });

    it('should handle number values', () => {
      const sql = 'SELECT * WHERE count > {{min_count}} AND price < {{max_price}}';
      const params = { min_count: 10, max_price: 99.99 };

      const result = ParameterProcessor.processParameters(sql, params);

      expect(result).toContain('count > 10');
      expect(result).toContain('price < 99.99');
    });

    it('should handle null values', () => {
      const sql = 'SELECT * WHERE value = {{val}}';
      const params = { val: null };

      const result = ParameterProcessor.processParameters(sql, params);

      expect(result).toContain('NULL');
    });
  });

  describe('Parameter detection', () => {
    it('should detect campaign parameters', () => {
      expect(ParameterProcessor.isCampaignParameter('campaign_id')).toBe(true);
      expect(ParameterProcessor.isCampaignParameter('campaigns')).toBe(true);
      expect(ParameterProcessor.isCampaignParameter('campaign_brand')).toBe(true);
      expect(ParameterProcessor.isCampaignParameter('product_id')).toBe(false);
    });

    it('should detect ASIN parameters', () => {
      expect(ParameterProcessor.isAsinParameter('asin')).toBe(true);
      expect(ParameterProcessor.isAsinParameter('product_asin')).toBe(true);
      expect(ParameterProcessor.isAsinParameter('tracked_asins')).toBe(true);
      expect(ParameterProcessor.isAsinParameter('campaign_id')).toBe(false);
    });
  });

  describe('Parameter info extraction', () => {
    it('should extract parameter information', () => {
      const sql = `
        SELECT * FROM campaigns
        WHERE campaign LIKE {{brand}}
        AND asin IN {{asins}}
        AND date = {{report_date}}
      `;

      const info = ParameterProcessor.getParameterInfo(sql);

      expect(info.brand.isLike).toBe(true);
      expect(info.asins.isAsin).toBe(true);
      expect(info.asins.expectedType).toBe('array');
      expect(info.report_date.expectedType).toBe('string');
    });
  });

  describe('Parameter validation', () => {
    it('should validate parameter types', () => {
      const params = {
        good_param: 'value',
        empty_array: [],
        null_param: null,
        long_string: 'x'.repeat(1500)
      };

      const warnings = ParameterProcessor.validateParameterTypes(params);

      expect(warnings.empty_array).toBeDefined();
      expect(warnings.null_param).toBeDefined();
      expect(warnings.long_string).toBeDefined();
      expect(warnings.good_param).toBeUndefined();
    });

    it('should throw on missing parameters', () => {
      const sql = 'SELECT * WHERE id = {{user_id}} AND name = {{name}}';
      const params = { user_id: 123 }; // Missing 'name'

      expect(() => {
        ParameterProcessor.processParameters(sql, params);
      }).toThrow('Missing required parameters: name');
    });
  });

  describe('Complex real-world queries', () => {
    it('should handle complex AMC query with multiple parameters', () => {
      const sql = `
        SELECT
            s.campaign,
            COUNT(DISTINCT a.user_id) as unique_users
        FROM sponsored_ads s
        JOIN attributions a ON s.campaign_id = a.campaign_id
        WHERE s.campaign LIKE {{campaign_brand}}
        AND s.asin IN {{tracked_asins}}
        AND s.advertiser_id = {{advertiser_id}}
        AND a.event_date BETWEEN {{start_date}} AND {{end_date}}
      `;

      const params = {
        campaign_brand: 'Nike',
        tracked_asins: ['B001', 'B002', 'B003'],
        advertiser_id: 'ADV123',
        start_date: '2024-01-01',
        end_date: '2024-01-31'
      };

      const result = ParameterProcessor.processParameters(sql, params);

      // Check all parameters are correctly substituted
      expect(result).toContain("'%Nike%'"); // LIKE pattern with wildcards
      expect(result).toContain("('B001','B002','B003')"); // Array formatting
      expect(result).toContain("'ADV123'"); // String value
      expect(result).toContain("'2024-01-01'");
      expect(result).toContain("'2024-01-31'");

      // Ensure no placeholders remain
      expect(result).not.toContain('{{');
      expect(result).not.toContain('}}');
    });

    it('should handle multiple occurrences of same parameter', () => {
      const sql = 'SELECT * WHERE a = {{val}} OR b = {{val}} OR c = {{val}}';
      const params = { val: 'test' };

      const result = ParameterProcessor.processParameters(sql, params);

      // Count occurrences of 'test' in the result
      const matches = result.match(/'test'/g);
      expect(matches?.length).toBe(3);
    });
  });
});