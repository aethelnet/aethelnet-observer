import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  try {
    await page.goto('http://localhost:1420', { waitUntil: 'networkidle' });
    console.log("Page loaded");
    
    // Add a Spider Node
    await page.click('button:has-text("SPIDER")');
    await page.waitForTimeout(1000);
    console.log("Added Spider Node");
    
    // Enter URL into Spider Node and click CRAWL
    await page.fill('input[placeholder="Enter URL or Search Query..."]', 'http://example.com');
    await page.click('button:has-text("CRAWL")');
    await page.waitForTimeout(3000); // Wait for crawl stream
    
    // Screenshot after crawl
    await page.screenshot({ path: 'frontend_spider_crawled.png' });
    console.log("Crawl executed, took screenshot");
    
    // Add a Pattern Matcher Node
    await page.click('button:has-text("PATTERN")');
    await page.waitForTimeout(1000);
    
    // Type pattern and click MATCH
    await page.fill('input[placeholder="Regex or text pattern..."]', 'example');
    await page.click('button:has-text("MATCH")');
    await page.waitForTimeout(1000);
    
    await page.screenshot({ path: 'frontend_pattern.png' });
    console.log("Pattern matched, took screenshot");
    
  } catch (e) {
    console.error("Test error:", e);
  } finally {
    await browser.close();
  }
})();
