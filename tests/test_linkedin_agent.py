import pytest
from pathlib import Path
from linkedin.agent import AutonomousLinkedInAgent, LINKEDIN_VECTORS


def test_linkedin_agent_initialization():
    agent = AutonomousLinkedInAgent()
    assert agent.profile.full_name == "Sachindra Shekhar Pandey"
    assert agent.proof_dir.exists()
    assert len(LINKEDIN_VECTORS) >= 3


def test_linkedin_vector_urls():
    for vec in LINKEDIN_VECTORS:
        assert "linkedin.com/jobs" in vec["url"]
        assert "location=" in vec["url"]
