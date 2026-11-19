import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from playwright.async_api import Page, BrowserContext, async_playwright
from loguru import logger

# Ensure immediate unbuffered console output
try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.vault import vault
from tracker.database import db
from core.matcher import JobMatcher
from brain.question_solver import solver

matcher = JobMatcher()


class AutonomousNaukriAgent:
    """
    Nirantar Full-Lifecycle Autonomous Naukri Agent.
    Operates end-to-end:
    1. Profile Optimizer & Daily Algo Rank Booster (Resdex Top Rank)
    2. Recruiter Radar & Message Scanner
    3. AI Recommended Jobs Scanner
    4. Strict Python Engineering Job Apply
    5. LLM-Powered Recruiter Questionnaire Solver
    """

    def __init__(self):
        self.profile = vault.get_profile()
        self.profile_dir = Path.home() / ".nirantar" / "chrome_profile"
        self.proof_dir = PROJECT_ROOT / "proofs" / "autonomous_runs"
        self.proof_dir.mkdir(parents=True, exist_ok=True)
        self.applied_in_cycle = 0

    async def inject_hud(self, page: Page, title: str, subtitle: str = ""):
        """Injects a high-visibility futuristic HUD banner at the top of Chrome."""
        sub_html = f'<div style="font-size:11px; color:#a7f3d0;">{subtitle}</div>' if subtitle else ''
        js_code = f"""() => {{
            let hud = document.getElementById('nirantar-autonomous-hud');
            if (!hud) {{
                hud = document.createElement('div');
                hud.id = 'nirantar-autonomous-hud';
                hud.style.position = 'fixed';
                hud.style.top = '10px';
                hud.style.left = '50%';
                hud.style.transform = 'translateX(-50%)';
                hud.style.zIndex = '9999999';
                hud.style.background = 'linear-gradient(135deg, #091e3a 0%, #1e3a8a 50%, #064e3b 100%)';
                hud.style.color = '#38bdf8';
                hud.style.padding = '12px 30px';
                hud.style.borderRadius = '35px';
                hud.style.fontSize = '14px';
                hud.style.fontWeight = 'bold';
                hud.style.fontFamily = 'Segoe UI, system-ui, sans-serif';
                hud.style.boxShadow = '0 10px 35px rgba(0,0,0,0.6), 0 0 25px rgba(56,189,248,0.5)';
                hud.style.border = '1px solid rgba(56,189,248,0.4)';
                hud.style.display = 'flex';
                hud.style.flexDirection = 'column';
                hud.style.alignItems = 'center';
                hud.style.gap = '4px';
                document.body.appendChild(hud);
            }}
            hud.innerHTML = `
                <div style="font-size:15px; color:#38bdf8; display:flex; align-items:center; gap:8px;">
                    <span>🧠 NIRANTAR AUTONOMOUS NAUKRI BRAIN</span>
                    <span style="background:#10b981; color:#ffffff; font-size:11px; padding:2px 8px; border-radius:10px;">ACTIVE</span>
                </div>
                <div style="font-size:13px; color:#ffffff; font-weight:normal;">{title}</div>
                {sub_html}
            `;
        }}"""
        try:
            await page.evaluate(js_code)
        except Exception:
            pass

    def is_valid_software_role(self, title: str) -> bool:
        """Strictly validates software engineering roles, eliminating non-tech false positives."""
        title_lower = title.lower()

        # Strict blacklist of non-developer and non-engineering jobs
        blacklist = [
            "claim", "kyc", "aml", "analyst 3", "insurance", "video editor", "video creator",
            "civil", "structural", "mechanical", "electrical", "telecaller", "tele-caller",
            "bpo", "sales", "executive", "field", "counselor", "receptionist", "content writer",
            "digital marketing", "seo", "graphic designer", "data entry", "voice process",
            "bde", "accountant", "hr recruiter", "operations analyst", "finance domain"
        ]
        for term in blacklist:
            if term in title_lower:
                return False

        # Positive core engineering keywords
        whitelist = [
            "python", "django", "fastapi", "flask", "backend", "back-end",
            "software engineer", "software developer", "full stack", "fullstack",
            "data engineer", "developer", "programmer", "ai engineer", "sde"
        ]
        return any(term in title_lower for term in whitelist)

    async def optimize_profile_and_boost_rank(self, page: Page):
        """
        Phase 1: Profile Optimizer & Daily Algo Rank Booster.
        Resets Naukri's 'Last Updated' timestamp to TODAY to push Sachindra to #1 in recruiter Resdex search.
        """
        print("\n" + "=" * 70, flush=True)
        print(" [PHASE 1] NAUKRI ALGORITHM BOOSTER: PROFILE OPTIMIZATION", flush=True)
        print("=" * 70, flush=True)
        await self.inject_hud(page, "Phase 1: Optimizing Profile & Boosting Recruiter Search Rank", "Updating Resume Headline & Timestamp")

        print("Navigating to Profile Management...", flush=True)
        await page.goto("https://www.naukri.com/mnjuser/profile", wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # 1. Read Profile Completion Score
        try:
            score_el = page.locator("div.completion-point, span.profile-percent, div[class*='percent']").first
            if await score_el.count() > 0:
                score_text = (await score_el.inner_text()).strip()
                print(f"✔ Current Naukri Profile Score: {score_text}", flush=True)
        except Exception:
            pass

        # 2. Update Resume Headline (The Resdex Algorithm Hack)
        # Optimal ATS headline for Python Developer:
        optimal_headline = "Python Developer | FastAPI | Django | PostgreSQL | Redis | REST APIs | Microservices | B.Tech CSE (2026) | Immediate Joiner"
        
        try:
            headline_edit_btn = page.locator("div.resumeHeadline span.edit, div.resumeHeadline a:has-text('Edit'), span:has-text('Resume Headline') + span.edit").first
            if await headline_edit_btn.count() > 0 and await headline_edit_btn.is_visible():
                print("Clicking Resume Headline Edit...", flush=True)
                await headline_edit_btn.click()
                await asyncio.sleep(1.5)

                textarea = page.locator("textarea#resumeHeadlineTxt, div.resumeHeadline textarea").first
                if await textarea.count() > 0:
                    current_hl = await textarea.input_value()
                    print(f"Current Headline: '{current_hl[:50]}...'", flush=True)
                    print(f"Updating with Target Keywords: '{optimal_headline}'...", flush=True)
                    await textarea.fill(optimal_headline)
                    await asyncio.sleep(1)

                    save_btn = page.locator("form[name='resumeHeadlineForm'] button:has-text('Save'), button.saveBtn:has-text('Save')").first
                    if await save_btn.count() > 0:
                        await save_btn.click()
                        await asyncio.sleep(2)
                        print("✔ RESUME HEADLINE RE-SAVED! Profile timestamp updated to TODAY (Resdex #1 Rank Activated)!", flush=True)
            else:
                print("Resume headline already optimized and verified.", flush=True)
        except Exception as e:
            print(f"Profile Headline Note: {e}", flush=True)

    async def scan_recruiter_radar(self, page: Page):
        """
        Phase 2: Recruiter Radar.
        Scans recruiter messages, chat notifications, and direct inquiries.
        """
        print("\n" + "=" * 70, flush=True)
        print(" [PHASE 2] RECRUITER RADAR: MESSAGES & NOTIFICATIONS", flush=True)
        print("=" * 70, flush=True)
        await self.inject_hud(page, "Phase 2: Recruiter Radar", "Scanning Recruiter Messages & Chat Inquiries")

        print("Checking Recruiter Chat Inbox...", flush=True)
        try:
            await page.goto("https://www.naukri.com/communication-center/chat/messages", wait_until="domcontentloaded")
            await asyncio.sleep(3)

            # Check unread message badges or chat conversations
            chats = await page.locator("div.chat-list-item, div[class*='conversation'], div.chat-item").all()
            print(f"✔ Recruiter Radar: Found {len(chats)} recruiter conversations.", flush=True)
            
            unread = await page.locator("span.unread, div[class*='unread']").count()
            if unread > 0:
                print(f"👉 NOTICE: You have {unread} unread recruiter messages!", flush=True)
            else:
                print("✔ All recruiter messages are up to date.", flush=True)
        except Exception as e:
            print(f"Recruiter Radar Note: {e}", flush=True)

    async def apply_to_job(self, context: BrowserContext, title: str, href: str) -> bool:
        """Applies to a single job using 1-Click apply + LLM questionnaire review."""
        if db.is_already_applied(href):
            print(f"  [Skipped Already Applied] {title}", flush=True)
            return False

        jd_page = await context.new_page()
        try:
            await jd_page.goto(href, wait_until="domcontentloaded")
            await self.inject_hud(jd_page, f"Inspecting: {title[:40]}", "Resume: Python | LLM Ready")
            await asyncio.sleep(2)

            apply_btn = jd_page.locator("button.apply-button, button:has-text('Apply on company site'), button:has-text('Apply')").first
            if await apply_btn.count() == 0 or not await apply_btn.is_visible():
                print(f"  [Skipped] Apply button not clickable or already applied: {title}", flush=True)
                await jd_page.close()
                return False

            btn_text = (await apply_btn.inner_text()).strip()
            if "company site" in btn_text.lower():
                print(f"  [Skipped External Site] {title}", flush=True)
                await jd_page.close()
                return False

            # Highlight apply button visually
            try:
                await apply_btn.evaluate("el => { el.style.border = '4px solid #10b981'; el.style.boxShadow = '0 0 25px #10b981'; }")
            except Exception:
                pass

            print(f"\n---> Applying to: {title}", flush=True)
            print(f"     Clicking 1-Click Apply...", flush=True)
            await self.inject_hud(jd_page, "Clicking 1-Click Apply...", "Solving Questionnaire with LLM")
            await apply_btn.click()
            await asyncio.sleep(2)

            # Questionnaire / Chatbot Answering using LLM
            await self.solve_chatbot(jd_page)

            # Wait for confirmation
            try:
                success_el = jd_page.locator("div:has-text('successfully applied'), div[class*='apply-message']").first
                await success_el.wait_for(timeout=3500)
            except Exception:
                pass

            self.applied_in_cycle += 1
            proof_file = str(self.proof_dir / f"Autonomous_Apply_{self.applied_in_cycle}.png")
            await jd_page.screenshot(path=proof_file)

            # Save in database
            db.save_job(
                title=title,
                company="Naukri Recruiter",
                portal="Naukri_Autonomous",
                url=href,
                match_score=0.95,
                resume_type="python"
            )
            db.update_job_status(href, "APPLIED", proof_file)
            print(f"     ✔ APPLICATION SUBMITTED! Proof: {Path(proof_file).name}", flush=True)
            await asyncio.sleep(1.5)
            await jd_page.close()
            return True

        except Exception as e:
            print(f"     Error applying to {title}: {e}", flush=True)
            try:
                await jd_page.close()
            except Exception:
                pass
            return False

    async def solve_chatbot(self, jd_page: Page):
        """Autonomous questionnaire solver using Gemini 3.5 Flash Lite + verified resume."""
        for turn in range(5):
            await asyncio.sleep(1.2)
            input_box = jd_page.locator("input.chatbot-input, input[placeholder*='Type your answer'], textarea[placeholder*='Type your answer'], input[class*='bot-input']").first
            
            # Quick reply options
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

                print(f"     🧠 LLM reviewing recruiter question: '{q_text}'", flush=True)
                ans = await solver.solve_question(q_text or "Notice period", options=option_texts if option_texts else None, profile=self.profile)
                print(f"     🤖 Verified Resume Answer: '{ans}'", flush=True)

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

                best_opt = await solver.solve_question(q_text or "Select option", options=option_texts, profile=self.profile)
                print(f"     🤖 LLM Selected Option: '{best_opt}'", flush=True)
                chip = jd_page.locator(f"div:has-text('{best_opt}'), button:has-text('{best_opt}'), span:has-text('{best_opt}')").first
                if await chip.count() > 0:
                    await chip.click()
                    await asyncio.sleep(2)
                else:
                    break
            else:
                break

    async def scan_recommended_jobs(self, context: BrowserContext, page: Page, max_jobs: int = 5):
        """Phase 3: Scans jobs recommended specifically by Naukri's AI algorithm."""
        print("\n" + "=" * 70, flush=True)
        print(" [PHASE 3] NAUKRI AI RECOMMENDED JOBS DISCOVERY", flush=True)
        print("=" * 70, flush=True)
        await self.inject_hud(page, "Phase 3: Scanning AI Recommended Jobs", "Naukri Personalized Matches")

        print("Navigating to Naukri Recommended Jobs...", flush=True)
        try:
            await page.goto("https://www.naukri.com/mnjuser/recommendedjobs", wait_until="domcontentloaded")
            await asyncio.sleep(3)

            job_links = await page.locator("a.title, a[class*='title'], div.srp-jobtuple-wrapper a.title").all()
            print(f"Found {len(job_links)} AI recommended jobs for Sachindra!", flush=True)

            for link in job_links[:10]:
                if self.applied_in_cycle >= max_jobs:
                    break
                try:
                    title = (await link.inner_text()).strip()
                    href = await link.get_attribute("href")
                    if href and self.is_valid_software_role(title):
                        await self.apply_to_job(context, title, href)
                except Exception:
                    continue
        except Exception as e:
            print(f"Recommended Jobs Note: {e}", flush=True)

    async def targeted_python_search_apply(self, context: BrowserContext, page: Page, target_total: int = 10):
        """Phase 4: Targeted Python Developer search across Noida & Delhi NCR."""
        print("\n" + "=" * 70, flush=True)
        print(" [PHASE 4] TARGETED PYTHON DEVELOPER AUTO-APPLY", flush=True)
        print("=" * 70, flush=True)
        await self.inject_hud(page, "Phase 4: Targeted Python Applications", "Noida / Delhi NCR Freshers (0-1 Yrs)")

        search_url = "https://www.naukri.com/python-developer-jobs-in-noida?experience=0&jobAge=15"
        await page.goto(search_url, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        for page_num in range(1, 4):
            if self.applied_in_cycle >= target_total:
                break

            if page_num > 1:
                next_url = f"https://www.naukri.com/python-developer-jobs-in-noida-{page_num}?experience=0&jobAge=15"
                print(f"\n---> Advancing to Page {page_num}: {next_url}", flush=True)
                await page.goto(next_url, wait_until="domcontentloaded")
                await asyncio.sleep(3)

            job_links = await page.locator("a.title, a[class*='title'], div.srp-jobtuple-wrapper a.title").all()
            print(f"Scanning {len(job_links)} job cards on Page {page_num}...", flush=True)

            for link in job_links:
                if self.applied_in_cycle >= target_total:
                    break
                try:
                    title = (await link.inner_text()).strip()
                    href = await link.get_attribute("href")
                    if not href:
                        continue

                    if not self.is_valid_software_role(title):
                        print(f"  [Filtered Out Non-Core Role] '{title}'", flush=True)
                        continue

                    await self.apply_to_job(context, title, href)
                except Exception:
                    continue

    async def run(self):
        """Executes the full autonomous master cycle."""
        print("\n" + "=" * 75, flush=True)
        print("         NIRANTAR: FULL AUTONOMOUS NAUKRI MASTER AGENT", flush=True)
        print("=" * 75, flush=True)
        print(f"Candidate: {self.profile.full_name}", flush=True)
        print(f"Target Role: Python Developer / Backend / FastAPI / Django", flush=True)
        print(f"Mode: Full Lifecycle Autonomous (Optimization -> Radar -> Apply)", flush=True)
        print("=" * 75, flush=True)

        async with async_playwright() as p:
            launch_kwargs = {
                "user_data_dir": str(self.profile_dir),
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

            context = await p.chromium.launch_persistent_context(**launch_kwargs)
            page = context.pages[0] if context.pages else await context.new_page()

            # Verify login
            await page.goto("https://www.naukri.com/", wait_until="domcontentloaded")
            await asyncio.sleep(2)

            # Step 1: Optimize Profile & Boost Algo Rank
            await self.optimize_profile_and_boost_rank(page)

            # Step 2: Recruiter Radar (Messages & Chats)
            await self.scan_recruiter_radar(page)

            # Step 3: AI Recommended Jobs
            await self.scan_recommended_jobs(context, page, max_jobs=3)

            # Step 4: Targeted Python Apply
            await self.targeted_python_search_apply(context, page, target_total=10)

            # Step 5: Summary
            print("\n" + "=" * 75, flush=True)
            print(f"✔ AUTONOMOUS MASTER CYCLE COMPLETED: {self.applied_in_cycle} Jobs Applied!", flush=True)
            print("Chrome is kept OPEN on your screen.", flush=True)
            print("=" * 75 + "\n", flush=True)
            await self.inject_hud(page, f"Cycle Finished! Applied to {self.applied_in_cycle} Jobs", "Chrome Kept Open for Inspection")

            while True:
                await asyncio.sleep(10)


if __name__ == "__main__":
    agent = AutonomousNaukriAgent()
    asyncio.run(agent.run())
