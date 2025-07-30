import { test } from '@playwright/test';

test('Manual UI inspection', async ({ page }) => {
  // Navigate to login
  await page.goto('http://localhost:5173/login');
  
  // Take screenshot
  await page.screenshot({ path: 'ui-test-login.png', fullPage: true });
  
  // Wait for manual inspection
  await page.waitForTimeout(3000);
});