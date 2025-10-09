/**
 * Tests for DateRangeStep component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DateRangeStep from './DateRangeStep';
import type { ScheduleConfig } from '../../types/schedule';

describe('DateRangeStep', () => {
  const mockOnChange = vi.fn();
  const mockOnNext = vi.fn();
  const mockOnBack = vi.fn();

  const defaultConfig: ScheduleConfig = {
    type: 'daily',
    timezone: 'UTC',
    executeTime: '02:00',
    parameters: {},
    notifications: {
      onSuccess: false,
      onFailure: true,
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render date range configuration heading', () => {
      render(
        <DateRangeStep
          config={defaultConfig}
          onChange={mockOnChange}
          onNext={mockOnNext}
          onBack={mockOnBack}
        />
      );

      expect(screen.getByText(/Date Range Configuration/i)).toBeInTheDocument();
    });

    it('should render window size selector', () => {
      render(
        <DateRangeStep
          config={defaultConfig}
          onChange={mockOnChange}
          onNext={mockOnNext}
          onBack={mockOnBack}
        />
      );

      // Check for preset buttons which are part of window size selector
      expect(screen.getByRole('button', { name: /7 days.*weekly/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /30 days.*monthly/i })).toBeInTheDocument();
    });

    it('should render rolling/fixed toggle', () => {
      render(
        <DateRangeStep
          config={defaultConfig}
          onChange={mockOnChange}
          onNext={mockOnNext}
          onBack={mockOnBack}
        />
      );

      expect(screen.getByText(/Rolling Window/i)).toBeInTheDocument();
      expect(screen.getByText(/Fixed Lookback/i)).toBeInTheDocument();
    });

    it('should render AMC data lag warning', () => {
      render(
        <DateRangeStep
          config={defaultConfig}
          onChange={mockOnChange}
          onNext={mockOnNext}
          onBack={mockOnBack}
        />
      );

      expect(screen.getByText(/14-day/i)).toBeInTheDocument();
      expect(screen.getByText(/lag/i)).toBeInTheDocument();
    });

    it('should render next 3 executions preview', () => {
      render(
        <DateRangeStep
          config={defaultConfig}
          onChange={mockOnChange}
          onNext={mockOnNext}
          onBack={mockOnBack}
        />
      );

      expect(screen.getByText(/Next 3 Executions/i)).toBeInTheDocument();
    });

    it('should render back and next buttons', () => {
      render(
        <DateRangeStep
          config={defaultConfig}
          onChange={mockOnChange}
          onNext={mockOnNext}
          onBack={mockOnBack}
        />
      );

      expect(screen.getByRole('button', { name: /back/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument();
    });
  });

  describe('Window Size Presets', () => {
    it('should display all preset options', () => {
      render(
        <DateRangeStep
          config={defaultConfig}
          onChange={mockOnChange}
          onNext={mockOnNext}
          onBack={mockOnBack}
        />
      );

      expect(screen.getByText(/7 days/i)).toBeInTheDocument();
      expect(screen.getByText(/14 days/i)).toBeInTheDocument();
      expect(screen.getByText(/30 days/i)).toBeInTheDocument();
      expect(screen.getByText(/60 days/i)).toBeInTheDocument();
      expect(screen.getByText(/90 days/i)).toBeInTheDocument();
    });

    it('should allow selecting a preset', async () => {
      const user = userEvent.setup();

      render(
        <DateRangeStep
          config={defaultConfig}
          onChange={mockOnChange}
          onNext={mockOnNext}
          onBack={mockOnBack}
        />
      );

      const button30Days = screen.getByRole('button', { name: /30 days.*monthly/i });
      await user.click(button30Days);

      expect(mockOnChange).toHaveBeenCalledWith({
        ...defaultConfig,
        lookbackDays: 30,
        windowSizeDays: 30,
      });
    });

    it('should highlight selected preset', () => {
      const configWith30Days = {
        ...defaultConfig,
        lookbackDays: 30,
        windowSizeDays: 30,
      };

      render(
        <DateRangeStep
          config={configWith30Days}
          onChange={mockOnChange}
          onNext={mockOnNext}
          onBack={mockOnBack}
        />
      );

      const button30Days = screen.getByRole('button', { name: /30 days.*monthly/i });
      expect(button30Days.className).toContain('bg-blue');
    });

    it('should support custom window size input', async () => {
      const user = userEvent.setup();

      render(
        <DateRangeStep
          config={defaultConfig}
          onChange={mockOnChange}
          onNext={mockOnNext}
          onBack={mockOnBack}
        />
      );

      const customButton = screen.getByRole('button', { name: /custom/i });
      await user.click(customButton);

      const input = screen.getByLabelText(/Custom days/i);
      await user.clear(input);
      await user.type(input, '45');

      expect(mockOnChange).toHaveBeenCalledWith({
        ...defaultConfig,
        lookbackDays: 45,
        windowSizeDays: 45,
      });
    });
  });

  describe('Date Range Type Toggle', () => {
    it('should default to rolling window', () => {
      render(
        <DateRangeStep
          config={defaultConfig}
          onChange={mockOnChange}
          onNext={mockOnNext}
          onBack={mockOnBack}
        />
      );

      const rollingButton = screen.getByRole('button', { name: /rolling window/i });
      expect(rollingButton).toHaveClass(/bg-blue/);
    });

    it('should allow switching to fixed lookback', async () => {
      const user = userEvent.setup();

      render(
        <DateRangeStep
          config={defaultConfig}
          onChange={mockOnChange}
          onNext={mockOnNext}
          onBack={mockOnBack}
        />
      );

      const fixedButton = screen.getByRole('button', { name: /fixed lookback/i });
      await user.click(fixedButton);

      expect(mockOnChange).toHaveBeenCalledWith({
        ...defaultConfig,
        dateRangeType: 'fixed',
      });
    });

    it('should display explanation for rolling window', () => {
      const rollingConfig = {
        ...defaultConfig,
        dateRangeType: 'rolling' as const,
      };

      render(
        <DateRangeStep
          config={rollingConfig}
          onChange={mockOnChange}
          onNext={mockOnNext}
          onBack={mockOnBack}
        />
      );

      expect(screen.getByText(/Always query the same window size relative to execution date/i)).toBeInTheDocument();
    });

    it('should display explanation for fixed lookback', () => {
      const fixedConfig = {
        ...defaultConfig,
        dateRangeType: 'fixed' as const,
      };

      render(
        <DateRangeStep
          config={fixedConfig}
          onChange={mockOnChange}
          onNext={mockOnNext}
          onBack={mockOnBack}
        />
      );

      expect(screen.getByText(/Always query from execution date back N days/i)).toBeInTheDocument();
    });
  });

  describe('Date Range Preview', () => {
    it('should show preview for daily schedule with 7-day window', () => {
      const config = {
        ...defaultConfig,
        type: 'daily' as const,
        lookbackDays: 7,
        executeTime: '02:00',
      };

      render(
        <DateRangeStep
          config={config}
          onChange={mockOnChange}
          onNext={mockOnNext}
          onBack={mockOnBack}
        />
      );

      // Should show 3 execution previews
      const previews = [
        screen.getByTestId('execution-preview-0'),
        screen.getByTestId('execution-preview-1'),
        screen.getByTestId('execution-preview-2'),
      ];
      expect(previews).toHaveLength(3);
    });

    it('should display date ranges accounting for AMC lag', () => {
      const config = {
        ...defaultConfig,
        type: 'daily' as const,
        lookbackDays: 7,
      };

      render(
        <DateRangeStep
          config={config}
          onChange={mockOnChange}
          onNext={mockOnNext}
          onBack={mockOnBack}
        />
      );

      // Preview should mention 14-day lag in description
      expect(screen.getByText(/accounting for AMC's 14-day lag/i)).toBeInTheDocument();
    });

    it('should update preview when window size changes', async () => {
      const user = userEvent.setup();

      const { rerender } = render(
        <DateRangeStep
          config={defaultConfig}
          onChange={mockOnChange}
          onNext={mockOnNext}
          onBack={mockOnBack}
        />
      );

      const button30Days = screen.getByRole('button', { name: /30 days.*monthly/i });
      await user.click(button30Days);

      // Rerender with updated config
      const updatedConfig = {
        ...defaultConfig,
        lookbackDays: 30,
        windowSizeDays: 30,
      };

      rerender(
        <DateRangeStep
          config={updatedConfig}
          onChange={mockOnChange}
          onNext={mockOnNext}
          onBack={mockOnBack}
        />
      );

      expect(screen.getByText(/30-day window/i)).toBeInTheDocument();
    });
  });

  describe('AMC Data Lag Indicator', () => {
    it('should display warning icon', () => {
      render(
        <DateRangeStep
          config={defaultConfig}
          onChange={mockOnChange}
          onNext={mockOnNext}
          onBack={mockOnBack}
        />
      );

      const alertIcon = screen.getByTestId('amc-lag-alert');
      expect(alertIcon).toBeInTheDocument();
    });

    it('should explain AMC data availability', () => {
      render(
        <DateRangeStep
          config={defaultConfig}
          onChange={mockOnChange}
          onNext={mockOnNext}
          onBack={mockOnBack}
        />
      );

      expect(screen.getByText(/Amazon Marketing Cloud data has a 14-day processing lag/i)).toBeInTheDocument();
    });

    it('should show lag is automatically applied', () => {
      render(
        <DateRangeStep
          config={defaultConfig}
          onChange={mockOnChange}
          onNext={mockOnNext}
          onBack={mockOnBack}
        />
      );

      expect(screen.getByText(/automatically applied/i)).toBeInTheDocument();
    });
  });

  describe('Validation', () => {
    it('should require a window size to be selected', async () => {
      const user = userEvent.setup();

      render(
        <DateRangeStep
          config={defaultConfig}
          onChange={mockOnChange}
          onNext={mockOnNext}
          onBack={mockOnBack}
        />
      );

      const nextButton = screen.getByRole('button', { name: /next/i });
      await user.click(nextButton);

      expect(screen.getByText(/please select a window size/i)).toBeInTheDocument();
      expect(mockOnNext).not.toHaveBeenCalled();
    });

    it('should validate custom window size is within range', async () => {
      const user = userEvent.setup();

      render(
        <DateRangeStep
          config={defaultConfig}
          onChange={mockOnChange}
          onNext={mockOnNext}
          onBack={mockOnBack}
        />
      );

      const customButton = screen.getByRole('button', { name: /custom/i });
      await user.click(customButton);

      const input = screen.getByLabelText(/Custom days/i);
      await user.clear(input);
      await user.type(input, '500');

      const nextButton = screen.getByRole('button', { name: /next/i });
      await user.click(nextButton);

      expect(screen.getByText(/must be between 1 and 365/i)).toBeInTheDocument();
      expect(mockOnNext).not.toHaveBeenCalled();
    });

    it('should allow next when valid window size is selected', async () => {
      const user = userEvent.setup();

      const configWithWindow = {
        ...defaultConfig,
        lookbackDays: 30,
        windowSizeDays: 30,
      };

      render(
        <DateRangeStep
          config={configWithWindow}
          onChange={mockOnChange}
          onNext={mockOnNext}
          onBack={mockOnBack}
        />
      );

      const nextButton = screen.getByRole('button', { name: /next/i });
      await user.click(nextButton);

      expect(mockOnNext).toHaveBeenCalled();
    });
  });

  describe('Navigation', () => {
    it('should call onBack when back button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <DateRangeStep
          config={defaultConfig}
          onChange={mockOnChange}
          onNext={mockOnNext}
          onBack={mockOnBack}
        />
      );

      const backButton = screen.getByRole('button', { name: /back/i });
      await user.click(backButton);

      expect(mockOnBack).toHaveBeenCalled();
    });

    it('should call onNext when valid and next button is clicked', async () => {
      const user = userEvent.setup();

      const validConfig = {
        ...defaultConfig,
        lookbackDays: 7,
        windowSizeDays: 7,
      };

      render(
        <DateRangeStep
          config={validConfig}
          onChange={mockOnChange}
          onNext={mockOnNext}
          onBack={mockOnBack}
        />
      );

      const nextButton = screen.getByRole('button', { name: /next/i });
      await user.click(nextButton);

      expect(mockOnNext).toHaveBeenCalled();
    });
  });
});
