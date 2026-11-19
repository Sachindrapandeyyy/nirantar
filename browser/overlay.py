from playwright.async_api import Page
from loguru import logger


HUD_CSS_AND_JS = """
(() => {
    // Prevent duplicate injection
    if (document.getElementById('nirantar-hud-overlay')) return;

    // Create HUD container
    const container = document.createElement('div');
    container.id = 'nirantar-hud-overlay';
    container.innerHTML = `
        <style>
            @keyframes nirantar-pulse {
                0% { box-shadow: inset 0 0 15px 4px rgba(0, 128, 255, 0.7), 0 0 12px rgba(0, 128, 255, 0.6); }
                50% { box-shadow: inset 0 0 30px 8px rgba(0, 180, 255, 0.95), 0 0 25px rgba(0, 180, 255, 0.85); }
                100% { box-shadow: inset 0 0 15px 4px rgba(0, 128, 255, 0.7), 0 0 12px rgba(0, 128, 255, 0.6); }
            }
            .nirantar-border-glow {
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                width: 100vw !important;
                height: 100vh !important;
                pointer-events: none !important;
                z-index: 2147483645 !important;
                border: 4px solid #0088ff !important;
                animation: nirantar-pulse 2.2s infinite ease-in-out !important;
                box-sizing: border-box !important;
            }
            .nirantar-banner {
                position: fixed !important;
                top: 16px !important;
                left: 50% !important;
                transform: translateX(-50%) !important;
                background: rgba(10, 15, 30, 0.92) !important;
                backdrop-filter: blur(12px) !important;
                -webkit-backdrop-filter: blur(12px) !important;
                border: 1px solid rgba(0, 160, 255, 0.6) !important;
                border-radius: 9999px !important;
                padding: 8px 24px !important;
                display: flex !important;
                align-items: center !important;
                gap: 12px !important;
                box-shadow: 0 10px 30px rgba(0, 100, 255, 0.35) !important;
                color: #ffffff !important;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
                font-size: 13px !important;
                font-weight: 500 !important;
                z-index: 2147483647 !important;
                pointer-events: none !important;
            }
            .nirantar-indicator {
                width: 10px !important;
                height: 10px !important;
                border-radius: 50% !important;
                background: #00e5ff !important;
                box-shadow: 0 0 10px #00e5ff !important;
            }
            .nirantar-title {
                font-weight: 700 !important;
                letter-spacing: 0.5px !important;
                color: #00d2ff !important;
            }
            .nirantar-msg {
                color: #e2e8f0 !important;
            }
        </style>
        <div class="nirantar-border-glow"></div>
        <div class="nirantar-banner">
            <div class="nirantar-indicator"></div>
            <span class="nirantar-title">NIRANTAR AGENT TAKEOVER</span>
            <span>|</span>
            <span id="nirantar-hud-status" class="nirantar-msg">Analyzing form elements...</span>
        </div>
    `;
    document.documentElement.appendChild(container);
})();
"""


class CometHUD:
    """Manages the visual agent takeover HUD (blue border glow + status pills)."""

    @staticmethod
    async def inject(page: Page):
        """Injects Comet-style visual glow into the current page."""
        try:
            await page.evaluate(HUD_CSS_AND_JS)
        except Exception as e:
            logger.debug(f"HUD injection skipped/failed: {e}")

    @staticmethod
    async def update_status(page: Page, message: str):
        """Updates the message in the top floating banner."""
        try:
            await CometHUD.inject(page)
            safe_msg = message.replace("'", "\\'").replace('"', '\\"')
            await page.evaluate(f"""
                const el = document.getElementById('nirantar-hud-status');
                if (el) el.innerText = '{safe_msg}';
            """)
        except Exception as e:
            logger.debug(f"Failed to update HUD status: {e}")
