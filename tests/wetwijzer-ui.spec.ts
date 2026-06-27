import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem('WETWIJZER_DISABLE_LOCAL_LLM', 'true');
  });
});

test.describe('WetWijzer legal information UI', () => {
  test('shows Netherlands branding, dataset semantics, and disclaimer', async ({ page }) => {
    await page.goto('/');

    await expect(page.getByRole('heading', { name: 'WetWijzer' })).toBeVisible();
    await expect(page.getByText('Netherlands', { exact: true }).first()).toBeVisible();
    await expect(page.getByText('WetWijzer is legal information, not legal advice')).toBeVisible();
    await expect(page.getByText('wetten.overheid.nl').first()).toBeVisible();
    await expect(page.getByRole('navigation', { name: 'Dutch law' })).toBeVisible();
  });

  test('searches Dutch sample articles and exposes status metadata', async ({ page }) => {
    await page.goto('/');

    const searchPanel = page.locator('#desktop-search-panel');
    await searchPanel.getByLabel('Search Dutch laws').fill('Wetboek van Strafrecht artikel 1');
    await searchPanel.getByRole('button', { name: /^Search$/ }).click();

    await expect(page.getByRole('button', { name: /BWBR0001854 art\. 1/ })).toBeVisible();
    await page.getByRole('button', { name: /BWBR0001854 art\. 1/ }).click();

    const articlePanel = page.locator('#panel-section');
    await expect(articlePanel.getByRole('heading', { name: 'Wetboek van Strafrecht - Artikel 1' })).toBeVisible();
    await expect(articlePanel.getByLabel('Law status')).toContainText('Current law');
    await expect(articlePanel.getByRole('link', { name: /Official source/ })).toHaveAttribute(
      'href',
      /wetten\.overheid\.nl\/BWBR0001854/,
    );
  });

  test('opens law chat with selected article context', async ({ page }) => {
    await page.goto('/');
    await page.locator('#tab-chat').click();
    const chatPanel = page.locator('#panel-chat');

    await expect(chatPanel.getByRole('heading', { name: 'Law Chat' })).toBeVisible();
    await expect(chatPanel.getByRole('textbox', { name: /Question/ })).toHaveValue(
      'Wat zegt Artikel 1 van het Wetboek van Strafrecht?',
    );
    await expect(chatPanel.getByLabel('Suggested chat questions')).toContainText('BWBR0001854 art. 1');
  });
});
