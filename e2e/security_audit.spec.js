import { test, expect } from '@playwright/test';

// Maximale Penetration Testing \u0026 Vulnerability Scan Suite für Auratic Systems Prime
// Dieses Skript ist darauf ausgelegt, die Schwachstellen des Frontends/Backends schonungslos aufzudecken.

test.describe('Auratic Systems Security Audit \u0026 Penetration Test', () => {
  const TARGET_URL = 'http://100.103.122.11:8000';
  const DEV_SERVER_URL = 'http://localhost:1420'; // Vite Dev Server

  test('1. API Endpoint Discovery \u0026 Enumeration', async ({ request }) => {
    // Wir feuern blind auf typische versteckte/Admin-Endpunkte, um zu sehen, was offen ist.
    const probeEndpoints = [
      '/api/config',
      '/api/debug/logs',
      '/api/admin',
      '/api/users',
      '/api/failsafe/status',
      '/metrics',
      '/health',
      '/.env',
      '/.git/config',
      '/api/trading/keys'
    ];

    console.log('\n=================================================');
    console.log('🛡️  PHASE 1: Endpoint Enumeration (DirBuster-Style) ');
    console.log('=================================================\n');

    for (const ep of probeEndpoints) {
      const response = await request.get(`${TARGET_URL}${ep}`, { failOnStatusCode: false });
      const status = response.status();
      const body = await response.text();
      
      if (status !== 404) {
         console.log(`[ALERT] Endpoint exposed: ${ep} (Status: ${status})`);
         if (status === 200) {
            console.log(`[DATA] Exfil snippet: ${body.substring(0, 100)}...`);
         }
      } else {
         console.log(`[SECURE] ${ep} is properly hidden (404).`);
      }
    }
  });

  test('2. WebSocket Hijacking \u0026 Authentication Bypass', async ({ page }) => {
    console.log('\n=================================================');
    console.log('🛡️  PHASE 2: WebSocket Interception \u0026 Auth Bypass ');
    console.log('=================================================\n');

    const leakedTokens = [];

    // Wir schnüffeln im LocalStorage und in den Websocket-Frames nach Authentifizierungs-Token
    page.on('websocket', ws => {
      console.log(`[WS] Connection opened to: ${ws.url()}`);
      
      ws.on('framesent', payload => {
        const text = payload.toString();
        if (text.toLowerCase().includes('token') || text.toLowerCase().includes('auth') || text.toLowerCase().includes('key')) {
           console.log(`[VULNERABILITY] WS is leaking auth/token data in plain text: ${text}`);
        }
      });
      
      ws.on('framereceived', payload => {
        const text = payload.toString();
        // Suchen nach sensitiven Daten, die das Backend vielleicht unverschlüsselt an alle broadcastet
        if (text.includes('balance') || text.includes('secret') || text.includes('api_key')) {
           console.log(`[VULNERABILITY] Backend is broadcasting sensitive state: ${text.substring(0, 150)}...`);
        }
      });
    });

    // Wir laden die Vite-Version (da wir wissen, dass die `api.js` Logik dort aktuell ist)
    try {
      await page.goto(DEV_SERVER_URL, { waitUntil: 'networkidle', timeout: 5000 });
    } catch(e) {
      // Fallback
      await page.goto(TARGET_URL);
    }
    
    // Prüfen, ob LocalStorage sensible Daten (wie API-Keys) im Klartext speichert
    const lsKeys = await page.evaluate(() => Object.keys(localStorage));
    for (const key of lsKeys) {
        if(key.toLowerCase().includes('key') || key.toLowerCase().includes('token') || key.toLowerCase().includes('secret')) {
             const val = await page.evaluate((k) => localStorage.getItem(k), key);
             console.log(`[CRITICAL VULNERABILITY] LocalStorage leaks sensitive key '${key}': ${val}`);
        }
    }
    
    await page.waitForTimeout(5000);
  });

  test('3. Cross-Site Scripting (XSS) \u0026 Injection Payload Tests', async ({ page, request }) => {
    console.log('\n=================================================');
    console.log('🛡️  PHASE 3: Injection \u0026 XSS Surface Scan ');
    console.log('=================================================\n');

    // Wir simulieren einen bösartigen POST Request auf die Auto-Discovery / Whitelist API
    // um zu sehen, ob das Backend unsanitized Input frisst.
    
    const maliciousPayload = {
       symbol: "\u003cscript\u003ealert('XSS')\u003c/script\u003e DROP TABLE users;--",
       username: "admin' OR 1=1--"
    };

    const response = await request.post(`${TARGET_URL}/api/stream/hive/add-ally`, {
        data: { username: maliciousPayload.username },
        failOnStatusCode: false
    });

    if (response.status() === 200 || response.status() === 201) {
        console.log(`[CRITICAL VULNERABILITY] Backend accepted SQL Injection / XSS payload in add-ally endpoint!`);
    } else {
        console.log(`[SECURE] Backend properly rejected malicious payload in add-ally (Status: ${response.status()}).`);
    }
    
  });

  test('4. WebSocket Fuzzing (Salat Sauce Chaos)', async ({ page }) => {
    console.log('\n=================================================');
    console.log('🛡️  PHASE 4: WebSocket Fuzzing (Salat Sauce) ');
    console.log('=================================================\n');
    
    await page.goto('about:blank');
    
    const wsUrl = TARGET_URL.replace('http', 'ws') + '/ws/stream';
    const fuzzingResults = await page.evaluate(async (url) => {
       return new Promise((resolve) => {
           let results = [];
           const ws = new WebSocket(url);
           
           ws.onopen = () => {
               results.push("WS Opened. Commencing Fuzzing...");
               // 1. Valid Auth format attempt
               ws.send(JSON.stringify({ type: "AUTH", token: "fuzz_token" }));
               
               // 2. Fuzzing Payload 1: Malformed JSON
               ws.send("{ malformed: json ]");
               
               // 3. Fuzzing Payload 2: Massive Array (Memory Exhaustion Attempt)
               const massiveArray = Array(100000).fill("A").join("");
               ws.send(JSON.stringify({ type: "FUZZ", payload: massiveArray }));
               
               // 4. Fuzzing Payload 3: Unexpected Data Types
               ws.send(JSON.stringify({ type: 12345, payload: null }));
               
               // 5. Fuzzing Payload 4: Injection in Type
               ws.send(JSON.stringify({ type: "FETCH_HISTORY' OR 1=1--", payload: {} }));
               
               setTimeout(() => {
                   results.push("All fuzzing payloads sent.");
                   ws.close();
                   resolve(results);
               }, 2000);
           };
           
           ws.onerror = (e) => {
               results.push("WS Error caught (expected during fuzzing).");
           };
           
           ws.onclose = (e) => {
               results.push(`WS Closed with code: ${e.code}`);
           };
           
           // Fail safe timeout
           setTimeout(() => resolve(results), 3000);
       });
    }, wsUrl);
    
    for(const res of fuzzingResults) {
        console.log(`[FUZZ] ${res}`);
    }
    console.log('[SECURE] If the backend is still running after this, it survived the Salat Sauce.');
  });
});
