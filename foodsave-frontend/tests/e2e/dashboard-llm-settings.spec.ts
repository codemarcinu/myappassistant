import { test, expect } from '@playwright/test';

// Zakładamy, że backend i frontend są uruchomione lokalnie
const DASHBOARD_URL = 'http://localhost:3000/dashboard';

// Przykładowy model, który powinien być widoczny (możesz zmienić na inny jeśli potrzeba)
const EXAMPLE_MODEL = 'SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0';
const SECOND_MODEL = 'SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M';

// Test e2e dla ustawień modeli LLM

test.describe('Dashboard LLM Model Settings', () => {
  test('powinien wyświetlać sekcję ustawień modeli LLM i listę modeli', async ({ page }) => {
    await page.goto('/dashboard');

    // Sprawdź, że sekcja ustawień modeli LLM jest widoczna
    await expect(page.getByText('Ustawienia Modelu LLM')).toBeVisible();

    // Sprawdź, że lista modeli zawiera przykładowy model (używaj specyficznego selektora)
    await expect(page.getByRole('button', { name: EXAMPLE_MODEL })).toBeVisible();

    // Sprawdź, że wyświetlany jest aktualny model
    await expect(page.getByText(/Aktualny model:/i)).toBeVisible();
  });

  test('po kliknięciu innego modelu i zapisaniu aktualny model się zmienia, a potem można przywrócić poprzedni', async ({ page }) => {
    await page.goto(DASHBOARD_URL);
    // Pobierz aktualny model
    const currentModel = await page.locator('.bg-gray-100 span').textContent();
    // Wybierz inny model
    const newModel = currentModel?.includes(EXAMPLE_MODEL) ? SECOND_MODEL : EXAMPLE_MODEL;
    await page.getByText(newModel, { exact: false }).click();
    const saveButton = page.getByRole('button', { name: /Zapisz model/i });
    await expect(saveButton).toBeEnabled({ timeout: 10000 });
    await saveButton.click();
    await expect(page.getByText(newModel, { exact: false })).toBeVisible({ timeout: 10000 });
    // Przywróć poprzedni model
    await page.getByRole('button', { name: currentModel! }).click();
    await expect(saveButton).toBeEnabled({ timeout: 10000 });
    await saveButton.click();
    await expect(page.getByText(currentModel!, { exact: false })).toBeVisible({ timeout: 10000 });
  });

  test('obsługa błędu backendu - wyświetla komunikat o błędzie', async ({ page, context }) => {
    // Przechwyć żądanie i zwróć błąd 500
    await context.route('**/api/settings/llm-models', route => {
      route.fulfill({ status: 500, body: 'Internal Server Error' });
    });
    await page.goto(DASHBOARD_URL);
    await expect(page.getByText('Błąd ładowania ustawień')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('Nie udało się załadować ustawień modeli LLM.')).toBeVisible({ timeout: 15000 });
    // Przywróć normalne żądania
    await context.unroute('**/api/settings/llm-models');
  });
});
