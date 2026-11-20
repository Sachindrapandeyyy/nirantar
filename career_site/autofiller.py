import asyncio
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger
from playwright.async_api import Page, Frame, Locator

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.vault import vault
from tracker.database import db
from core.career_knowledge_base import get_career_knowledge_base, match_field_to_value
from brain.question_solver import solver


class CareerSiteAutofiller:
    """
    Autonomous External Career Site Engine.
    Handles applications on:
    - Greenhouse (Direct & Embedded Iframes)
    - Lever (Direct & Embedded)
    - SmartRecruiters, Workable, BambooHR
    - Google Forms
    - Generic HTML / React / Angular ATS Career Pages

    Equipped with:
    1. Deterministic Multi-Signal Submission Verification
    2. Strict 75-Second Timeout Per Job (prevents infinite hangs)
    3. Network & Dynamic SPA Event Synchronization
    4. Dual-Resume Stack Routing (Python vs Java)
    """

    def __init__(self, resume_type: str = "python"):
        self.resume_type = str(resume_type).lower()
        self.proof_dir = PROJECT_ROOT / "proofs" / "career_sites"
        self.proof_dir.mkdir(parents=True, exist_ok=True)
        self.profile = vault.get_profile()
        self.kb = get_career_knowledge_base(self.resume_type)

    async def inject_hud(self, page: Page, title: str, subtitle: str = ""):
        """Injects a visible HUD status banner at the top of the browser page."""
        sub_html = f'<div style="font-size:11px; color:#a7f3d0;">{subtitle}</div>' if subtitle else ''
        js_code = f"""() => {{
            let hud = document.getElementById('nirantar-career-hud');
            if (!hud) {{
                hud = document.createElement('div');
                hud.id = 'nirantar-career-hud';
                hud.style.position = 'fixed';
                hud.style.top = '10px';
                hud.style.left = '50%';
                hud.style.transform = 'translateX(-50%)';
                hud.style.zIndex = '9999999';
                hud.style.background = 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #064e3b 100%)';
                hud.style.color = '#38bdf8';
                hud.style.padding = '10px 26px';
                hud.style.borderRadius = '30px';
                hud.style.fontSize = '13px';
                hud.style.fontWeight = 'bold';
                hud.style.fontFamily = 'Segoe UI, system-ui, sans-serif';
                hud.style.boxShadow = '0 8px 30px rgba(0,0,0,0.7), 0 0 20px rgba(56,189,248,0.5)';
                hud.style.border = '1px solid rgba(56,189,248,0.4)';
                hud.style.display = 'flex';
                hud.style.flexDirection = 'column';
                hud.style.alignItems = 'center';
                hud.style.gap = '3px';
                hud.style.pointerEvents = 'none';
                document.body.appendChild(hud);
            }}
            hud.innerHTML = `
                <div style="font-size:14px; color:#38bdf8; display:flex; align-items:center; gap:8px;">
                    <span>⚡ NIRANTAR CAREER SITE AUTONOMOUS ENGINE</span>
                    <span style="background:#0284c7; color:#ffffff; font-size:10px; padding:2px 7px; border-radius:8px;">HEADED</span>
                </div>
                <div style="font-size:12px; color:#ffffff; font-weight:normal;">{title}</div>
                {sub_html}
            `;
        }}"""
        try:
            await page.evaluate(js_code)
        except Exception:
            pass

    async def highlight_element(self, element: Locator, color: str = "#10b981"):
        """Visually highlights an element before interacting with it."""
        try:
            await element.evaluate(
                f"(el) => {{ el.style.border = '2px solid {color}'; el.style.boxShadow = '0 0 12px {color}'; el.scrollIntoView({{behavior: 'smooth', block: 'center'}}); }}"
            )
        except Exception:
            pass

    def get_resume_path(self) -> Optional[Path]:
        """Fetches the verified resume from the candidate vault."""
        resume = vault.get_resume(self.resume_type)
        if not resume or not resume.exists():
            resume = vault.get_resume("python")
        if not resume or not resume.exists():
            resume = vault.get_resume("java")
        return resume

    async def apply_on_career_site(
        self,
        page: Page,
        job_title: str,
        company: str,
        job_url: str = ""
    ) -> Dict[str, Any]:
        """
        Main entry point: Inspects page, detects platform, fills all fields,
        attaches resume, submits application, and records verified proof.
        Guarded by a strict 75-second timeout to prevent stalling the runner.
        """
        try:
            return await asyncio.wait_for(
                self._execute_workflow(page, job_title, company, job_url),
                timeout=25.0
            )
        except asyncio.TimeoutError:
            print(f"  ⚡ [SLOW SITE SKIPPED] Career portal for {company} took >25s. Fast-skipping to next job.", flush=True)
            safe_company = re.sub(r'[^a-zA-Z0-9]', '_', company)[:20]
            safe_title = re.sub(r'[^a-zA-Z0-9]', '_', job_title)[:20]
            proof_path = str(self.proof_dir / f"TIMEOUT_{safe_company}_{safe_title}_{int(time.time())}.png")
            try:
                await page.screenshot(path=proof_path)
            except Exception:
                pass
            return {
                "success": False,
                "status": "TIMEOUT",
                "proof": proof_path,
                "message": "Career application exceeded 25s timeout limit (fast-skipped to prevent hang)."
            }

    async def dismiss_cookie_banners(self, page: Page):
        """Proactively dismisses GDPR / Cookie consent banners that block interactions."""
        cookie_selectors = [
            "button#onetrust-accept-btn-handler",
            "button:has-text('Accept All')",
            "button:has-text('Accept Cookies')",
            "button:has-text('Accept all cookies')",
            "button:has-text('I Accept')",
            "button:has-text('Allow all')",
            "button:has-text('Agree')",
            "button:has-text('Got it')",
            "button[id*='cookie-accept']",
            "button[class*='cookie-accept']",
            "button[class*='consent-accept']",
            "button[class*='cookie-btn']"
        ]
        for sel in cookie_selectors:
            try:
                btn = page.locator(sel).first
                if await btn.count() > 0 and await btn.is_visible():
                    await btn.click(timeout=1500)
                    print(f"  [Cookie Banner Dismissed] via '{sel}'", flush=True)
                    await asyncio.sleep(0.5)
                    break
            except Exception:
                pass

    async def _execute_workflow(
        self,
        page: Page,
        job_title: str,
        company: str,
        job_url: str = ""
    ) -> Dict[str, Any]:
        """Core execution workflow."""
        current_url = page.url
        print(f"\n" + "=" * 70, flush=True)
        print(f" [CAREER SITE ENGINE] Applying to: {company} - {job_title}", flush=True)
        print(f" Target URL: {current_url}", flush=True)
        print(f" Target Stack: [{self.resume_type.upper()}]", flush=True)
        print("=" * 70, flush=True)

        await self.inject_hud(page, f"Target: {company}", f"Role: {job_title[:30]} | Stack: {self.resume_type.upper()} | Detecting ATS...")

        # 0. Fast Dead Page / Error Page Check (< 1s)
        try:
            page_title = (await page.title()).lower()
            page_url_lower = page.url.lower()
            page_body = (await page.evaluate("() => document.body ? document.body.innerText.trim() : ''")).lower()

            dead_signatures = [
                "404", "not found", "500 internal server error", "502 bad gateway",
                "503 service unavailable", "site can't be reached", "server error",
                "access denied", "403 forbidden", "dns_probe_finished", "err_connection",
                "page not found", "job expired", "job is no longer available", "this site can’t be reached"
            ]
            if any(sig in page_title for sig in dead_signatures) or any(sig in page_body[:200] for sig in dead_signatures):
                print(f"  ⚠️ [Dead Page Fast-Bail] Detected error page: '{page_title}'. Safely skipping in 1s.", flush=True)
                return {
                    "success": False,
                    "status": "DEAD_PAGE",
                    "message": f"Website unreachable or dead error page: {page_title}"
                }

            # Check for completely blank screen (<30 chars)
            if len(page_body) < 30:
                print("  Page appears blank/loading. Waiting 3s for hydration/redirect...", flush=True)
                await asyncio.sleep(3)
                page_body = (await page.evaluate("() => document.body ? document.body.innerText.trim() : ''")).lower()
                if len(page_body) < 30:
                    print("  ⚠️ [Blank Page Fast-Bail] Page stayed blank (<30 chars). Safely skipping to next job.", flush=True)
                    return {
                        "success": False,
                        "status": "BLANK_PAGE",
                        "message": "Career page is empty or failed to load."
                    }
        except Exception:
            pass

        # Proactively dismiss GDPR / Cookie banners
        await self.dismiss_cookie_banners(page)

        # Wait for dynamic form elements to render
        try:
            await page.wait_for_selector("input, textarea, form, div[role='main']", state="visible", timeout=10000)
        except Exception:
            pass

        # 1. Platform Detection & Routing
        if "greenhouse.io" in current_url or await page.locator("iframe#grnhse_iframe").count() > 0 or (await page.locator("#application_form, #app_form").count() > 0 and "greenhouse" in (await page.content()).lower()):
            res = await self.handle_greenhouse(page, job_title, company)
        elif "lever.co" in current_url or "jobs.lever.co" in current_url:
            res = await self.handle_lever(page, job_title, company)
        elif "docs.google.com/forms" in current_url:
            res = await self.handle_google_form(page, job_title, company)
        else:
            # Generic ATS / HTML Form
            res = await self.handle_generic_form(page, job_title, company)

        # 2. Database Recording & Proof (ONLY for verified submissions)
        proof_path = res.get("proof", "")
        if res.get("success", False):
            db.save_job(
                title=job_title,
                company=company,
                portal="CareerSite",
                url=job_url or current_url,
                match_score=0.95,
                resume_type=self.resume_type
            )
            db.update_job_status(job_url or current_url, "APPLIED", proof_path)
            print(f" ✔ APPLICATION VERIFIED for {company}! Proof saved: {Path(proof_path).name}", flush=True)
        else:
            print(f" ⚠️ Application status for {company}: {res.get('message')}", flush=True)

        return res

    async def handle_greenhouse(self, page: Page, job_title: str, company: str) -> Dict[str, Any]:
        """Handles Greenhouse job boards and embedded Greenhouse iframes."""
        print(" -> Detected ATS: Greenhouse", flush=True)
        await self.inject_hud(page, f"ATS: Greenhouse | {company}", f"Filling Info ({self.resume_type.upper()})...")

        target = page
        if await page.locator("iframe#grnhse_iframe").count() > 0:
            target = page.frame_locator("iframe#grnhse_iframe")

        filled_count = 0

        # Fill identity
        field_mappings = [
            ("#first_name", self.kb["first_name"]),
            ("#last_name", self.kb["last_name"]),
            ("#email", self.kb["email"]),
            ("#phone", self.kb["phone"]),
            ("#job_application_location", f"{self.kb['city']}, {self.kb['country']}"),
        ]

        for selector, val in field_mappings:
            loc = target.locator(selector).first
            if await loc.count() > 0 and await loc.is_visible():
                await self.highlight_element(loc)
                await loc.fill(val)
                filled_count += 1
                await asyncio.sleep(0.15)

        # Social links
        for selector, val in [
            ("input[id*='linkedin'], input[name*='linkedin']", self.kb["linkedin"]),
            ("input[id*='github'], input[name*='github']", self.kb["github"]),
            ("input[id*='website'], input[name*='website'], input[id*='portfolio']", self.kb["portfolio"]),
        ]:
            loc = target.locator(selector).first
            if await loc.count() > 0 and await loc.is_visible():
                await self.highlight_element(loc)
                await loc.fill(val)
                filled_count += 1
                await asyncio.sleep(0.15)

        # Resume upload
        resume_file = self.get_resume_path()
        if resume_file and resume_file.exists():
            await self.inject_hud(page, f"ATS: Greenhouse | {company}", f"Attaching {self.resume_type.upper()} Resume ({resume_file.name})...")
            file_input = target.locator("input[type='file']").first
            if await file_input.count() > 0:
                await file_input.set_input_files(str(resume_file))
                print(f"  Attached {self.resume_type.upper()} resume: {resume_file.name}", flush=True)
                filled_count += 1
                await asyncio.sleep(1.5)

        # Dynamic questions & dropdowns
        filled_dyn = await self.autofill_form_elements(target, page)
        filled_count += filled_dyn

        # Submit Application
        await self.inject_hud(page, f"ATS: Greenhouse | {company}", f"Submitting ({filled_count} fields filled)...")
        submit_btn = target.locator("#submit_app, input[type='submit'], button[type='submit']:has-text('Submit')").first
        return await self._click_submit_and_verify(page, submit_btn, company, job_title, fields_filled=filled_count)

    async def handle_lever(self, page: Page, job_title: str, company: str) -> Dict[str, Any]:
        """Handles Lever.co application pages."""
        print(" -> Detected ATS: Lever", flush=True)
        await self.inject_hud(page, f"ATS: Lever | {company}", "Navigating to Application Form...")

        # If on JD overview page, click Apply
        if "/apply" not in page.url:
            apply_btn = page.locator("a:has-text('Apply for this job'), a.postings-btn, button:has-text('Apply')").first
            if await apply_btn.count() > 0:
                await apply_btn.click()
                await asyncio.sleep(2)

        await self.inject_hud(page, f"ATS: Lever | {company}", f"Filling Application Details ({self.resume_type.upper()})...")

        filled_count = 0

        # Personal details
        field_mappings = [
            ("input[name='name']", self.kb["full_name"]),
            ("input[name='email']", self.kb["email"]),
            ("input[name='phone']", self.kb["phone"]),
            ("input[name='org']", self.kb["current_company"]),
            ("input[name='urls[LinkedIn]']", self.kb["linkedin"]),
            ("input[name='urls[GitHub]']", self.kb["github"]),
            ("input[name='urls[Portfolio]']", self.kb["portfolio"]),
        ]

        for selector, val in field_mappings:
            loc = page.locator(selector).first
            if await loc.count() > 0 and await loc.is_visible():
                await self.highlight_element(loc)
                await loc.fill(val)
                filled_count += 1
                await asyncio.sleep(0.15)

        # Resume upload
        resume_file = self.get_resume_path()
        if resume_file and resume_file.exists():
            await self.inject_hud(page, f"ATS: Lever | {company}", f"Attaching {self.resume_type.upper()} Resume ({resume_file.name})...")
            file_input = page.locator("input[type='file']").first
            if await file_input.count() > 0:
                await file_input.set_input_files(str(resume_file))
                print(f"  Attached {self.resume_type.upper()} resume: {resume_file.name}", flush=True)
                filled_count += 1
                await asyncio.sleep(1.5)

        # Dynamic questions & dropdowns
        filled_dyn = await self.autofill_form_elements(page, page)
        filled_count += filled_dyn

        # Submit
        await self.inject_hud(page, f"ATS: Lever | {company}", f"Submitting ({filled_count} fields filled)...")
        submit_btn = page.locator("#btn-submit, button[data-qa='btn-submit'], button:has-text('Submit Application')").first
        return await self._click_submit_and_verify(page, submit_btn, company, job_title, fields_filled=filled_count)

    async def handle_google_form(self, page: Page, job_title: str, company: str) -> Dict[str, Any]:
        """Handles Google Forms job applications."""
        print(" -> Detected ATS: Google Forms", flush=True)
        await self.inject_hud(page, f"Portal: Google Form | {company}", "Inspecting Form Fields...")

        filled_count = 0
        # Find questions
        question_containers = await page.locator("div[role='listitem']").all()
        for container in question_containers:
            try:
                # Question title
                title_el = container.locator("div[role='heading'], span[class*='heading']").first
                q_text = (await title_el.inner_text()).strip() if await title_el.count() > 0 else ""

                ans = match_field_to_value("question", q_text, "", resume_type=self.resume_type)
                if not ans:
                    ans = await solver.solve_question(q_text, profile=self.profile)

                # Check text input
                text_input = container.locator("input[type='text'], input[type='email'], textarea").first
                if await text_input.count() > 0 and await text_input.is_visible():
                    await self.highlight_element(text_input)
                    await text_input.fill(ans)
                    filled_count += 1
                    await asyncio.sleep(0.15)
                    continue

                # Check radio buttons
                radios = await container.locator("div[role='radio']").all()
                if radios:
                    for r in radios:
                        lbl = (await r.inner_text()).strip()
                        if ans.lower() in lbl.lower() or lbl.lower() in ans.lower():
                            await r.click()
                            filled_count += 1
                            await asyncio.sleep(0.15)
                            break
            except Exception as e:
                logger.debug(f"Google Form field error: {e}")

        submit_btn = page.locator("div[role='button']:has-text('Submit'), span:has-text('Submit')").first
        return await self._click_submit_and_verify(page, submit_btn, company, job_title, fields_filled=filled_count)

    async def handle_generic_form(self, page: Page, job_title: str, company: str) -> Dict[str, Any]:
        """Handles arbitrary company career portals, Workable, SmartRecruiters, React/Angular apps."""
        print(" -> Detected ATS: Generic HTML / React Portal", flush=True)
        await self.inject_hud(page, f"Portal: {company}", f"Scanning Fields ({self.resume_type.upper()})...")

        # 0. Check if this is a JD / Landing page where form is not yet visible
        try:
            visible_inputs = await page.locator("input:not([type='hidden']):not([type='submit']):not([type='button']), textarea").all()
            visible_count = 0
            for vi in visible_inputs:
                if await vi.is_visible():
                    visible_count += 1

            if visible_count < 2:
                print(f"  Only {visible_count} visible input(s) found. Searching for 'Apply Now' form opener...", flush=True)
                openers = [
                    "a:has-text('I\'m Interested')",
                    "button:has-text('I\'m Interested')",
                    "a:has-text('I\'m interested')",
                    "button:has-text('I\'m interested')",
                    "a.apply_btn",
                    "button.apply_btn",
                    "a.apply_job",
                    "#btn-apply",
                    "a:has-text('Apply for this job')",
                    "button:has-text('Apply for this job')",
                    "a:has-text('Apply Now')",
                    "button:has-text('Apply Now')",
                    "a:has-text('Apply now')",
                    "button:has-text('Apply now')",
                    "a:has-text('Apply Online')",
                    "button:has-text('Apply Online')",
                    "a.postings-btn",
                    "a[href*='apply']",
                    "button[data-qa*='apply']",
                    "a:has-text('Apply')",
                    "button:has-text('Apply')"
                ]
                for op in openers:
                    try:
                        op_btn = page.locator(op).first
                        if await op_btn.count() > 0 and await op_btn.is_visible():
                            btn_txt = (await op_btn.inner_text()).strip()
                            print(f"  Clicking form opener: '{btn_txt}' ({op})", flush=True)
                            await self.highlight_element(op_btn, "#38bdf8")
                            await op_btn.click()
                            await asyncio.sleep(2.5)
                            break
                    except Exception:
                        pass
        except Exception:
            pass

        # Check for application iframe (e.g. Workable, Greenhouse embedded)
        target_scope = page
        for fr in page.frames:
            if fr != page.main_frame:
                if any(kw in fr.url.lower() for kw in ["greenhouse", "lever", "workable", "smartrecruiters", "bamboohr", "apply"]):
                    target_scope = fr
                    print(f"  Target application iframe detected: {fr.url[:60]}...", flush=True)
                    break

        total_fields_filled = 0

        # First, upload resume if file input is available
        resume_file = self.get_resume_path()
        if resume_file and resume_file.exists():
            file_inputs = await target_scope.locator("input[type='file']").all()
            for fi in file_inputs:
                try:
                    await fi.set_input_files(str(resume_file))
                    print(f"  Attached {self.resume_type.upper()} resume to file input: {resume_file.name}", flush=True)
                    total_fields_filled += 1
                    await asyncio.sleep(1.5)
                    break
                except Exception:
                    pass

        # Autofill all form elements (inputs, textareas, selects, radios, checkboxes)
        filled = await self.autofill_form_elements(target_scope, page)
        total_fields_filled += filled

        # Check for multi-step "Next" / "Continue"
        next_btn = target_scope.locator("button:has-text('Next'), button:has-text('Continue'), input[value='Next'], input[value='Continue']").first
        if await next_btn.count() > 0 and await next_btn.is_visible():
            submit_count = await target_scope.locator("button[type='submit'], input[type='submit'], button:has-text('Submit')").count()
            if submit_count == 0 or not await target_scope.locator("button:has-text('Submit')").first.is_visible():
                print("  Multi-step form detected! Proceeding to next step...", flush=True)
                await self.inject_hud(page, f"Portal: {company}", "Moving to Next Step...")
                await self.highlight_element(next_btn, "#38bdf8")
                await next_btn.click()
                await asyncio.sleep(2.5)
                # Fill second step
                filled_step2 = await self.autofill_form_elements(target_scope, page)
                total_fields_filled += filled_step2

        # ZERO-FILL GUARD: If zero fields were filled, try Browser-Use AI agent or safely abort
        if total_fields_filled == 0:
            # Check if Browser-Use AI Visual Fallback can resolve this custom form
            try:
                from career_site.browser_use_agent import AutonomousBrowserUseAgent
                bu_agent = AutonomousBrowserUseAgent(resume_type=self.resume_type)
                if bu_agent.is_ready():
                    print(f"  🧠 [AI Visual Fallback] Invoking Browser-Use Agent for {company}...", flush=True)
                    await self.inject_hud(page, f"AI Agent: {company}", "Activating Browser-Use Vision Agent...")
                    bu_res = await bu_agent.apply_on_portal(page.url, job_title, company)
                    if bu_res.get("success", False):
                        return bu_res
            except Exception as e:
                logger.debug(f"Browser-Use fallback error: {e}")

            print(f"  ⚠️ [Submission Aborted] No form fields were filled (0 fields filled). Skipping false submission.", flush=True)
            safe_company = re.sub(r'[^a-zA-Z0-9]', '_', company)[:20]
            safe_title = re.sub(r'[^a-zA-Z0-9]', '_', job_title)[:20]
            proof_path = str(self.proof_dir / f"UNFILLED_{safe_company}_{safe_title}_{int(time.time())}.png")
            try:
                await page.screenshot(path=proof_path)
            except Exception:
                pass
            return {
                "success": False,
                "status": "ZERO_FIELDS_FILLED",
                "proof": proof_path,
                "message": "Application form had 0 fields filled. Aborted submission to prevent false applied state."
            }

        # Submit Application (STRICTLY submit buttons, NEVER 'Apply Now')
        await self.inject_hud(page, f"Portal: {company}", f"Submitting ({total_fields_filled} fields filled)...")
        submit_btn = target_scope.locator(
            "button[type='submit'], input[type='submit'], button:has-text('Submit Application'), button:has-text('Submit'), button:has-text('Send Application'), button:has-text('Complete Application')"
        ).first
        return await self._click_submit_and_verify(page, submit_btn, company, job_title, fields_filled=total_fields_filled)

    async def autofill_form_elements(self, target: Any, page: Page) -> int:
        """
        Extracts semantic context for every visible input, textarea, select, and radio,
        and fills with verified candidate data without hallucination.
        Fires native DOM events for seamless React / Angular / Vue state binding.
        Returns total number of fields filled.
        """
        filled_count = 0

        # 1. TEXT INPUTS
        inputs = await target.locator(
            "input:not([type='hidden']):not([type='submit']):not([type='button']):not([type='reset']):not([type='file']):not([type='checkbox']):not([type='radio'])"
        ).all()

        for inp in inputs:
            try:
                if not await inp.is_visible():
                    continue

                # Check if already filled
                cur_val = await inp.input_value()
                if cur_val and len(cur_val.strip()) > 0:
                    continue

                ctx = await self._get_element_context(inp)
                matched_val = match_field_to_value(ctx, resume_type=self.resume_type)

                if not matched_val:
                    # Check if required
                    is_req = await inp.get_attribute("required") is not None
                    if is_req or "*" in ctx:
                        matched_val = await solver.solve_question(ctx, profile=self.profile)

                if matched_val:
                    await self.highlight_element(inp, "#10b981")
                    await inp.fill(str(matched_val))
                    # Trigger native input events for React/Angular bindings
                    try:
                        await inp.evaluate("(el) => { el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); }")
                    except Exception:
                        pass
                    print(f"    [Field Filled] '{ctx[:30]}...' -> {str(matched_val)[:25]}", flush=True)
                    filled_count += 1
                    await asyncio.sleep(0.1)
            except Exception as e:
                logger.debug(f"Error filling text input: {e}")

        # 2. TEXTAREAS (Screening questions, essays, cover letter)
        textareas = await target.locator("textarea").all()
        for ta in textareas:
            try:
                if not await ta.is_visible():
                    continue

                cur_val = await ta.input_value()
                if cur_val and len(cur_val.strip()) > 0:
                    continue

                ctx = await self._get_element_context(ta)
                matched_val = match_field_to_value(ctx, resume_type=self.resume_type)
                if not matched_val:
                    matched_val = await solver.solve_question(ctx, profile=self.profile)

                if matched_val:
                    await self.highlight_element(ta, "#10b981")
                    await ta.fill(str(matched_val))
                    try:
                        await ta.evaluate("(el) => { el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); }")
                    except Exception:
                        pass
                    print(f"    [Textarea Filled] '{ctx[:30]}...' -> {str(matched_val)[:30]}...", flush=True)
                    filled_count += 1
                    await asyncio.sleep(0.15)
            except Exception as e:
                logger.debug(f"Error filling textarea: {e}")

        # 3. SELECT DROPDOWNS
        selects = await target.locator("select").all()
        for sel in selects:
            try:
                if not await sel.is_visible():
                    continue

                ctx = await self._get_element_context(sel)
                if await self._handle_select_dropdown(sel, ctx):
                    filled_count += 1
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.debug(f"Error handling select: {e}")

        # 4. RADIO GROUPS (Yes/No questions e.g. Work Auth, Sponsorship)
        try:
            radios = await target.locator("input[type='radio']").all()
            for rad in radios:
                if not await rad.is_visible():
                    continue
                ctx = await self._get_element_context(rad)
                val_attr = (await rad.get_attribute("value") or "").lower()

                # If question is about authorization or relocation -> pick YES
                if any(k in ctx for k in ["authorized", "relocate", "18 years", "eligible"]):
                    if val_attr in ["yes", "true", "1"] or "yes" in ctx:
                        await rad.check()
                        filled_count += 1
                        await asyncio.sleep(0.1)
                # If question is about sponsorship or criminal record -> pick NO
                elif any(k in ctx for k in ["sponsorship", "require visa", "criminal", "felony", "backlog"]):
                    if val_attr in ["no", "false", "0"] or "no" in ctx:
                        await rad.check()
                        filled_count += 1
                        await asyncio.sleep(0.1)
        except Exception:
            pass

        # 5. MANDATORY CHECKBOXES (Terms / Consent / Privacy Policy)
        try:
            checkboxes = await target.locator("input[type='checkbox']").all()
            for cb in checkboxes:
                if not await cb.is_visible():
                    continue
                ctx = await self._get_element_context(cb)
                if any(k in ctx for k in ["agree", "consent", "terms", "policy", "certify", "acknowledge"]):
                    await cb.check()
                    filled_count += 1
                    await asyncio.sleep(0.1)
        except Exception:
            pass

        return filled_count

    async def _handle_select_dropdown(self, sel: Locator, ctx: str) -> bool:
        """Intelligently matches select options based on verified candidate knowledge base. Returns True if selected."""
        options = await sel.locator("option").all()
        if not options:
            return False

        opt_texts = []
        for o in options:
            txt = (await o.inner_text()).strip()
            if txt and not any(skip in txt.lower() for skip in ["select", "choose", "pick", "--"]):
                opt_texts.append(txt)

        if not opt_texts:
            return False

        ctx_lower = ctx.lower()
        target_val = None

        if "country" in ctx_lower or "nationality" in ctx_lower:
            target_val = "India"
        elif "gender" in ctx_lower:
            target_val = "Male"
        elif "notice" in ctx_lower or "availability" in ctx_lower:
            target_val = "Immediate"
        elif "degree" in ctx_lower or "education" in ctx_lower:
            target_val = "B.Tech"
        elif "passing" in ctx_lower or "graduation" in ctx_lower or "batch" in ctx_lower:
            target_val = "2026"
        elif "authorized" in ctx_lower or "relocate" in ctx_lower:
            target_val = "Yes"
        elif "sponsorship" in ctx_lower:
            target_val = "No"

        # Try selecting matching option
        if target_val:
            for opt in opt_texts:
                if target_val.lower() in opt.lower() or opt.lower() in target_val.lower():
                    await self.highlight_element(sel, "#10b981")
                    await sel.select_option(label=opt)
                    print(f"    [Select Chosen] '{ctx[:25]}' -> {opt}", flush=True)
                    return True

        # Fallback to LLM
        best = await solver.solve_question(ctx, options=opt_texts, profile=self.profile)
        if best:
            for opt in opt_texts:
                if best.lower() in opt.lower() or opt.lower() in best.lower():
                    await self.highlight_element(sel, "#10b981")
                    await sel.select_option(label=opt)
                    print(f"    [Select Chosen (AI)] '{ctx[:25]}' -> {opt}", flush=True)
                    return True

        return False

    async def _get_element_context(self, el: Locator) -> str:
        """Extracts comprehensive semantic context (labels, placeholders, IDs) for an element."""
        js_get_ctx = """(element) => {
            let parts = [];
            if (element.name) parts.push(element.name);
            if (element.id) parts.push(element.id);
            if (element.type) parts.push(element.type);
            if (element.placeholder) parts.push(element.placeholder);
            if (element.getAttribute('aria-label')) parts.push(element.getAttribute('aria-label'));
            if (element.getAttribute('title')) parts.push(element.getAttribute('title'));
            
            // Check label[for]
            if (element.id) {
                let lbl = document.querySelector(`label[for="${element.id}"]`);
                if (lbl) parts.push(lbl.innerText);
            }
            // Check closest parent label
            let parentLabel = element.closest('label');
            if (parentLabel) parts.push(parentLabel.innerText);
            
            // Check preceding sibling
            let prev = element.previousElementSibling;
            if (prev && (prev.tagName === 'LABEL' || prev.tagName === 'SPAN' || prev.tagName === 'P')) {
                parts.push(prev.innerText);
            }
            
            // Walk up to 4 parent elements to capture <p>, <label>, <span>, <div> labels
            let p = element.parentElement;
            let depth = 0;
            while (p && depth < 4) {
                let candidates = p.querySelectorAll('label, p, span, div, b, strong');
                for (let c of candidates) {
                    if (c !== element && !c.contains(element)) {
                        let txt = (c.innerText || '').trim();
                        if (txt && txt.length > 1 && txt.length < 80 && !parts.includes(txt)) {
                            parts.push(txt);
                        }
                    }
                }
                p = p.parentElement;
                depth++;
            }
            
            return parts.join(' ').toLowerCase().trim();
        }"""
        try:
            return await el.evaluate(js_get_ctx)
        except Exception:
            return ""

    async def _click_submit_and_verify(
        self,
        page: Page,
        submit_btn: Locator,
        company: str,
        job_title: str,
        fields_filled: int = 1
    ) -> Dict[str, Any]:
        """
        Clicks Submit and executes deterministic multi-signal verification:
        1. Checks for CAPTCHA
        2. Clicks Submit
        3. Actively polls for confirmation signals (URL change, confirmation banner, form dismissal)
        4. Detects validation errors that blocked submission
        5. Does NOT mark as applied unless verified!
        """
        safe_company = re.sub(r'[^a-zA-Z0-9]', '_', company)[:20]
        safe_title = re.sub(r'[^a-zA-Z0-9]', '_', job_title)[:20]
        timestamp = int(time.time())
        proof_path = str(self.proof_dir / f"{safe_company}_{safe_title}_{timestamp}.png")

        # Guard: If no fields were filled, abort immediately!
        if fields_filled == 0:
            print("  ⚠️ Verification Refused: 0 form fields were filled.", flush=True)
            await page.screenshot(path=proof_path)
            return {
                "success": False,
                "status": "ZERO_FIELDS_FILLED",
                "proof": proof_path,
                "message": "Aborted: Zero fields were filled on the form."
            }

        if await submit_btn.count() == 0 or not await submit_btn.is_visible():
            await page.screenshot(path=proof_path)
            return {
                "success": False,
                "status": "NO_SUBMIT_BUTTON",
                "proof": proof_path,
                "message": "Submit button not visible or already submitted."
            }

        # Check for CAPTCHA before submitting
        captcha_el = page.locator("iframe[src*='recaptcha'], iframe[src*='hcaptcha'], div.cf-turnstile, div[class*='captcha']").first
        if await captcha_el.count() > 0 and await captcha_el.is_visible():
            print("  ⚠️ Anti-Bot / CAPTCHA detected on career page! Waiting up to 25s for resolution...", flush=True)
            await self.inject_hud(page, "⚠️ CAPTCHA Detected!", "Please solve the captcha on screen. Waiting 25s...")
            for _ in range(12):
                await asyncio.sleep(2)
                if not await captcha_el.is_visible():
                    break

        await self.highlight_element(submit_btn, "#06b6d4")
        print("  Clicking Submit Application button...", flush=True)
        initial_url = page.url

        try:
            await submit_btn.click()
        except Exception:
            try:
                await submit_btn.click(force=True)
            except Exception as ex:
                logger.error(f"Failed clicking submit: {ex}")

        # Active Submission Verification Loop (up to 25 seconds)
        confirmed = False
        error_msg = ""

        print("  Verifying application submission with live server...", flush=True)
        for elapsed in range(1, 26):
            await asyncio.sleep(1)

            # Check 1: URL change away from form to confirmation page
            cur_url = page.url.lower()
            if cur_url != initial_url.lower() and any(kw in cur_url for kw in ["confirm", "thank", "success", "submitted", "done", "complete", "applied", "status"]):
                confirmed = True
                print(f"  ✔ Confirmation Signal 1: Redirected to confirmed URL ({cur_url})", flush=True)
                break

            # Check 2: DOM confirmation messages or banners
            try:
                page_text = (await page.content()).lower()
                confirmation_keywords = [
                    "thank you for applying", "application submitted", "successfully submitted",
                    "we have received your application", "application received", "thanks for applying",
                    "submission confirmed", "your application has been sent", "application has been submitted",
                    "we've received your application", "thank you for your interest"
                ]
                if any(kw in page_text for kw in confirmation_keywords):
                    confirmed = True
                    print(f"  ✔ Confirmation Signal 2: Confirmation banner verified in DOM", flush=True)
                    break
            except Exception:
                pass

            # Check 3: Check for form validation errors that blocked submission
            try:
                error_loc = page.locator("div.error, span.error, [class*='error-message'], .has-error, [aria-invalid='true'], div.field-validation-error, div.alert-danger").first
                if await error_loc.count() > 0 and await error_loc.is_visible():
                    err_text = (await error_loc.inner_text()).strip()
                    if err_text and ("require" in err_text.lower() or "invalid" in err_text.lower() or "error" in err_text.lower()):
                        error_msg = f"Form validation error: {err_text}"
                        print(f"  ⚠️ Submission blocked by validation error: {err_text}", flush=True)
                        break
            except Exception:
                pass

            # Check 4: Check if form disappeared after submit (ONLY if fields were filled and positive signal exists)
            if elapsed >= 6 and fields_filled > 0 and not error_msg:
                try:
                    remaining_inputs = await page.locator("input:not([type='hidden']), textarea").all()
                    visible_inputs = [i for i in remaining_inputs if await i.is_visible()]
                    if len(visible_inputs) == 0:
                        cur_url = page.url.lower()
                        page_body = (await page.content()).lower()
                        if cur_url != initial_url.lower() or any(w in page_body for w in ["thank", "success", "received", "submitted", "confirmed", "appreciate", "status"]):
                            confirmed = True
                            print(f"  ✔ Confirmation Signal 3: Form inputs cleared and server confirmation detected", flush=True)
                            break
                except Exception:
                    pass

            if elapsed % 5 == 0:
                await self.inject_hud(page, f"Verifying Submission ({company})...", f"Checking server response ({elapsed}s/25s)")

        await page.screenshot(path=proof_path)

        if confirmed:
            await self.inject_hud(page, "✔ APPLICATION VERIFIED!", "Submission confirmed and proof saved.")
            return {
                "success": True,
                "status": "VERIFIED_APPLIED",
                "proof": proof_path,
                "message": "Application submitted and verified successfully."
            }

        await self.inject_hud(page, "⚠️ SUBMISSION UNVERIFIED", error_msg or "Server confirmation not detected.")
        return {
            "success": False,
            "status": "VALIDATION_FAILED" if error_msg else "UNVERIFIED",
            "proof": proof_path,
            "message": error_msg or "Form submitted but server confirmation could not be verified within 25s."
        }
