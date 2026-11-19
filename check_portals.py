import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        page = await b.new_page(viewport={"width": 1400, "height": 900})
        
        # Check LinkedIn public behavior
        print("Checking LinkedIn...")
        await page.goto("https://www.linkedin.com/jobs/search/?keywords=java%20developer&location=India", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        await page.screenshot(path=r"C:\Users\Sachi\OneDrive\Desktop\nirantar\proofs\linkedin_live_check.png")
        
        # Check Naukri behavior
        print("Checking Naukri...")
        await page.goto("https://www.naukri.com/java-developer-jobs-in-noida", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        await page.screenshot(path=r"C:\Users\Sachi\OneDrive\Desktop\nirantar\proofs\naukri_live_check.png")
        
        print("Done!")
        await b.close()

asyncio.run(main())
