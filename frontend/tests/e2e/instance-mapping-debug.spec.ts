import { test, expect } from '@playwright/test';

test.describe('Instance Mapping Tab - Debug', () => {
  let instanceId: string;

  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('http://localhost:5173/login');
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'password');
    await page.click('button[type="submit"]');

    // Wait for redirect to instances
    await page.waitForURL('**/instances');

    // Click on first instance
    const firstInstance = page.locator('[data-testid="instance-card"]').first();
    await firstInstance.click();

    // Extract instance ID from URL
    await page.waitForURL(/\/instances\/.+/);
    const url = page.url();
    instanceId = url.split('/instances/')[1];

    // Navigate to Mappings tab
    await page.click('text=Mappings');
    await page.waitForLoadState('networkidle');
  });

  test('should load brands and allow selection', async ({ page }) => {
    console.log('=== Test: Load brands and selection ===');

    // Wait for brands to load
    await page.waitForSelector('text=Brands', { timeout: 10000 });

    // Check if brands are displayed
    const brandCount = await page.locator('[data-testid="brand-item"]').count();
    console.log(`Found ${brandCount} brands`);

    if (brandCount === 0) {
      // Check for alternative selectors
      const brandButtons = await page.locator('button:has-text("ASINs •")').count();
      console.log(`Found ${brandButtons} brand buttons using alternative selector`);
    }

    // Click on first brand
    const firstBrand = page.locator('button').filter({ hasText: 'ASINs •' }).first();
    await firstBrand.click();

    // Check if ASINs panel updates
    const asinsHeader = page.locator('text=ASINs').first();
    await expect(asinsHeader).toBeVisible();

    console.log('✓ Brand selection works');
  });

  test('should load and select ASINs', async ({ page }) => {
    console.log('=== Test: ASIN selection ===');

    // Select first brand
    const firstBrand = page.locator('button').filter({ hasText: 'ASINs •' }).first();
    await firstBrand.click();
    await page.waitForTimeout(1000); // Wait for ASIN loading

    // Check for ASIN checkboxes
    const asinCheckboxes = await page.locator('input[type="checkbox"]').count();
    console.log(`Found ${asinCheckboxes} checkboxes`);

    // Select first ASIN
    if (asinCheckboxes > 0) {
      await page.locator('input[type="checkbox"]').first().check();

      // Verify selection counter updates
      const selectedText = await page.locator('text=/\\d+ selected/').textContent();
      console.log(`Selection counter: ${selectedText}`);

      expect(selectedText).toContain('1 selected');
      console.log('✓ ASIN selection works');
    } else {
      console.log('⚠ No ASINs found to select');
    }
  });

  test('should load and select campaigns', async ({ page }) => {
    console.log('=== Test: Campaign selection ===');

    // Select first brand
    const firstBrand = page.locator('button').filter({ hasText: 'ASINs •' }).first();
    await firstBrand.click();
    await page.waitForTimeout(1000);

    // Look for campaign checkboxes in the third column
    const campaignSection = page.locator('text=Campaigns').first();
    await expect(campaignSection).toBeVisible();

    // Count campaign items
    const campaignCheckboxes = await page.locator('div:has-text("campaign_type") input[type="checkbox"]').count();
    console.log(`Found ${campaignCheckboxes} campaign checkboxes`);

    if (campaignCheckboxes > 0) {
      // Select first campaign
      await page.locator('div:has-text("campaign_type") input[type="checkbox"]').first().check();

      const selectedText = await page.locator('text=Campaigns').locator('..').locator('text=/\\d+ selected/').textContent();
      console.log(`Campaign selection counter: ${selectedText}`);

      console.log('✓ Campaign selection works');
    }
  });

  test('should capture save button click and API errors', async ({ page, context }) => {
    console.log('=== Test: Save operation with network monitoring ===');

    // Listen to all network requests
    const requests: any[] = [];
    const responses: any[] = [];

    page.on('request', request => {
      if (request.url().includes('/mappings')) {
        console.log(`→ REQUEST: ${request.method()} ${request.url()}`);
        if (request.method() === 'POST') {
          request.postData().then(data => {
            console.log('  POST Data:', data);
          });
        }
        requests.push({
          method: request.method(),
          url: request.url(),
          headers: request.headers()
        });
      }
    });

    page.on('response', async response => {
      if (response.url().includes('/mappings')) {
        const status = response.status();
        console.log(`← RESPONSE: ${status} ${response.url()}`);

        try {
          const body = await response.json();
          console.log('  Response body:', JSON.stringify(body, null, 2));
          responses.push({ status, body });
        } catch (e) {
          const text = await response.text();
          console.log('  Response text:', text);
          responses.push({ status, text });
        }
      }
    });

    // Listen to console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log('❌ Console Error:', msg.text());
      }
    });

    // Select a brand and some items
    const firstBrand = page.locator('button').filter({ hasText: 'ASINs •' }).first();
    await firstBrand.click();
    await page.waitForTimeout(1000);

    // Select an ASIN
    const asinCheckbox = page.locator('input[type="checkbox"]').first();
    if (await asinCheckbox.isVisible()) {
      await asinCheckbox.check();
      console.log('✓ Selected an ASIN');
    }

    // Click Save button
    const saveButton = page.locator('button:has-text("Save Changes")');
    await expect(saveButton).toBeVisible();

    console.log('Clicking Save button...');
    await saveButton.click();

    // Wait for network activity
    await page.waitForTimeout(2000);

    // Check for any error messages on page
    const errorMessage = await page.locator('.bg-red-50').textContent().catch(() => null);
    if (errorMessage) {
      console.log('❌ Error message displayed:', errorMessage);
    }

    // Check for success messages
    const successMessage = await page.locator('.bg-green-50').textContent().catch(() => null);
    if (successMessage) {
      console.log('✓ Success message:', successMessage);
    }

    // Log summary
    console.log('\n=== SUMMARY ===');
    console.log(`Requests captured: ${requests.length}`);
    console.log(`Responses captured: ${responses.length}`);

    if (responses.length > 0) {
      responses.forEach((r, i) => {
        console.log(`Response ${i + 1}: Status ${r.status}`);
        if (r.body) {
          console.log('  Body:', r.body);
        }
      });
    }
  });

  test('should check for blank pages after save', async ({ page }) => {
    console.log('=== Test: Blank page detection ===');

    // Select brand and items
    const firstBrand = page.locator('button').filter({ hasText: 'ASINs •' }).first();
    await firstBrand.click();
    await page.waitForTimeout(1000);

    const asinCheckbox = page.locator('input[type="checkbox"]').first();
    if (await asinCheckbox.isVisible()) {
      await asinCheckbox.check();
    }

    // Click save
    await page.click('button:has-text("Save Changes")');
    await page.waitForTimeout(3000);

    // Check if page is blank
    const bodyText = await page.locator('body').textContent();
    const isBlank = !bodyText || bodyText.trim().length < 50;

    if (isBlank) {
      console.log('❌ PAGE IS BLANK after save');
      console.log('Body text:', bodyText);

      // Check network errors
      const failed = await page.evaluate(() => {
        return (window as any).__networkErrors || [];
      });
      console.log('Network errors:', failed);
    } else {
      console.log('✓ Page still has content');
      console.log(`Content length: ${bodyText?.length || 0} chars`);
    }

    // Check if mappings tab is still active
    const mappingsTab = page.locator('text=Mappings');
    const isVisible = await mappingsTab.isVisible();
    console.log(`Mappings tab visible: ${isVisible}`);
  });

  test('should inspect API endpoint responses', async ({ page }) => {
    console.log('=== Test: API endpoint inspection ===');

    // Test each endpoint
    const endpoints = [
      `/api/instances/${instanceId}/available-brands`,
      `/api/instances/${instanceId}/mappings`
    ];

    for (const endpoint of endpoints) {
      console.log(`\nTesting: ${endpoint}`);

      const response = await page.evaluate(async (url) => {
        try {
          const res = await fetch(`http://localhost:8001${url}`, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          });
          const data = await res.json();
          return { status: res.status, data };
        } catch (err: any) {
          return { error: err.message };
        }
      }, endpoint);

      console.log('Response:', JSON.stringify(response, null, 2));
    }
  });
});
