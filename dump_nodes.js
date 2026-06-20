import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  page.on('console', msg => console.log('BROWSER_LOG:', msg.text()));
  
  await page.goto('http://localhost:1420', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(5000);
  
  const data = await page.evaluate(() => {
    // We want to dump some properties of the node elements.
    const nodes = Array.from(document.querySelectorAll('.concept-circle'));
    return nodes.map(n => ({
      classes: n.className,
      style: n.getAttribute('style'),
      text: n.innerText
    }));
  });
  console.log(JSON.stringify(data, null, 2));
  
  await browser.close();
})();
