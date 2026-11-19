import pytest
from core.naukri_agent import AutonomousNaukriAgent
from core.matcher import matcher
from tracker.database import db


def test_agent_role_filtering():
    agent = AutonomousNaukriAgent()
    # Positive software roles
    assert agent.is_valid_software_role("Python Developer") is True
    assert agent.is_valid_software_role("Backend Software Engineer") is True
    assert agent.is_valid_software_role("FastAPI / Django Engineer") is True
    assert agent.is_valid_software_role("AI Engineer Intern") is True

    # Negative non-tech / noise roles
    assert agent.is_valid_software_role("Insurance Claim - Backend Operations") is False
    assert agent.is_valid_software_role("AML/KYC Analyst - Finance Domain") is False
    assert agent.is_valid_software_role("AI Video Editor Intern") is False
    assert agent.is_valid_software_role("Telecaller Support") is False
    assert agent.is_valid_software_role("Field Sales Executive") is False


def test_database_deduplication():
    test_url = "https://www.naukri.com/test-job-dedup-ci"
    db.save_job("Test Dev", "Test Co", "Naukri", test_url, 0.9, "python")
    assert db.is_already_applied(test_url) is False

    db.update_job_status(test_url, "APPLIED")
    assert db.is_already_applied(test_url) is True

    # Cleanup
    import sqlite3
    c = sqlite3.connect("nirantar.db")
    c.execute("DELETE FROM jobs WHERE url = ?", (test_url,))
    c.commit()
    c.close()


def test_matcher_backward_compatibility():
    res = matcher.match("Python FastAPI Developer")
    assert res.resume_type == "python"
    assert res.selected_resume_type == "python"
    assert res.score == res.compatibility_score
