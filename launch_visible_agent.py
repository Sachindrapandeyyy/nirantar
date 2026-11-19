import subprocess
import time
import httpx
import asyncio
from playwright.async_api import async_playwright

async def launch_and_control():
    # Kill any stuck Chrome processes first
    subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], capture_output=True)
    time.sleep(2)

    # Launch Real Chrome with persistent profile & remote debugging
    cmd = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "--remote-debugging-port=9222",
        r"--user-data-dir=C:\Users\Sachi\.nirantar\chrome_profile",
        "--start-maximized",
        "https://www.linkedin.com/jobs/"
    ]
    
    print("Launching Real Chrome directly on your screen...")
    # Using creationflags=subprocess.DETACHED_PROCESS so it stays alive permanently on screen!
    proc = subprocess.Popen(cmd, close_fds=True)
    
    # Wait for CDP to respond
    cdp_connected = False
    for i in range(15):
        time.sleep(1)
        try:
            r = httpx.get("http://127.0.0.1:9222/json/version", timeout=1.0)
            if r.status_code == 200:
                print("CDP Connected successfully on port 9222! Version:", r.json().get("Browser"))
                cdp_connected = True
                break
        except Exception:
            pass

    if not cdp_connected:
        print("Failed to connect to CDP on 9222.")
        return

    # Connect Nirantar Agent via CDP
    print("Nirantar Agent taking over your Chrome window...")
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        
        # Get active page or create one
        page = context.pages[0] if context.pages else await context.new_page()
        await page.bring_to_front()
        
        # Navigate to LinkedIn search
        await page.goto("https://www.linkedin.com/jobs/search/?keywords=Java%20Spring%20Boot&location=Noida%2C%20India", wait_until="domcontentloaded")
        await asyncio.sleep(2)
        
        # Inject Comet Blue Glow Takeover HUD
        await page.evaluate("""
            (() => {
                if (document.getElementById('nirantar-screen-hud')) return;
                const glow = document.createElement('div');
                glow.id = 'nirantar-screen-hud';
                glow.style.cssText = `
                    position: fixed !important;
                    top: 0 !important;
                    left: 0 !important;
                    width: 100vw !important;
                    height: 100vh !important;
                    border: 6px solid #0088ff !important;
                    box-shadow: inset 0 0 40px 10px rgba(0, 136, 255, 0.85) !important;
                    z-index: 2147483640 !important;
                    pointer-events: none !important;
                `;
                document.body.appendChild(glow);

                const banner = document.createElement('div');
                banner.style.cssText = `
                    position: fixed !important;
                    top: 20px !important;
                    left: 50% !important;
                    transform: translateX(-50%) !important;
                    background: #0a0f1e !important;
                    border: 2px solid #00d2ff !important;
                    box-shadow: 0 10px 30px rgba(0, 136, 255, 0.6) !important;
                    color: #ffffff !important;
                    padding: 10px 30px !important;
                    border-radius: 9999px !important;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
                    font-size: 15px !important;
                    font-weight: bold !important;
                    display: flex !important;
                    align-items: center !important;
                    gap: 12px !important;
                    z-index: 2147483647 !important;
                    pointer-events: none !important;
                `;
                banner.innerHTML = `
                    <span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:#00e5ff;box-shadow:0 0 12px #00e5ff;"></span>
                    <span style="color:#00e5ff;letter-spacing:1px;">NIRANTAR AGENT TAKEOVER</span>
                    <span style="color:#718096;">|</span>
                    <span style="color:#fff;">Candidate: Sachindra Shekhar Pandey | Status: Active</span>
                `;
                document.body.appendChild(banner);
            })();
        """)
        
        print("Blue Glow HUD injected on your screen!")
        await asyncio.sleep(4)
        
        # Open second tab for Naukri
        naukri_page = await context.new_page()
        await naukri_page.bring_to_front()
        await naukri_page.goto("https://www.naukri.com/java-developer-jobs-in-noida", wait_until="domcontentloaded")
        await asyncio.sleep(2)
        
        await naukri_page.evaluate("""
            (() => {
                const glow = document.createElement('div');
                glow.style.cssText = `
                    position: fixed !important;
                    top: 0 !important;
                    left: 0 !important;
                    width: 100vw !important;
                    height: 100vh !important;
                    border: 6px solid #0088ff !important;
                    box-shadow: inset 0 0 40px 10px rgba(0, 136, 255, 0.85) !important;
                    z-index: 2147483640 !important;
                    pointer-events: none !important;
                `;
                document.body.appendChild(glow);

                const banner = document.createElement('div');
                banner.style.cssText = `
                    position: fixed !important;
                    top: 20px !important;
                    left: 50% !important;
                    transform: translateX(-50%) !important;
                    background: #0a0f1e !important;
                    border: 2px solid #00d2ff !important;
                    color: #ffffff !important;
                    padding: 10px 30px !important;
                    border-radius: 9999px !important;
                    font-family: sans-serif !important;
                    font-size: 15px !important;
                    font-weight: bold !important;
                    z-index: 2147483647 !important;
                    pointer-events: none !important;
                `;
                banner.innerHTML = '🤖 NIRANTAR AGENT TAKEOVER | Scanning Naukri Java Jobs...';
                document.body.appendChild(banner);
            })();
        """)
        
        print("Naukri tab active with Blue Glow HUD!")
        
        # Disconnect CDP without closing the browser
        await browser.close()
        print("Done! Chrome remains completely open and visible on your screen.")

if __name__ == "__main__":
    asyncio.run(launch_and_control())
