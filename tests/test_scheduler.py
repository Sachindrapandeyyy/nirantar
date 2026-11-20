import pytest
from core.scheduler import scheduler, PacingScheduler


def test_scheduler_summary():
    summary = scheduler.get_status_summary()
    assert "ist_time" in summary
    assert "mode" in summary
    assert "status_label" in summary


@pytest.mark.asyncio
async def test_scheduler_turbo_pacing():
    turbo_sched = PacingScheduler(mode="TURBO")
    assert turbo_sched.mode == "TURBO"
    # Turbo pacing executes quickly
    await turbo_sched.pace_next_application()
    assert turbo_sched.applications_this_hour == 1
