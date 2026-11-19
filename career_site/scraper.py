import asyncio
import re
import sys
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger
from playwright.async_api import Page, BrowserContext

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.matcher import matcher
from naukri.filters import is_fresher_job
from career_site.autofiller import CareerSiteAutofiller
from tracker.database import db

# Curated High-Yield Tech Company Career Boards (Greenhouse, Lever, Direct Portals)
CURATED_CAREER_BOARDS = [
    {
        "company": "Kuku FM",
        "url": "https://jobs.lever.co/kukufm",
        "type": "lever"
    },
    {
        "company": "BrowserStack",
        "url": "https://job-boards.greenhouse.io/browserstack",
        "type": "greenhouse"
    },
    {
        "company": "Postman",
        "url": "https://job-boards.greenhouse.io/postman",
        "type": "greenhouse"
    },
    {
        "company": "Razorpay",
        "url": "https://jobs.lever.co/razorpay",
        "type": "lever"
    },
    {
        "company": "Harness",
        "url": "https://job-boards.greenhouse.io/harness",
        "type": "greenhouse"
    }
]


class FresherCareerScraper:
    """
    Autonomous Scraper that crawls company career pages directly,
    filters for 0-2 Yrs Fresher software roles (Python & Java),
    and dispatches CareerSiteAutofiller to apply automatically.
    """

    def __init__(self):
        self.total_scraped = 0
        self.total_applied = 0

    async def scan_career_board(self, context: BrowserContext, board: Dict[str, str], max_jobs: int = 3):
        company = board["company"]
        url = board["url"]
        logger.info(f"Scanning career board: {company} -> {url}")
        print(f"\n[CAREER SCRAPER] Scanning Direct Board: {company} ({url})", flush=True)

        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2.5)

            # Discover open job listings
            job_links = await page.locator("a[href*='/jobs/'], a[href*='lever.co/'], a[href*='greenhouse.io/'], div.posting a, a.posting-title").all()
            print(f"  Found {len(job_links)} listings on {company} career page...", flush=True)

            applied_in_board = 0
            for link in job_links:
                if applied_in_board >= max_jobs:
                    break

                try:
                    title = (await link.inner_text()).strip()
                    href = await link.get_attribute("href")
                    if not href or not title:
                        continue

                    # Filter: Fresher / 0-2 Years only
                    is_fresh, reason = is_fresher_job(title)
                    if not is_fresh:
                        continue

                    # Filter: Stack alignment (Java or Python)
                    is_app, match_res = matcher.is_applicable(title)
                    if not is_app:
                        continue

                    if db.is_already_applied(href):
                        continue

                    print(f"  🎯 Found Target Fresher Role: '{title}' [{match_res.resume_type.upper()}]", flush=True)

                    # Launch separate tab to apply
                    apply_page = await context.new_page()
                    try:
                        await apply_page.goto(href, wait_until="domcontentloaded", timeout=30000)
                        autofiller = CareerSiteAutofiller(resume_type=match_res.resume_type)
                        res = await autofiller.apply_on_career_site(
                            page=apply_page,
                            job_title=title,
                            company=company,
                            job_url=href
                        )

                        if res.get("success", False):
                            applied_in_board += 1
                            self.total_applied += 1
                    finally:
                        try:
                            await apply_page.close()
                        except Exception:
                            pass

                except Exception as ex:
                    logger.debug(f"Error checking job on {company}: {ex}")

        except Exception as e:
            logger.warning(f"Error accessing career board {company}: {e}")
        finally:
            try:
                await page.close()
            except Exception:
                pass


career_scraper = FresherCareerScraper()
