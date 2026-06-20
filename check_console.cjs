const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  page.on('console', msg => console.log('BROWSER_CONSOLE:', msg.text()));
  page.on('pageerror', error => console.log('BROWSER_ERROR:', error));
  await page.goto('http://localhost:8088/');
  await page.waitForTimeout(1000);
  await page.evaluate(() => {
    const icon = document.querySelector('.sidebar-item[title="The Lens (Observer)"]');
    if (icon) icon.click();
  });
  await page.waitForTimeout(2000);
  await browser.close();
})();
