import { test, expect } from '@playwright/test';

// Zakładamy, że backend i frontend są uruchomione lokalnie
const DASHBOARD_URL = 'http://localhost:3000/dashboard';

// Przykładowy model, który powinien być widoczny (możesz zmienić na inny jeśli potrzeba)
const EXAMPLE_MODEL = 'SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0';

// Test e2e dla ustawień modeli LLM

test.describe('Dashboard LLM Model Settings', () => {
  test('powinien wyświetlać sekcję ustawień modeli LLM i listę modeli', async ({ page }) => {
    await page.goto(DASHBOARD_URL);

    // Sprawdź nagłówek sekcji
    await expect(page.getByRole('heading', { name: /Ustawienia Modelu LLM/i })).toBeVisible();

    // Sprawdź, że lista modeli zawiera przykładowy model
    await expect(page.getByText(EXAMPLE_MODEL, { exact: false })).toBeVisible();

    // Sprawdź, że wyświetlany jest aktualny model
    await expect(page.getByText(/Aktualny model:/i)).toBeVisible();
  });
});
