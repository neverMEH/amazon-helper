/**
 * Tests for report type definitions
 *
 * These tests verify type correctness for the report schedule configuration,
 * particularly the rolling date range feature.
 */

import { describe, it, expect } from 'vitest';
import type { Report, ScheduleConfig, CreateReportRequest } from './report';

describe('Report Types', () => {
  describe('ScheduleConfig interface', () => {
    it('should accept a valid schedule config with lookback_days (unified terminology)', () => {
      const config: ScheduleConfig = {
        frequency: 'daily',
        time: '02:00',
        timezone: 'America/New_York',
        lookback_days: 7,
      };

      expect(config.lookback_days).toBe(7);
      expect(config.frequency).toBe('daily');
    });

    it('should accept backfill_period for backward compatibility', () => {
      const config: ScheduleConfig = {
        frequency: 'daily',
        time: '02:00',
        timezone: 'America/New_York',
        backfill_period: 7,
      };

      expect(config.backfill_period).toBe(7);
      expect(config.frequency).toBe('daily');
    });

    it('should accept weekly config with day_of_week', () => {
      const config: ScheduleConfig = {
        frequency: 'weekly',
        time: '03:00',
        day_of_week: 1, // Monday
        timezone: 'UTC',
        lookback_days: 30,
      };

      expect(config.day_of_week).toBe(1);
      expect(config.lookback_days).toBe(30);
    });

    it('should accept monthly config with day_of_month', () => {
      const config: ScheduleConfig = {
        frequency: 'monthly',
        time: '00:00',
        day_of_month: 1,
        timezone: 'America/Los_Angeles',
        lookback_days: 90,
      };

      expect(config.day_of_month).toBe(1);
      expect(config.lookback_days).toBe(90);
    });

    it('should accept all valid frequency values', () => {
      const frequencies: Array<ScheduleConfig['frequency']> = [
        'daily',
        'weekly',
        'monthly',
      ];

      frequencies.forEach((freq) => {
        const config: ScheduleConfig = {
          frequency: freq,
        };
        expect(config.frequency).toBe(freq);
      });
    });

    it('should allow optional lookback_days field', () => {
      const withLookback: ScheduleConfig = {
        frequency: 'daily',
        lookback_days: 14,
      };

      const withoutLookback: ScheduleConfig = {
        frequency: 'daily',
      };

      expect(withLookback.lookback_days).toBe(14);
      expect(withoutLookback.lookback_days).toBeUndefined();
    });
  });

  describe('CreateReportRequest interface', () => {
    it('should accept ad-hoc execution with time_window', () => {
      const request: CreateReportRequest = {
        name: 'Ad-hoc Report',
        template_id: 'template-123',
        instance_id: 'instance-456',
        parameters: { brand: 'TestBrand' },
        execution_type: 'once',
        time_window_start: '2025-09-01',
        time_window_end: '2025-09-30',
      };

      expect(request.execution_type).toBe('once');
      expect(request.time_window_start).toBe('2025-09-01');
      expect(request.time_window_end).toBe('2025-09-30');
    });

    it('should accept recurring execution with schedule_config', () => {
      const request: CreateReportRequest = {
        name: 'Daily Rolling Report',
        description: 'Daily report with 7-day window',
        template_id: 'template-123',
        instance_id: 'instance-456',
        parameters: {},
        execution_type: 'recurring',
        schedule_config: {
          frequency: 'daily',
          time: '02:00',
          timezone: 'UTC',
          lookback_days: 7,
        },
      };

      expect(request.execution_type).toBe('recurring');
      expect(request.schedule_config?.lookback_days).toBe(7);
    });

    it('should accept backfill execution with schedule_config', () => {
      const request: CreateReportRequest = {
        name: 'Historical Backfill',
        template_id: 'template-123',
        instance_id: 'instance-456',
        parameters: {},
        execution_type: 'backfill',
        schedule_config: {
          frequency: 'weekly',
          lookback_days: 365, // Full year backfill
        },
      };

      expect(request.execution_type).toBe('backfill');
      expect(request.schedule_config?.lookback_days).toBe(365);
    });

    it('should accept all valid execution_type values', () => {
      const types: Array<CreateReportRequest['execution_type']> = [
        'once',
        'recurring',
        'backfill',
      ];

      types.forEach((type) => {
        const request: CreateReportRequest = {
          name: 'Test Report',
          instance_id: 'instance-123',
          parameters: {},
          execution_type: type,
        };
        expect(request.execution_type).toBe(type);
      });
    });

    it('should support Snowflake integration options', () => {
      const request: CreateReportRequest = {
        name: 'Snowflake Report',
        template_id: 'template-123',
        instance_id: 'instance-456',
        parameters: {},
        execution_type: 'recurring',
        schedule_config: {
          frequency: 'daily',
          lookback_days: 7,
        },
        snowflake_enabled: true,
        snowflake_table_name: 'daily_metrics',
        snowflake_schema_name: 'analytics',
      };

      expect(request.snowflake_enabled).toBe(true);
      expect(request.snowflake_table_name).toBe('daily_metrics');
    });
  });

  describe('Report interface', () => {
    it('should accept report with schedule_config', () => {
      const report: Report = {
        id: 'report-123',
        name: 'Daily Report',
        template_id: 'template-456',
        instance_id: 'instance-789',
        parameters: {},
        status: 'active',
        frequency: 'daily',
        schedule_config: {
          frequency: 'daily',
          time: '02:00',
          timezone: 'UTC',
          lookback_days: 7,
        },
        created_at: '2025-10-09T00:00:00Z',
        updated_at: '2025-10-09T00:00:00Z',
      };

      expect(report.schedule_config?.lookback_days).toBe(7);
      expect(report.frequency).toBe('daily');
    });

    it('should accept all valid status values', () => {
      const statuses: Array<Report['status']> = [
        'active',
        'paused',
        'failed',
        'completed',
      ];

      statuses.forEach((status) => {
        const report: Partial<Report> = {
          status,
        };
        expect(report.status).toBe(status);
      });
    });

    it('should accept all valid frequency values', () => {
      const frequencies: Array<Report['frequency']> = [
        'once',
        'daily',
        'weekly',
        'monthly',
      ];

      frequencies.forEach((freq) => {
        const report: Partial<Report> = {
          frequency: freq,
        };
        expect(report.frequency).toBe(freq);
      });
    });
  });

  describe('Rolling Date Range Feature - Report Type Coverage', () => {
    it('should support daily report with rolling 7-day window', () => {
      const request: CreateReportRequest = {
        name: 'Daily Performance',
        template_id: 'template-123',
        instance_id: 'instance-456',
        parameters: {},
        execution_type: 'recurring',
        schedule_config: {
          frequency: 'daily',
          time: '02:00',
          timezone: 'America/New_York',
          lookback_days: 7, // Rolling 7-day window
          date_range_type: 'rolling',
          window_size_days: 7,
        },
      };

      expect(request.schedule_config?.lookback_days).toBe(7);
      expect(request.schedule_config?.date_range_type).toBe('rolling');
      expect(request.schedule_config?.window_size_days).toBe(7);
    });

    it('should support weekly report with 30-day rolling window', () => {
      const request: CreateReportRequest = {
        name: 'Weekly Summary',
        template_id: 'template-123',
        instance_id: 'instance-456',
        parameters: {},
        execution_type: 'recurring',
        schedule_config: {
          frequency: 'weekly',
          day_of_week: 1, // Monday
          time: '03:00',
          timezone: 'UTC',
          lookback_days: 30, // Rolling 30-day window
          date_range_type: 'rolling',
          window_size_days: 30,
        },
      };

      expect(request.schedule_config?.lookback_days).toBe(30);
      expect(request.schedule_config?.window_size_days).toBe(30);
      expect(request.schedule_config?.date_range_type).toBe('rolling');
      expect(request.schedule_config?.day_of_week).toBe(1);
    });

    it('should support monthly report with quarterly window', () => {
      const request: CreateReportRequest = {
        name: 'Monthly Trends',
        template_id: 'template-123',
        instance_id: 'instance-456',
        parameters: {},
        execution_type: 'recurring',
        schedule_config: {
          frequency: 'monthly',
          day_of_month: 1,
          time: '00:00',
          timezone: 'America/Los_Angeles',
          lookback_days: 90, // Rolling 90-day (quarterly) window
          date_range_type: 'rolling',
          window_size_days: 90,
        },
      };

      expect(request.schedule_config?.lookback_days).toBe(90);
      expect(request.schedule_config?.window_size_days).toBe(90);
      expect(request.schedule_config?.date_range_type).toBe('rolling');
      expect(request.schedule_config?.day_of_month).toBe(1);
    });

    it('should support fixed date range type', () => {
      const request: CreateReportRequest = {
        name: 'Fixed Range Report',
        template_id: 'template-123',
        instance_id: 'instance-456',
        parameters: {},
        execution_type: 'recurring',
        schedule_config: {
          frequency: 'daily',
          date_range_type: 'fixed',
          lookback_days: 7,
        },
      };

      expect(request.schedule_config?.date_range_type).toBe('fixed');
    });
  });
});
