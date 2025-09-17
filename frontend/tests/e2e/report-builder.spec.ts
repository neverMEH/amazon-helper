import { test, expect, Page } from '@playwright/test';

test.describe('Report Builder End-to-End Tests', () => {
  let page: Page;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;

    // Mock authentication
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.setItem('access_token', 'test-token');
      localStorage.setItem('user', JSON.stringify({
        id: 'test-user-id',
        email: 'test@example.com',
        name: 'Test User'
      }));
    });
  });

  test.describe('Complete Flow: One-Time Execution', () => {
    test('should complete full flow for one-time report execution', async () => {
      // Navigate to report builder
      await page.goto('/report-builder/new');

      // Step 1: Parameter Selection
      await expect(page.locator('h2:has-text("Step 1: Parameters & Lookback")')).toBeVisible();

      // Select predefined lookback (30 days)
      await page.click('button:has-text("Last 30 Days")');
      await expect(page.locator('button:has-text("Last 30 Days").bg-blue-500')).toBeVisible();

      // Fill in parameters
      await page.fill('input[name="startDate"]', '2025-08-01');
      await page.fill('input[name="endDate"]', '2025-08-31');

      // Select campaigns
      await page.click('button:has-text("Select Campaigns")');
      await page.waitForSelector('.campaign-selector-modal');
      await page.click('input[type="checkbox"][value="campaign1"]');
      await page.click('input[type="checkbox"][value="campaign2"]');
      await page.click('button:has-text("Apply Selection")');

      // Continue to next step
      await page.click('button:has-text("Continue to Schedule")');

      // Step 2: Schedule Selection
      await expect(page.locator('h2:has-text("Step 2: Schedule Configuration")')).toBeVisible();

      // Select "Run Once"
      await page.click('input[value="once"]');
      await expect(page.locator('text=Will execute immediately upon submission')).toBeVisible();

      // Continue to review
      await page.click('button:has-text("Continue to Review")');

      // Step 3: Review
      await expect(page.locator('h2:has-text("Step 3: Review Configuration")')).toBeVisible();

      // Verify SQL preview is visible
      await expect(page.locator('.monaco-editor')).toBeVisible();

      // Check parameter summary
      await expect(page.locator('text=Last 30 Days')).toBeVisible();
      await expect(page.locator('text=Run Once')).toBeVisible();

      // Continue to submit
      await page.click('button:has-text("Submit Report")');

      // Step 4: Submission
      await expect(page.locator('h2:has-text("Step 4: Submitting Report")')).toBeVisible();

      // Wait for success
      await expect(page.locator('text=Report submitted successfully!')).toBeVisible({ timeout: 10000 });

      // Verify navigation options
      await expect(page.locator('button:has-text("View Execution")')).toBeVisible();
      await expect(page.locator('button:has-text("Go to Workflows")')).toBeVisible();
    });
  });

  test.describe('Complete Flow: Scheduled with Backfill', () => {
    test('should complete flow with 365-day backfill and weekly schedule', async () => {
      await page.goto('/report-builder/new');

      // Step 1: Custom date range for 365 days
      await page.click('button:has-text("Custom Dates")');

      const startDate = new Date();
      startDate.setDate(startDate.getDate() - 365);
      const endDate = new Date();

      await page.fill('input[name="customStartDate"]', startDate.toISOString().split('T')[0]);
      await page.fill('input[name="customEndDate"]', endDate.toISOString().split('T')[0]);

      await page.click('button:has-text("Continue to Schedule")');

      // Step 2: Backfill with schedule
      await page.click('input[value="backfill_with_schedule"]');

      // Configure backfill
      await page.selectOption('select[name="backfillSegmentation"]', 'weekly');
      await expect(page.locator('text=52 weekly segments will be created')).toBeVisible();

      // Configure schedule
      await page.selectOption('select[name="scheduleFrequency"]', 'weekly');
      await page.selectOption('select[name="dayOfWeek"]', '1'); // Monday
      await page.fill('input[name="scheduleTime"]', '09:00');
      await page.selectOption('select[name="timezone"]', 'America/New_York');

      await page.click('button:has-text("Continue to Review")');

      // Step 3: Review with warnings
      await expect(page.locator('.warning-banner:has-text("52 segments")')).toBeVisible();
      await expect(page.locator('text=Estimated Duration: ~4.3 hours')).toBeVisible();

      await page.click('button:has-text("Submit Report")');

      // Step 4: Track backfill progress
      await expect(page.locator('.progress-bar')).toBeVisible();
      await expect(page.locator('text=Processing 52 segments')).toBeVisible();

      // Should show progress updates
      await page.waitForSelector('text=/\\d+ of 52 completed/', { timeout: 15000 });
    });
  });

  test.describe('Parameter Validation', () => {
    test('should validate AMC 14-month data retention limit', async () => {
      await page.goto('/report-builder/new');

      // Try to select date beyond 14 months
      await page.click('button:has-text("Custom Dates")');

      const tooOldDate = new Date();
      tooOldDate.setMonth(tooOldDate.getMonth() - 15);

      await page.fill('input[name="customStartDate"]', tooOldDate.toISOString().split('T')[0]);

      // Should show validation error
      await expect(page.locator('.error-message:has-text("exceeds AMC\'s 14-month")')).toBeVisible();

      // Continue button should be disabled
      await expect(page.locator('button:has-text("Continue to Schedule")')).toBeDisabled();
    });

    test('should validate required parameters', async () => {
      await page.goto('/report-builder/new');

      // Try to continue without selecting lookback
      await page.click('button:has-text("Continue to Schedule")');

      // Should show validation error
      await expect(page.locator('.error-message:has-text("Please select a lookback period")')).toBeVisible();
    });
  });

  test.describe('Navigation and Editing', () => {
    test('should allow editing from review step', async () => {
      await page.goto('/report-builder/new');

      // Complete steps 1 and 2
      await page.click('button:has-text("Last 7 Days")');
      await page.click('button:has-text("Continue to Schedule")');

      await page.click('input[value="once"]');
      await page.click('button:has-text("Continue to Review")');

      // Click edit on parameters section
      await page.click('button[aria-label="Edit parameters"]');

      // Should go back to step 1
      await expect(page.locator('h2:has-text("Step 1: Parameters & Lookback")')).toBeVisible();

      // Change selection
      await page.click('button:has-text("Last 14 Days")');
      await page.click('button:has-text("Continue to Schedule")');

      // Skip to review (schedule already configured)
      await page.click('button:has-text("Continue to Review")');

      // Verify change is reflected
      await expect(page.locator('text=Last 14 Days')).toBeVisible();
    });

    test('should preserve state when navigating between steps', async () => {
      await page.goto('/report-builder/new');

      // Configure step 1
      await page.click('button:has-text("Last 30 Days")');
      await page.fill('textarea[name="notes"]', 'Test notes for report');
      await page.click('button:has-text("Continue to Schedule")');

      // Configure step 2
      await page.click('input[value="scheduled"]');
      await page.selectOption('select[name="scheduleFrequency"]', 'daily');

      // Go back
      await page.click('button:has-text("Back")');

      // Verify state is preserved
      await expect(page.locator('button:has-text("Last 30 Days").bg-blue-500')).toBeVisible();
      await expect(page.locator('textarea[name="notes"]')).toHaveValue('Test notes for report');

      // Go forward
      await page.click('button:has-text("Continue to Schedule")');

      // Verify schedule state is preserved
      await expect(page.locator('input[value="scheduled"]:checked')).toBeVisible();
      await expect(page.locator('select[name="scheduleFrequency"]')).toHaveValue('daily');
    });
  });

  test.describe('Error Handling', () => {
    test('should handle API errors gracefully', async () => {
      await page.goto('/report-builder/new');

      // Mock API error
      await page.route('**/api/report-builder/submit', route => {
        route.fulfill({
          status: 500,
          json: { error: 'Internal server error', detail: 'Database connection failed' }
        });
      });

      // Complete flow
      await page.click('button:has-text("Last 7 Days")');
      await page.click('button:has-text("Continue to Schedule")');
      await page.click('input[value="once"]');
      await page.click('button:has-text("Continue to Review")');
      await page.click('button:has-text("Submit Report")');

      // Should show error
      await expect(page.locator('.error-message:has-text("Failed to submit report")')).toBeVisible();
      await expect(page.locator('button:has-text("Retry")')).toBeVisible();
    });

    test('should handle network timeout', async () => {
      await page.goto('/report-builder/new');

      // Mock slow network
      await page.route('**/api/report-builder/preview-schedule', async route => {
        await new Promise(resolve => setTimeout(resolve, 35000)); // Longer than timeout
        route.abort();
      });

      await page.click('button:has-text("Last 7 Days")');
      await page.click('button:has-text("Continue to Schedule")');

      // Should show timeout error
      await expect(page.locator('.error-message:has-text("Request timeout")')).toBeVisible({ timeout: 40000 });
    });
  });

  test.describe('Performance', () => {
    test('should handle large campaign selection efficiently', async () => {
      await page.goto('/report-builder/new');

      // Mock large campaign list
      await page.route('**/api/campaigns/', route => {
        const campaigns = Array.from({ length: 1000 }, (_, i) => ({
          id: `campaign${i}`,
          name: `Campaign ${i}`,
          brand: `Brand ${i % 10}`,
          status: 'ACTIVE'
        }));

        route.fulfill({
          status: 200,
          json: campaigns
        });
      });

      // Open campaign selector
      await page.click('button:has-text("Select Campaigns")');

      // Should render efficiently with virtual scrolling
      await expect(page.locator('.campaign-list-virtual')).toBeVisible();

      // Search should be responsive
      await page.fill('input[placeholder="Search campaigns..."]', 'Campaign 500');
      await expect(page.locator('text=Campaign 500')).toBeVisible({ timeout: 2000 });

      // Select all should work
      await page.click('button:has-text("Select All Filtered")');
      await expect(page.locator('text=1 campaign selected')).toBeVisible();
    });

    test('should show progress for large backfill operations', async () => {
      await page.goto('/report-builder/new');

      // Configure 365-day backfill
      await page.click('button:has-text("Custom Dates")');

      const startDate = new Date();
      startDate.setFullYear(startDate.getFullYear() - 1);

      await page.fill('input[name="customStartDate"]', startDate.toISOString().split('T')[0]);
      await page.fill('input[name="customEndDate"]', new Date().toISOString().split('T')[0]);

      await page.click('button:has-text("Continue to Schedule")');
      await page.click('input[value="backfill_with_schedule"]');
      await page.selectOption('select[name="backfillSegmentation"]', 'daily');

      // Should show warning for 365 segments
      await expect(page.locator('.warning-banner:has-text("365 segments")')).toBeVisible();
      await expect(page.locator('text=This is a large operation')).toBeVisible();
    });
  });

  test.describe('Accessibility', () => {
    test('should be keyboard navigable', async () => {
      await page.goto('/report-builder/new');

      // Tab through controls
      await page.keyboard.press('Tab');
      await expect(page.locator('button:has-text("Last 7 Days")')).toBeFocused();

      // Select with Enter
      await page.keyboard.press('Enter');
      await expect(page.locator('button:has-text("Last 7 Days").bg-blue-500')).toBeVisible();

      // Tab to continue
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      await expect(page.locator('button:has-text("Continue to Schedule")')).toBeFocused();

      await page.keyboard.press('Enter');

      // Should advance to next step
      await expect(page.locator('h2:has-text("Step 2: Schedule Configuration")')).toBeVisible();
    });

    test('should have proper ARIA labels', async () => {
      await page.goto('/report-builder/new');

      // Check ARIA labels
      await expect(page.locator('[aria-label="Report Builder Progress"]')).toBeVisible();
      await expect(page.locator('[aria-label="Select lookback period"]')).toBeVisible();
      await expect(page.locator('[aria-label="Continue to next step"]')).toBeVisible();
    });
  });

  test.describe('Mobile Responsiveness', () => {
    test('should work on mobile viewport', async () => {
      await page.setViewportSize({ width: 375, height: 812 }); // iPhone X
      await page.goto('/report-builder/new');

      // Check responsive layout
      await expect(page.locator('.step-indicator')).toBeVisible();

      // Buttons should stack vertically
      const buttons = await page.locator('.lookback-buttons').boundingBox();
      expect(buttons?.width).toBeLessThan(375);

      // Modal should be full-screen on mobile
      await page.click('button:has-text("Select Campaigns")');
      const modal = await page.locator('.campaign-selector-modal').boundingBox();
      expect(modal?.width).toBeGreaterThan(350);
    });
  });
});