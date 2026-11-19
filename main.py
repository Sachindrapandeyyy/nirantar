import asyncio
import sys
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from loguru import logger

from config.settings import settings
from core.vault import vault
from core.matcher import matcher
from core.models import JobListing, ApplicationStatus, JobPortalType
from brain.gemini_provider import GeminiProvider
from browser.driver import BrowserDriver
from browser.overlay import CometHUD
from adapters.greenhouse import GreenhouseAdapter
from adapters.lever import LeverAdapter
from adapters.linkedin import LinkedInEasyApplyAdapter
from adapters.naukri import NaukriAdapter
from tracker.database import db
from listeners.email_watcher import EmailWatcher

console = Console()


class NirantarEngine:
    def __init__(self):
        self.brain = GeminiProvider()
        self.adapters = [
            GreenhouseAdapter(),
            LeverAdapter(),
            LinkedInEasyApplyAdapter(),
            NaukriAdapter()
        ]

    def resolve_adapter(self, url: str):
        for adapter in self.adapters:
            if adapter.can_handle(url):
                return adapter
        return None

    async def apply_to_job(self, url: str, job_title: str = "Software Engineer", company: str = "Target Company"):
        console.print(f"\n[bold cyan]🚀 NIRANTAR AUTONOMOUS ENGINE STARTING...[/bold cyan]")
        console.print(f"[dim]URL: {url}[/dim]")

        # 1. Match against master resumes
        match_result = matcher.match(title=job_title, description="")
        console.print(
            f"🧠 [bold green]Resume Matched:[/bold green] [yellow]{match_result.resume_type.upper()}[/yellow] "
            f"(Score: {match_result.score}) -> {match_result.reasoning}"
        )

        job = JobListing(
            title=job_title,
            company=company,
            url=url,
            match_result=match_result
        )

        # 2. Find matching adapter
        adapter = self.resolve_adapter(url)
        if not adapter:
            console.print(f"[bold red]❌ No specialized adapter found for this portal URL.[/bold red]")
            return

        # 3. Launch Comet-style Browser
        console.print(f"🔵 [bold blue]Launching Comet Takeover Browser (Blue Glow Active)...[/bold blue]")
        driver = BrowserDriver()
        try:
            page = await driver.start()
            result = await adapter.apply(job, page, self.brain)

            if result.success:
                console.print(f"[bold green]✔ {result.message}[/bold green]")
                if result.screenshot_path:
                    console.print(f"📸 [dim]Proof saved at: {result.screenshot_path}[/dim]")
                db.save_job(
                    title=job.title,
                    company=job.company,
                    portal=adapter.__class__.__name__,
                    url=job.url,
                    match_score=match_result.score,
                    resume_type=match_result.resume_type
                )
                db.update_job_status(job.url, "APPLIED", result.screenshot_path)
            else:
                console.print(f"[bold yellow]⚠ Application partial/failed: {result.message}[/bold yellow]")
                db.update_job_status(job.url, "FAILED")

            # Pause briefly so user can see the completed page
            await asyncio.sleep(4)

        finally:
            await driver.close()


def print_banner():
    banner_text = """
 [bold cyan]███╗   ██╗██╗██████╗  █████╗ ███╗   ██╗████████╗ █████╗ ██████╗ [/bold cyan]
 [bold cyan]████╗  ██║██║██╔══██╗██╔══██╗████╗  ██║╚══██╔══╝██╔══██╗██╔══██╗[/bold cyan]
 [bold cyan]██╔██╗ ██║██║██████╔╝███████║██╔██╗ ██║   ██║   ███████║██████╔╝[/bold cyan]
 [bold cyan]██║╚██╗██║██║██╔══██╗██╔══██║██║╚██╗██║   ██║   ██╔══██║██╔══██╗[/bold cyan]
 [bold cyan]██║ ╚████║██║██║  ██║██║  ██║██║ ╚████║   ██║   ██║  ██║██║  ██║[/bold cyan]
        [dim]Autonomous, Continuous, Industry-Grade Job Agent[/dim]
    """
    console.print(banner_text)


def show_status():
    jobs = db.list_recent_jobs(limit=25)
    table = Table(title="Recent Job Applications & Status", header_style="bold magenta")
    table.add_column("ID", justify="center", style="dim")
    table.add_column("Company", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Portal", style="blue")
    table.add_column("Resume", style="yellow")
    table.add_column("Score", justify="right")
    table.add_column("Status", style="bold")

    for j in jobs:
        status_color = "green" if j.status == "APPLIED" else "red" if j.status == "FAILED" else "yellow"
        table.add_row(
            str(j.id),
            j.company,
            j.title,
            j.portal,
            j.resume_type.upper(),
            f"{j.match_score:.2f}",
            f"[{status_color}]{j.status}[/{status_color}]"
        )

    console.print(table)


async def test_hud_demo():
    console.print("\n[bold cyan]Launching Comet Takeover Visual Demo (30s)...[/bold cyan]")
    driver = BrowserDriver()
    try:
        page = await driver.start()
        await page.goto("https://httpbin.org/forms/post")
        await CometHUD.inject(page)
        await CometHUD.update_status(page, "Comet Takeover Demo: Analyzing Customer Form...")
        await asyncio.sleep(2)
        await CometHUD.update_status(page, "Filling Candidate verified fields...")
        await page.fill("input[name='custname']", "Sachindra Shekhar Pandey")
        await page.fill("input[name='custtel']", "7905604539")
        await page.fill("input[name='custemail']", "sachindrapandey328@gmail.com")
        await CometHUD.update_status(page, "Verified Form Autofilled! Notice Blue Glow HUD.")
        await asyncio.sleep(4)
    finally:
        await driver.close()


def main():
    print_banner()
    if len(sys.argv) < 2:
        console.print("[yellow]Usage:[/yellow]")
        console.print("  python main.py apply <url> [job_title] [company]")
        console.print("  python main.py status")
        console.print("  python main.py check-email")
        console.print("  python main.py test-hud")
        return

    cmd = sys.argv[1].lower()
    if cmd == "status":
        show_status()
    elif cmd == "check-email":
        console.print("[cyan]Checking inbox for interview updates...[/cyan]")
        watcher = EmailWatcher()
        res = watcher.check_inbox()
        console.print(f"[green]Inbox scan finished. Found {len(res)} key recruiter emails.[/green]")
    elif cmd == "test-hud":
        asyncio.run(test_hud_demo())
    elif cmd == "apply":
        if len(sys.argv) < 3:
            console.print("[red]Please provide a job URL to apply to.[/red]")
            return
        url = sys.argv[2]
        title = sys.argv[3] if len(sys.argv) > 3 else "Software Engineer"
        company = sys.argv[4] if len(sys.argv) > 4 else "Company"
        engine = NirantarEngine()
        asyncio.run(engine.apply_to_job(url, title, company))


if __name__ == "__main__":
    main()
