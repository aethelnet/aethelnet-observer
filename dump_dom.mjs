import { chromium } from 'playwright';
import * as fs from 'fs';

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
  
  // Find the node and click expand
  const html = await page.evaluate(() => {
    const expandBtns = document.querySelectorAll('.expand-btn');
    for (const btn of expandBtns) {
        btn.click();
    }
    return new Promise(resolve => {
        setTimeout(() => {
            resolve(document.body.innerHTML);
        }, 2000);
    });
  });
  
  fs.writeFileSync('page_dom.html', html);
  
  await browser.close();
})();
