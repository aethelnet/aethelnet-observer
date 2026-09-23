import { chromium } from 'playwright';

async function verify() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  page.on('console', msg => console.log('[BROWSER CONSOLE]', msg.type(), msg.text()));
  page.on('pageerror', err => console.error('[BROWSER ERROR]', err));

  console.log('Navigating to http://localhost:1420...');
  await page.goto('http://localhost:1420', { waitUntil: 'networkidle' });

  // Wait 3 seconds for ethers to query the local RPC and update reactive state
  await page.waitForTimeout(3000);

  // Read header metrics
  const headerText = await page.innerText('.header-metrics');
  console.log('Header Metrics:\n', headerText);

  // Read active nodes count from pill
  const activeNodesText = await page.innerText('.metric-pill:has-text("ACTIVE NODES") .pill-val');
  console.log('Pill Active Nodes Count:', activeNodesText);

  // Read node labels in radar
  const nodeLabels = await page.$$eval('.node-ip-label', els => els.map(e => e.textContent));
  console.log('Rendered Node Labels in Topology SVG:', nodeLabels);

  // Read node time labels
  const timeLabels = await page.$$eval('.node-time-label', els => els.map(e => e.textContent));
  console.log('Rendered Time Labels in Topology SVG:', timeLabels);

  // Read HUD details
  const hudDetails = await page.innerText('.hud-left');
  console.log('HUD Left Text:\n', hudDetails);

  // Read Inspector details
  const inspectorText = await page.innerText('.node-inspector');
  console.log('Inspector Details:\n', inspectorText);

  await page.screenshot({ path: './tests/e2e/screenshots/observer_live_topology.png', fullPage: true });
  console.log('Screenshot saved to tests/e2e/screenshots/observer_live_topology.png');

  await browser.close();
}

verify().catch(console.error);
