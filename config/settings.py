import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # LLM Settings
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"

    # Vault & Storage
    VAULT_DIR: Path = Path(r"C:\Users\Sachi\OneDrive\Desktop\dacs")
    DATABASE_URL: str = "sqlite:///./nirantar.db"
    SCREENSHOTS_DIR: Path = Path("./proofs")

    # Browser Automation Settings
    HEADLESS: bool = False
    USE_REAL_CHROME: bool = True
    CHROME_USER_DATA_DIR: Path = Path.home() / ".nirantar" / "chrome_profile"
    BROWSER_TIMEOUT_MS: int = 30000
    SLOW_MO_MS: int = 120
    AGENT_BORDER_GLOW: bool = True
    HUMAN_DELAY_MIN: float = 0.5
    HUMAN_DELAY_MAX: float = 2.0

    # Notification & Tracking
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # Email Monitoring
    IMAP_SERVER: str = "imap.gmail.com"
    IMAP_PORT: int = 993
    IMAP_USER: str = "sachindrapandey328@gmail.com"
    IMAP_PASSWORD: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

# Ensure directories exist
settings.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def unlock_chrome_profile(profile_dir: Optional[Path] = None) -> None:
    """
    Terminates any orphaned Chrome processes holding locks on the profile directory
    and cleans up SingletonLock, SingletonCookie, SingletonSocket to prevent
    ProcessSingleton crash errors.
    """
    target_dir = profile_dir or settings.CHROME_USER_DATA_DIR
    if not target_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)
        return

    import sys
    if sys.platform == "win32":
        try:
            import subprocess
            dir_name = target_dir.name
            ps_script = (
                f"$dir = '{dir_name}'; "
                "Get-CimInstance Win32_Process -Filter \"Name = 'chrome.exe'\" | "
                "Where-Object { $_.CommandLine -like ('*' + $dir + '*') } | "
                "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
            )
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, timeout=5)
        except Exception:
            pass

    for pattern in ["Singleton*", "SingletonLock", "SingletonCookie", "SingletonSocket"]:
        for f in target_dir.glob(pattern):
            try:
                f.unlink(missing_ok=True)
            except Exception:
                pass
