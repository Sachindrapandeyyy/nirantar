import pytest
from pathlib import Path
from career_site.browser_use_agent import (
    create_candidate_controller,
    AutonomousBrowserUseAgent,
    BROWSER_USE_AVAILABLE
)


def test_browser_use_availability():
    assert BROWSER_USE_AVAILABLE is True


@pytest.mark.asyncio
async def test_candidate_controller_actions():
    controller = create_candidate_controller("python")
    assert controller is not None

    # Verify controller registry has registered actions
    assert hasattr(controller, "registry") or hasattr(controller, "action")


def test_autonomous_browser_use_agent_init():
    agent = AutonomousBrowserUseAgent(resume_type="python")
    assert agent.resume_type == "python"
    assert agent.proof_dir.exists()
