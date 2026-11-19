import asyncio
import subprocess
from playwright.async_api import async_playwright
import httpx

async def test_cdp():
    # Check if 9222 is active
    try:
        r = httpx.get("http://127.0.0.1:9222/json/version", timeout=2.0)
        print("Chrome CDP is active:", r.json().get("Browser"))
    except Exception as e:
        print("CDP not listening yet:", e)

asyncio.run(test_cdp())
