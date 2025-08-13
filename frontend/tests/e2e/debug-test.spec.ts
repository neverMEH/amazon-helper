import { test, expect } from '@playwright/test';

test('Debug: Check what renders', async ({ page }) => {
  // Enable console logging
  page.on('console', msg => console.log('Browser console:', msg.text()));
  page.on('pageerror', err => console.log('Page error:', err));
  
  console.log('Navigating to login page...');
  await page.goto('/login');
  
  // Wait a bit for React to render
  await page.waitForTimeout(2000);
  
  // Take a screenshot
  await page.screenshot({ path: 'login-page.png', fullPage: true });
  
  // Log the page content
  const pageContent = await page.content();
  console.log('Page title:', await page.title());
  console.log('Page URL:', page.url());
  console.log('Body text content:', await page.locator('body').textContent());
  
  // Check if React rendered anything
  const rootElement = await page.locator('#root').innerHTML();
  console.log('Root element content:', rootElement);
  
  // Check for any error messages
  const errors = await page.locator('.error, [class*="error"]').allTextContents();
  if (errors.length > 0) {
    console.log('Found errors:', errors);
  }
});