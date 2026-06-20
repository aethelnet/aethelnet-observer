const { test, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;

test.describe('Accessibility Checks', () => {
  test('should not have any automatically detectable accessibility issues', async ({ page }) => {
    await page.goto('/');

    // Wait for the components to initialize
    await page.waitForTimeout(1000); 

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      // Exclude specific rules if necessary (e.g. contrast if design is intentional, though we should fix them)
      .analyze();

    // If there are violations, this will print them out nicely in the test reporter
    expect(accessibilityScanResults.violations).toEqual([]);
  });
});
