import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from playwright.async_api import Page, BrowserContext, async_playwright
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.vault import vault
from tracker.database import db
from core.notifier import notify_user
from core.scheduler import scheduler
from core.stealth import apply_stealth_to_context
from config.settings import unlock_chrome_profile

from naukri.agent import AutonomousNaukriAgent, SEARCH_VECTORS
from linkedin.agent import AutonomousLinkedInAgent, LINKEDIN_VECTORS
from career_site.scraper import FresherCareerScraper, CURATED_CAREER_BOARDS


class UnifiedMultiAgentBrain:
    """
    Unified Multi-Agent Autonomous Brain.
    Rotates continuously through:
    1. Naukri.com (Resdex Algo Rank Booster, Recruiter Radar, AI Recommended, 12 Search Vectors)
    2. LinkedIn (Easy Apply multi-step & external career routing for Python/Java entry-level)
    3. Direct Company Career Portals (Curated tech boards: BrowserStack, Postman, Razorpay, etc.)
    Runs non-stop in ONE synchronized, stealth-shielded Chrome session.
    """

    def __init__(self):
        self.profile = vault.get_profile()
        self.profile_dir = Path.home() / ".nirantar" / "chrome_profile"
        self.cycle_count = 1
        self.total_applied = 0
        self.naukri_agent = AutonomousNaukriAgent()
        self.linkedin_agent = AutonomousLinkedInAgent()
        self.career_scraper = FresherCareerScraper()

    async def inject_hud(self, page: Page, phase_name: str, subtitle: str = ""):
        """Injects unified master HUD banner at the top of the browser."""
        sub_html = f'<div style="font-size:11px; color:#a7f3d0;">{subtitle}</div>' if subtitle else ''
        js_code = f"""() => {{
            let hud = document.getElementById('nirantar-unified-hud');
            if (!hud) {{
                hud = document.createElement('div');
                hud.id = 'nirantar-unified-hud';
                hud.style.position = 'fixed';
                hud.style.top = '10px';
                hud.style.left = '50%';
                hud.style.transform = 'translateX(-50%)';
                hud.style.zIndex = '9999999';
                hud.style.background = 'linear-gradient(135deg, #020617 0%, #0f172a 50%, #064e3b 100%)';
                hud.style.color = '#38bdf8';
                hud.style.padding = '10px 28px';
                hud.style.borderRadius = '35px';
                hud.style.fontSize = '13px';
                hud.style.fontWeight = 'bold';
                hud.style.fontFamily = 'Segoe UI, system-ui, sans-serif';
                hud.style.boxShadow = '0 10px 35px rgba(0,0,0,0.7), 0 0 25px rgba(56,189,248,0.4)';
                hud.style.border = '1px solid rgba(56,189,248,0.3)';
                hud.style.display = 'flex';
                hud.style.flexDirection = 'column';
                hud.style.alignItems = 'center';
                hud.style.gap = '3px';
                hud.style.pointerEvents = 'none';
                document.body.appendChild(hud);
            }}
            hud.innerHTML = `
                <div style="font-size:14px; color:#38bdf8; display:flex; align-items:center; gap:8px;">
                    <span>🧠 NIRANTAR UNIFIED MULTI-AGENT BRAIN</span>
                    <span style="background:#10b981; color:#ffffff; font-size:10px; padding:2px 8px; border-radius:10px;">CYCLE #{self.cycle_count}</span>
                </div>
                <div style="font-size:12px; color:#ffffff; font-weight:normal;">{phase_name}</div>
                {sub_html}
            `;
        }}"""
        try:
            await page.evaluate(js_code)
        except Exception:
            pass

    async def run_unified_continuous_lifecycle(self):
        """Runs the all-in-one non-stop multi-portal application loop."""
        print("\n" + "=" * 78, flush=True)
        print("     🧠 NIRANTAR: UNIFIED MULTI-PORTAL AUTONOMOUS ENGINE", flush=True)
        print("=" * 78, flush=True)
        print(f" Candidate: {self.profile.full_name}", flush=True)
        print(" Active Portals: Naukri + LinkedIn + Direct Career ATS Boards", flush=True)
        print(" Target Stacks: Python & Java Engineering (0-2 Yrs Freshers Gatekept)", flush=True)
        print(" Web Dashboard: http://localhost:8000", flush=True)
        print("=" * 78 + "\n", flush=True)

        unlock_chrome_profile(self.profile_dir)

        async with async_playwright() as p:
            launch_kwargs = {
                "user_data_dir": str(self.profile_dir),
                "channel": "chrome",
                "headless": False,
                "slow_mo": 250,
                "args": [
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox"
                ],
                "viewport": None
            }

            try:
                context = await p.chromium.launch_persistent_context(**launch_kwargs)
            except Exception as e:
                if "ProcessSingleton" in str(e) or "already in use" in str(e):
                    print("⚠️ Profile lock detected. Re-cleaning locks and retrying launch...", flush=True)
                    unlock_chrome_profile(self.profile_dir)
                    await asyncio.sleep(2)
                    context = await p.chromium.launch_persistent_context(**launch_kwargs)
                else:
                    raise e

            # Apply Enterprise Stealth & Anti-Fingerprinting Evasions
            await apply_stealth_to_context(context)
            page = context.pages[0] if context.pages else await context.new_page()

            while True:
                print(f"\n{'#' * 78}", flush=True)
                print(f"   STARTING UNIFIED MULTI-AGENT CYCLE #{self.cycle_count}", flush=True)
                print(f"   Session Verified Lifetime Applications: {self.total_applied}", flush=True)
                print(f"{'#' * 78}\n", flush=True)

                # -------------------------------------------------------------
                # STAGE 1: NAUKRI ALGO RANK BOOSTER & RECRUITER RADAR
                # -------------------------------------------------------------
                print("\n" + "-" * 60, flush=True)
                print(" [STAGE 1/4] NAUKRI RESDEX RANK BOOSTER & RADAR", flush=True)
                print("-" * 60, flush=True)
                await self.inject_hud(page, "Stage 1: Naukri Profile Refresh & Radar", "Toggling Resdex Dot & Checking Inbox")
                try:
                    await self.naukri_agent.optimize_profile_and_boost_rank(page)
                    await self.naukri_agent.scan_recruiter_radar(page)
                except Exception as e:
                    logger.debug(f"Naukri Stage 1 note: {e}")

                # -------------------------------------------------------------
                # STAGE 2: NAUKRI MULTI-VECTOR DISCOVERY & APPLY
                # -------------------------------------------------------------
                print("\n" + "-" * 60, flush=True)
                print(" [STAGE 2/4] NAUKRI AI RECOMMENDED & VECTOR ROTATION", flush=True)
                print("-" * 60, flush=True)
                await self.inject_hud(page, "Stage 2: Naukri Application Rotation", "AI Matches & 12 Dual-Stack Vectors")
                try:
                    await self.naukri_agent.scan_recommended_jobs(context, page, max_jobs=4)
                    for vector in SEARCH_VECTORS[:6]:  # Run top vectors per cycle
                        await self.naukri_agent.execute_vector_search(context, page, vector, max_pages=3)
                    self.total_applied = self.naukri_agent.total_applied
                except Exception as e:
                    logger.debug(f"Naukri Stage 2 note: {e}")

                # -------------------------------------------------------------
                # STAGE 3: LINKEDIN MASTER AGENT (EASY APPLY & ATS)
                # -------------------------------------------------------------
                print("\n" + "-" * 60, flush=True)
                print(" [STAGE 3/4] LINKEDIN ENTRY-LEVEL VECTORS", flush=True)
                print("-" * 60, flush=True)
                await self.inject_hud(page, "Stage 3: LinkedIn Master Agent", "Easy Apply & External Routing (Python/Java)")
                try:
                    for li_vec in LINKEDIN_VECTORS:
                        await self.linkedin_agent.scan_vector(context, page, li_vec, max_jobs=5)
                    self.total_applied += self.linkedin_agent.total_applied
                except Exception as e:
                    logger.debug(f"LinkedIn Stage 3 note: {e}")

                # -------------------------------------------------------------
                # STAGE 4: DIRECT CAREER BOARDS SCRAPER (GREENHOUSE / LEVER)
                # -------------------------------------------------------------
                print("\n" + "-" * 60, flush=True)
                print(" [STAGE 4/4] DIRECT COMPANY CAREER BOARDS", flush=True)
                print("-" * 60, flush=True)
                await self.inject_hud(page, "Stage 4: Direct Career Boards", "Scanning BrowserStack, Postman, Razorpay, Harness")
                try:
                    for board in CURATED_CAREER_BOARDS:
                        await self.career_scraper.scan_career_board(context, board, max_jobs=3)
                    self.total_applied += self.career_scraper.total_applied
                except Exception as e:
                    logger.debug(f"Career Scraper Stage 4 note: {e}")

                # -------------------------------------------------------------
                # STAGE 5: CYCLE COMPLETE & LIVE COUNTDOWN
                # -------------------------------------------------------------
                print("\n" + "=" * 78, flush=True)
                print(f"✔ UNIFIED CYCLE #{self.cycle_count} COMPLETE! Total Verified Applications: {self.total_applied}", flush=True)
                print("Resting for 4 minutes before next unified scan...", flush=True)
                print("=" * 78 + "\n", flush=True)

                self.cycle_count += 1

                # Live Countdown before next cycle
                wait_seconds = 240
                for remaining in range(wait_seconds, 0, -10):
                    mins = remaining // 60
                    secs = remaining % 60
                    await self.inject_hud(
                        page,
                        f"Unified Brain: {self.total_applied} Applications Verified",
                        f"Next Multi-Portal Scan in {mins}m {secs}s (Cycle #{self.cycle_count})"
                    )
                    await asyncio.sleep(10)


unified_brain = UnifiedMultiAgentBrain()

if __name__ == "__main__":
    asyncio.run(unified_brain.run_unified_continuous_lifecycle())
