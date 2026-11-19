import asyncio
import subprocess
import time
import httpx
from playwright.async_api import async_playwright
from core.vault import vault
from core.matcher import matcher

async def run_live_on_screen():
    profile = vault.get_profile()
    
    # 1. Check if Chrome on 9222 is already listening
    cdp_ready = False
    try:
        r = httpx.get("http://127.0.0.1:9222/json/version", timeout=1.0)
        cdp_ready = r.status_code == 200
    except Exception:
        pass

    if not cdp_ready:
        print("Launching Real Google Chrome on your screen...")
        subprocess.Popen([
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "--remote-debugging-port=9222",
            r"--user-data-dir=C:\Users\Sachi\.nirantar\chrome_profile",
            "--start-maximized"
        ])
        
        # Wait for Chrome to pop up and bind port 9222
        for _ in range(10):
            await asyncio.sleep(1)
            try:
                r = httpx.get("http://127.0.0.1:9222/json/version", timeout=1.0)
                if r.status_code == 200:
                    cdp_ready = True
                    break
            except Exception:
                pass

    if not cdp_ready:
        print("Error: Could not bind Chrome to port 9222.")
        return

    print("Connecting Nirantar Agent directly to your open Chrome window...")
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = await context.new_page()
        await page.bring_to_front()

        # Step A: Navigate to a live search & show Blue Glow Takeover
        print("Navigating to LinkedIn Job Portal on your screen...")
        await page.goto("https://www.linkedin.com/jobs/search/?keywords=Java%20Spring%20Boot%20Developer&location=Noida%2C%20Uttar%20Pradesh%2C%20India", wait_until="domcontentloaded")
        
        # Inject Comet Blue Glow Takeover overlay
        await page.evaluate("""
            (() => {
                const glow = document.createElement('div');
                glow.id = 'nirantar-live-glow';
                glow.style.cssText = `
                    position: fixed !important;
                    top: 0 !important;
                    left: 0 !important;
                    width: 100vw !important;
                    height: 100vh !important;
                    border: 5px solid #0088ff !important;
                    box-shadow: inset 0 0 35px 8px rgba(0, 136, 255, 0.8), 0 0 25px rgba(0, 136, 255, 0.7) !important;
                    z-index: 2147483640 !important;
                    pointer-events: none !important;
                `;
                document.body.appendChild(glow);

                const banner = document.createElement('div');
                banner.id = 'nirantar-live-banner';
                banner.style.cssText = `
                    position: fixed !important;
                    top: 18px !important;
                    left: 50% !important;
                    transform: translateX(-50%) !important;
                    background: rgba(10, 18, 38, 0.95) !important;
                    border: 1px solid #00d2ff !important;
                    box-shadow: 0 10px 30px rgba(0, 136, 255, 0.4) !important;
                    color: #ffffff !important;
                    padding: 10px 28px !important;
                    border-radius: 9999px !important;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
                    font-size: 14px !important;
                    font-weight: 600 !important;
                    display: flex !important;
                    align-items: center !important;
                    gap: 12px !important;
                    z-index: 2147483647 !important;
                    pointer-events: none !important;
                `;
                banner.innerHTML = `
                    <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#00e5ff;box-shadow:0 0 10px #00e5ff;"></span>
                    <span style="color:#00d2ff;letter-spacing:0.5px;">NIRANTAR AGENT TAKEOVER</span>
                    <span style="color:#718096;">|</span>
                    <span id="nirantar-live-text">Target: Java Jobs in Noida | Candidate: Sachindra Shekhar Pandey</span>
                `;
                document.body.appendChild(banner);
            })();
        """)
        
        print("Blue Glow HUD active on your screen!")
        await asyncio.sleep(4)

        # Step B: Open Naukri Java Developer Jobs in another tab
        print("Opening Naukri in your Chrome window...")
        naukri_page = await context.new_page()
        await naukri_page.bring_to_front()
        await naukri_page.goto("https://www.naukri.com/java-developer-jobs-in-noida", wait_until="domcontentloaded")
        
        await naukri_page.evaluate("""
            (() => {
                const glow = document.createElement('div');
                glow.style.cssText = `
                    position: fixed !important;
                    top: 0 !important;
                    left: 0 !important;
                    width: 100vw !important;
                    height: 100vh !important;
                    border: 5px solid #0088ff !important;
                    box-shadow: inset 0 0 35px 8px rgba(0, 136, 255, 0.8) !important;
                    z-index: 2147483640 !important;
                    pointer-events: none !important;
                `;
                document.body.appendChild(glow);

                const banner = document.createElement('div');
                banner.style.cssText = `
                    position: fixed !important;
                    top: 18px !important;
                    left: 50% !important;
                    transform: translateX(-50%) !important;
                    background: rgba(10, 18, 38, 0.95) !important;
                    border: 1px solid #00d2ff !important;
                    color: #ffffff !important;
                    padding: 10px 28px !important;
                    border-radius: 9999px !important;
                    font-family: sans-serif !important;
                    font-size: 14px !important;
                    font-weight: 600 !important;
                    z-index: 2147483647 !important;
                    pointer-events: none !important;
                `;
                banner.innerHTML = '🤖 NIRANTAR AGENT TAKEOVER | Scanning Naukri Java Jobs...';
                document.body.appendChild(banner);
            })();
        """)
        
        await asyncio.sleep(5)
        print("Naukri tab loaded with Blue Glow HUD!")
        
        # We do NOT close the browser - it remains open on the user's screen!
        await browser.close() # Only disconnects Playwright, Chrome stays OPEN!
        print("SUCCESS: Real Chrome remains active and open on your screen!")

asyncio.run(run_live_on_screen())
