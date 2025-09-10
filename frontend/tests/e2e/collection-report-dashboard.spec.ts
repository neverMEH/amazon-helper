import { test, expect, Page } from '@playwright/test';

test.describe('Collection Report Dashboard', () => {
  let page: Page;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
    
    // Login with test credentials
    await page.goto('/login');
    await page.fill('input[type="email"]', 'nick@nevermeh.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    // Wait for dashboard to load
    await page.waitForURL('/dashboard');
    await expect(page.locator('h1')).toContainText('Dashboard');
  });

  test.describe('Dashboard Navigation and Display', () => {
    test('should navigate to collection report dashboard from collection progress', async () => {
      // Navigate to Reports page
      await page.click('a[href="/reports"]');
      await page.waitForURL('/reports');
      
      // Click on a collection with data
      await page.click('text=Test Collection >> nth=0');
      
      // Should see collection progress page
      await expect(page.locator('h2')).toContainText('Collection Progress');
      
      // Click on View Dashboard button
      await page.click('button:has-text("View Dashboard")');
      
      // Should see report dashboard
      await expect(page.locator('h3')).toContainText('Report Dashboard');
      await expect(page.locator('[data-testid="dashboard-container"]')).toBeVisible();
    });

    test('should display charts with data', async () => {
      // Navigate directly to a collection dashboard
      await page.goto('/reports/collection/test-collection-id/dashboard');
      
      // Wait for charts to load
      await page.waitForSelector('[data-testid="chart-container"]');
      
      // Should see multiple chart types
      await expect(page.locator('[data-testid="line-chart"]')).toBeVisible();
      await expect(page.locator('[data-testid="bar-chart"]')).toBeVisible();
      
      // Should have chart controls
      await expect(page.locator('[data-testid="chart-type-selector"]')).toBeVisible();
      await expect(page.locator('[data-testid="metric-selector"]')).toBeVisible();
    });

    test('should handle empty data gracefully', async () => {
      // Navigate to collection without data
      await page.goto('/reports/collection/empty-collection-id/dashboard');
      
      // Should show empty state
      await expect(page.locator('[data-testid="empty-state"]')).toBeVisible();
      await expect(page.locator('text=No data available')).toBeVisible();
    });
  });

  test.describe('Week Selection and Filtering', () => {
    test('should allow single week selection', async () => {
      await page.goto('/reports/collection/test-collection-id/dashboard');
      
      // Open week selector
      await page.click('[data-testid="week-selector"]');
      
      // Select a specific week
      await page.click('text=Week of Jan 1, 2025');
      
      // Chart should update
      await page.waitForSelector('[data-testid="chart-loading"]', { state: 'hidden' });
      
      // Verify selected week is displayed
      await expect(page.locator('[data-testid="selected-week"]')).toContainText('Jan 1, 2025');
    });

    test('should allow multiple week selection for comparison', async () => {
      await page.goto('/reports/collection/test-collection-id/dashboard');
      
      // Enable comparison mode
      await page.click('[data-testid="comparison-toggle"]');
      
      // Select first period
      await page.click('[data-testid="period1-selector"]');
      await page.click('text=Week 1-4');
      
      // Select second period
      await page.click('[data-testid="period2-selector"]');
      await page.click('text=Week 5-8');
      
      // Should show comparison view
      await expect(page.locator('[data-testid="comparison-panel"]')).toBeVisible();
      await expect(page.locator('[data-testid="period1-metrics"]')).toBeVisible();
      await expect(page.locator('[data-testid="period2-metrics"]')).toBeVisible();
    });

    test('should show week-over-week changes', async () => {
      await page.goto('/reports/collection/test-collection-id/dashboard');
      
      // Enable week-over-week view
      await page.click('[data-testid="wow-toggle"]');
      
      // Should show percentage changes
      await expect(page.locator('[data-testid="wow-indicator"]')).toBeVisible();
      await expect(page.locator('[data-testid="percent-change"]')).toBeVisible();
      
      // Verify color coding (green for positive, red for negative)
      const positiveChange = page.locator('[data-testid="positive-change"]');
      if (await positiveChange.isVisible()) {
        await expect(positiveChange).toHaveClass(/text-green/);
      }
    });
  });

  test.describe('Chart Configuration and Interaction', () => {
    test('should switch between chart types', async () => {
      await page.goto('/reports/collection/test-collection-id/dashboard');
      
      // Default should be line chart
      await expect(page.locator('[data-testid="line-chart"]')).toBeVisible();
      
      // Switch to bar chart
      await page.selectOption('[data-testid="chart-type-selector"]', 'bar');
      await page.waitForSelector('[data-testid="bar-chart"]');
      await expect(page.locator('[data-testid="bar-chart"]')).toBeVisible();
      
      // Switch to pie chart
      await page.selectOption('[data-testid="chart-type-selector"]', 'pie');
      await page.waitForSelector('[data-testid="pie-chart"]');
      await expect(page.locator('[data-testid="pie-chart"]')).toBeVisible();
    });

    test('should select and display different metrics', async () => {
      await page.goto('/reports/collection/test-collection-id/dashboard');
      
      // Select impressions metric
      await page.click('[data-testid="metric-selector"]');
      await page.click('[data-testid="metric-impressions"]');
      
      // Select clicks metric
      await page.click('[data-testid="metric-clicks"]');
      
      // Should show both metrics on chart
      await expect(page.locator('[data-testid="legend-impressions"]')).toBeVisible();
      await expect(page.locator('[data-testid="legend-clicks"]')).toBeVisible();
    });

    test('should handle chart zoom and pan', async () => {
      await page.goto('/reports/collection/test-collection-id/dashboard');
      
      // Get initial chart bounds
      const chartElement = page.locator('[data-testid="chart-container"]');
      const initialBounds = await chartElement.boundingBox();
      
      // Perform zoom action (scroll on chart)
      await chartElement.hover();
      await page.mouse.wheel(0, -100); // Zoom in
      
      // Verify zoom controls appear
      await expect(page.locator('[data-testid="reset-zoom"]')).toBeVisible();
      
      // Reset zoom
      await page.click('[data-testid="reset-zoom"]');
    });
  });

  test.describe('Export and Sharing', () => {
    test('should export dashboard data', async () => {
      await page.goto('/reports/collection/test-collection-id/dashboard');
      
      // Click export button
      await page.click('[data-testid="export-button"]');
      
      // Select export format
      await page.click('[data-testid="export-csv"]');
      
      // Should trigger download
      const downloadPromise = page.waitForEvent('download');
      await page.click('[data-testid="confirm-export"]');
      const download = await downloadPromise;
      
      // Verify download
      expect(download.suggestedFilename()).toContain('.csv');
    });

    test('should create and share dashboard snapshot', async () => {
      await page.goto('/reports/collection/test-collection-id/dashboard');
      
      // Click share button
      await page.click('[data-testid="share-button"]');
      
      // Create snapshot
      await page.fill('[data-testid="snapshot-name"]', 'Test Dashboard Snapshot');
      await page.click('[data-testid="create-snapshot"]');
      
      // Should show shareable link
      await expect(page.locator('[data-testid="share-link"]')).toBeVisible();
      
      // Copy link
      await page.click('[data-testid="copy-link"]');
      
      // Should show success message
      await expect(page.locator('text=Link copied')).toBeVisible();
    });

    test('should save dashboard configuration', async () => {
      await page.goto('/reports/collection/test-collection-id/dashboard');
      
      // Configure dashboard
      await page.selectOption('[data-testid="chart-type-selector"]', 'bar');
      await page.click('[data-testid="metric-revenue"]');
      
      // Save configuration
      await page.click('[data-testid="save-config"]');
      await page.fill('[data-testid="config-name"]', 'Revenue Analysis');
      await page.click('[data-testid="confirm-save"]');
      
      // Should show success message
      await expect(page.locator('text=Configuration saved')).toBeVisible();
      
      // Reload page
      await page.reload();
      
      // Configuration should persist
      await expect(page.locator('[data-testid="bar-chart"]')).toBeVisible();
      await expect(page.locator('[data-testid="legend-revenue"]')).toBeVisible();
    });
  });

  test.describe('Performance and Loading', () => {
    test('should show loading states appropriately', async () => {
      await page.goto('/reports/collection/test-collection-id/dashboard');
      
      // Should show loading skeleton initially
      await expect(page.locator('[data-testid="chart-skeleton"]')).toBeVisible();
      
      // Wait for data to load
      await page.waitForSelector('[data-testid="chart-container"]', { timeout: 10000 });
      
      // Loading skeleton should be hidden
      await expect(page.locator('[data-testid="chart-skeleton"]')).not.toBeVisible();
    });

    test('should handle large datasets with virtualization', async () => {
      // Navigate to collection with large dataset
      await page.goto('/reports/collection/large-collection-id/dashboard');
      
      // Switch to table view
      await page.click('[data-testid="view-table"]');
      
      // Should use virtual scrolling
      await expect(page.locator('[data-testid="virtual-scroller"]')).toBeVisible();
      
      // Scroll down
      await page.locator('[data-testid="virtual-scroller"]').evaluate(el => {
        el.scrollTop = 10000;
      });
      
      // Should load more rows
      await page.waitForTimeout(500); // Wait for virtual scroll to update
      await expect(page.locator('tr').nth(50)).toBeVisible();
    });

    test('should cache data and show stale indicator', async () => {
      await page.goto('/reports/collection/test-collection-id/dashboard');
      
      // Wait for initial load
      await page.waitForSelector('[data-testid="chart-container"]');
      
      // Navigate away and back
      await page.click('a[href="/dashboard"]');
      await page.goBack();
      
      // Should load from cache (no loading state)
      await expect(page.locator('[data-testid="chart-container"]')).toBeVisible();
      
      // Should show stale data indicator after 5 minutes (simulate)
      await page.evaluate(() => {
        // Simulate stale data
        window.dispatchEvent(new CustomEvent('data-stale'));
      });
      
      await expect(page.locator('[data-testid="stale-indicator"]')).toBeVisible();
    });
  });

  test.describe('Accessibility', () => {
    test('should support keyboard navigation', async () => {
      await page.goto('/reports/collection/test-collection-id/dashboard');
      
      // Tab through controls
      await page.keyboard.press('Tab');
      await expect(page.locator('[data-testid="week-selector"]')).toBeFocused();
      
      await page.keyboard.press('Tab');
      await expect(page.locator('[data-testid="chart-type-selector"]')).toBeFocused();
      
      // Use arrow keys in selectors
      await page.keyboard.press('ArrowDown');
      await page.keyboard.press('Enter');
      
      // Should update chart
      await expect(page.locator('[data-testid="bar-chart"]')).toBeVisible();
    });

    test('should have proper ARIA labels', async () => {
      await page.goto('/reports/collection/test-collection-id/dashboard');
      
      // Check main landmarks
      await expect(page.locator('[role="main"]')).toBeVisible();
      await expect(page.locator('[aria-label="Report Dashboard"]')).toBeVisible();
      
      // Check interactive elements
      await expect(page.locator('[aria-label="Select weeks"]')).toBeVisible();
      await expect(page.locator('[aria-label="Chart type"]')).toBeVisible();
      await expect(page.locator('[aria-label="Export data"]')).toBeVisible();
    });

    test('should announce chart updates to screen readers', async () => {
      await page.goto('/reports/collection/test-collection-id/dashboard');
      
      // Check for live region
      await expect(page.locator('[aria-live="polite"]')).toBeVisible();
      
      // Change chart type
      await page.selectOption('[data-testid="chart-type-selector"]', 'bar');
      
      // Should update live region
      await expect(page.locator('[aria-live="polite"]')).toContainText('Chart updated');
    });
  });

  test.describe('Error Handling', () => {
    test('should handle API errors gracefully', async () => {
      // Simulate API error
      await page.route('**/api/collections/**/report-dashboard', route => {
        route.fulfill({ status: 500, body: 'Internal Server Error' });
      });
      
      await page.goto('/reports/collection/test-collection-id/dashboard');
      
      // Should show error message
      await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
      await expect(page.locator('text=Failed to load dashboard data')).toBeVisible();
      
      // Should show retry button
      await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
    });

    test('should handle network timeouts', async () => {
      // Simulate slow network
      await page.route('**/api/collections/**/report-dashboard', async route => {
        await new Promise(resolve => setTimeout(resolve, 15000)); // 15 second delay
        route.fulfill({ status: 200, body: '{}' });
      });
      
      await page.goto('/reports/collection/test-collection-id/dashboard');
      
      // Should show timeout message after 10 seconds
      await page.waitForSelector('[data-testid="timeout-message"]', { timeout: 12000 });
      await expect(page.locator('text=Request timed out')).toBeVisible();
    });

    test('should validate user inputs', async () => {
      await page.goto('/reports/collection/test-collection-id/dashboard');
      
      // Try to save config with empty name
      await page.click('[data-testid="save-config"]');
      await page.fill('[data-testid="config-name"]', '');
      await page.click('[data-testid="confirm-save"]');
      
      // Should show validation error
      await expect(page.locator('[data-testid="validation-error"]')).toBeVisible();
      await expect(page.locator('text=Name is required')).toBeVisible();
    });
  });

  test.describe('Responsive Design', () => {
    test('should adapt to desktop viewport', async () => {
      // Set desktop viewport
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.goto('/reports/collection/test-collection-id/dashboard');
      
      // Should show full layout
      await expect(page.locator('[data-testid="sidebar-filters"]')).toBeVisible();
      await expect(page.locator('[data-testid="main-dashboard"]')).toBeVisible();
      
      // Charts should be in grid layout
      await expect(page.locator('[data-testid="chart-grid"]')).toHaveCSS('display', 'grid');
    });

    test('should adapt to tablet viewport', async () => {
      // Set tablet viewport
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.goto('/reports/collection/test-collection-id/dashboard');
      
      // Sidebar should be collapsible
      await expect(page.locator('[data-testid="toggle-sidebar"]')).toBeVisible();
      
      // Charts should stack vertically
      await expect(page.locator('[data-testid="chart-grid"]')).toHaveCSS('display', 'flex');
    });

    test('should adapt to mobile viewport', async () => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('/reports/collection/test-collection-id/dashboard');
      
      // Should show mobile-optimized layout
      await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible();
      
      // Filters should be in dropdown
      await page.click('[data-testid="mobile-menu"]');
      await expect(page.locator('[data-testid="mobile-filters"]')).toBeVisible();
    });
  });
});