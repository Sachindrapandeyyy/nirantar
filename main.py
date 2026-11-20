import argparse
import asyncio
import sys
from pathlib import Path
from loguru import logger
from rich.console import Console

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.vault import vault
from core.matcher import matcher
from tracker.database import db
from naukri.agent import AutonomousNaukriAgent
from career_site.autofiller import CareerSiteAutofiller
from career_site.scraper import FresherCareerScraper, CURATED_CAREER_BOARDS

console = Console()


async def run_master_orchestrator(portal: str = "naukri", apply_url: str = ""):
    console.print("\n[bold cyan]🧠 NIRANTAR MULTI-AGENT AUTONOMOUS BRAIN[/bold cyan]")
    console.print(f"Candidate: [bold green]{vault.get_profile().full_name}[/bold green]")
    console.print(f"Target Stacks: [yellow]Python & Java Engineering (0-2 Yrs Freshers)[/yellow]\n")

    if apply_url:
        console.print(f"[bold yellow]Direct External Apply Mode:[/bold yellow] {apply_url}")
        from playwright.async_api import async_playwright
        profile_dir = Path.home() / ".nirantar" / "chrome_profile"
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                str(profile_dir),
                headless=False,
                viewport={"width": 1280, "height": 800}
            )
            page = await context.new_page()
            await page.goto(apply_url, wait_until="domcontentloaded")
            match_res = matcher.match(page.title())
            autofiller = CareerSiteAutofiller(resume_type=match_res.resume_type)
            await autofiller.apply_on_career_site(page, page.title(), "Target Company", apply_url)
            await context.close()
        return

    portal_lower = portal.lower()
    if portal_lower == "naukri":
        console.print("[bold green]Launching Dedicated Naukri Master Agent...[/bold green]")
        agent = AutonomousNaukriAgent()
        await agent.run_continuous_engine()
    elif portal_lower == "linkedin":
        console.print("[bold cyan]Launching Dedicated LinkedIn Master Agent...[/bold cyan]")
        from linkedin.agent import AutonomousLinkedInAgent
        li_agent = AutonomousLinkedInAgent()
        await li_agent.run()
    elif portal_lower == "all":
        console.print("[bold magenta]Launching Unified Multi-Agent Brain (Naukri + LinkedIn + Career Boards)...[/bold magenta]")
        from linkedin.agent import AutonomousLinkedInAgent
        li_agent = AutonomousLinkedInAgent()
        await li_agent.run()
        naukri_agent = AutonomousNaukriAgent()
        await naukri_agent.run_continuous_engine()
    elif portal_lower == "career_scraper":
        console.print("[bold green]Launching Direct Career Pages Scraper...[/bold green]")
        from playwright.async_api import async_playwright
        profile_dir = Path.home() / ".nirantar" / "chrome_profile"
        scraper = FresherCareerScraper()
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                str(profile_dir),
                headless=False,
                viewport={"width": 1280, "height": 800}
            )
            for board in CURATED_CAREER_BOARDS:
                await scraper.scan_career_board(context, board)
            await context.close()
    else:
        console.print(f"[bold yellow]Portal '{portal}' runner initialized. Running Naukri Master Engine...[/bold yellow]")
        agent = AutonomousNaukriAgent()
        await agent.run_continuous_engine()


def main():
    parser = argparse.ArgumentParser(description="Nirantar Autonomous Job Application Engine")
    parser.add_argument("--portal", type=str, default="naukri", help="Target portal: naukri, career_scraper, linkedin, ziprecruiter, indeed")
    parser.add_argument("--apply", type=str, default="", help="Direct apply to a specific external career page URL")
    args = parser.parse_args()

    asyncio.run(run_master_orchestrator(portal=args.portal, apply_url=args.apply))


if __name__ == "__main__":
    main()
