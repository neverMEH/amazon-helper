import { test, expect } from '@playwright/test';

test.describe('Amazon Helper UI Test Suite', () => {
  test('Login flow and navigation', async ({ page }) => {
    // 1. Test Login Page
    await page.goto('/login');
    await expect(page.locator('h2')).toContainText('Amazon Marketing Cloud Manager');
    
    // Fill in login form with demo credentials
    await page.fill('input[type="email"]', 'nick@nevermeh.com');
    await page.fill('input[type="password"]', 'password123'); // Any password works for now
    await page.click('button[type="submit"]');
    
    // Should redirect to dashboard
    await page.waitForURL('**/dashboard');
    
    // 2. Test Dashboard
    await expect(page.locator('h1')).toContainText('Dashboard');
    await expect(page.locator('text=Overview of your Amazon Marketing Cloud resources')).toBeVisible();
    
    // Check for dashboard cards
    await expect(page.locator('text=AMC Instances')).toBeVisible();
    await expect(page.locator('text=Workflows')).toBeVisible();
    await expect(page.locator('text=Campaigns')).toBeVisible();
    await expect(page.locator('text=Recent Executions')).toBeVisible();
    
    // 3. Test Navigation Sidebar
    const sidebar = page.locator('nav');
    await expect(sidebar.locator('text=Dashboard')).toBeVisible();
    await expect(sidebar.locator('text=AMC Instances')).toBeVisible();
    await expect(sidebar.locator('text=Campaigns')).toBeVisible();
    await expect(sidebar.locator('text=Workflows')).toBeVisible();
    
    // Check user info in sidebar
    await expect(page.locator('text=nick@nevermeh.com')).toBeVisible();
    
    // 4. Navigate to AMC Instances
    await page.click('text=AMC Instances');
    await page.waitForURL('**/instances');
    await expect(page.locator('h1')).toContainText('AMC Instances');
    await expect(page.locator('text=Manage your Amazon Marketing Cloud instances')).toBeVisible();
    
    // 5. Navigate to Campaigns
    await page.click('text=Campaigns');
    await page.waitForURL('**/campaigns');
    await expect(page.locator('h1')).toContainText('Campaigns');
    await expect(page.locator('text=Manage campaign mappings and brand tags')).toBeVisible();
    
    // Check for filter dropdowns
    await expect(page.locator('label:has-text("Brand")')).toBeVisible();
    await expect(page.locator('label:has-text("Type")')).toBeVisible();
    await expect(page.locator('button:has-text("Sync Campaigns")')).toBeVisible();
    
    // 6. Navigate to Workflows
    await page.click('text=Workflows');
    await page.waitForURL('**/workflows');
    await expect(page.locator('h1')).toContainText('Workflows');
    await expect(page.locator('text=Create and manage AMC query workflows')).toBeVisible();
    await expect(page.locator('button:has-text("New Workflow")')).toBeVisible();
    
    // 7. Test Logout
    await page.click('button[title="Logout"]');
    await page.waitForURL('**/login');
    await expect(page.locator('h2')).toContainText('Amazon Marketing Cloud Manager');
  });
  
  test('Protected routes should redirect to login', async ({ page }) => {
    // Try to access dashboard without login
    await page.goto('/dashboard');
    await page.waitForURL('**/login');
    await expect(page.locator('h2')).toContainText('Amazon Marketing Cloud Manager');
    
    // Try other protected routes
    await page.goto('/instances');
    await page.waitForURL('**/login');
    
    await page.goto('/campaigns');
    await page.waitForURL('**/login');
    
    await page.goto('/workflows');
    await page.waitForURL('**/login');
  });
  
  test('Responsive design check', async ({ page }) => {
    await page.goto('/login');
    
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator('h2')).toBeVisible();
    await expect(page.locator('input[type="email"]')).toBeVisible();
    
    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.locator('h2')).toBeVisible();
    
    // Test desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await expect(page.locator('h2')).toBeVisible();
  });
});