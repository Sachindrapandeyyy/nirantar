import asyncio
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger
from playwright.async_api import Page, BrowserContext, async_playwright

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.vault import vault
from tracker.database import db
from core.matcher import matcher
from naukri.filters import is_fresher_job
from career_site.autofiller import CareerSiteAutofiller
from config.settings import unlock_chrome_profile

LINKEDIN_VECTORS = [
    {
        "name": "LinkedIn Python Entry Level (India)",
        "url": "https://www.linkedin.com/jobs/search/?keywords=Python%20Developer&f_E=1%2C2&location=India"
    },
    {
        "name": "LinkedIn Java Entry Level (India)",
        "url": "https://www.linkedin.com/jobs/search/?keywords=Java%20Developer&f_E=1%2C2&location=India"
    },
    {
        "name": "LinkedIn Backend Entry Level (Delhi NCR)",
        "url": "https://www.linkedin.com/jobs/search/?keywords=Backend%20Developer&f_E=1%2C2&location=Delhi%2C%20India"
    }
]


class AutonomousLinkedInAgent:
    """
    Autonomous LinkedIn Job Agent.
    Operates in headed Chrome profile:
    1. Scans filtered fresher & entry-level roles (0-2 Yrs)
    2. Dynamically routes between Java and Python resumes
    3. Handles 1-Click 'Easy Apply' multi-step modals
    4. Automatically routes external company sites to CareerSiteAutofiller
    5. Saves visual proofs to proofs/linkedin/ and records to nirantar.db
    """

    def __init__(self):
        self.profile = vault.get_profile()
        self.profile_dir = Path.home() / ".nirantar" / "chrome_profile"
        self.proof_dir = PROJECT_ROOT / "proofs" / "linkedin"
        self.proof_dir.mkdir(parents=True, exist_ok=True)
        self.total_applied = 0

    async def inject_hud(self, page: Page, title: str, subtitle: str = ""):
        """Injects status banner at top of LinkedIn tabs."""
        sub_html = f'<div style="font-size:11px; color:#a7f3d0;">{subtitle}</div>' if subtitle else ''
        js_code = f"""() => {{
            let hud = document.getElementById('nirantar-linkedin-hud');
            if (!hud) {{
                hud = document.createElement('div');
                hud.id = 'nirantar-linkedin-hud';
                hud.style.position = 'fixed';
                hud.style.top = '10px';
                hud.style.left = '50%';
                hud.style.transform = 'translateX(-50%)';
                hud.style.zIndex = '9999999';
                hud.style.background = 'linear-gradient(135deg, #004182 0%, #0a66c2 100%)';
                hud.style.color = '#ffffff';
                hud.style.padding = '8px 24px';
                hud.style.borderRadius = '30px';
                hud.style.fontSize = '12px';
                hud.style.fontWeight = 'bold';
                hud.style.fontFamily = 'Segoe UI, system-ui, sans-serif';
                hud.style.boxShadow = '0 6px 20px rgba(0,0,0,0.5)';
                hud.style.display = 'flex';
                hud.style.flexDirection = 'column';
                hud.style.alignItems = 'center';
                hud.style.pointerEvents = 'none';
                document.body.appendChild(hud);
            }}
            hud.innerHTML = `
                <div style="font-size:13px; color:#ffffff;">⚡ NIRANTAR LINKEDIN MASTER AGENT</div>
                <div style="font-size:11px; color:#e0f2fe;">{title}</div>
                {sub_html}
            `;
        }}"""
        try:
            await page.evaluate(js_code)
        except Exception:
            pass

    async def apply_to_job(self, context: BrowserContext, title: str, company: str, href: str) -> bool:
        """Applies to a LinkedIn job via Easy Apply or external career site."""
        if db.is_already_applied(href):
            print(f"  [Skipped Already Applied] {title} at {company}", flush=True)
            return False

        is_app, match_res = matcher.is_applicable(title, url=href)
        if not is_app:
            print(f"  [Skipped Inapplicable Role] '{title}' -> {match_res.reasoning}", flush=True)
            return False

        resume_type = match_res.resume_type
        print(f"\n---> [LinkedIn] Processing: {title} at {company}", flush=True)
        print(f"     Target Stack: [{resume_type.upper()}] | Reasoning: {match_res.reasoning}", flush=True)

        page = await context.new_page()
        try:
            await page.goto(href, wait_until="domcontentloaded", timeout=15000)
            await self.inject_hud(page, f"{title[:30]} at {company[:20]}", f"Stack: {resume_type.upper()}")
            await asyncio.sleep(2)

            # Check for Easy Apply button
            easy_apply_btn = page.locator("button.jobs-apply-button, button:has-text('Easy Apply')").first
            if await easy_apply_btn.count() > 0 and await easy_apply_btn.is_visible():
                return await self.handle_easy_apply(page, title, company, href, resume_type)

            # Check for external apply button
            external_btn = page.locator("button:has-text('Apply'), a:has-text('Apply')").first
            if await external_btn.count() > 0 and await external_btn.is_visible():
                autofiller = CareerSiteAutofiller(resume_type=resume_type)
                res = await autofiller.apply_on_career_site(page, title, company, href)
                if res.get("success", False):
                    self.total_applied += 1
                    return True
                return False

            print(f"  No clickable apply button found for {title}.", flush=True)
            return False

        except Exception as e:
            logger.debug(f"LinkedIn apply error: {e}")
            return False
        finally:
            try:
                await page.close()
            except Exception:
                pass

    async def handle_easy_apply(self, page: Page, title: str, company: str, href: str, resume_type: str) -> bool:
        """Handles LinkedIn multi-step Easy Apply modal."""
        print(f"  Detected LinkedIn 'Easy Apply' for {company}!", flush=True)
        await self.inject_hud(page, f"Easy Apply: {company}", f"Filling Form [{resume_type.upper()}]...")

        apply_btn = page.locator("button.jobs-apply-button, button:has-text('Easy Apply')").first
        await apply_btn.click()
        await asyncio.sleep(1.5)

        autofiller = CareerSiteAutofiller(resume_type=resume_type)

        # Multi-step loop (up to 5 steps)
        for step in range(1, 6):
            await autofiller.autofill_form_elements(page, page)
            await asyncio.sleep(0.5)

            # Check if Submit button is visible
            submit_btn = page.locator("button:has-text('Submit application'), button[aria-label='Submit application']").first
            if await submit_btn.count() > 0 and await submit_btn.is_visible():
                await submit_btn.click()
                await asyncio.sleep(2)
                timestamp = int(time.time())
                proof_path = str(self.proof_dir / f"LI_{re.sub(r'[^a-zA-Z0-9]', '_', company)[:15]}_{timestamp}.png")
                await page.screenshot(path=proof_path)

                db.save_job(title=title, company=company, portal="LinkedIn", url=href, match_score=0.9, resume_type=resume_type)
                db.update_job_status(href, "APPLIED", proof_path)
                self.total_applied += 1
                print(f"  ✔ [LINKEDIN EASY APPLY VERIFIED] #{self.total_applied} for {company}! Proof: {Path(proof_path).name}", flush=True)
                return True

            # Check for Next / Review button
            next_btn = page.locator("button:has-text('Next'), button:has-text('Review'), button[aria-label='Continue to next step']").first
            if await next_btn.count() > 0 and await next_btn.is_visible():
                await next_btn.click()
                await asyncio.sleep(1.2)
            else:
                break

        return False

    async def scan_vector(self, context: BrowserContext, page: Page, vector: Dict[str, str], max_jobs: int = 10):
        """Scans a targeted LinkedIn search vector for entry-level roles."""
        name = vector["name"]
        url = vector["url"]
        print(f"\n---> [LinkedIn Vector] Scanning: {name}", flush=True)
        await self.inject_hud(page, f"Scanning: {name}", f"Total LinkedIn Applied: {self.total_applied}")

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(2.5)

            job_cards = await page.locator("div.job-card-container, li.jobs-search-results__list-item").all()
            if not job_cards:
                job_cards = await page.locator("a.job-card-list__title, a.job-card-container__link").all()

            print(f"  Found {len(job_cards)} job cards on LinkedIn!", flush=True)
            for card in job_cards[:max_jobs]:
                try:
                    title_el = card.locator("a.job-card-list__title, a[class*='title']").first if await card.locator("a.job-card-list__title").count() > 0 else card
                    title = (await title_el.inner_text()).strip()
                    href = await title_el.get_attribute("href")
                    if not href:
                        continue
                    if not href.startswith("http"):
                        href = f"https://www.linkedin.com{href}"

                    comp_el = card.locator("span.job-card-container__primary-description, [class*='company-name']").first
                    company = (await comp_el.inner_text()).strip() if await comp_el.count() > 0 else "Company"

                    await self.apply_to_job(context, title, company, href)
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f"LinkedIn vector error: {e}")

    async def run(self):
        """Entry point for standalone execution."""
        print("\n" + "=" * 70, flush=True)
        print(" [LINKEDIN AGENT] Launching Autonomous LinkedIn Engine", flush=True)
        print(f" Candidate: {self.profile.full_name}", flush=True)
        print("=" * 70, flush=True)

        unlock_chrome_profile(self.profile_dir)

        async with async_playwright() as p:
            launch_args = {
                "user_data_dir": str(self.profile_dir),
                "channel": "chrome",
                "headless": False,
                "args": ["--start-maximized", "--disable-blink-features=AutomationControlled", "--no-sandbox"]
            }
            try:
                context = await p.chromium.launch_persistent_context(**launch_args)
            except Exception as e:
                if "ProcessSingleton" in str(e) or "already in use" in str(e):
                    unlock_chrome_profile(self.profile_dir)
                    await asyncio.sleep(2)
                    context = await p.chromium.launch_persistent_context(**launch_args)
                else:
                    raise e

            try:
                from core.stealth import apply_stealth_to_context
                await apply_stealth_to_context(context)
            except Exception:
                pass

            page = context.pages[0] if context.pages else await context.new_page()

            for vector in LINKEDIN_VECTORS:
                await self.scan_vector(context, page, vector, max_jobs=8)

            await context.close()


linkedin_agent = AutonomousLinkedInAgent()
