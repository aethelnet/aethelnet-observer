import { test, expect } from '@playwright/test';

test('Sniff Network Traffic and WebSockets', async ({ page }) => {
  // 1. Alle HTTP Requests abfangen und loggen
  page.on('request', request => {
    console.log(`>> [HTTP REQ] ${request.method()} ${request.url()}`);
  });

  // 2. Alle HTTP Responses abfangen und loggen
  page.on('response', response => {
    console.log(`<< [HTTP RES] ${response.status()} ${response.url()}`);
  });

  // 3. WebSockets abfangen (Hier wird es für uns interessant!)
  page.on('websocket', ws => {
    console.log(`\n=================================================`);
    console.log(`🚀 [WEBSOCKET] Verbindungsaufbau zu: ${ws.url()}`);
    console.log(`=================================================\n`);

    ws.on('framesent', payload => {
      console.log(`[WS ->] Gesendet:`, payload);
    });
    
    ws.on('framereceived', payload => {
      console.log(`[WS <-] Empfangen:`, payload);
    });

    ws.on('close', () => {
      console.log(`[WS ❌] Verbindung geschlossen: ${ws.url()}`);
    });
  });

  // Wir rufen den Frontend-Server auf
  console.log("Navigiere zum Frontend...");
  await page.goto('http://100.103.122.11:8000');

  // Wir warten 10 Sekunden, um dem Frontend Zeit zu geben, Verbindungen aufzubauen und Traffic zu generieren
  await page.waitForTimeout(10000);
});
