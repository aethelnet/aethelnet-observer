import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  page.on('console', msg => console.log('BROWSER CONSOLE:', msg.text()));
  page.on('pageerror', err => console.log('BROWSER ERROR:', err.message));
  
  await page.goto('http://127.0.0.1:1420');
  await page.waitForTimeout(3000);
  
  // Click the top nav toolbox button. Let's find any button with "ASSET" or click the nav item.
  // The LgnnTopNav.vue emits toggle-toolbox.
  // There is a nav-link 'ASSETS'.
  await page.evaluate(() => {
    const assetsBtn = Array.from(document.querySelectorAll('.nav-link')).find(el => el.textContent.includes('ASSETS'));
    if (assetsBtn) assetsBtn.click();
  });
  await page.waitForTimeout(1000);
  
  // Click LGNN Bridge button
  await page.evaluate(() => {
    const lgnnBtn = Array.from(document.querySelectorAll('.tool-btn')).find(el => el.textContent.includes('LGNN Bridge'));
    if (lgnnBtn) lgnnBtn.click();
  });
  
  await page.waitForTimeout(3000);
  
  // Try to find the node on the canvas and double click it or expand it
  await page.evaluate(() => {
    const expandBtn = Array.from(document.querySelectorAll('.expand-btn')).find(el => {
      const parent = el.closest('.concept-node');
      return parent && parent.textContent.includes('LgnnChat');
    });
    if (expandBtn) expandBtn.click();
  });
  
  await page.waitForTimeout(2000);
  
  await page.screenshot({ path: '/home/nikahrlyn/.gemini/antigravity-cli/brain/e97c7052-e9e3-459b-a0d2-ae7218897ad4/screenshot_spawn.png' });
  await browser.close();
})();
