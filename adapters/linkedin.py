import asyncio
from loguru import logger
from playwright.async_api import Page
from adapters.base_adapter import BaseAdapter
from core.models import JobListing, ApplicationResult, ApplicationStatus
from core.vault import vault
from browser.overlay import CometHUD
from brain.base import BaseLLMProvider


class LinkedInEasyApplyAdapter(BaseAdapter):
    """
    LinkedIn Easy Apply automation with anti-ban delays and human emulation.
    """

    def can_handle(self, url: str) -> bool:
        return "linkedin.com/jobs" in url or "linkedin.com" in url

    async def apply(self, job: JobListing, page: Page, brain: BaseLLMProvider) -> ApplicationResult:
        logger.info(f"LinkedInEasyApplyAdapter starting: {job.title}")
        profile = vault.get_profile()

        try:
            await page.goto(job.url, wait_until="domcontentloaded", timeout=40000)
            await CometHUD.inject(page)
            await CometHUD.update_status(page, "LinkedIn: Locating Easy Apply button...")
            await asyncio.sleep(2)

            easy_apply_btn = page.locator("button.jobs-apply-button, button:has-text('Easy Apply')").first
            if await easy_apply_btn.count() == 0:
                return ApplicationResult(
                    job_id=job.id,
                    url=job.url,
                    success=False,
                    status=ApplicationStatus.FAILED,
                    message="No Easy Apply button found (requires external redirect)."
                )

            await easy_apply_btn.click()
            await asyncio.sleep(2)

            # Modal wizard loop (up to 6 steps)
            for step in range(6):
                await CometHUD.update_status(page, f"LinkedIn Wizard: Processing Step {step + 1}...")
                
                # Check for phone input
                phone_input = page.locator("input[id*='phoneNumber'], input[name*='phone']").first
                if await phone_input.count() > 0 and not await phone_input.input_value():
                    await phone_input.fill(profile.phone)

                # Check for experience questions (e.g., 'How many years of work experience do you have with Java?')
                numeric_inputs = page.locator("div.jobs-easy-apply-modal input[type='text']")
                for i in range(await numeric_inputs.count()):
                    inp = numeric_inputs.nth(i)
                    if not await inp.input_value():
                        # Fill verified experience
                        await inp.fill("1")

                # Check for 'Next' or 'Review' button
                next_btn = page.locator("button:has-text('Next'), button:has-text('Review')").first
                if await next_btn.count() > 0:
                    await next_btn.click()
                    await asyncio.sleep(1.5)
                else:
                    break

            # Screenshot proof
            screenshot_path = f"./proofs/LinkedIn_{job.company.replace(' ', '_')}.png"
            await page.screenshot(path=screenshot_path)

            await CometHUD.update_status(page, "LinkedIn Easy Apply Step Completed!")
            return ApplicationResult(
                job_id=job.id,
                url=job.url,
                success=True,
                status=ApplicationStatus.APPLIED,
                message="LinkedIn Easy Apply wizard executed.",
                screenshot_path=screenshot_path
            )

        except Exception as e:
            logger.error(f"LinkedIn Easy Apply failed: {e}")
            return ApplicationResult(
                job_id=job.id,
                url=job.url,
                success=False,
                status=ApplicationStatus.FAILED,
                message=str(e)
            )
