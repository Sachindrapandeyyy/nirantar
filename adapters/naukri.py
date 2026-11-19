import asyncio
from loguru import logger
from playwright.async_api import Page
from adapters.base_adapter import BaseAdapter
from core.models import JobListing, ApplicationResult, ApplicationStatus
from core.vault import vault
from browser.overlay import CometHUD
from brain.base import BaseLLMProvider


class NaukriAdapter(BaseAdapter):
    """
    Automates 1-Click and Questionnaire applications on Naukri.com.
    """

    def can_handle(self, url: str) -> bool:
        return "naukri.com" in url

    async def apply(self, job: JobListing, page: Page, brain: BaseLLMProvider) -> ApplicationResult:
        logger.info(f"NaukriAdapter processing {job.title}")
        profile = vault.get_profile()

        try:
            await page.goto(job.url, wait_until="domcontentloaded", timeout=40000)
            await CometHUD.inject(page)
            await CometHUD.update_status(page, "Naukri: Checking Apply button...")
            await asyncio.sleep(2)

            apply_btn = page.locator("button.apply-button, button:has-text('Apply on company site'), button:has-text('Apply')").first
            if await apply_btn.count() == 0:
                return ApplicationResult(
                    job_id=job.id,
                    url=job.url,
                    success=False,
                    status=ApplicationStatus.FAILED,
                    message="Naukri: No direct apply button located."
                )

            await apply_btn.click()
            await asyncio.sleep(2)

            # Check for chatbot / questionnaire popup
            chatbot_input = page.locator("input.chatbot-input, input[placeholder*='Type your answer']")
            if await chatbot_input.count() > 0:
                await CometHUD.update_status(page, "Answering Naukri Bot questionnaire...")
                # Bot typically asks for notice period or CTC
                await chatbot_input.first.fill(profile.salary.notice_period_text)
                await page.keyboard.press("Enter")
                await asyncio.sleep(1.5)

            screenshot_path = f"./proofs/Naukri_{job.company.replace(' ', '_')}.png"
            await page.screenshot(path=screenshot_path)

            return ApplicationResult(
                job_id=job.id,
                url=job.url,
                success=True,
                status=ApplicationStatus.APPLIED,
                message="Successfully applied on Naukri.",
                screenshot_path=screenshot_path
            )

        except Exception as e:
            logger.error(f"Naukri apply failed: {e}")
            return ApplicationResult(
                job_id=job.id,
                url=job.url,
                success=False,
                status=ApplicationStatus.FAILED,
                message=str(e)
            )
