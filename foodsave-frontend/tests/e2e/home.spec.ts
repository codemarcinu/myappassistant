import { test, expect } from '@playwright/test';

test.describe('FoodSave AI E2E Tests', () => {
  test('should load dashboard page successfully', async ({ page }) => {
    // Visit the dashboard page directly since home redirects to dashboard
    await page.goto('/dashboard');

    // Wait for the page to load
    await page.waitForLoadState('networkidle');

    // Check if the page title is correct
    await expect(page).toHaveTitle(/FoodSave AI/);

    // Check if main content is visible (6 headers: h1 for title, h3 for weather, h2 for chat, h3 for LLM settings, etc.)
    await expect(page.locator('h1, h2, h3')).toHaveCount(6);

    // Check if weather section is present
    await expect(page.getByText('Prognoza pogody')).toBeVisible();

    // Check if chat interface is present
    await expect(page.locator('[data-testid="chat-interface"]')).toBeVisible();
  });

  test('should handle navigation between pages', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto('/dashboard');

    // Test navigation to shopping page
    await page.click('text=Zakupy');
    await expect(page).toHaveURL(/.*shopping/);

    // Test navigation to cooking page
    await page.click('text=Gotowanie');
    await expect(page).toHaveURL(/.*cooking/);

    // Test navigation to chat page
    await page.click('text=Czat');
    await expect(page).toHaveURL(/.*chat/);

    // Test navigation back to dashboard
    await page.click('text=Dashboard');
    await expect(page).toHaveURL(/.*dashboard/);
  });

  test('should handle responsive design', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/dashboard');

    // Check if mobile navigation is visible
    await expect(page.locator('[data-testid="mobile-navigation"]')).toBeVisible();

    // Test desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.reload();

    // Check if sidebar navigation is visible
    await expect(page.locator('[data-testid="sidebar-navigation"]')).toBeVisible();
  });

  test('should handle error states gracefully', async ({ page }) => {
    // Mock network error for weather API
    await page.route('**/api/v2/weather', route => {
      route.abort('failed');
    });

    await page.goto('/dashboard');

    // Check if error message is displayed (with longer timeout and alternative error messages)
    await expect(
      page.getByText(/Nie udało się pobrać danych pogodowych|Błąd pobierania pogody|Weather error/i)
    ).toBeVisible({ timeout: 10000 });
  });
});
