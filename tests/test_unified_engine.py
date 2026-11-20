import pytest
from core.unified_engine import UnifiedMultiAgentBrain, unified_brain


def test_unified_engine_initialization():
    assert unified_brain.profile.full_name == "Sachindra Shekhar Pandey"
    assert unified_brain.naukri_agent is not None
    assert unified_brain.linkedin_agent is not None
    assert unified_brain.career_scraper is not None
    assert hasattr(unified_brain, "run_unified_continuous_lifecycle")
