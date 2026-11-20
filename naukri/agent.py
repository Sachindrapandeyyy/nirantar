import asyncio
import os
import sys
import time
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
from naukri.filters import is_valid_software_role
from career_site.autofiller import CareerSiteAutofiller
from config.settings import unlock_chrome_profile

matcher = JobMatcher()

SEARCH_VECTORS = [
    # --- Python Engineering Stack ---
    {
        "name": "Python Developer (Noida)",
        "base_url": "https://www.naukri.com/python-developer-jobs-in-noida?experience=0&jobAge=15"
    },
    {
        "name": "Python Developer (Delhi NCR)",
        "base_url": "https://www.naukri.com/python-developer-jobs-in-delhi-ncr?experience=0&jobAge=15"
    },
    {
        "name": "Python Developer (Gurgaon)",
        "base_url": "https://www.naukri.com/python-developer-jobs-in-gurgaon?experience=0&jobAge=15"
    },
    {
        "name": "FastAPI / Django Roles",
        "base_url": "https://www.naukri.com/fastapi-jobs?experience=0&jobAge=15"
    },
    {
        "name": "Python Fresher Jobs (All India)",
        "base_url": "https://www.naukri.com/python-fresher-jobs?experience=0&jobAge=15"
    },

    # --- Java Engineering Stack ---
    {
        "name": "Java Developer (Noida)",
        "base_url": "https://www.naukri.com/java-developer-jobs-in-noida?experience=0&jobAge=15"
    },
    {
        "name": "Java Developer (Delhi NCR)",
        "base_url": "https://www.naukri.com/java-developer-jobs-in-delhi-ncr?experience=0&jobAge=15"
    },
    {
        "name": "Java Developer (Gurgaon)",
        "base_url": "https://www.naukri.com/java-developer-jobs-in-gurgaon?experience=0&jobAge=15"
    },
    {
        "name": "Spring Boot Developer Roles",
        "base_url": "https://www.naukri.com/spring-boot-jobs?experience=0&jobAge=15"
    },
    {
        "name": "Java Fresher Jobs (All India)",
        "base_url": "https://www.naukri.com/java-fresher-jobs?experience=0&jobAge=15"
    },

    # --- General Backend & SDE Freshers ---
    {
        "name": "Backend Developer (Noida)",
        "base_url": "https://www.naukri.com/backend-developer-jobs-in-noida?experience=0&jobAge=15"
    },
    {
        "name": "Software Engineer Freshers (Noida)",
        "base_url": "https://www.naukri.com/software-engineer-freshers-jobs-in-noida?experience=0&jobAge=15"
    }
]


class AutonomousNaukriAgent:
    """
    Dedicated Autonomous Naukri Agent.
    Operates non-stop:
    1. 2-Hour Resdex Dot-Toggle Rank Booster (Resets Profile Rank to #1)
    2. Recruiter Radar & Message Inspector
    3. AI-Recommended Jobs Discovery
    4. 7-Vector Multi-Search Non-Stop Engine
    5. LLM-Powered Recruiter Questionnaire Solver
    """

    def __init__(self):
        self.profile = vault.get_profile()
        self.profile_dir = Path.home() / ".nirantar" / "chrome_profile"
        self.proof_dir = PROJECT_ROOT / "proofs" / "autonomous_runs"
        self.proof_dir.mkdir(parents=True, exist_ok=True)
        self.total_applied = 0
        self.cycle_count = 1
        self.last_profile_refresh_time = 0.0
        self.PROFILE_REFRESH_INTERVAL = 2 * 3600  # 2 Hours in seconds

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
                    <span>🧠 NIRANTAR NON-STOP NAUKRI ENGINE</span>
                    <span style="background:#10b981; color:#ffffff; font-size:11px; padding:2px 8px; border-radius:10px;">CYCLE #{self.cycle_count}</span>
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
        return is_valid_software_role(title)

    async def optimize_profile_and_boost_rank(self, page: Page, force: bool = False):
        """
        Phase 1: Resdex Algorithm Hack (2-Hour Profile Dot Refresh).
        Every 2 hours, visits profile, toggles a trailing dot '.' in Resume Headline & Profile Summary,
        and saves. This forces Naukri's backend to refresh 'Last Active / Updated' timestamp to 'JUST NOW',
        boosting candidate to #1 rank in recruiter search filters!
        """
        now = time.time()
        elapsed = now - self.last_profile_refresh_time

        if not force and self.last_profile_refresh_time > 0 and elapsed < self.PROFILE_REFRESH_INTERVAL:
            remaining_mins = int((self.PROFILE_REFRESH_INTERVAL - elapsed) // 60)
            print(f"ℹ Resdex Rank Booster: Profile recently refreshed. Next 2-hour dot toggle in {remaining_mins} minutes.", flush=True)
            return

        print("\n" + "=" * 70, flush=True)
        print(f" [ALGO HACK] 2-HOUR PROFILE REFRESH: TOGGLING RESDEX DOT (Cycle #{self.cycle_count})", flush=True)
        print("=" * 70, flush=True)
        await self.inject_hud(page, "2-Hour Profile Refresh: Toggling Dot '.'", "Resetting Resdex Search Rank to #1 (Active: Just Now)")

        try:
            await page.goto("https://www.naukri.com/mnjuser/profile", wait_until="domcontentloaded")
            await asyncio.sleep(2.5)

            score_el = page.locator("div.completion-point, span.profile-percent, div[class*='percent']").first
            if await score_el.count() > 0:
                score_text = (await score_el.inner_text()).strip()
                print(f"✔ Current Naukri Profile Score: {score_text}", flush=True)

            # 1. Toggle dot on Resume Headline
            headline_edit_btn = page.locator("div.resumeHeadline span.edit, div.resumeHeadline a:has-text('Edit'), span:has-text('Resume Headline') + span.edit").first
            if await headline_edit_btn.count() > 0 and await headline_edit_btn.is_visible():
                await headline_edit_btn.click()
                await asyncio.sleep(1.5)

                textarea = page.locator("textarea#resumeHeadlineTxt, div.resumeHeadline textarea").first
                if await textarea.count() > 0:
                    current_txt = (await textarea.input_value()).strip()
                    if not current_txt:
                        current_txt = "Python Developer | FastAPI | Django | PostgreSQL | Redis | REST APIs | Microservices | B.Tech CSE (2026) | Immediate Joiner"

                    # Toggle dot
                    if current_txt.endswith("."):
                        new_txt = current_txt.rstrip(".")
                        action_msg = "Removed trailing dot '.'"
                    else:
                        new_txt = current_txt + "."
                        action_msg = "Added trailing dot '.'"

                    print(f"Resume Headline: {action_msg} -> '{new_txt[-25:]}'", flush=True)
                    await textarea.fill(new_txt)
                    await asyncio.sleep(0.8)

                    save_btn = page.locator("form[name='resumeHeadlineForm'] button:has-text('Save'), button.saveBtn:has-text('Save')").first
                    if await save_btn.count() > 0:
                        await save_btn.click()
                        await asyncio.sleep(2)
                        self.last_profile_refresh_time = now
                        print(f"✔ RESDEX RANK RESET TO #1! Profile updated successfully ({action_msg})!", flush=True)
                        await self.inject_hud(page, "Profile Refreshed!", f"Resdex Rank: #1 (Active: Just Now) - {action_msg}")

            # 2. Also toggle dot on Profile Summary if present
            summary_edit_btn = page.locator("div.profileSummary span.edit, div.profileSummary a:has-text('Edit')").first
            if await summary_edit_btn.count() > 0 and await summary_edit_btn.is_visible():
                try:
                    await summary_edit_btn.click()
                    await asyncio.sleep(1.2)
                    sum_textarea = page.locator("textarea#profileSummaryTxt, div.profileSummary textarea").first
                    if await sum_textarea.count() > 0:
                        sum_txt = (await sum_textarea.input_value()).strip()
                        if sum_txt:
                            if sum_txt.endswith("."):
                                sum_new = sum_txt.rstrip(".")
                            else:
                                sum_new = sum_txt + "."
                            await sum_textarea.fill(sum_new)
                            await asyncio.sleep(0.8)
                            sum_save = page.locator("form[name='profileSummaryForm'] button:has-text('Save'), button.saveBtn:has-text('Save')").first
                            if await sum_save.count() > 0:
                                await sum_save.click()
                                await asyncio.sleep(1.5)
                                print("✔ Profile Summary dot also synchronized!", flush=True)
                except Exception:
                    pass

        except Exception as e:
            print(f"Profile Dot Refresh Note: {e}", flush=True)

    async def scan_recruiter_radar(self, page: Page):
        """Phase 2: Recruiter Radar."""
        print("\n" + "=" * 70, flush=True)
        print(" [PHASE 2] RECRUITER RADAR: MESSAGES & NOTIFICATIONS", flush=True)
        print("=" * 70, flush=True)
        await self.inject_hud(page, "Phase 2: Recruiter Radar", "Scanning Recruiter Messages & Chat Inquiries")

        try:
            await page.goto("https://www.naukri.com/communication-center/chat/messages", wait_until="domcontentloaded")
            await asyncio.sleep(2.5)

            chats = await page.locator("div.chat-list-item, div[class*='conversation'], div.chat-item").all()
            print(f"✔ Recruiter Radar: Found {len(chats)} active conversations.", flush=True)

            unread = await page.locator("span.unread, div[class*='unread']").count()
            if unread > 0:
                print(f"👉 NOTICE: You have {unread} unread recruiter messages!", flush=True)

            # Recruiter Radar: Also check Gmail for interview alerts / test links
            try:
                from listeners.email_watcher import EmailWatcher
                ew = EmailWatcher()
                email_alerts = ew.check_inbox()
                if email_alerts:
                    for alert in email_alerts:
                        if alert.get("type") == "INTERVIEW":
                            print(f"  🎯 [INTERVIEW INVITATION] {alert.get('subject')} from {alert.get('from')}", flush=True)
            except Exception:
                pass
        except Exception as e:
            print(f"Recruiter Radar Note: {e}", flush=True)

    async def apply_to_job(self, context: BrowserContext, title: str, href: str, match_res: Optional[Any] = None) -> bool:
        """
        Applies to a job either via:
        1. External Career Site (Greenhouse, Lever, Workday, Google Forms, Custom ATS)
        2. Naukri 1-Click apply + LLM questionnaire review
        Dynamically matches candidate's Java vs Python resume.
        """
        if db.is_already_applied(href):
            print(f"  [Skipped Already Applied] {title}", flush=True)
            return False

        if match_res is None:
            match_res = matcher.match(title)

        resume_type = match_res.resume_type
        score = match_res.score
        reasoning = match_res.reasoning

        jd_page = await context.new_page()
        try:
            await jd_page.goto(href, wait_until="domcontentloaded", timeout=12000)
            await self.inject_hud(jd_page, f"Target: {title[:35]}", f"Auto-Selected: {resume_type.upper()} Resume | {reasoning[:35]}")
            await asyncio.sleep(1.8)

            apply_btn = jd_page.locator("button.apply-button, button:has-text('Apply on company site'), button:has-text('Apply on website'), button:has-text('Apply')").first
            if await apply_btn.count() == 0 or not await apply_btn.is_visible():
                print(f"  [Skipped] Apply button not clickable or already applied: {title}", flush=True)
                await jd_page.close()
                return False

            btn_text = (await apply_btn.inner_text()).strip()

            # Case 1: Explicit External Career Site
            if "company site" in btn_text.lower() or "website" in btn_text.lower() or "career site" in btn_text.lower():
                return await self.apply_on_external_career_site(context, jd_page, title, href, apply_btn=apply_btn, resume_type=resume_type)

            # Case 2: Standard Apply button - check if it opens external site or 1-click
            try:
                await apply_btn.evaluate("el => { el.style.border = '4px solid #10b981'; el.style.boxShadow = '0 0 25px #10b981'; }")
            except Exception:
                pass

            print(f"\n---> Applying to: {title}", flush=True)
            print(f"     Target Stack: [{resume_type.upper()}] | Score: {score} ({reasoning})", flush=True)
            print(f"     Clicking Apply button...", flush=True)
            await self.inject_hud(jd_page, "Clicking Apply...", f"Checking 1-Click / External Portal [{resume_type.upper()}]...")

            # Check if clicking spawns a new tab (external career redirect)
            career_page = None
            try:
                async with context.expect_page(timeout=4000) as new_page_info:
                    await apply_btn.click()
                career_page = await new_page_info.value
            except Exception:
                pass

            if career_page and "naukri.com" not in career_page.url:
                return await self.apply_on_external_career_site(context, jd_page, title, href, existing_career_page=career_page, resume_type=resume_type)

            await asyncio.sleep(1.5)

            # Check if daily quota limit modal appeared on Naukri
            quota_limit_el = jd_page.locator("div:has-text('limit reached'), div:has-text('daily limit'), div:has-text('application quota'), div:has-text('Upgrade to apply')").first
            if await quota_limit_el.count() > 0 and await quota_limit_el.is_visible():
                print(f"  ⚠️ [Naukri 1-Click Quota Exhausted] Daily limit reached for 1-click apply. Skipping this job to prioritize Career Site applications!", flush=True)
                await jd_page.close()
                return False

            # Solve questionnaire using LLM
            await self.solve_chatbot(jd_page)

            # Active 1-Click Submission Verification Loop (up to 8 seconds)
            verified_1click = False
            for _ in range(16):
                await asyncio.sleep(0.5)
                success_el = jd_page.locator("div:has-text('successfully applied'), div[class*='apply-message'], div.apply-success, div[class*='success-msg']").first
                if await success_el.count() > 0 and await success_el.is_visible():
                    verified_1click = True
                    break
                page_text = (await jd_page.content()).lower()
                if any(kw in page_text for kw in ["successfully applied", "application has been sent", "applied successfully"]):
                    verified_1click = True
                    break

            if not verified_1click:
                print(f"  ⚠️ [Unverified Application] 1-Click apply on Naukri could not be confirmed for '{title}'. Skipping false count.", flush=True)
                await jd_page.close()
                return False

            self.total_applied += 1
            proof_file = str(self.proof_dir / f"Autonomous_Apply_{self.total_applied}.png")
            await jd_page.screenshot(path=proof_file)

            db.save_job(
                title=title,
                company="Naukri Recruiter",
                portal="Naukri_Autonomous",
                url=href,
                match_score=score,
                resume_type=resume_type
            )
            db.update_job_status(href, "APPLIED", proof_file)
            print(f"     ✔ APPLICATION #{self.total_applied} VERIFIED! [{resume_type.upper()} RESUME] Proof: {Path(proof_file).name}", flush=True)
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

    async def apply_on_external_career_site(
        self,
        context: BrowserContext,
        jd_page: Page,
        title: str,
        href: str,
        apply_btn: Optional[Any] = None,
        existing_career_page: Optional[Page] = None,
        resume_type: str = "python"
    ) -> bool:
        """Handles applying on external company career sites autonomously."""
        print(f"\n---> [External Career Site Detected] {title}", flush=True)
        print(f"     Routing to {resume_type.upper()} Resume Vault...", flush=True)
        await self.inject_hud(jd_page, f"External Career Site: {title[:35]}", f"Launching Company Portal | {resume_type.upper()} Stack...")

        # Extract company name
        company_name = "Company"
        try:
            comp_el = jd_page.locator("a.company-name, a[class*='comp-name'], div[class*='comp-name']").first
            if await comp_el.count() > 0:
                company_name = (await comp_el.inner_text()).strip()
        except Exception:
            pass

        career_page: Optional[Page] = existing_career_page

        if not career_page and apply_btn:
            try:
                # Try clicking and waiting for popup
                async with context.expect_page(timeout=7000) as new_page_info:
                    await apply_btn.click()
                career_page = await new_page_info.value
            except Exception:
                # Check for modal with "Proceed" or "Continue"
                modal_btn = jd_page.locator("button:has-text('Proceed'), button:has-text('Continue'), a:has-text('Proceed'), a:has-text('Continue')").first
                if await modal_btn.count() > 0 and await modal_btn.is_visible():
                    try:
                        async with context.expect_page(timeout=7000) as new_page_info:
                            await modal_btn.click()
                        career_page = await new_page_info.value
                    except Exception:
                        await modal_btn.click()
                        await asyncio.sleep(3)
                        if "naukri.com" not in jd_page.url:
                            career_page = jd_page
                else:
                    await asyncio.sleep(3)
                    if "naukri.com" not in jd_page.url:
                        career_page = jd_page

        # Fallback search among open tabs
        if not career_page:
            for p in context.pages:
                if p != jd_page and "naukri.com" not in p.url:
                    career_page = p
                    break

        if not career_page:
            print(f"  [External Site] Could not access external career portal for {title}", flush=True)
            await jd_page.close()
            return False

        try:
            await career_page.wait_for_load_state("domcontentloaded", timeout=10000)
        except Exception:
            pass

        autofiller = CareerSiteAutofiller(resume_type=resume_type)
        res = await autofiller.apply_on_career_site(
            page=career_page,
            job_title=title,
            company=company_name,
            job_url=href
        )

        try:
            if career_page != jd_page:
                await career_page.close()
        except Exception:
            pass

        try:
            await jd_page.close()
        except Exception:
            pass

        if res.get("success", False):
            self.total_applied += 1
            print(f"     ✔ APPLICATION #{self.total_applied} VERIFIED ON CAREER SITE! [{resume_type.upper()}] Proof: {Path(res.get('proof', '')).name}", flush=True)
            return True
        else:
            print(f"     ❌ Application not verified/completed for {title}: {res.get('message', 'Unverified')}", flush=True)
            return False

    async def solve_chatbot(self, jd_page: Page):
        """Autonomous questionnaire solver using Gemini 3.5 Flash Lite + verified resume."""
        for turn in range(5):
            await asyncio.sleep(1.2)
            input_box = jd_page.locator("input.chatbot-input, input[placeholder*='Type your answer'], textarea[placeholder*='Type your answer'], input[class*='bot-input']").first
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
        """Scans jobs recommended specifically by Naukri's AI algorithm."""
        print("\n" + "=" * 70, flush=True)
        print(" [PHASE 3] NAUKRI AI RECOMMENDED JOBS DISCOVERY", flush=True)
        print("=" * 70, flush=True)
        await self.inject_hud(page, "Phase 3: Scanning AI Recommended Jobs", "Naukri Personalized Matches")

        try:
            await page.goto("https://www.naukri.com/mnjuser/recommendedjobs", wait_until="domcontentloaded")
            await asyncio.sleep(2.5)

            job_cards = await page.locator("div.srp-jobtuple-wrapper, div.cust-job-tuple, div[class*='jobTuple']").all()
            if not job_cards:
                job_cards = await page.locator("a.title, a[class*='title']").all()

            print(f"Found {len(job_cards)} AI recommended jobs for Sachindra!", flush=True)

            applied_in_step = 0
            for card in job_cards[:15]:
                if applied_in_step >= max_jobs:
                    break
                try:
                    title_el = card.locator("a.title").first if await card.locator("a.title").count() > 0 else card
                    title = (await title_el.inner_text()).strip()
                    href = await title_el.get_attribute("href")
                    if not href:
                        continue

                    exp_text = ""
                    try:
                        exp_el = card.locator("span.expwdth, span[class*='exp'], li.experience, span[title*='Yrs']").first
                        if await exp_el.count() > 0:
                            exp_text = (await exp_el.inner_text()).strip()
                    except Exception:
                        pass

                    is_app, match_res = matcher.is_applicable(title, exp_text=exp_text, url=href)
                    if not is_app:
                        print(f"  [Skipped Role] '{title}' ({exp_text or 'No Exp Tag'}) -> {match_res.reasoning}", flush=True)
                        continue

                    success = await self.apply_to_job(context, title, href, match_res=match_res)
                    if success:
                        applied_in_step += 1
                except Exception:
                    continue
        except Exception as e:
            print(f"Recommended Jobs Note: {e}", flush=True)

    async def execute_vector_search(self, context: BrowserContext, page: Page, vector: Dict[str, str], max_pages: int = 4):
        """Paginates through a targeted search vector (up to max_pages)."""
        name = vector["name"]
        base_url = vector["base_url"]

        print(f"\n---> Searching Vector: {name}", flush=True)
        await self.inject_hud(page, f"Target: {name}", f"Total Applications So Far: {self.total_applied}")

        for page_num in range(1, max_pages + 1):
            if page_num == 1:
                url = base_url
            else:
                if "?" in base_url:
                    parts = base_url.split("?")
                    url = f"{parts[0]}-{page_num}?{parts[1]}"
                else:
                    url = f"{base_url}-{page_num}"

            print(f"   [Page {page_num}/{max_pages}] Loading: {url}", flush=True)
            try:
                await page.goto(url, wait_until="domcontentloaded")
                await asyncio.sleep(2.5)

                job_cards = await page.locator("div.srp-jobtuple-wrapper, div.cust-job-tuple, div[class*='jobTuple']").all()
                if not job_cards:
                    job_cards = await page.locator("a.title, a[class*='title']").all()

                if not job_cards:
                    print(f"   No more jobs found on Page {page_num}. Moving to next vector.", flush=True)
                    break

                print(f"   Found {len(job_cards)} job cards on Page {page_num}...", flush=True)
                for card in job_cards:
                    try:
                        title_el = card.locator("a.title").first if await card.locator("a.title").count() > 0 else card
                        title = (await title_el.inner_text()).strip()
                        href = await title_el.get_attribute("href")
                        if not href:
                            continue

                        exp_text = ""
                        try:
                            exp_el = card.locator("span.expwdth, span[class*='exp'], li.experience, span[title*='Yrs']").first
                            if await exp_el.count() > 0:
                                exp_text = (await exp_el.inner_text()).strip()
                        except Exception:
                            pass

                        is_app, match_res = matcher.is_applicable(title, exp_text=exp_text, url=href)
                        if not is_app:
                            print(f"   [Skipped Role] '{title}' ({exp_text or 'No Exp Tag'}) -> {match_res.reasoning}", flush=True)
                            continue

                        await self.apply_to_job(context, title, href, match_res=match_res)
                    except Exception:
                        continue
            except Exception as e:
                print(f"   Search Vector Error on Page {page_num}: {e}", flush=True)
                break

    async def run_continuous_engine(self):
        """Runs the continuous, non-stop autonomous loop."""
        print("\n" + "=" * 75, flush=True)
        print("       NIRANTAR: CONTINUOUS NON-STOP NAUKRI AUTONOMOUS ENGINE", flush=True)
        print("=" * 75, flush=True)
        print(f"Candidate: {self.profile.full_name}", flush=True)
        print("Target Stacks: Python & Java Engineering (0-2 Yrs Freshers)", flush=True)
        print("Engine Mode: CONTINUOUS NON-STOP (Will keep running while laptop is on)", flush=True)
        print("=" * 75, flush=True)

        unlock_chrome_profile(self.profile_dir)

        async with async_playwright() as p:
            launch_kwargs = {
                "user_data_dir": str(self.profile_dir),
                "channel": "chrome",
                "headless": False,
                "slow_mo": 250,
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
                if "ProcessSingleton" in str(e) or "already in use" in str(e):
                    print("⚠️ Profile lock detected. Re-cleaning locks and retrying launch...", flush=True)
                    unlock_chrome_profile(self.profile_dir)
                    await asyncio.sleep(2)
                    context = await p.chromium.launch_persistent_context(**launch_kwargs)
                else:
                    raise e

            page = context.pages[0] if context.pages else await context.new_page()

            # Verify login
            await page.goto("https://www.naukri.com/", wait_until="domcontentloaded")
            await asyncio.sleep(2)

            while True:
                print(f"\n{'#' * 75}", flush=True)
                print(f"   STARTING CONTINUOUS ENGINE CYCLE #{self.cycle_count}", flush=True)
                print(f"   Total Lifetime Applications in this session: {self.total_applied}", flush=True)
                print(f"{'#' * 75}\n", flush=True)

                # Step 1: Optimize Profile & Boost Algo Rank (Every 2 Hours Dot Toggle)
                await self.optimize_profile_and_boost_rank(page)

                # Step 2: Recruiter Radar (Messages & Chats)
                await self.scan_recruiter_radar(page)

                # Step 3: AI Recommended Jobs
                await self.scan_recommended_jobs(context, page, max_jobs=5)

                # Step 4: Multi-Vector Continuous Search Rotation
                for vector in SEARCH_VECTORS:
                    await self.execute_vector_search(context, page, vector, max_pages=4)

                print("\n" + "=" * 75, flush=True)
                print(f"✔ CYCLE #{self.cycle_count} COMPLETE! Total Applied: {self.total_applied}", flush=True)
                print("Resting for 5 minutes before next continuous scan...", flush=True)
                print("=" * 75 + "\n", flush=True)

                self.cycle_count += 1

                # Live HUD Countdown (5 minutes) before next continuous scan
                wait_seconds = 300
                for remaining in range(wait_seconds, 0, -10):
                    mins = remaining // 60
                    secs = remaining % 60
                    await self.inject_hud(
                        page,
                        f"Non-Stop Engine: {self.total_applied} Jobs Applied",
                        f"Next Continuous Scan in {mins}m {secs}s (Cycle #{self.cycle_count})"
                    )
                    await asyncio.sleep(10)


if __name__ == "__main__":
    agent = AutonomousNaukriAgent()
    asyncio.run(agent.run_continuous_engine())
