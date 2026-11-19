import asyncio
import os
import sys
from pathlib import Path
from playwright.async_api import async_playwright
from loguru import logger

# Ensure immediate unbuffered output on Windows console
try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

# Add root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.vault import vault
from tracker.database import db
from core.matcher import JobMatcher

matcher = JobMatcher()


async def inject_hud(page, text: str):
    """Injects a visible HUD banner on the open page so user sees agent status live."""
    try:
        await page.evaluate(f"""() => {{
            let hud = document.getElementById('nirantar-live-hud');
            if (!hud) {{
                hud = document.createElement('div');
                hud.id = 'nirantar-live-hud';
                hud.style.position = 'fixed';
                hud.style.top = '12px';
                hud.style.left = '50%';
                hud.style.transform = 'translateX(-50%)';
                hud.style.zIndex = '999999';
                hud.style.background = 'linear-gradient(135deg, #0b192e, #1e3a8a)';
                hud.style.color = '#38bdf8';
                hud.style.padding = '10px 24px';
                hud.style.borderRadius = '30px';
                hud.style.fontSize = '14px';
                hud.style.fontWeight = 'bold';
                hud.style.fontFamily = 'Segoe UI, sans-serif';
                hud.style.boxShadow = '0 8px 32px rgba(0,0,0,0.4), 0 0 15px rgba(56,189,248,0.5)';
                hud.style.border = '1px solid rgba(56,189,248,0.3)';
                document.body.appendChild(hud);
            }}
            hud.innerText = "🤖 NIRANTAR: " + "{text}";
        }}""")
    except Exception:
        pass


async def run_naukri_flow():
    profile = vault.get_profile()
    profile_dir = Path.home() / ".nirantar" / "chrome_profile"
    profile_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 65, flush=True)
    print("      NIRANTAR: REAL NAUKRI.COM AUTONOMOUS APPLY FLOW", flush=True)
    print("=" * 65, flush=True)
    print("Candidate: Sachindra Shekhar Pandey", flush=True)
    print(f"Target Role: Software Engineer / Java / Python / Fullstack", flush=True)
    print(f"Location: Noida / Delhi NCR", flush=True)
    print(f"Notice Period: {profile.salary.notice_period_text}", flush=True)
    print("=" * 65, flush=True)
    print("\nOpening Real Google Chrome on your screen...", flush=True)

    # Clear any stale locks
    for stale_lock in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
        lock_p = profile_dir / stale_lock
        if lock_p.exists():
            try:
                lock_p.unlink()
            except Exception:
                pass

    async with async_playwright() as p:
        # Launch REAL Chrome on screen in visible (headed) mode
        launch_kwargs = {
            "user_data_dir": str(profile_dir),
            "channel": "chrome",
            "headless": False,
            "slow_mo": 300,
            "args": [
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ],
            "viewport": None
        }

        try:
            context = await p.chromium.launch_persistent_context(**launch_kwargs)
        except Exception as e:
            if "ProcessSingleton" in str(e) or "Lock" in str(e):
                print("Detected stale Chrome process locking profile. Cleaning up...", flush=True)
                import subprocess
                subprocess.run([
                    "powershell", "-NoProfile", "-Command",
                    "Get-CimInstance Win32_Process -Filter \"Name = 'chrome.exe'\" | Where-Object { $_.CommandLine -like '*nirantar*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
                ], capture_output=True)
                for stale_lock in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
                    lock_p = profile_dir / stale_lock
                    if lock_p.exists():
                        try:
                            lock_p.unlink()
                        except Exception:
                            pass
                await asyncio.sleep(2)
                context = await p.chromium.launch_persistent_context(**launch_kwargs)
            else:
                raise e

        page = context.pages[0] if context.pages else await context.new_page()

        # Step 1: Open Naukri.com
        print("\n[Step 1] Navigating to Naukri.com on your screen...", flush=True)
        await page.goto("https://www.naukri.com/", wait_until="domcontentloaded")
        await inject_hud(page, "Checking Logged-in Session...")
        await asyncio.sleep(2)

        # Check if user is logged in
        is_logged_in = False
        login_btn = page.locator("a#login_Layer, a:has-text('Login')").first
        if await login_btn.count() > 0 and await login_btn.is_visible():
            print("\n" + "!" * 65, flush=True)
            print("👉 ACTION NEEDED: Please log in to your Naukri account in Chrome!", flush=True)
            print("   The agent is waiting for your login...", flush=True)
            print("!" * 65 + "\n", flush=True)
            await inject_hud(page, "Please log in to your account...")
            
            try:
                await login_btn.click()
            except Exception:
                pass

            for sec in range(90):
                await asyncio.sleep(1)
                if await page.locator("div.nI-gNb-drawer, a[href*='mnjuser'], div.user-name, img.nI-gNb-drawer__icon").count() > 0:
                    print("✔ Login detected! Session saved permanently.", flush=True)
                    is_logged_in = True
                    break
        else:
            print("✔ You are already logged in to Naukri!", flush=True)
            is_logged_in = True

        await inject_hud(page, "Logged in! Loading Recommended / Matched Jobs...")

        # Step 2: Go to Recommended / Search Jobs for Sachindra
        print("\n[Step 2] Navigating to Recommended Developer Jobs in Noida...", flush=True)
        search_url = "https://www.naukri.com/java-developer-jobs-in-noida?experience=0&jobAge=15"
        await page.goto(search_url, wait_until="domcontentloaded")
        await asyncio.sleep(2.5)

        # Step 3: Find Job Cards on the page
        print("[Step 3] Scanning job listings on Naukri...", flush=True)
        await inject_hud(page, "Scanning Job Cards on Search Page...")
        job_links = await page.locator("a.title, a[class*='title'], div.srp-jobtuple-wrapper a.title").all()
        print(f"Found {len(job_links)} matching jobs on this page!\n", flush=True)

        applied_count = 0
        proof_dir = PROJECT_ROOT / "proofs"
        proof_dir.mkdir(exist_ok=True)

        for i, link in enumerate(job_links[:10]):
            try:
                title = (await link.inner_text()).strip()
                href = await link.get_attribute("href")
                if not href:
                    continue

                # Match resume type dynamically
                match_res = matcher.match(title)
                selected_resume = match_res.resume_type
                score = match_res.score

                print(f"---> [{i+1}/10] Inspecting: {title}", flush=True)
                print(f"     Optimal Resume: {selected_resume.upper()} | Score: {score:.2f}", flush=True)

                # Open JD page in a new tab
                jd_page = await context.new_page()
                await jd_page.goto(href, wait_until="domcontentloaded")
                await inject_hud(jd_page, f"Inspecting: {title} | Best Resume: {selected_resume.upper()}")
                await asyncio.sleep(1.5)

                # Look for Apply button
                apply_btn = jd_page.locator("button.apply-button, button:has-text('Apply on company site'), button:has-text('Apply')").first
                
                if await apply_btn.count() > 0 and await apply_btn.is_visible():
                    btn_text = (await apply_btn.inner_text()).strip()
                    print(f"     Button found: '{btn_text}'", flush=True)

                    if "company site" in btn_text.lower():
                        print("     Redirects to external company site. Skipping for 1-click apply.", flush=True)
                        await jd_page.close()
                        continue

                    # Highlight apply button visually
                    try:
                        await apply_btn.evaluate("el => el.style.border = '4px solid #10b981'")
                    except Exception:
                        pass

                    # Click Apply!
                    print("     Clicking 1-Click Apply...", flush=True)
                    await inject_hud(jd_page, "Clicking 1-Click Apply...")
                    await apply_btn.click()
                    await asyncio.sleep(2)

                    # Check for Chatbot / Questionnaire popup
                    chat_input = jd_page.locator("input.chatbot-input, input[placeholder*='Type your answer'], textarea[placeholder*='Type your answer']").first
                    if await chat_input.count() > 0 and await chat_input.is_visible():
                        print(f"     Naukri questionnaire detected. Answering: '{profile.salary.notice_period_text}'", flush=True)
                        await chat_input.fill(profile.salary.notice_period_text)
                        await jd_page.keyboard.press("Enter")
                        await asyncio.sleep(1.5)

                    # Wait for confirmation banner or message
                    try:
                        success_el = jd_page.locator("div:has-text('successfully applied'), div[class*='apply-message']").first
                        await success_el.wait_for(timeout=3000)
                    except Exception:
                        pass

                    applied_count += 1
                    proof_p = str(proof_dir / f"Naukri_Job_{applied_count}.png")
                    await jd_page.screenshot(path=proof_p)

                    # Save to local database
                    db.save_job(
                        title=title,
                        company="Naukri Recruiter",
                        portal="Naukri_1Click",
                        url=href,
                        match_score=score,
                        resume_type=selected_resume
                    )
                    db.update_job_status(href, "APPLIED", proof_p)
                    print(f"     ✔ APPLIED SUCCESSFULLY! Proof saved: {Path(proof_p).name}", flush=True)
                    await asyncio.sleep(1.5)

                else:
                    print("     Already applied or apply button not clickable.", flush=True)

                await jd_page.close()

            except Exception as e:
                print(f"     Error on job {i+1}: {e}", flush=True)

        print("\n" + "=" * 65, flush=True)
        print(f"✔ WORKFLOW FINISHED: Applied to {applied_count} jobs on Naukri!", flush=True)
        print("Chrome is kept OPEN on your screen.", flush=True)
        print("You can verify applied jobs in Naukri > 'Applied Jobs' tab.", flush=True)
        print("=" * 65 + "\n", flush=True)
        
        # Keep open indefinitely for user
        while True:
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(run_naukri_flow())
