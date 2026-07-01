import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  page.on('console', msg => console.log('BROWSER CONSOLE:', msg.text()));
  page.on('pageerror', err => console.log('BROWSER ERROR:', err.message));
  
  await page.goto('http://127.0.0.1:1420');
  await page.waitForTimeout(3000);
  
  // Click LGNN Bridge button to spawn
  await page.evaluate(() => {
    const assetsBtn = Array.from(document.querySelectorAll('.nav-link')).find(el => el.textContent.includes('ASSETS'));
    if (assetsBtn) assetsBtn.click();
  });
  await page.waitForTimeout(1000);
  
  await page.evaluate(() => {
    const lgnnBtn = Array.from(document.querySelectorAll('.tool-btn')).find(el => el.textContent.includes('LGNN Bridge'));
    if (lgnnBtn) lgnnBtn.click();
  });
  
  await page.waitForTimeout(3000);
  
  // Try to open it in 3D Mode or force AppWindowOverlay by double clicking?
  // Wait, in 2D mode, we click EXPAND to open it inline. But the user said App Window is blank.
  // How did the user open it? They might have clicked it.
  await page.evaluate(() => {
    const expandBtns = document.querySelectorAll('.expand-btn');
    for (const btn of expandBtns) {
        btn.click();
    }
  });
  
  await page.waitForTimeout(2000);
  
  await page.screenshot({ path: '/home/nikahrlyn/.gemini/antigravity-cli/brain/e97c7052-e9e3-459b-a0d2-ae7218897ad4/screenshot_blank.png' });
  await browser.close();
})();
