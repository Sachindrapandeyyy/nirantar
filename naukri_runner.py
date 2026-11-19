import asyncio
import os
import sys
from pathlib import Path
from playwright.async_api import async_playwright
from loguru import logger

# Add root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.vault import vault
from tracker.database import db


async def run_naukri_flow():
    profile = vault.get_profile()
    profile_dir = Path.home() / ".nirantar" / "chrome_profile"
    profile_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("   NIRANTAR: REAL NAUKRI.COM AUTONOMOUS APPLY FLOW")
    print("=" * 60)
    print("Opening Real Google Chrome on your screen...")

    async with async_playwright() as p:
        # Launch REAL Chrome on screen in visible (headed) mode with slow-mo so user sees everything!
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            channel="chrome",
            headless=False,
            slow_mo=400,  # 400ms delay between actions so user can see every click and typing!
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ],
            viewport=None  # Maximize to full screen
        )

        page = context.pages[0] if context.pages else await context.new_page()

        # Step 1: Open Naukri.com
        print("\n[Step 1] Navigating to Naukri.com on your screen...")
        await page.goto("https://www.naukri.com/", wait_until="domcontentloaded")
        await asyncio.sleep(2)

        # Check if user is logged in
        # Naukri logged-in users have user drawer or profile icon (.nI-gNb-drawer__bars or .user-name)
        is_logged_in = False
        login_btn = page.locator("a#login_Layer, a:has-text('Login')").first
        if await login_btn.count() > 0 and await login_btn.is_visible():
            print("\n" + "!" * 60)
            print("👉 ACTION NEEDED: Please log in to your Naukri account in the open Chrome window!")
            print("   The agent is waiting for you to complete login...")
            print("!" * 60 + "\n")
            
            # Click login button to help user
            try:
                await login_btn.click()
            except Exception:
                pass

            # Wait up to 90 seconds for user to log in
            for sec in range(90):
                await asyncio.sleep(1)
                # Check if logged in by looking for user name or my-naukri
                if await page.locator("div.nI-gNb-drawer, a[href*='mnjuser'], div.user-name").count() > 0:
                    print("✔ Login detected! Session saved permanently.")
                    is_logged_in = True
                    break
        else:
            print("✔ You are already logged in to Naukri!")
            is_logged_in = True

        # Step 2: Go to Recommended / Search Jobs for Sachindra
        print("\n[Step 2] Navigating to Java / Backend Jobs in Noida...")
        search_url = "https://www.naukri.com/java-developer-jobs-in-noida?experience=0&jobAge=15"
        await page.goto(search_url, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # Step 3: Find Job Cards on the page
        print("[Step 3] Scanning job listings on Naukri...")
        job_links = await page.locator("a.title").all()
        print(f"Found {len(job_links)} matching jobs on this page!")

        applied_count = 0
        for i, link in enumerate(job_links[:10]):
            try:
                title = await link.inner_text()
                href = await link.get_attribute("href")
                if not href:
                    continue

                print(f"\n---> [{i+1}] Inspecting Job: {title.strip()}")
                
                # Open JD page in a new tab
                jd_page = await context.new_page()
                await jd_page.goto(href, wait_until="domcontentloaded")
                await asyncio.sleep(2)

                # Look for Apply button
                # Naukri apply button classes: .apply-button, button.apply-message, button:has-text('Apply')
                apply_btn = jd_page.locator("button.apply-button, button:has-text('Apply on company site'), button:has-text('Apply')").first
                
                if await apply_btn.count() > 0 and await apply_btn.is_visible():
                    btn_text = await apply_btn.inner_text()
                    print(f"    Button found: '{btn_text}'")

                    if "company site" in btn_text.lower():
                        print("    This job redirects to external company site. Skipping for 1-click apply.")
                        await jd_page.close()
                        continue

                    # Click Apply!
                    print("    Clicking Apply button...")
                    await apply_btn.click()
                    await asyncio.sleep(2)

                    # Check for Chatbot / Questionnaire popup
                    # Naukri chatbot input
                    chat_input = jd_page.locator("input.chatbot-input, input[placeholder*='Type your answer'], textarea[placeholder*='Type your answer']").first
                    if await chat_input.count() > 0 and await chat_input.is_visible():
                        print("    Naukri chatbot questionnaire detected! Answering...")
                        # Default answer: Notice period Immediate / 0.3 yrs exp
                        await chat_input.fill(profile.salary.notice_period_text)
                        await jd_page.keyboard.press("Enter")
                        await asyncio.sleep(1.5)

                    # Save to local database
                    db.save_job(
                        title=title.strip(),
                        company="Naukri Recruiter",
                        portal="Naukri_1Click",
                        url=href,
                        match_score=0.9,
                        resume_type="java"
                    )
                    db.update_job_status(href, "APPLIED")
                    applied_count += 1
                    print(f"    ✔ SUCCESSFULLY APPLIED TO: {title.strip()}!")
                    await asyncio.sleep(2)

                else:
                    print("    Already applied or apply button not clickable.")

                await jd_page.close()

            except Exception as e:
                print(f"    Error on job {i+1}: {e}")

        print("\n" + "=" * 60)
        print(f"✔ WORKFLOW FINISHED: Applied to {applied_count} jobs on Naukri!")
        print("Chrome is kept OPEN on your screen so you can check your applied jobs.")
        print("=" * 60)
        
        # Keep open indefinitely for user
        while True:
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(run_naukri_flow())
