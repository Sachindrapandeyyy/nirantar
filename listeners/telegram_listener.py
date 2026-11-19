import re
from typing import List
from loguru import logger
from core.matcher import matcher
from tracker.database import db


class TelegramJobListener:
    """
    Listens to Telegram hiring channels/groups and extracts job links.
    """

    URL_PATTERN = re.compile(r"https?://(?:www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_+.~#?&/=]*)")

    @classmethod
    def process_message(cls, text: str, sender: str = "Telegram"):
        """Extracts job links and enqueues high-match jobs."""
        urls = cls.URL_PATTERN.findall(text)
        if not urls:
            return

        for url in urls:
            url_lower = url.lower()
            portal = "generic"
            if "greenhouse.io" in url_lower:
                portal = "greenhouse"
            elif "lever.co" in url_lower:
                portal = "lever"
            elif "linkedin.com" in url_lower:
                portal = "linkedin"
            elif "naukri.com" in url_lower:
                portal = "naukri"
            elif "myworkdayjobs.com" in url_lower:
                portal = "workday"

            # Match against profile
            match_res = matcher.match(title=text[:100], description=text)
            
            logger.info(f"Telegram Job Discovered: {portal.upper()} | Score: {match_res.score} | Best: {match_res.resume_type}")
            db.save_job(
                title=text[:80].replace("\n", " "),
                company="Discovered via Telegram",
                portal=portal,
                url=url,
                match_score=match_res.score,
                resume_type=match_res.resume_type
            )
