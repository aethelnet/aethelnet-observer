import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  page.on('console', msg => {
    console.log(`[CONSOLE] ${msg.type().toUpperCase()}: ${msg.text()}`);
  });
  
  page.on('pageerror', error => {
    console.log(`[PAGE_ERROR] ${error.message}`);
  });
  
  page.on('requestfailed', request => {
    console.log(`[NETWORK_ERROR] ${request.url()} - ${request.failure()?.errorText}`);
  });

  page.on('response', response => {
    if (response.status() >= 400) {
      console.log(`[RESPONSE_ERROR] ${response.status()} ${response.url()}`);
    }
  });

  try {
    console.log("Navigating to http://127.0.0.1:1420...");
    await page.goto('http://127.0.0.1:1420', { waitUntil: 'networkidle' });
    console.log("Waiting a bit for Vue to mount...");
    await page.waitForTimeout(3000);
    
    // Check if #app is empty
    const appHtml = await page.$eval('#app', el => el.innerHTML);
    if (!appHtml || appHtml.trim() === '') {
       console.log("[ERROR] The #app div is completely empty!");
    } else {
       console.log("[INFO] #app has content.");
    }
    
    console.log("Taking screenshot...");
    await page.screenshot({ path: '/home/nikahrlyn/.gemini/antigravity-cli/brain/e97c7052-e9e3-459b-a0d2-ae7218897ad4/screenshot.png', fullPage: true });
    console.log("Screenshot saved!");
  } catch (err) {
    console.error("[FATAL ERROR]", err);
  } finally {
    await browser.close();
  }
})();
