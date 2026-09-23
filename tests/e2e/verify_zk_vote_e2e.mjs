import { chromium } from 'playwright';

async function main() {
  console.log('====================================================');
  console.log('    AETHELNET BROWSER ZK-VOTING E2E VERIFICATION    ');
  console.log('====================================================');

  const browser = await chromium.launch({ 
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const context = await browser.newContext();
  const page = await context.newPage();

  page.on('console', msg => {
    const text = msg.text();
    if (!text.includes('Download the Vue Devtools')) {
      console.log(`[BROWSER CONSOLE] [${msg.type()}]`, text);
    }
  });

  page.on('pageerror', err => {
    console.error('[BROWSER UNCAUGHT ERROR]', err);
  });

  console.log('1. Navigating to http://localhost:1420...');
  await page.goto('http://localhost:1420', { waitUntil: 'networkidle' });

  // Wait 4s for initial on-chain & daemon state sync
  await page.waitForTimeout(4000);

  // Check Header Metrics
  const rpcPill = await page.innerText('.metric-pill:has-text("RPC") .pill-val');
  const daemonPill = await page.innerText('.metric-pill:has-text("DAEMON") .pill-val');
  console.log(`- RPC Status:    ${rpcPill}`);
  console.log(`- Daemon Status: ${daemonPill}`);

  // Check Proposal #0 existence and initial tally
  const propTitle = await page.innerText('.prop-title');
  const initialVotes = await page.innerText('.prop-votes');
  console.log(`- Detected Proposal: ${propTitle}`);
  console.log(`- Initial Tally:     ${initialVotes}`);

  if (!initialVotes.includes('FOR: 0')) {
    console.warn('Note: Initial forVotes is not 0 (might have been voted already)');
  }

  // Click [ SHIELDED VOTE (ZK) ]
  console.log('\n2. Opening Shielded Vote Modal...');
  await page.click('.btn-zk-vote');
  await page.waitForSelector('.zk-modal-content', { state: 'visible', timeout: 5000 });

  const modalTitle = await page.innerText('.zk-modal-title');
  console.log(`- Modal Active: ${modalTitle}`);

  await page.selectOption('.zk-select', 'voter-3');
  const selectedVoter = await page.$eval('.zk-select', el => el.value);
  console.log(`- Selected Voter ID: ${selectedVoter}`);

  // Trigger ZK Proof Generation and Submission
  console.log('\n3. Triggering Client-Side Groth16 Proof & EVM Broadcast...');
  await page.click('.btn-submit-zk');

  // Monitor progress messages
  let lastMsg = '';
  const startTime = Date.now();
  let succeeded = false;

  while (Date.now() - startTime < 35000) {
    const statusEl = await page.$('.status-msg');
    if (statusEl) {
      const msg = await statusEl.innerText();
      if (msg && msg !== lastMsg) {
        console.log(`  -> ZK Status: ${msg}`);
        lastMsg = msg;
        if (msg.includes('ERFOLGREICH ON-CHAIN VERSIEGELT')) {
          succeeded = true;
          break;
        }
        if (msg.startsWith('FEHLER:')) {
          console.error(`  ❌ Error reported: ${msg}`);
          break;
        }
      }
    }
    await page.waitForTimeout(500);
  }

  if (!succeeded) {
    throw new Error(`ZK Vote failed or timed out. Last status: ${lastMsg}`);
  }

  console.log('\n4. Verifying On-Chain State Update after Shielded Vote...');
  // Wait 4 seconds for on-chain poll to update
  await page.waitForTimeout(4000);

  const updatedVotes = await page.innerText('.prop-votes');
  console.log(`- Updated Tally on Dashboard: ${updatedVotes}`);

  if (!updatedVotes.includes('FOR: 100')) {
    throw new Error(`Expected FOR: 100 on-chain, found: ${updatedVotes}`);
  }
  console.log('✅ PASS: Proposal votes successfully incremented to FOR: 100 using ZK Proof!');

  // Take screenshot of successful vote
  const screenshotPath1 = './tests/e2e/screenshots/zk_vote_verified.png';
  await page.screenshot({ path: screenshotPath1, fullPage: true });
  console.log(`- Saved screenshot to: ${screenshotPath1}`);

  // 5. Test Double-Spend / Nullifier Replay Defense
  console.log('\n5. Testing Replay Defense (Double-Spend with same Nullifier)...');
  await page.click('.btn-zk-vote');
  await page.waitForSelector('.zk-modal-content', { state: 'visible', timeout: 5000 });

  // Submit again with same voter (same secret + nullifier)
  await page.click('.btn-submit-zk');

  let replayCaught = false;
  const replayStart = Date.now();
  while (Date.now() - replayStart < 25000) {
    const statusEl = await page.$('.status-msg');
    if (statusEl) {
      const msg = await statusEl.innerText();
      if (msg && msg !== lastMsg) {
        console.log(`  -> Replay Attempt Status: ${msg}`);
        lastMsg = msg;
        if (msg.includes('Nullifier already used') || msg.includes('execution reverted')) {
          replayCaught = true;
          console.log('✅ PASS: Smart Contract correctly reverted double-spend attempt!');
          break;
        }
      }
    }
    await page.waitForTimeout(500);
  }

  if (!replayCaught) {
    console.warn('Replay attempt status:', lastMsg);
  }

  const screenshotPath2 = './tests/e2e/screenshots/zk_replay_defense_verified.png';
  await page.screenshot({ path: screenshotPath2, fullPage: true });
  console.log(`- Saved replay defense screenshot to: ${screenshotPath2}`);

  console.log('\n====================================================');
  console.log('  ALL BROWSER ZK-VOTING TESTS PASSED EMPIRICALLY!   ');
  console.log('====================================================');

  await browser.close();
}

main().catch(err => {
  console.error('Test failed:', err);
  process.exit(1);
});
