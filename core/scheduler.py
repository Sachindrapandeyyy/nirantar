import asyncio
import random
from datetime import datetime, timezone, timedelta
from typing import Literal
from loguru import logger

# Indian Standard Time (UTC + 5:30)
IST = timezone(timedelta(hours=5, minutes=30))


class PacingScheduler:
    """
    Intelligent Recruiter Working Hours & Application Pacing Strategy.
    Prevents platform rate limits and anti-bot flags by simulating
    authentic human candidate applying patterns.
    """

    def __init__(self, mode: Literal["TURBO", "BALANCED", "SMART_RECRUITER"] = "BALANCED"):
        self.mode = mode
        self.applications_this_hour = 0
        self.current_hour_marker = -1

    def get_ist_now(self) -> datetime:
        return datetime.now(timezone.utc).astimezone(IST)

    def is_recruiter_active_hours(self) -> bool:
        """
        Peak hiring activity in India occurs Monday through Saturday, 09:00 to 19:30 IST.
        """
        now = self.get_ist_now()
        # Monday=0, Sunday=6
        if now.weekday() == 6:  # Sunday is off-peak
            return False
        
        hour = now.hour + now.minute / 60.0
        return 9.0 <= hour <= 19.5

    def get_status_summary(self) -> dict:
        now = self.get_ist_now()
        is_active = self.is_recruiter_active_hours()
        return {
            "ist_time": now.strftime("%I:%M %p IST (%A)"),
            "mode": self.mode,
            "is_recruiter_hours": is_active,
            "status_label": "🟢 Peak Recruiter Window" if is_active else "🌙 Off-Peak / Algo Boost Window"
        }

    async def pace_next_application(self):
        """
        Calculates and waits for an optimal human breathing interval before applying to next job.
        """
        now = self.get_ist_now()
        if now.hour != self.current_hour_marker:
            self.current_hour_marker = now.hour
            self.applications_this_hour = 0

        self.applications_this_hour += 1

        if self.mode == "TURBO":
            delay = random.uniform(1.0, 2.5)
        elif self.mode == "BALANCED":
            # Natural human rhythm: 8 to 18 seconds between jobs
            delay = random.uniform(8.0, 18.0)
        else:  # SMART_RECRUITER
            if self.is_recruiter_active_hours():
                # Peak hours: Steady natural rhythm (6 to 15s)
                delay = random.uniform(6.0, 15.0)
            else:
                # Night / Off-peak: Slower, stealthy pace (25 to 45s)
                delay = random.uniform(25.0, 45.0)

        logger.debug(f"Pacing scheduler delay: {delay:.1f}s (Hour count: {self.applications_this_hour})")
        await asyncio.sleep(delay)


scheduler = PacingScheduler(mode="BALANCED")
