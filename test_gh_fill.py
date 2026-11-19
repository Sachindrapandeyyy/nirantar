import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        page = await b.new_page(viewport={"width": 1400, "height": 900})
        await page.goto("https://job-boards.greenhouse.io/canonical/jobs/3433732", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)

        # 1. First & Last & Email & Phone
        await page.fill("#first_name", "Sachindra")
        await page.fill("#last_name", "Pandey")
        await page.fill("#email", "sachindrapandey328@gmail.com")
        await page.fill("#phone", "7905604539")

        # 2. Country select (React Combobox)
        # Check what #country actually is
        country_el = page.locator("#country")
        print("Country tag:", await country_el.evaluate("el => el.tagName"))
        # Type India and press Enter or ArrowDown + Enter
        await country_el.click()
        await country_el.fill("India")
        await page.wait_for_timeout(500)
        await page.keyboard.press("ArrowDown")
        await page.keyboard.press("Enter")

        # 3. Resume upload
        resume_path = r"C:\Users\Sachi\OneDrive\Desktop\dacs\Sachindra_Pandey_Java_Resume.pdf"
        file_input = page.locator("input#resume")
        await file_input.set_input_files(resume_path)
        await page.wait_for_timeout(1500)

        # Check if file upload reflected in UI
        upload_text = await page.locator("#resume-preview, div:has-text('Sachindra_Pandey')").all_inner_texts()
        print("Upload UI reflection:", upload_text)

        # 4. Education Fields
        school_el = page.locator("#school--0")
        if await school_el.count() > 0:
            print("School element found, tag:", await school_el.evaluate("el => el.tagName"))
            await school_el.click()
            await school_el.fill("Shri Ramswaroop Memorial University")
            await page.wait_for_timeout(500)
            await page.keyboard.press("ArrowDown")
            await page.keyboard.press("Enter")

        degree_el = page.locator("#degree--0")
        if await degree_el.count() > 0:
            await degree_el.click()
            await degree_el.fill("Bachelor of Technology")
            await page.wait_for_timeout(500)
            await page.keyboard.press("ArrowDown")
            await page.keyboard.press("Enter")

        discipline_el = page.locator("#discipline--0")
        if await discipline_el.count() > 0:
            await discipline_el.click()
            await discipline_el.fill("Computer Science")
            await page.wait_for_timeout(500)
            await page.keyboard.press("ArrowDown")
            await page.keyboard.press("Enter")

        # Take full page screenshot
        await page.screenshot(path="./proofs/full_test_canonical.png", full_page=True)
        print("Saved full page screenshot to ./proofs/full_test_canonical.png")
        await b.close()

asyncio.run(main())
