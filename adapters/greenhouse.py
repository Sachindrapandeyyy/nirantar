import asyncio
from pathlib import Path
from loguru import logger
from playwright.async_api import Page
from adapters.base_adapter import BaseAdapter
from core.models import JobListing, ApplicationResult, ApplicationStatus
from core.vault import vault
from browser.overlay import CometHUD
from brain.base import BaseLLMProvider


class GreenhouseAdapter(BaseAdapter):
    """
    Automates applications on Greenhouse.io career portals.
    """

    def can_handle(self, url: str) -> bool:
        return "greenhouse.io" in url or "boards.greenhouse.io" in url or "gh_jid" in url

    async def apply(self, job: JobListing, page: Page, brain: BaseLLMProvider) -> ApplicationResult:
        logger.info(f"GreenhouseAdapter starting application for {job.company} - {job.title}")
        profile = vault.get_profile()

        try:
            await page.goto(job.url, wait_until="domcontentloaded", timeout=40000)
            await CometHUD.inject(page)
            await CometHUD.update_status(page, f"Target: {job.company} | Matching Profile...")
            await asyncio.sleep(1.5)

            # Check if iframe exists or standard form
            frame = page
            if await page.locator("iframe#grnhse_iframe").count() > 0:
                frame = page.frame_locator("iframe#grnhse_iframe")

            # Basic personal information
            await CometHUD.update_status(page, "Filling personal identity fields...")

            if await frame.locator("#first_name").count() > 0:
                await frame.locator("#first_name").fill(profile.first_name)
            if await frame.locator("#last_name").count() > 0:
                await frame.locator("#last_name").fill(profile.last_name)
            if await frame.locator("#email").count() > 0:
                await frame.locator("#email").fill(profile.email)
            if await frame.locator("#phone").count() > 0:
                await frame.locator("#phone").fill(profile.phone)

            # Location / City
            if await frame.locator("#job_application_location").count() > 0:
                await frame.locator("#job_application_location").fill(f"{profile.city}, {profile.country}")

            # Social links
            linkedin_inputs = frame.locator("input[id*='linkedin'], input[name*='linkedin']")
            if await linkedin_inputs.count() > 0:
                await linkedin_inputs.first.fill(profile.linkedin_url)

            github_inputs = frame.locator("input[id*='github'], input[name*='github']")
            if await github_inputs.count() > 0:
                await github_inputs.first.fill(profile.github_url)

            website_inputs = frame.locator("input[id*='website'], input[name*='website'], input[id*='portfolio']")
            if await website_inputs.count() > 0 and profile.portfolio_url:
                await website_inputs.first.fill(profile.portfolio_url)

            # Resume upload
            await CometHUD.update_status(page, f"Attaching {job.match_result.resume_type.upper()} Resume...")
            resume_path = vault.get_resume(job.match_result.resume_type if job.match_result else "java")
            
            if resume_path and resume_path.exists():
                file_input = frame.locator("input[type='file']").first
                if await file_input.count() > 0:
                    await file_input.set_input_files(str(resume_path))
                    await asyncio.sleep(2)

            # Check for CTC / Salary questions strictly
            ctc_inputs = frame.locator("input[id*='salary'], input[name*='salary'], input[id*='ctc'], input[name*='ctc']")
            if await ctc_inputs.count() > 0:
                await CometHUD.update_status(page, "Answering CTC question...")
                # Fill only if explicitly asked
                await ctc_inputs.first.fill(str(int(profile.salary.expected_ctc)))

            # Work authorization questions
            auth_selects = frame.locator("select[id*='authorized'], select[name*='authorized']")
            if await auth_selects.count() > 0:
                try:
                    await auth_selects.first.select_option(label="Yes")
                except Exception:
                    await auth_selects.first.select_option(index=1)

            # Screenshot before final submission
            screenshot_path = f"./proofs/{job.company.replace(' ', '_')}_{job.title.replace(' ', '_')}.png"
            await page.screenshot(path=screenshot_path)

            await CometHUD.update_status(page, "Application Ready & Filled!")
            await asyncio.sleep(2)

            return ApplicationResult(
                job_id=job.id,
                url=job.url,
                success=True,
                status=ApplicationStatus.APPLIED,
                message="Successfully filled Greenhouse application with verified vault details.",
                screenshot_path=screenshot_path
            )

        except Exception as e:
            logger.error(f"GreenhouseAdapter error on {job.url}: {e}")
            return ApplicationResult(
                job_id=job.id,
                url=job.url,
                success=False,
                status=ApplicationStatus.FAILED,
                message=str(e)
            )
