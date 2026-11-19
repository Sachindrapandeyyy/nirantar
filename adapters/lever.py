import asyncio
from loguru import logger
from playwright.async_api import Page
from adapters.base_adapter import BaseAdapter
from core.models import JobListing, ApplicationResult, ApplicationStatus
from core.vault import vault
from browser.overlay import CometHUD
from brain.base import BaseLLMProvider


class LeverAdapter(BaseAdapter):
    """
    Automates applications on Lever.co career portals.
    """

    def can_handle(self, url: str) -> bool:
        return "lever.co" in url or "jobs.lever.co" in url

    async def apply(self, job: JobListing, page: Page, brain: BaseLLMProvider) -> ApplicationResult:
        logger.info(f"LeverAdapter processing {job.company} - {job.title}")
        profile = vault.get_profile()

        try:
            # Ensure URL points to /apply
            apply_url = job.url.rstrip("/") + "/apply" if not job.url.endswith("/apply") else job.url
            await page.goto(apply_url, wait_until="domcontentloaded", timeout=40000)
            await CometHUD.inject(page)
            await CometHUD.update_status(page, f"Target: {job.company} (Lever) | Filling fields...")
            await asyncio.sleep(1.5)

            # Name, Email, Phone
            if await page.locator("input[name='name']").count() > 0:
                await page.locator("input[name='name']").fill(profile.full_name)
            if await page.locator("input[name='email']").count() > 0:
                await page.locator("input[name='email']").fill(profile.email)
            if await page.locator("input[name='phone']").count() > 0:
                await page.locator("input[name='phone']").fill(profile.phone)

            # Current Company / Education
            if await page.locator("input[name='org']").count() > 0:
                recent_exp = profile.experience[0].company if profile.experience else profile.education[0].institution
                await page.locator("input[name='org']").fill(recent_exp)

            # Links
            if await page.locator("input[name='urls[LinkedIn]']").count() > 0:
                await page.locator("input[name='urls[LinkedIn]']").fill(profile.linkedin_url)
            if await page.locator("input[name='urls[GitHub]']").count() > 0:
                await page.locator("input[name='urls[GitHub]']").fill(profile.github_url)
            if await page.locator("input[name='urls[Portfolio]']").count() > 0 and profile.portfolio_url:
                await page.locator("input[name='urls[Portfolio]']").fill(profile.portfolio_url)

            # Resume upload
            await CometHUD.update_status(page, f"Uploading {job.match_result.resume_type.upper()} Resume...")
            resume_path = vault.get_resume(job.match_result.resume_type if job.match_result else "java")
            if resume_path and resume_path.exists():
                file_input = page.locator("input[type='file']").first
                if await file_input.count() > 0:
                    await file_input.set_input_files(str(resume_path))
                    await asyncio.sleep(2)

            # CTC questions strictly answered only if present
            ctc_inputs = page.locator("input[name*='salary'], input[name*='compensation'], input[name*='ctc']")
            if await ctc_inputs.count() > 0:
                await ctc_inputs.first.fill(str(int(profile.salary.expected_ctc)))

            screenshot_path = f"./proofs/{job.company.replace(' ', '_')}_{job.title.replace(' ', '_')}.png"
            await page.screenshot(path=screenshot_path)

            await CometHUD.update_status(page, "Lever Form Completed!")
            await asyncio.sleep(2)

            return ApplicationResult(
                job_id=job.id,
                url=job.url,
                success=True,
                status=ApplicationStatus.APPLIED,
                message="Successfully filled Lever application.",
                screenshot_path=screenshot_path
            )

        except Exception as e:
            logger.error(f"LeverAdapter error on {job.url}: {e}")
            return ApplicationResult(
                job_id=job.id,
                url=job.url,
                success=False,
                status=ApplicationStatus.FAILED,
                message=str(e)
            )
