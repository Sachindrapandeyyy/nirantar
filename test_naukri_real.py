import asyncio
from playwright.async_api import async_playwright

async def test_real_chrome():
    async with async_playwright() as p:
        # Launch REAL Chrome
        context = await p.chromium.launch_persistent_context(
            user_data_dir=r"C:\Users\Sachi\.nirantar\chrome_profile",
            channel="chrome",
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        page = context.pages[0] if context.pages else await context.new_page()
        print("Opening Naukri with Real Chrome...")
        await page.goto("https://www.naukri.com/java-developer-jobs-in-noida", wait_until="domcontentloaded")
        await page.wait_for_timeout(4000)
        await page.screenshot(path=r"C:\Users\Sachi\OneDrive\Desktop\nirantar\proofs\naukri_real_chrome.png")
        print("Page title:", await page.title())
        await context.close()

asyncio.run(test_real_chrome())
