import asyncio
import random
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from loguru import logger
from config.settings import settings
from browser.overlay import CometHUD


class BrowserDriver:
    """
    Manages Playwright browser lifecycle with anti-detection and Comet HUD styling.
    """

    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def start(self) -> Page:
        self.playwright = await async_playwright().start()

        # Stealth browser arguments to avoid bot detection
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-infobars",
            "--start-maximized"
        ]

        # Use persistent Chrome profile so logins (LinkedIn, Naukri, Google) are preserved forever
        settings.CHROME_USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
        user_data_path = str(settings.CHROME_USER_DATA_DIR)

        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_path,
            channel="chrome" if settings.USE_REAL_CHROME else None,
            headless=settings.HEADLESS,
            slow_mo=settings.SLOW_MO_MS,
            args=launch_args,
            viewport={"width": 1400, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            locale="en-IN",
            timezone_id="Asia/Kolkata"
        )

        # Remove webdriver flag
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()

        # Auto-inject Comet HUD on page load
        if settings.AGENT_BORDER_GLOW:
            self.page.on("load", lambda page: asyncio.create_task(CometHUD.inject(page)))

        logger.info(f"Playwright BrowserDriver started using Real Chrome with persistent profile at: {user_data_path}")
        return self.page

    async def human_type(self, selector: str, text: str):
        """Simulates human typing with variable inter-keystroke delays."""
        if not self.page:
            return
        
        await self.page.locator(selector).scroll_into_view_if_needed()
        await self.page.click(selector)
        
        for char in text:
            await self.page.keyboard.type(char)
            await asyncio.sleep(random.uniform(0.03, 0.09))

    async def human_click(self, selector: str):
        """Smooth human click with realistic pre-click pause."""
        if not self.page:
            return
        
        locator = self.page.locator(selector).first
        await locator.scroll_into_view_if_needed()
        await asyncio.sleep(random.uniform(0.2, 0.5))
        await locator.click()

    async def close(self):
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("BrowserDriver stopped.")
        except Exception as e:
            logger.debug(f"BrowserDriver close cleanup: {e}")
