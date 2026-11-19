import asyncio
import os
import sys
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
    Operates in headed Chrome profile, searches targeted fresher roles,
    and applies via Easy Apply or external Career Site engine.
    """

    def __init__(self):
        self.profile = vault.get_profile()
        self.profile_dir = Path.home() / ".nirantar" / "chrome_profile"
        self.proof_dir = PROJECT_ROOT / "proofs" / "linkedin"
        self.proof_dir.mkdir(parents=True, exist_ok=True)
        self.total_applied = 0

    async def run(self):
        logger.info("Starting Autonomous LinkedIn Agent...")
        print("\n" + "=" * 70, flush=True)
        print(" [LINKEDIN AGENT] Launching Autonomous LinkedIn Engine", flush=True)
        print("=" * 70, flush=True)


linkedin_agent = AutonomousLinkedInAgent()
