/**
 * Tests for schedule type definitions
 *
 * These tests verify type correctness and serve as documentation for the rolling date range feature.
 */

import { describe, it, expect } from 'vitest';
import type { Schedule, ScheduleConfig, ScheduleCreatePreset } from './schedule';

describe('Schedule Types', () => {
  describe('Schedule interface', () => {
    it('should accept a valid schedule with lookback_days', () => {
      const schedule: Schedule = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        schedule_id: 'schedule-123',
        workflow_id: 'workflow-456',
        user_id: 'user-789',
        name: 'Daily Report',
        description: 'Daily rolling report with 7-day window',
        schedule_type: 'daily',
        lookback_days: 7,
        cron_expression: '0 2 * * *',
        timezone: 'America/New_York',
        is_active: true,
        execution_history_limit: 30,
        auto_pause_on_failure: true,
        failure_threshold: 3,
        consecutive_failures: 0,
        created_at: '2025-10-09T00:00:00Z',
      };

      expect(schedule.lookback_days).toBe(7);
      expect(schedule.schedule_type).toBe('daily');
    });

    it('should accept a schedule with interval_days for interval schedules', () => {
      const schedule: Schedule = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        schedule_id: 'schedule-123',
        workflow_id: 'workflow-456',
        user_id: 'user-789',
        schedule_type: 'interval',
        interval_days: 7,
        lookback_days: 30,
        cron_expression: '0 2 */7 * *',
        timezone: 'UTC',
        is_active: true,
        execution_history_limit: 30,
        auto_pause_on_failure: false,
        failure_threshold: 5,
        consecutive_failures: 0,
        created_at: '2025-10-09T00:00:00Z',
      };

      expect(schedule.interval_days).toBe(7);
      expect(schedule.lookback_days).toBe(30);
    });

    it('should accept all valid schedule_type values', () => {
      const types: Array<Schedule['schedule_type']> = [
        'daily',
        'interval',
        'weekly',
        'monthly',
        'custom',
      ];

      types.forEach((type) => {
        const schedule: Partial<Schedule> = {
          schedule_type: type,
        };
        expect(schedule.schedule_type).toBe(type);
      });
    });

    it('should allow optional lookback_days field', () => {
      const withLookback: Schedule = {
        id: '123',
        schedule_id: 'sched-1',
        workflow_id: 'wf-1',
        user_id: 'user-1',
        schedule_type: 'daily',
        lookback_days: 14,
        cron_expression: '0 2 * * *',
        timezone: 'UTC',
        is_active: true,
        execution_history_limit: 30,
        auto_pause_on_failure: false,
        failure_threshold: 3,
        consecutive_failures: 0,
        created_at: '2025-10-09T00:00:00Z',
      };

      const withoutLookback: Schedule = {
        id: '123',
        schedule_id: 'sched-1',
        workflow_id: 'wf-1',
        user_id: 'user-1',
        schedule_type: 'daily',
        cron_expression: '0 2 * * *',
        timezone: 'UTC',
        is_active: true,
        execution_history_limit: 30,
        auto_pause_on_failure: false,
        failure_threshold: 3,
        consecutive_failures: 0,
        created_at: '2025-10-09T00:00:00Z',
      };

      expect(withLookback.lookback_days).toBe(14);
      expect(withoutLookback.lookback_days).toBeUndefined();
    });
  });

  describe('ScheduleConfig interface', () => {
    it('should accept a valid config with lookbackDays', () => {
      const config: ScheduleConfig = {
        name: 'Daily Rolling Report',
        description: 'Rolling 30-day window',
        type: 'daily',
        lookbackDays: 30,
        timezone: 'America/New_York',
        executeTime: '02:00',
        parameters: {},
        notifications: {
          onSuccess: false,
          onFailure: true,
          email: 'admin@example.com',
        },
      };

      expect(config.lookbackDays).toBe(30);
      expect(config.type).toBe('daily');
    });

    it('should accept interval config with intervalDays and lookbackDays', () => {
      const config: ScheduleConfig = {
        type: 'interval',
        intervalDays: 7,
        lookbackDays: 30,
        timezone: 'UTC',
        executeTime: '03:00',
        parameters: {},
        notifications: {
          onSuccess: true,
          onFailure: true,
        },
      };

      expect(config.intervalDays).toBe(7);
      expect(config.lookbackDays).toBe(30);
    });

    it('should accept weekly config with dayOfWeek', () => {
      const config: ScheduleConfig = {
        type: 'weekly',
        dayOfWeek: 1, // Monday
        lookbackDays: 7,
        timezone: 'America/Los_Angeles',
        executeTime: '09:00',
        parameters: {},
        notifications: {
          onSuccess: false,
          onFailure: false,
        },
      };

      expect(config.dayOfWeek).toBe(1);
      expect(config.lookbackDays).toBe(7);
    });

    it('should accept monthly config with dayOfMonth', () => {
      const config: ScheduleConfig = {
        type: 'monthly',
        dayOfMonth: 1,
        monthlyType: 'specific',
        lookbackDays: 30,
        timezone: 'UTC',
        executeTime: '00:00',
        parameters: {},
        notifications: {
          onSuccess: false,
          onFailure: true,
        },
      };

      expect(config.dayOfMonth).toBe(1);
      expect(config.monthlyType).toBe('specific');
    });

    it('should accept custom CRON config', () => {
      const config: ScheduleConfig = {
        type: 'custom',
        cronExpression: '0 2 * * 1-5', // Weekdays at 2 AM
        lookbackDays: 1,
        timezone: 'UTC',
        executeTime: '02:00',
        parameters: {},
        notifications: {
          onSuccess: false,
          onFailure: false,
        },
      };

      expect(config.cronExpression).toBe('0 2 * * 1-5');
    });

    it('should allow optional lookbackDays field', () => {
      const withLookback: ScheduleConfig = {
        type: 'daily',
        lookbackDays: 14,
        timezone: 'UTC',
        executeTime: '02:00',
        parameters: {},
        notifications: { onSuccess: false, onFailure: false },
      };

      const withoutLookback: ScheduleConfig = {
        type: 'daily',
        timezone: 'UTC',
        executeTime: '02:00',
        parameters: {},
        notifications: { onSuccess: false, onFailure: false },
      };

      expect(withLookback.lookbackDays).toBe(14);
      expect(withoutLookback.lookbackDays).toBeUndefined();
    });
  });

  describe('ScheduleCreatePreset interface', () => {
    it('should accept preset with lookback_days', () => {
      const preset: ScheduleCreatePreset = {
        preset_type: 'daily',
        name: 'Daily Report',
        description: 'Daily report with 7-day rolling window',
        lookback_days: 7,
        timezone: 'America/New_York',
        execute_time: '02:00',
        parameters: {},
        notification_config: {
          on_success: false,
          on_failure: true,
          email: 'admin@example.com',
        },
      };

      expect(preset.lookback_days).toBe(7);
      expect(preset.preset_type).toBe('daily');
    });

    it('should accept preset with interval_days and lookback_days', () => {
      const preset: ScheduleCreatePreset = {
        preset_type: 'interval',
        interval_days: 7,
        lookback_days: 30,
        timezone: 'UTC',
        execute_time: '03:00',
      };

      expect(preset.interval_days).toBe(7);
      expect(preset.lookback_days).toBe(30);
    });

    it('should allow optional fields to be undefined', () => {
      const minimalPreset: ScheduleCreatePreset = {
        preset_type: 'daily',
        timezone: 'UTC',
        execute_time: '02:00',
      };

      expect(minimalPreset.name).toBeUndefined();
      expect(minimalPreset.lookback_days).toBeUndefined();
      expect(minimalPreset.interval_days).toBeUndefined();
    });
  });

  describe('Rolling Date Range Feature - Type Coverage', () => {
    it('should support daily schedule with rolling window', () => {
      const config: ScheduleConfig = {
        type: 'daily',
        lookbackDays: 7, // Always query last 7 days
        dateRangeType: 'rolling',
        windowSizeDays: 7,
        timezone: 'America/New_York',
        executeTime: '02:00',
        parameters: {},
        notifications: { onSuccess: false, onFailure: true },
      };

      // Verify type allows this configuration
      expect(config.type).toBe('daily');
      expect(config.lookbackDays).toBe(7);
      expect(config.dateRangeType).toBe('rolling');
      expect(config.windowSizeDays).toBe(7);
    });

    it('should support weekly schedule with 30-day rolling window', () => {
      const config: ScheduleConfig = {
        type: 'weekly',
        dayOfWeek: 1, // Monday
        lookbackDays: 30, // Always query last 30 days
        dateRangeType: 'rolling',
        windowSizeDays: 30,
        timezone: 'UTC',
        executeTime: '03:00',
        parameters: {},
        notifications: { onSuccess: false, onFailure: false },
      };

      expect(config.lookbackDays).toBe(30);
      expect(config.windowSizeDays).toBe(30);
      expect(config.dateRangeType).toBe('rolling');
      expect(config.dayOfWeek).toBe(1);
    });

    it('should support interval schedule with custom window', () => {
      const config: ScheduleConfig = {
        type: 'interval',
        intervalDays: 14, // Run every 14 days
        lookbackDays: 90, // Query 90-day window each time
        dateRangeType: 'rolling',
        windowSizeDays: 90,
        timezone: 'UTC',
        executeTime: '00:00',
        parameters: {},
        notifications: { onSuccess: true, onFailure: true },
      };

      expect(config.intervalDays).toBe(14);
      expect(config.lookbackDays).toBe(90);
      expect(config.windowSizeDays).toBe(90);
      expect(config.dateRangeType).toBe('rolling');
    });

    it('should support fixed date range type', () => {
      const config: ScheduleConfig = {
        type: 'daily',
        dateRangeType: 'fixed',
        lookbackDays: 7,
        timezone: 'UTC',
        executeTime: '02:00',
        parameters: {},
        notifications: { onSuccess: false, onFailure: false },
      };

      expect(config.dateRangeType).toBe('fixed');
      expect(config.lookbackDays).toBe(7);
    });

    it('should accept both dateRangeType options', () => {
      const rolling: ScheduleConfig['dateRangeType'] = 'rolling';
      const fixed: ScheduleConfig['dateRangeType'] = 'fixed';

      expect(rolling).toBe('rolling');
      expect(fixed).toBe('fixed');
    });
  });
});
