import asyncio
import subprocess
import time
from playwright.async_api import async_playwright

async def demo_real_screen_takeover():
    # 1. Launch real Chrome with 9222
    print("Launching visible Real Chrome on screen...")
    proc = subprocess.Popen([
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "--remote-debugging-port=9222",
        r"--user-data-dir=C:\Users\Sachi\.nirantar\chrome_profile"
    ])
    
    # Wait for CDP port to be ready
    await asyncio.sleep(2.5)

    async with async_playwright() as p:
        print("Connecting Nirantar Agent to your Chrome screen via CDP...")
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = await context.new_page()
        
        # Navigate to a real page
        await page.goto("https://www.google.com")
        await page.bring_to_front()
        
        # Inject Comet Blue Glow Takeover
        await page.evaluate("""
            const b = document.createElement('div');
            b.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;border:6px solid #0088ff;box-shadow:inset 0 0 30px #0088ff;z-index:9999999;pointer-events:none;';
            document.body.appendChild(b);
            const banner = document.createElement('div');
            banner.style.cssText = 'position:fixed;top:20px;left:50%;transform:translateX(-50%);background:#0a0f1e;color:#00e5ff;padding:10px 24px;border-radius:30px;font-family:sans-serif;font-weight:bold;font-size:14px;box-shadow:0 10px 25px rgba(0,128,255,0.5);z-index:10000000;';
            banner.innerText = '🤖 NIRANTAR AGENT TAKEOVER ON YOUR SCREEN!';
            document.body.appendChild(banner);
        """)
        
        print("Simulating visual interaction in front of user...")
        search_input = page.locator("textarea[name='q'], input[name='q']").first
        if await search_input.count() > 0:
            await search_input.click()
            for char in "Sachindra Shekhar Pandey Software Engineer":
                await page.keyboard.type(char)
                await asyncio.sleep(0.08)
        
        await asyncio.sleep(4)
        print("Demo completed successfully on user screen!")
        await page.close()
        await browser.close()
    
    proc.terminate()

asyncio.run(demo_real_screen_takeover())
