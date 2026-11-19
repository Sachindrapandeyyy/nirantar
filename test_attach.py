import asyncio
from playwright.async_api import async_playwright

async def t():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        page = await b.new_page(viewport={"width": 1400, "height": 900})
        await page.goto('https://job-boards.greenhouse.io/canonical/jobs/3433732', wait_until='domcontentloaded')
        await page.wait_for_timeout(2000)
        
        attach_btn = page.locator("button:has-text('Attach')").first
        if await attach_btn.count() > 0:
            async with page.expect_file_chooser() as fc_info:
                await attach_btn.click()
            file_chooser = await fc_info.value
            await file_chooser.set_files(r'C:\Users\Sachi\OneDrive\Desktop\dacs\Sachindra_Pandey_Java_Resume.pdf')
            await page.wait_for_timeout(2000)
            print("Attached via file chooser successfully!")

        await page.screenshot(path='./proofs/test_attach_result.png')
        await b.close()

asyncio.run(t())
