import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem('WETWIJZER_DISABLE_LOCAL_LLM', 'true');
    window.localStorage.setItem('WETWIJZER_DATA_PROVIDER', 'static');
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
    await expect(articlePanel.getByLabel('Identifiers and version metadata')).toContainText('ipfs://bafywetwijzer');
    await expect(articlePanel.getByLabel('Legal hierarchy')).toContainText('Artikel');
    await expect(articlePanel.getByRole('link', { name: /Official source/ })).toHaveAttribute(
      'href',
      /wetten\.overheid\.nl\/BWBR0001854/,
    );
  });

  test('shows CID metadata and knowledge graph relationships for a selected article', async ({ page }) => {
    await page.goto('/');

    const searchPanel = page.locator('#desktop-search-panel');
    await searchPanel.getByLabel('Search Dutch laws').fill('Wetboek van Strafrecht artikel 1');
    await searchPanel.getByRole('button', { name: /^Search$/ }).click();

    const result = page.getByRole('button', { name: /BWBR0001854 art\. 1/ });
    await expect(result).toContainText('CID');
    await expect(page.getByText(/ipfs:\/\/bafywetwijzer/).first()).toBeVisible();
    await result.click();

    await page.locator('#tab-graph').click();
    const graphPanel = page.locator('#panel-graph');
    await expect(graphPanel.getByRole('heading', { name: 'Knowledge Graph' })).toBeVisible();
    await expect(graphPanel.getByLabel('Knowledge graph relationships')).toContainText('Part Of Law');
    await expect(graphPanel.getByLabel('Knowledge graph relationships')).toContainText('Has Law Status');
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
