import sys
import subprocess
from loguru import logger

def notify_user(title: str, message: str, alert_type: str = "info"):
    """
    Sends audio chime and Windows Desktop notification to candidate.
    Used for Interview calls, test links, and milestones.
    """
    # 1. Audio Chime (Windows Built-in)
    try:
        import winsound
        if alert_type == "interview":
            # Distinct double-chime for interview call
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        else:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
    except Exception:
        pass

    # 2. Windows Desktop Toast Notification via PowerShell
    if sys.platform == "win32":
        try:
            clean_title = title.replace("'", "").replace('"', '')
            clean_msg = message.replace("'", "").replace('"', '')
            ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
$b = New-Object System.Windows.Forms.NotifyIcon
$b.Icon = [System.Drawing.SystemIcons]::Information
$b.BalloonTipIcon = [System.Windows.Forms.ToolTipIcon]::Info
$b.BalloonTipTitle = '{clean_title}'
$b.BalloonTipText = '{clean_msg}'
$b.Visible = $true
$b.ShowBalloonTip(4000)
"""
            subprocess.Popen(
                ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception as e:
            logger.debug(f"Notification error: {e}")

    logger.info(f"📢 [NOTIFICATION] {title}: {message}")
