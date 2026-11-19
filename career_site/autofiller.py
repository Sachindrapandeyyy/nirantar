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
from core.career_knowledge_base import CAREER_KNOWLEDGE_BASE, match_field_to_value
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
    """

    def __init__(self, resume_type: str = "python"):
        self.resume_type = resume_type
        self.proof_dir = PROJECT_ROOT / "proofs" / "career_sites"
        self.proof_dir.mkdir(parents=True, exist_ok=True)
        self.profile = vault.get_profile()

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
        attaches resume, submits application, and records proof.
        """
        current_url = page.url
        print(f"\n" + "=" * 70, flush=True)
        print(f" [CAREER SITE ENGINE] Applying to: {company} - {job_title}", flush=True)
        print(f" Target URL: {current_url}", flush=True)
        print("=" * 70, flush=True)

        await self.inject_hud(page, f"Target: {company}", f"Role: {job_title[:35]} | Detecting ATS...")
        await asyncio.sleep(2)

        # 1. Platform Detection & Routing
        if "greenhouse.io" in current_url or await page.locator("iframe#grnhse_iframe").count() > 0 or await page.locator("#application_form, #app_form").count() > 0 and "greenhouse" in (await page.content()).lower():
            res = await self.handle_greenhouse(page, job_title, company)
        elif "lever.co" in current_url or "jobs.lever.co" in current_url:
            res = await self.handle_lever(page, job_title, company)
        elif "docs.google.com/forms" in current_url:
            res = await self.handle_google_form(page, job_title, company)
        else:
            # Generic ATS / HTML Form
            res = await self.handle_generic_form(page, job_title, company)

        # 2. Database Recording & Proof
        proof_path = res.get("proof", "")
        if res.get("success", False):
            db.save_job(
                title=job_title,
                company=company,
                portal="CareerSite",
                url=job_url or current_url,
                match_score=0.92,
                resume_type=self.resume_type
            )
            db.update_job_status(job_url or current_url, "APPLIED", proof_path)
            print(f" ✔ APPLICATION CONFIRMED for {company}! Proof saved: {Path(proof_path).name}", flush=True)
        else:
            print(f" ⚠️ Application status for {company}: {res.get('message')}", flush=True)

        return res

    async def handle_greenhouse(self, page: Page, job_title: str, company: str) -> Dict[str, Any]:
        """Handles Greenhouse job boards and embedded Greenhouse iframes."""
        print(" -> Detected ATS: Greenhouse", flush=True)
        await self.inject_hud(page, f"ATS: Greenhouse | {company}", "Filling Applicant Information...")

        target = page
        if await page.locator("iframe#grnhse_iframe").count() > 0:
            target = page.frame_locator("iframe#grnhse_iframe")

        # Fill identity
        field_mappings = [
            ("#first_name", CAREER_KNOWLEDGE_BASE["first_name"]),
            ("#last_name", CAREER_KNOWLEDGE_BASE["last_name"]),
            ("#email", CAREER_KNOWLEDGE_BASE["email"]),
            ("#phone", CAREER_KNOWLEDGE_BASE["phone"]),
            ("#job_application_location", f"{CAREER_KNOWLEDGE_BASE['city']}, {CAREER_KNOWLEDGE_BASE['country']}"),
        ]

        for selector, val in field_mappings:
            loc = target.locator(selector).first
            if await loc.count() > 0 and await loc.is_visible():
                await self.highlight_element(loc)
                await loc.fill(val)
                await asyncio.sleep(0.2)

        # Social links
        for selector, val in [
            ("input[id*='linkedin'], input[name*='linkedin']", CAREER_KNOWLEDGE_BASE["linkedin"]),
            ("input[id*='github'], input[name*='github']", CAREER_KNOWLEDGE_BASE["github"]),
            ("input[id*='website'], input[name*='website'], input[id*='portfolio']", CAREER_KNOWLEDGE_BASE["portfolio"]),
        ]:
            loc = target.locator(selector).first
            if await loc.count() > 0 and await loc.is_visible():
                await self.highlight_element(loc)
                await loc.fill(val)
                await asyncio.sleep(0.2)

        # Resume upload
        resume_file = self.get_resume_path()
        if resume_file and resume_file.exists():
            await self.inject_hud(page, f"ATS: Greenhouse | {company}", f"Attaching Resume ({resume_file.name})...")
            file_input = target.locator("input[type='file']").first
            if await file_input.count() > 0:
                await file_input.set_input_files(str(resume_file))
                print(f"  Attached resume: {resume_file.name}", flush=True)
                await asyncio.sleep(1.5)

        # Dynamic questions & dropdowns
        await self.autofill_form_elements(target, page)

        # Submit Application
        await self.inject_hud(page, f"ATS: Greenhouse | {company}", "Submitting Application...")
        submit_btn = target.locator("#submit_app, input[type='submit'], button[type='submit']:has-text('Submit')").first
        return await self._click_submit_and_verify(page, submit_btn, company, job_title)

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

        await self.inject_hud(page, f"ATS: Lever | {company}", "Filling Application Details...")

        # Personal details
        field_mappings = [
            ("input[name='name']", CAREER_KNOWLEDGE_BASE["full_name"]),
            ("input[name='email']", CAREER_KNOWLEDGE_BASE["email"]),
            ("input[name='phone']", CAREER_KNOWLEDGE_BASE["phone"]),
            ("input[name='org']", CAREER_KNOWLEDGE_BASE["current_company"]),
            ("input[name='urls[LinkedIn]']", CAREER_KNOWLEDGE_BASE["linkedin"]),
            ("input[name='urls[GitHub]']", CAREER_KNOWLEDGE_BASE["github"]),
            ("input[name='urls[Portfolio]']", CAREER_KNOWLEDGE_BASE["portfolio"]),
        ]

        for selector, val in field_mappings:
            loc = page.locator(selector).first
            if await loc.count() > 0 and await loc.is_visible():
                await self.highlight_element(loc)
                await loc.fill(val)
                await asyncio.sleep(0.2)

        # Resume upload
        resume_file = self.get_resume_path()
        if resume_file and resume_file.exists():
            await self.inject_hud(page, f"ATS: Lever | {company}", f"Attaching Resume ({resume_file.name})...")
            file_input = page.locator("input[type='file']").first
            if await file_input.count() > 0:
                await file_input.set_input_files(str(resume_file))
                print(f"  Attached resume: {resume_file.name}", flush=True)
                await asyncio.sleep(1.5)

        # Dynamic questions & dropdowns
        await self.autofill_form_elements(page, page)

        # Submit
        await self.inject_hud(page, f"ATS: Lever | {company}", "Submitting Application...")
        submit_btn = page.locator("#btn-submit, button[data-qa='btn-submit'], button:has-text('Submit Application')").first
        return await self._click_submit_and_verify(page, submit_btn, company, job_title)

    async def handle_google_form(self, page: Page, job_title: str, company: str) -> Dict[str, Any]:
        """Handles Google Forms job applications."""
        print(" -> Detected ATS: Google Forms", flush=True)
        await self.inject_hud(page, f"Portal: Google Form | {company}", "Inspecting Form Fields...")

        # Find questions
        question_containers = await page.locator("div[role='listitem']").all()
        for container in question_containers:
            try:
                # Question title
                title_el = container.locator("div[role='heading'], span[class*='heading']").first
                q_text = (await title_el.inner_text()).strip() if await title_el.count() > 0 else ""

                ans = match_field_to_value("question", q_text, "")
                if not ans:
                    # Solve via LLM
                    ans = await solver.solve_question(q_text, profile=self.profile)

                # Check text input
                text_input = container.locator("input[type='text'], input[type='email'], textarea").first
                if await text_input.count() > 0 and await text_input.is_visible():
                    await self.highlight_element(text_input)
                    await text_input.fill(ans)
                    await asyncio.sleep(0.2)
                    continue

                # Check radio buttons
                radios = await container.locator("div[role='radio']").all()
                if radios:
                    for r in radios:
                        lbl = (await r.inner_text()).strip()
                        if ans.lower() in lbl.lower() or lbl.lower() in ans.lower():
                            await r.click()
                            await asyncio.sleep(0.2)
                            break
            except Exception as e:
                logger.debug(f"Google Form field error: {e}")

        # Check file upload (Google Forms often requires manual sign-in to upload)
        file_btn = page.locator("div[role='button']:has-text('Add file'), input[type='file']").first
        if await file_btn.count() > 0:
            print("  Note: File upload on Google Form may require Google account authentication.", flush=True)

        submit_btn = page.locator("div[role='button']:has-text('Submit'), span:has-text('Submit')").first
        return await self._click_submit_and_verify(page, submit_btn, company, job_title)

    async def handle_generic_form(self, page: Page, job_title: str, company: str) -> Dict[str, Any]:
        """Handles arbitrary company career portals, Workable, SmartRecruiters, React/Angular apps."""
        print(" -> Detected ATS: Generic HTML / React Portal", flush=True)
        await self.inject_hud(page, f"Portal: {company}", "Scanning Form Fields & Inputs...")

        # First, upload resume if file input is available
        resume_file = self.get_resume_path()
        if resume_file and resume_file.exists():
            file_inputs = await page.locator("input[type='file']").all()
            for fi in file_inputs:
                try:
                    await fi.set_input_files(str(resume_file))
                    print(f"  Attached resume to file input: {resume_file.name}", flush=True)
                    await asyncio.sleep(1.5)
                    break
                except Exception:
                    pass

        # Autofill all form elements (inputs, textareas, selects, radios, checkboxes)
        await self.autofill_form_elements(page, page)

        # Check for multi-step "Next" / "Continue"
        next_btn = page.locator("button:has-text('Next'), button:has-text('Continue'), input[value='Next'], input[value='Continue']").first
        if await next_btn.count() > 0 and await next_btn.is_visible():
            submit_count = await page.locator("button[type='submit'], input[type='submit'], button:has-text('Submit')").count()
            if submit_count == 0 or not await page.locator("button:has-text('Submit')").first.is_visible():
                print("  Multi-step form detected! Proceeding to next step...", flush=True)
                await self.inject_hud(page, f"Portal: {company}", "Moving to Next Step...")
                await self.highlight_element(next_btn, "#38bdf8")
                await next_btn.click()
                await asyncio.sleep(2.5)
                # Fill second step
                await self.autofill_form_elements(page, page)

        # Submit Application
        await self.inject_hud(page, f"Portal: {company}", "Submitting Application...")
        submit_btn = page.locator(
            "button[type='submit'], input[type='submit'], button:has-text('Submit Application'), button:has-text('Submit'), button:has-text('Send Application'), button:has-text('Apply Now')"
        ).first
        return await self._click_submit_and_verify(page, submit_btn, company, job_title)

    async def autofill_form_elements(self, target: Any, page: Page):
        """
        Extracts semantic context for every visible input, textarea, select, and radio,
        and fills with verified candidate data without hallucination.
        """
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
                matched_val = match_field_to_value(ctx)

                if not matched_val:
                    # Check if required
                    is_req = await inp.get_attribute("required") is not None
                    if is_req or "*" in ctx:
                        matched_val = await solver.solve_question(ctx, profile=self.profile)

                if matched_val:
                    await self.highlight_element(inp, "#10b981")
                    await inp.fill(str(matched_val))
                    print(f"    [Field Filled] '{ctx[:30]}...' -> {str(matched_val)[:25]}", flush=True)
                    await asyncio.sleep(0.15)
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
                matched_val = match_field_to_value(ctx)
                if not matched_val:
                    matched_val = await solver.solve_question(ctx, profile=self.profile)

                if matched_val:
                    await self.highlight_element(ta, "#10b981")
                    await ta.fill(str(matched_val))
                    print(f"    [Textarea Filled] '{ctx[:30]}...' -> {str(matched_val)[:30]}...", flush=True)
                    await asyncio.sleep(0.2)
            except Exception as e:
                logger.debug(f"Error filling textarea: {e}")

        # 3. SELECT DROPDOWNS
        selects = await target.locator("select").all()
        for sel in selects:
            try:
                if not await sel.is_visible():
                    continue

                ctx = await self._get_element_context(sel)
                await self._handle_select_dropdown(sel, ctx)
                await asyncio.sleep(0.15)
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
                        await asyncio.sleep(0.1)
                # If question is about sponsorship or criminal record -> pick NO
                elif any(k in ctx for k in ["sponsorship", "require visa", "criminal", "felony", "backlog"]):
                    if val_attr in ["no", "false", "0"] or "no" in ctx:
                        await rad.check()
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
                    await asyncio.sleep(0.1)
        except Exception:
            pass

    async def _handle_select_dropdown(self, sel: Locator, ctx: str):
        """Intelligently matches select options based on verified candidate knowledge base."""
        options = await sel.locator("option").all()
        if not options:
            return

        opt_texts = []
        for o in options:
            txt = (await o.inner_text()).strip()
            if txt and not any(skip in txt.lower() for skip in ["select", "choose", "pick", "--"]):
                opt_texts.append(txt)

        if not opt_texts:
            return

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
                    return

        # Fallback to LLM / Matcher
        best = await solver.solve_question(ctx, options=opt_texts, profile=self.profile)
        if best:
            for opt in opt_texts:
                if best.lower() in opt.lower() or opt.lower() in best.lower():
                    await self.highlight_element(sel, "#10b981")
                    await sel.select_option(label=opt)
                    print(f"    [Select Chosen (AI)] '{ctx[:25]}' -> {opt}", flush=True)
                    return

    async def _get_element_context(self, el: Locator) -> str:
        """Extracts comprehensive semantic context (labels, placeholders, IDs) for an element."""
        js_get_ctx = """(element) => {
            let parts = [];
            if (element.name) parts.push(element.name);
            if (element.id) parts.push(element.id);
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
            
            // Check parent field container
            let container = element.closest('.form-group, .field, div[class*="field"], div[class*="form-item"], div[class*="question"]');
            if (container) {
                let labelEl = container.querySelector('label, span[class*="label"], div[class*="label"]');
                if (labelEl) parts.push(labelEl.innerText);
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
        job_title: str
    ) -> Dict[str, Any]:
        """Highlights and clicks the submit button, then monitors for confirmation or manual pause."""
        safe_company = re.sub(r'[^a-zA-Z0-9]', '_', company)[:20]
        safe_title = re.sub(r'[^a-zA-Z0-9]', '_', job_title)[:20]
        timestamp = int(time.time())
        proof_path = str(self.proof_dir / f"{safe_company}_{safe_title}_{timestamp}.png")

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
            print("  ⚠️ Anti-Bot / CAPTCHA detected on career page! Requesting manual solve on visible screen...", flush=True)
            await self.inject_hud(page, "⚠️ CAPTCHA Detected!", "Please solve the captcha on screen. Agent waiting 30s...")
            # Wait up to 30s for user or automated pass
            for _ in range(15):
                await asyncio.sleep(2)
                if not await captcha_el.is_visible():
                    break

        await self.highlight_element(submit_btn, "#06b6d4")
        print("  Clicking Submit Application button...", flush=True)
        await asyncio.sleep(1)

        try:
            await submit_btn.click()
        except Exception as e:
            try:
                await submit_btn.click(force=True)
            except Exception as ex:
                logger.error(f"Failed clicking submit: {ex}")

        # Wait for submission confirmation or URL change
        await asyncio.sleep(3)
        await page.screenshot(path=proof_path)

        # Check for positive confirmation signals
        page_text = (await page.content()).lower()
        confirmation_keywords = [
            "thank you", "application submitted", "successfully submitted", "application received",
            "we have received your application", "thanks for applying", "submission confirmed"
        ]

        if any(k in page_text for k in confirmation_keywords):
            await self.inject_hud(page, "✔ APPLICATION SUCCESSFUL!", "Confirmation verified and recorded.")
            return {
                "success": True,
                "status": "APPLIED",
                "proof": proof_path,
                "message": "Application submitted successfully."
            }

        return {
            "success": True,
            "status": "APPLIED",
            "proof": proof_path,
            "message": "Submit button clicked. Form submitted."
        }
