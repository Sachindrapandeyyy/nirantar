import random
import asyncio
from typing import Any
from playwright.async_api import BrowserContext, Page
from loguru import logger

STEALTH_EVASION_JS = """
(() => {
    // 1. Mask navigator.webdriver
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
        configurable: true
    });

    // 2. Mock window.chrome runtime & plugins
    if (!window.chrome) {
        window.chrome = {
            runtime: {
                OnInstalledReason: { INSTALL: "install", UPDATE: "update", CHROME_UPDATE: "chrome_update", SHARED_MODULE_UPDATE: "shared_module_update" },
                OnRestartRequiredReason: { APP_UPDATE: "app_update", OS_UPDATE: "os_update", PERIODIC: "periodic" },
                PlatformArch: { ARM: "arm", ARM64: "arm64", MIPS: "mips", MIPS64: "mips64", X86_32: "x86-32", X86_64: "x86-64" },
                PlatformNaclArch: { ARM: "arm", MIPS: "mips", MIPS64: "mips64", X86_32: "x86-32", X86_64: "x86-64" },
                PlatformOs: { ANDROID: "android", CROS: "cros", LINUX: "linux", MAC: "mac", OPENBSD: "openbsd", WIN: "win" },
                RequestUpdateCheckStatus: { THROTTLED: "throttled", NO_UPDATE: "no_update", UPDATE_AVAILABLE: "update_available" }
            },
            app: { isInstalled: false },
            csi: () => {},
            loadTimes: () => {}
        };
    }

    // 3. Mock languages to realistic Indian candidate setup
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en-IN', 'en', 'hi'],
        configurable: true
    });

    // 4. Mock hardware concurrency & device memory
    Object.defineProperty(navigator, 'hardwareConcurrency', {
        get: () => 8,
        configurable: true
    });
    Object.defineProperty(navigator, 'deviceMemory', {
        get: () => 16,
        configurable: true
    });

    // 5. Mock permissions query
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
    );
})();
"""


async def apply_stealth_to_context(context: BrowserContext):
    """
    Injects enterprise-grade stealth and anti-fingerprinting evasions
    into a Playwright browser context.
    """
    try:
        await context.add_init_script(STEALTH_EVASION_JS)
    except Exception as e:
        logger.debug(f"Stealth init script error: {e}")


async def human_bezier_move(page: Page, target_x: float, target_y: float, steps: int = 15):
    """
    Moves mouse to (target_x, target_y) using a smooth curved trajectory
    to mimic authentic human hand movement.
    """
    try:
        # Get current mouse position estimate or randomize start
        start_x = random.randint(100, 300)
        start_y = random.randint(100, 300)

        # Generate control point for cubic bezier curve
        ctrl_x = (start_x + target_x) / 2 + random.randint(-80, 80)
        ctrl_y = (start_y + target_y) / 2 + random.randint(-80, 80)

        for step in range(steps + 1):
            t = step / steps
            # Quadratic Bezier formula: (1-t)^2*P0 + 2*(1-t)*t*P1 + t^2*P2
            x = (1 - t) ** 2 * start_x + 2 * (1 - t) * t * ctrl_x + (t ** 2) * target_x
            y = (1 - t) ** 2 * start_y + 2 * (1 - t) * t * ctrl_y + (t ** 2) * target_y
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.005, 0.015))
    except Exception:
        pass


async def human_natural_scroll(page: Page, total_pixels: int = 400):
    """
    Scrolls down using realistic human acceleration and deceleration.
    """
    try:
        chunks = [
            int(total_pixels * 0.15),
            int(total_pixels * 0.35),
            int(total_pixels * 0.30),
            int(total_pixels * 0.20)
        ]
        for c in chunks:
            await page.evaluate(f"window.scrollBy({{top: {c}, behavior: 'smooth'}})")
            await asyncio.sleep(random.uniform(0.08, 0.22))
    except Exception:
        pass
