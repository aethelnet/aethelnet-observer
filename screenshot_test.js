const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('http://localhost:5173');
  await page.waitForTimeout(3000);
  await page.screenshot({ path: '/home/nikahrlyn/.gemini/antigravity-cli/brain/e97c7052-e9e3-459b-a0d2-ae7218897ad4/screenshot_blank.png' });
  await browser.close();
})();
