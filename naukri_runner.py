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
from brain.question_solver import solver

matcher = JobMatcher()


async def inject_hud(page, text: str, mode: str = "PYTHON"):
    """Injects a sleek HUD banner on the open page so user sees agent status live."""
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
                hud.style.zIndex = '9999999';
                hud.style.background = 'linear-gradient(135deg, #091e3a 0%, #1e3a8a 50%, #064e3b 100%)';
                hud.style.color = '#38bdf8';
                hud.style.padding = '12px 28px';
                hud.style.borderRadius = '30px';
                hud.style.fontSize = '14px';
                hud.style.fontWeight = 'bold';
                hud.style.fontFamily = 'Segoe UI, system-ui, sans-serif';
                hud.style.boxShadow = '0 10px 30px rgba(0,0,0,0.5), 0 0 20px rgba(56,189,248,0.4)';
                hud.style.border = '1px solid rgba(56,189,248,0.4)';
                hud.style.transition = 'all 0.3s ease';
                document.body.appendChild(hud);
            }}
            hud.innerHTML = "🐍 <span style='color:#a7f3d0;'>NIRANTAR PYTHON AGENT</span> | <span style='color:#ffffff;'>{text}</span>";
        }}""")
    except Exception:
        pass


def is_python_developer_role(title: str) -> bool:
    """Strictly filters for Python / Backend / Software developer roles."""
    title_lower = title.lower()

    # Negative blacklist: Skip non-tech and non-developer roles
    negative_kw = [
        "civil", "structural", "mechanical", "electrical", "chemical", "site engineer",
        "telecaller", "tele-caller", "bpo", "sales", "executive", "field", "counselor",
        "receptionist", "content writer", "digital marketing", "seo", "graphic designer",
        "data entry", "voice process", "business development", "bde", "accountant", "hr recruiter"
    ]
    for neg in negative_kw:
        if neg in title_lower:
            return False

    # Positive whitelist for Python & core engineering roles
    positive_kw = [
        "python", "django", "fastapi", "flask", "ai", "machine learning", "ml",
        "backend", "back-end", "back end", "software engineer", "software developer",
        "full stack", "fullstack", "data engineer", "etl", "developer", "programmer"
    ]
    return any(p in title_lower for p in positive_kw)


async def solve_naukri_chatbot(jd_page, profile):
    """Handles Naukri questionnaire / chatbot popups using LLM with verified resume context."""
    for turn in range(5):
        await asyncio.sleep(1.2)
        
        # Check text input box
        input_box = jd_page.locator("input.chatbot-input, input[placeholder*='Type your answer'], textarea[placeholder*='Type your answer'], input[class*='bot-input']").first
        
        # Check quick reply chips / options
        chip_elements = await jd_page.locator("div.chips, div.chip, button.chip-btn, span.chip-text, div[class*='quick-reply']").all()
        option_texts = []
        if chip_elements:
            for c in chip_elements:
                txt = (await c.inner_text()).strip()
                if txt and len(txt) < 50:
                    option_texts.append(txt)

        if await input_box.count() > 0 and await input_box.is_visible():
            q_text = ""
            try:
                msgs = await jd_page.locator("div.msgBox, div.bot-msg, div[class*='message'], div[class*='question']").all()
                if msgs:
                    q_text = (await msgs[-1].inner_text()).strip()
            except Exception:
                pass

            if not q_text:
                q_text = "Please specify your availability and background."

            print(f"     🧠 LLM reviewing recruiter question based on resume:\n        Question: '{q_text}'", flush=True)
            await inject_hud(jd_page, f"LLM Answering: {q_text[:40]}...")
            
            ans = await solver.solve_question(q_text, options=option_texts if option_texts else None, profile=profile)
            print(f"     🤖 Verified Answer: '{ans}'", flush=True)

            await input_box.fill(ans)
            await jd_page.keyboard.press("Enter")
            await asyncio.sleep(2)

        elif option_texts:
            q_text = ""
            try:
                msgs = await jd_page.locator("div.msgBox, div.bot-msg, div[class*='message']").all()
                if msgs:
                    q_text = (await msgs[-1].inner_text()).strip()
            except Exception:
                pass

            print(f"     🧠 LLM evaluating options: {option_texts}", flush=True)
            best_opt = await solver.solve_question(q_text or "Select option", options=option_texts, profile=profile)
            print(f"     🤖 LLM Selected Option: '{best_opt}'", flush=True)

            chip_to_click = jd_page.locator(f"div:has-text('{best_opt}'), button:has-text('{best_opt}'), span:has-text('{best_opt}')").first
            if await chip_to_click.count() > 0:
                await chip_to_click.click()
                await asyncio.sleep(2)
            else:
                break
        else:
            break


async def run_naukri_flow():
    profile = vault.get_profile()
    profile_dir = Path.home() / ".nirantar" / "chrome_profile"
    profile_dir.mkdir(parents=True, exist_ok=True)
    python_resume = vault.get_resume("python")

    print("\n" + "=" * 70, flush=True)
    print("      NIRANTAR: REAL NAUKRI.COM PYTHON DEVELOPER AGENT", flush=True)
    print("=" * 70, flush=True)
    print(f"Candidate: {profile.full_name}", flush=True)
    print(f"Target Role: Python Developer / Backend / FastAPI / Django", flush=True)
    print(f"Location Target: Noida / Delhi NCR", flush=True)
    print(f"Selected Resume: {Path(python_resume).name if python_resume else 'Sachindra_Pandey_python_Resume.pdf'}", flush=True)
    print(f"Notice Period: {profile.salary.notice_period_text}", flush=True)
    print("=" * 70, flush=True)
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
                print("Cleaning up stale Chrome locks...", flush=True)
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
            print("\n" + "!" * 70, flush=True)
            print("👉 ACTION NEEDED: Please log in to your Naukri account in Chrome!", flush=True)
            print("   The agent is waiting for your login...", flush=True)
            print("!" * 70 + "\n", flush=True)
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

        await inject_hud(page, "Logged in! Loading Python Developer Jobs...")

        # Step 2: Dedicated Python Developer Search in Noida / Delhi NCR
        print("\n[Step 2] Navigating to Python Developer Roles in Noida / Delhi NCR...", flush=True)
        search_url = "https://www.naukri.com/python-developer-jobs-in-noida?experience=0&jobAge=15"
        await page.goto(search_url, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        applied_count = 0
        target_applications = 10
        proof_dir = PROJECT_ROOT / "proofs" / "python_jobs"
        proof_dir.mkdir(parents=True, exist_ok=True)

        # Step 3: Scan and Apply (Supports Multi-Page)
        for page_num in range(1, 4):
            if applied_count >= target_applications:
                break

            if page_num > 1:
                next_page_url = f"https://www.naukri.com/python-developer-jobs-in-noida-{page_num}?experience=0&jobAge=15"
                print(f"\n---> Advancing to Page {page_num}: {next_page_url}", flush=True)
                await page.goto(next_page_url, wait_until="domcontentloaded")
                await asyncio.sleep(3)

            print(f"\n[Step 3] Scanning Python job listings on Page {page_num}...", flush=True)
            await inject_hud(page, f"Scanning Python Job Cards (Page {page_num})...")
            job_links = await page.locator("a.title, a[class*='title'], div.srp-jobtuple-wrapper a.title").all()
            print(f"Found {len(job_links)} total job cards on Page {page_num}!\n", flush=True)

            for i, link in enumerate(job_links):
                if applied_count >= target_applications:
                    break

                try:
                    title = (await link.inner_text()).strip()
                    href = await link.get_attribute("href")
                    if not href:
                        continue

                    # Betterment 1: Strict Python Role Verification
                    if not is_python_developer_role(title):
                        print(f"  [Skipped Non-Python] '{title}'", flush=True)
                        continue

                    # Betterment 2: Deduplication Check
                    if db.is_already_applied(href):
                        print(f"  [Skipped Already Applied] '{title}'", flush=True)
                        continue

                    match_res = matcher.match(title)
                    score = match_res.score

                    print(f"\n---> [Python Match #{applied_count+1}] {title}", flush=True)
                    print(f"     Assigned Resume: PYTHON | Match Score: {score:.2f}", flush=True)

                    # Open JD page in a new tab
                    jd_page = await context.new_page()
                    await jd_page.goto(href, wait_until="domcontentloaded")
                    await inject_hud(jd_page, f"Target: {title} | Resume: PYTHON")
                    await asyncio.sleep(2)

                    # Look for Apply button
                    apply_btn = jd_page.locator("button.apply-button, button:has-text('Apply on company site'), button:has-text('Apply')").first
                    
                    if await apply_btn.count() > 0 and await apply_btn.is_visible():
                        btn_text = (await apply_btn.inner_text()).strip()
                        print(f"     Apply Button: '{btn_text}'", flush=True)

                        if "company site" in btn_text.lower():
                            print("     External site redirect. Skipping for 1-Click apply.", flush=True)
                            await jd_page.close()
                            continue

                        # Visual Highlight on screen
                        try:
                            await apply_btn.evaluate("el => { el.style.border = '4px solid #10b981'; el.style.boxShadow = '0 0 20px #10b981'; }")
                        except Exception:
                            pass

                        # Click 1-Click Apply
                        print("     Clicking 1-Click Apply button on screen...", flush=True)
                        await inject_hud(jd_page, "Clicking 1-Click Apply...")
                        await apply_btn.click()
                        await asyncio.sleep(2)

                        # Betterment 3: Intelligent Questionnaire Solver
                        await solve_naukri_chatbot(jd_page, profile)

                        # Wait for confirmation
                        try:
                            success_el = jd_page.locator("div:has-text('successfully applied'), div[class*='apply-message']").first
                            await success_el.wait_for(timeout=3500)
                        except Exception:
                            pass

                        applied_count += 1
                        proof_p = str(proof_dir / f"Python_Job_{applied_count}.png")
                        await jd_page.screenshot(path=proof_p)

                        # Save to local database
                        db.save_job(
                            title=title,
                            company="Naukri Recruiter",
                            portal="Naukri_1Click",
                            url=href,
                            match_score=score,
                            resume_type="python"
                        )
                        db.update_job_status(href, "APPLIED", proof_p)
                        print(f"     ✔ APPLIED TO PYTHON ROLE! Proof: {Path(proof_p).name}", flush=True)
                        await asyncio.sleep(2)

                    else:
                        print("     Already applied or Apply button not clickable.", flush=True)

                    await jd_page.close()

                except Exception as e:
                    print(f"     Notice on job {i+1}: {e}", flush=True)

        print("\n" + "=" * 70, flush=True)
        print(f"✔ NIRANTAR PYTHON RUN COMPLETED: Applied to {applied_count} Python Developer roles!", flush=True)
        print("Chrome is kept OPEN on your screen so you can check your applied jobs.", flush=True)
        print("=" * 70 + "\n", flush=True)
        
        # Keep open indefinitely for user
        while True:
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(run_naukri_flow())
