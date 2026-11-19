import asyncio
import subprocess
import httpx
from playwright.async_api import async_playwright

async def main():
    print("Step 1: Closing existing Chrome to enable remote agent control...")
    subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], capture_output=True)
    await asyncio.sleep(2)

    print("Step 2: Launching your personal Google Chrome with agent access...")
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    subprocess.Popen([
        chrome_path,
        "--remote-debugging-port=9222",
        "--restore-last-session",
        "--start-maximized"
    ])

    # Wait for port 9222 to be ready
    cdp_ready = False
    for i in range(12):
        await asyncio.sleep(1)
        try:
            r = httpx.get("http://127.0.0.1:9222/json/version", timeout=1.0)
            if r.status_code == 200:
                print("CDP connected to your real Chrome:", r.json().get("Browser"))
                cdp_ready = True
                break
        except Exception:
            pass

    if not cdp_ready:
        print("Failed to bind port 9222.")
        return

    print("Step 3: Connecting Nirantar Agent to your live Chrome window...")
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        
        # Open a new tab right in front of the user!
        page = await context.new_page()
        await page.bring_to_front()
        
        print("Navigating to LinkedIn in your Chrome...")
        await page.goto("https://www.linkedin.com/jobs/search/?keywords=Java%20Spring%20Boot%20Developer&location=Noida%2C%20India", wait_until="domcontentloaded")
        
        # Inject Comet Blue Glow Takeover
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
                    border: 6px solid #0088ff !important;
                    box-shadow: inset 0 0 35px 8px rgba(0, 136, 255, 0.85), 0 0 25px rgba(0, 136, 255, 0.75) !important;
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
                    box-shadow: 0 10px 30px rgba(0, 136, 255, 0.5) !important;
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
                    <span>Candidate: Sachindra Shekhar Pandey | Status: Active</span>
                `;
                document.body.appendChild(banner);
            })();
        """)
        
        print("Blue Glow HUD active right on your screen!")
        await asyncio.sleep(6)
        
        # Disconnect CDP cleanly so user can continue using Chrome
        await browser.close()
        print("SUCCESS: Nirantar connected, took over the tab, and Chrome is right on your screen!")

if __name__ == "__main__":
    asyncio.run(main())
