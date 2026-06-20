import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  page.on('console', msg => console.log('BROWSER_LOG:', msg.text()));
  page.on('pageerror', error => console.log('BROWSER_ERROR:', error.message));
  
  await page.goto('http://localhost:1420', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3000);
  
  // Dump Vue data
  const data = await page.evaluate(() => {
    // Traverse DOM to find Vue instance and its state
    const appEl = document.querySelector('#app');
    return {
      numNodes: document.querySelectorAll('.concept-circle').length,
      numBlobs: document.querySelectorAll('.concept-blob').length
    };
  });
  console.log('VUE DATA:', data);
  
  await browser.close();
})();
