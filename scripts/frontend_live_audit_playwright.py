#!/usr/bin/env python3
"""
frontend_live_audit_playwright.py

Lightweight frontend live verification using Playwright (headless Chromium).

What it does:
- Launches a headless Chromium instance using Playwright.
- Visits each frontend view (ports 1420-1429).
- Waits for page load and a short observation window.
- Captures network requests made during the visit (to detect API calls / WS handshakes).
- Extracts API_BASE and websocket URLs discovered in page scripts or runtime globals.
- Scans page HTML for expected endpoints and key libraries (Chart.js, LightweightCharts, Three.js).
- Produces a concise JSON report.

Requirements:
- Python 3.8+
- pip install playwright
- playwright install chromium

Usage:
    python3 scripts/frontend_live_audit_playwright.py

Notes:
- The script is intentionally conservative with timeouts to avoid long hangs.
- If Chromium can't launch due to sandboxing in some environments, Playwright launch args include --no-sandbox.
"""

from __future__ import annotations
import asyncio
import json
import re
import sys
import time
import socket
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, List

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
except ImportError:
    print("ERROR: playwright is required. Install it with: pip install playwright", file=sys.stderr)
    print("Then run: playwright install chromium", file=sys.stderr)
    sys.exit(1)

# Configuration
HOST = "localhost"
PORT = 1420
API_BASE_DEFAULT = f"http://{HOST}:8000/api"
WS_URL_DEFAULT = f"ws://{HOST}:8000/ws"
NAV_TIMEOUT = 15000  # ms
OBSERVE_MS = 3000  # milliseconds to observe network activity after load
CONCURRENT_PAGES = 3  # how many pages to open concurrently
OUTPUT_JSON = Path("frontend_live_audit_playwright_report.json")

# Routes to probe instead of multiple ports
ROUTES = [
    {"name": "status", "path": ""},
    {"name": "opportunities", "path": "#opportunities"},
    {"name": "auto-discovery", "path": "#auto-discovery"},
    {"name": "galaxy", "path": "#galaxy"},
    {"name": "chart", "path": "#chart"},
    {"name": "execution", "path": "#execution"},
    {"name": "settings", "path": "#settings"}
]

# Endpoints to look for (subset used in the audit)
ENDPOINTS = [
    "/api/dashboard/metrics",
    "/api/dashboard/market-data",
    "/api/dashboard/recent-trades",
    "/api/dashboard/positions",
    "/api/failsafe/panic",
    "/api/failsafe/resume",
    "/api/failsafe/status",
    "/api/trades",
    "/api/signals",
    "/api/physics",
]

# Library detection regexes (simple)
LIB_CHECKS = {
    "chartjs": re.compile(r"Chart\.|chart\.umd|chartjs", re.IGNORECASE),
    "lightweight_charts": re.compile(r"LightweightCharts", re.IGNORECASE),
    "three": re.compile(r"three|three\.module", re.IGNORECASE),
    "gsap": re.compile(r"gsap", re.IGNORECASE),
}


def check_backend_connectivity(host: str = HOST, port: int = 8000, timeout: float = 2.0) -> tuple:
    """
    Check if backend is reachable before starting audit.
    Returns (is_reachable, message).
    """
    # First, check TCP connectivity
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        tcp_ok = True
    except (socket.timeout, ConnectionRefusedError, OSError):
        tcp_ok = False
    
    if not tcp_ok:
        return False, f"Backend not reachable at {host}:{port} (TCP connection failed)"
    
    # Try HTTP GET to /api/dashboard/metrics
    try:
        url = f"http://{host}:{port}/api/dashboard/metrics"
        req = urllib.request.Request(url, headers={'User-Agent': 'frontend-live-audit/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as res:
            status = res.status
            if 200 <= status < 500:
                return True, f"Backend reachable at {host}:{port} (HTTP {status})"
            else:
                return False, f"Backend responded with HTTP {status}"
    except urllib.error.HTTPError as e:
        # Even 404/500 means backend is running
        return True, f"Backend reachable at {host}:{port} (HTTP {e.code})"
    except Exception as e:
        # TCP works but HTTP fails - backend might be running something else
        return True, f"Backend port {port} is open (HTTP check failed: {e})"


async def probe_route(browser, route: Dict[str, str]) -> Dict[str, Any]:
    url = f"http://{HOST}:{PORT}/{route['path']}"
    page = await browser.new_page()
    # Shorter viewport to speed rendering
    await page.set_viewport_size({"width": 1200, "height": 800})
    requests: List[Dict[str, Any]] = []
    ws_requests: List[Dict[str, Any]] = []

    def _on_request(req):
        try:
            requests.append({
                "url": req.url,
                "method": req.method,
                "resourceType": req.resource_type,
            })
        except Exception:
            pass

    page.on("request", _on_request)

    # collect console messages too (helpful)
    console_msgs: List[str] = []

    def _on_console(msg):
        try:
            console_msgs.append(f"{msg.type}: {msg.text}")
        except Exception:
            pass

    page.on("console", _on_console)

    result: Dict[str, Any] = {
        "route": route["name"],
        "url": url,
        "loaded": False,
        "status": None,
        "error": None,
        "api_bases": [],
        "ws_urls": [],
        "endpoints_found": [],
        "network_requests": [],
        "libraries_detected": {},
        "backend_status_text": None,
        "console_messages": [],
        "html_snippet": "",
    }

    try:
        # Navigate
        response = await page.goto(url, wait_until="load", timeout=NAV_TIMEOUT)
        if response:
            result["status"] = response.status
        result["loaded"] = True
    except PlaywrightTimeoutError as e:
        result["error"] = f"Navigation timeout: {e}"
    except Exception as e:
        result["error"] = f"Navigation error: {e}"

    # Observe network for a short window to capture dynamic API calls / WS attempts
    await asyncio.sleep(OBSERVE_MS / 1000.0)

    # Snapshot network requests
    result["network_requests"] = requests[-200:]  # keep last 200 for brevity

    # Try to extract API_BASE and WS_URL from runtime (if exposed) and from HTML
    try:
        # Evaluate simple script in page context to return possible globals
        js = """
        (() => {
            const found = { globals: {}, htmlMatches: [] };
            try {
                if (typeof API_BASE !== 'undefined') found.globals.API_BASE = API_BASE;
            } catch(e){}
            try {
                if (typeof WS_URL !== 'undefined') found.globals.WS_URL = WS_URL;
            } catch(e){}
            // Search scripts and inline for common names
            const text = document.documentElement.innerHTML || '';
            const apiMatches = text.match(/API_BASE\\s*=\\s*['`](.*?)['`"]/g) || text.match(/API_BASE\\s*=\\s*["'](.*?)["']/g) || [];
            found.htmlMatches = apiMatches.slice(0, 10);
            // Also search for ws:// occurrences
            const wsMatches = text.match(/ws:\\/\\/[^\\s'"]+/g) || [];
            found.htmlWs = wsMatches.slice(0, 10);
            return found;
        })();
        """
        eval_res = await page.evaluate(js)
        if eval_res:
            g = eval_res.get("globals", {})
            if g.get("API_BASE"):
                result["api_bases"].append(g.get("API_BASE"))
            if g.get("WS_URL"):
                result["ws_urls"].append(g.get("WS_URL"))
            # HTML matches
            html_matches = eval_res.get("htmlMatches", []) or []
            for m in html_matches:
                # extract URL inside quotes
                m_url_match = re.search(r"['\"](.*?)['\"]", m)
                if m_url_match:
                    result["api_bases"].append(m_url_match.group(1))
            html_ws = eval_res.get("htmlWs", []) or []
            for w in html_ws:
                result["ws_urls"].append(w)
    except Exception:
        # ignore evaluation errors
        pass

    # Fallback: search page content for API_BASE-like patterns and WS
    try:
        html = await page.content()
        result["html_snippet"] = "\n".join(html.splitlines()[:40])
        # find API_BASE patterns
        for match in re.finditer(r"API_BASE\s*=\s*['\"]([^'\"]+)['\"]", html):
            result["api_bases"].append(match.group(1))
        for match in re.finditer(r"ws://[^\s'\"<>]+", html):
            result["ws_urls"].append(match.group(0))
        # endpoint presence
        eps_found = [ep for ep in ENDPOINTS if ep in html]
        result["endpoints_found"] = eps_found
    except Exception:
        pass

    # Deduplicate
    result["api_bases"] = list(dict.fromkeys(result["api_bases"]))
    result["ws_urls"] = list(dict.fromkeys(result["ws_urls"]))

    # Detect libraries by checking window globals and by searching HTML text
    libs_detected: Dict[str, bool] = {}
    try:
        # runtime check
        lib_eval = await page.evaluate(
            """() => ({
                Chart: typeof Chart !== 'undefined',
                LightweightCharts: typeof LightweightCharts !== 'undefined',
                THREE: typeof THREE !== 'undefined',
                gsap: typeof gsap !== 'undefined'
            })"""
        )
        libs_detected["chartjs"] = bool(lib_eval.get("Chart"))
        libs_detected["lightweight_charts"] = bool(lib_eval.get("LightweightCharts"))
        libs_detected["three"] = bool(lib_eval.get("THREE"))
        libs_detected["gsap"] = bool(lib_eval.get("gsap"))
    except Exception:
        # fallback to HTML regex search
        html_lower = result["html_snippet"].lower()
        libs_detected["chartjs"] = bool(LIB_CHECKS["chartjs"].search(html_lower))
        libs_detected["lightweight_charts"] = bool(LIB_CHECKS["lightweight_charts"].search(html_lower))
        libs_detected["three"] = bool(LIB_CHECKS["three"].search(html_lower))
        libs_detected["gsap"] = bool(LIB_CHECKS["gsap"].search(html_lower))

    result["libraries_detected"] = libs_detected

    # Try to read the backend status badge text (best-effort)
    try:
        status_text = await page.evaluate(
            """() => {
                const sel = document.querySelector('#backend-status, #status');
                return sel ? (sel.textContent || sel.innerText || '') : null;
            }"""
        )
        if status_text:
            result["backend_status_text"] = status_text.strip()
    except Exception:
        pass

    # Short list of API requests observed (filter network requests)
    api_calls = [r for r in requests if "/api/" in r["url"] or r["url"].startswith("ws://") or r["url"].startswith("wss://")]
    result["api_requests_observed"] = api_calls[-200:]

    # Console messages snapshot
    result["console_messages"] = console_msgs[-200:]

    try:
        await page.close()
    except Exception:
        pass

    return result


async def main() -> int:
    start = time.time()
    
    # Validate backend connectivity before starting
    backend_ok, backend_msg = check_backend_connectivity()
    if not backend_ok:
        print(f"WARNING: {backend_msg}", file=sys.stderr)
        print("The audit will continue, but frontend views may show connection errors.", file=sys.stderr)
        print("", file=sys.stderr)
    elif backend_ok:
        if "--verbose" in sys.argv or "-v" in sys.argv:
            print(f"✓ {backend_msg}")
    
    report: Dict[str, Any] = {
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "api_base_default": API_BASE_DEFAULT,
        "ws_default": WS_URL_DEFAULT,
        "backend_check": {"reachable": backend_ok, "message": backend_msg},
        "probes": [],
        "summary": {}
    }

    try:
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )

            sem = asyncio.Semaphore(CONCURRENT_PAGES)

            async def _probe_with_sem(route):
                async with sem:
                    return await probe_route(browser, route)

            tasks = [_probe_with_sem(r) for r in ROUTES]
            results = await asyncio.gather(*tasks)
            report["probes"] = results

            await browser.close()
    except Exception as e:
        print(f"ERROR: Failed to launch browser: {e}", file=sys.stderr)
        print("Make sure Chromium is installed: playwright install chromium", file=sys.stderr)
        return 1

    # Summarize
    probes_ok = sum(1 for r in results if r.get("loaded") and not r.get("error"))
    report["summary"] = {
        "total_views": len(ROUTES),
        "probed": len(results),
        "successful_loads": probes_ok,
        "routes": [r["name"] for r in ROUTES],
    }

    # Write JSON report
    try:
        OUTPUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Report written to {OUTPUT_JSON}")
    except Exception as e:
        print("Failed to write report:", e, file=sys.stderr)

    elapsed = time.time() - start
    print(f"Completed in {elapsed:.2f}s")
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("Interrupted by user", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)

