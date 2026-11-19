import asyncio
import time
from playwright.async_api import async_playwright
from core.vault import vault

async def execute_live_workflow():
    profile = vault.get_profile()
    resume_path = vault.get_resume("java")
    
    print("Connecting Nirantar Agent to your active Chrome on screen...")
    async with async_playwright() as p:
        # Connect to the running Chrome on port 9222
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = await context.new_page()
        await page.bring_to_front()

        # Step 1: Navigate to the job application
        job_url = "https://job-boards.greenhouse.io/canonical/jobs/3433732"
        print(f"Navigating to {job_url} on your Chrome screen...")
        await page.goto(job_url, wait_until="domcontentloaded")
        await asyncio.sleep(2)

        # Step 2: Inject Comet Blue Glow Takeover HUD
        print("Injecting Comet Blue Glow HUD on your screen...")
        await page.evaluate("""
            (() => {
                const glow = document.createElement('div');
                glow.id = 'nirantar-active-hud';
                glow.style.cssText = `
                    position: fixed !important;
                    top: 0 !important;
                    left: 0 !important;
                    width: 100vw !important;
                    height: 100vh !important;
                    border: 6px solid #0088ff !important;
                    box-shadow: inset 0 0 45px 12px rgba(0, 136, 255, 0.9), 0 0 30px rgba(0, 136, 255, 0.8) !important;
                    z-index: 2147483640 !important;
                    pointer-events: none !important;
                `;
                document.body.appendChild(glow);

                const banner = document.createElement('div');
                banner.id = 'nirantar-banner';
                banner.style.cssText = `
                    position: fixed !important;
                    top: 18px !important;
                    left: 50% !important;
                    transform: translateX(-50%) !important;
                    background: #060913 !important;
                    border: 2px solid #00e5ff !important;
                    box-shadow: 0 10px 35px rgba(0, 136, 255, 0.6) !important;
                    color: #ffffff !important;
                    padding: 12px 32px !important;
                    border-radius: 9999px !important;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
                    font-size: 15px !important;
                    font-weight: 700 !important;
                    display: flex !important;
                    align-items: center !important;
                    gap: 14px !important;
                    z-index: 2147483647 !important;
                    pointer-events: none !important;
                `;
                banner.innerHTML = `
                    <span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:#00e5ff;box-shadow:0 0 12px #00e5ff;"></span>
                    <span style="color:#00e5ff;letter-spacing:1px;">NIRANTAR WORKFLOW ACTIVE</span>
                    <span style="color:#64748b;">|</span>
                    <span id="nirantar-step" style="color:#f8fafc;">Filling Candidate Details...</span>
                `;
                document.body.appendChild(banner);
            })();
        """)
        await asyncio.sleep(2)

        # Step 3: Visually Fill First Name
        print("Filling First Name: Sachindra...")
        await page.evaluate("document.getElementById('nirantar-step').innerText = 'Step 1/5: Typing First Name...';")
        await page.locator("#first_name").scroll_into_view_if_needed()
        await page.click("#first_name")
        for char in profile.first_name:
            await page.keyboard.type(char)
            await asyncio.sleep(0.08)

        # Step 4: Visually Fill Last Name
        print("Filling Last Name: Pandey...")
        await page.evaluate("document.getElementById('nirantar-step').innerText = 'Step 2/5: Typing Last Name...';")
        await page.click("#last_name")
        for char in profile.last_name:
            await page.keyboard.type(char)
            await asyncio.sleep(0.08)

        # Step 5: Visually Fill Email
        print("Filling Email...")
        await page.evaluate("document.getElementById('nirantar-step').innerText = 'Step 3/5: Typing Email Address...';")
        await page.click("#email")
        for char in profile.email:
            await page.keyboard.type(char)
            await asyncio.sleep(0.05)

        # Step 6: Visually Fill Phone
        print("Filling Phone...")
        await page.evaluate("document.getElementById('nirantar-step').innerText = 'Step 4/5: Typing Phone Number...';")
        await page.click("#phone")
        for char in profile.phone:
            await page.keyboard.type(char)
            await asyncio.sleep(0.06)

        # Step 7: Attach Resume
        print(f"Attaching Resume from Vault: {resume_path}...")
        await page.evaluate("document.getElementById('nirantar-step').innerText = 'Step 5/5: Attaching Java Resume PDF...';")
        file_input = page.locator("input[type='file']#resume").first
        if await file_input.count() > 0 and resume_path and resume_path.exists():
            await file_input.set_input_files(str(resume_path))
            await asyncio.sleep(2)

        await page.evaluate("document.getElementById('nirantar-step').innerText = '✔ WORKFLOW COMPLETED! Form Ready on Screen.';")
        print("LIVE WORKFLOW COMPLETED ON USER SCREEN!")
        await asyncio.sleep(4)
        
        # Disconnect CDP so Chrome stays OPEN in front of user
        await browser.close()

if __name__ == "__main__":
    asyncio.run(execute_live_workflow())
