/**
 * Tests for template execution service helper functions
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  generateExecutionName,
  calculateDefaultDateRange,
  formatScheduleDescription,
} from './templateExecutionService';

describe('templateExecutionService helpers', () => {
  describe('generateExecutionName', () => {
    it('should generate correct execution name format', () => {
      const name = generateExecutionName(
        'Nike Brand',
        'Top Products Analysis',
        '2025-10-01',
        '2025-10-31'
      );

      expect(name).toBe('Nike Brand - Top Products Analysis - 2025-10-01 - 2025-10-31');
    });

    it('should handle single-word brand names', () => {
      const name = generateExecutionName(
        'Nike',
        'Campaign Report',
        '2025-09-01',
        '2025-09-30'
      );

      expect(name).toBe('Nike - Campaign Report - 2025-09-01 - 2025-09-30');
    });

    it('should handle long template names', () => {
      const name = generateExecutionName(
        'Test Brand',
        'Very Long Template Name With Multiple Words',
        '2025-01-01',
        '2025-12-31'
      );

      expect(name).toContain('Test Brand');
      expect(name).toContain('Very Long Template Name With Multiple Words');
      expect(name).toContain('2025-01-01');
      expect(name).toContain('2025-12-31');
    });
  });

  describe('calculateDefaultDateRange', () => {
    beforeEach(() => {
      // Mock current date to 2025-10-15
      vi.useFakeTimers();
      vi.setSystemTime(new Date('2025-10-15T12:00:00Z'));
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('should calculate 30-day window with 14-day AMC lag', () => {
      const { start, end } = calculateDefaultDateRange(30);

      // End date: Oct 15 - 14 days = Oct 1
      expect(end).toBe('2025-10-01');

      // Start date: Oct 1 - 30 days = Sep 1
      expect(start).toBe('2025-09-01');
    });

    it('should calculate 7-day window with 14-day AMC lag', () => {
      const { start, end } = calculateDefaultDateRange(7);

      // End date: Oct 15 - 14 days = Oct 1
      expect(end).toBe('2025-10-01');

      // Start date: Oct 1 - 7 days = Sep 24
      expect(start).toBe('2025-09-24');
    });

    it('should calculate 60-day window with 14-day AMC lag', () => {
      const { start, end } = calculateDefaultDateRange(60);

      // End date: Oct 15 - 14 days = Oct 1
      expect(end).toBe('2025-10-01');

      // Start date: Oct 1 - 60 days = Aug 2
      expect(start).toBe('2025-08-02');
    });

    it('should use 30-day default when no window specified', () => {
      const { start, end } = calculateDefaultDateRange();

      expect(end).toBe('2025-10-01');
      expect(start).toBe('2025-09-01');
    });

    it('should return dates in YYYY-MM-DD format', () => {
      const { start, end } = calculateDefaultDateRange(30);

      // Test date format
      expect(start).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      expect(end).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    });
  });

  describe('formatScheduleDescription', () => {
    it('should format daily schedule correctly', () => {
      const description = formatScheduleDescription({
        frequency: 'daily',
        time: '09:00',
        timezone: 'America/New_York',
      });

      expect(description).toBe('Every day at 09:00 America/New_York');
    });

    it('should format weekly schedule with Monday', () => {
      const description = formatScheduleDescription({
        frequency: 'weekly',
        time: '14:30',
        day_of_week: 1, // Monday
        timezone: 'America/Los_Angeles',
      });

      expect(description).toBe('Every Monday at 14:30 America/Los_Angeles');
    });

    it('should format weekly schedule with Sunday', () => {
      const description = formatScheduleDescription({
        frequency: 'weekly',
        time: '08:00',
        day_of_week: 0, // Sunday
        timezone: 'UTC',
      });

      expect(description).toBe('Every Sunday at 08:00 UTC');
    });

    it('should format monthly schedule on 1st', () => {
      const description = formatScheduleDescription({
        frequency: 'monthly',
        time: '00:00',
        day_of_month: 1,
        timezone: 'America/Chicago',
      });

      expect(description).toBe('Every month on the 1st at 00:00 America/Chicago');
    });

    it('should format monthly schedule on 15th', () => {
      const description = formatScheduleDescription({
        frequency: 'monthly',
        time: '12:00',
        day_of_month: 15,
        timezone: 'Europe/London',
      });

      expect(description).toBe('Every month on the 15th at 12:00 Europe/London');
    });

    it('should format monthly schedule on 23rd', () => {
      const description = formatScheduleDescription({
        frequency: 'monthly',
        time: '18:00',
        day_of_month: 23,
        timezone: 'Asia/Tokyo',
      });

      expect(description).toBe('Every month on the 23rd at 18:00 Asia/Tokyo');
    });

    it('should default to Monday for weekly without day_of_week', () => {
      const description = formatScheduleDescription({
        frequency: 'weekly',
        time: '10:00',
        timezone: 'America/New_York',
      });

      expect(description).toContain('Monday');
    });

    it('should default to 1st for monthly without day_of_month', () => {
      const description = formatScheduleDescription({
        frequency: 'monthly',
        time: '10:00',
        timezone: 'America/New_York',
      });

      expect(description).toContain('1st');
    });
  });
});
