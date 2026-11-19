import pytest
from pathlib import Path
from career_site.autofiller import CareerSiteAutofiller
from core.career_knowledge_base import match_field_to_value, CAREER_KNOWLEDGE_BASE


def test_knowledge_base_coverage():
    # Identity & Contact
    assert match_field_to_value("first_name") == "Sachindra"
    assert match_field_to_value("last_name") == "Pandey"
    assert match_field_to_value("full_name") == "Sachindra Shekhar Pandey"
    assert match_field_to_value("email") == "sachindrapandey328@gmail.com"
    assert match_field_to_value("phone") == "7905604539"
    assert match_field_to_value("city", "Current City") == "Noida"
    assert match_field_to_value("pincode", "Postal Code") == "201301"

    # Social Profiles
    assert "linkedin.com" in match_field_to_value("linkedin")
    assert "github.com" in match_field_to_value("github")
    assert "vercel.app" in match_field_to_value("portfolio")

    # Education
    assert match_field_to_value("university", "Institution Name") == "Shri Ramswaroop Memorial University"
    assert match_field_to_value("degree", "Highest Degree") == "B.Tech"
    assert match_field_to_value("major", "Field of Study") == "Computer Science & Engineering"
    assert match_field_to_value("grad_year", "Year of Passing") == "2026"
    assert match_field_to_value("cgpa", "Cumulative GPA") == "8.2"
    assert match_field_to_value("percentage", "12th Board Marks") == "82.4"
    assert match_field_to_value("percentage", "10th Board Marks") == "84.6"

    # Experience & CTC
    assert "NTPC" in match_field_to_value("current_company", "Current Employer")
    assert match_field_to_value("experience", "Total Years of Experience") == "0.3"
    assert match_field_to_value("expected_ctc", "Expected Salary") == "750000"
    assert match_field_to_value("notice_period", "Notice Period / Availability") == "Immediate"

    # Legal & Compliance
    assert match_field_to_value("work_auth", "Are you legally authorized to work in India?") == "Yes"
    assert match_field_to_value("sponsorship", "Will you require visa sponsorship?") == "No"
    assert match_field_to_value("relocate", "Are you willing to relocate?") == "Yes"
    assert match_field_to_value("gender", "Gender / Sex") == "Male"

    # Screening Essays
    assert "FastAPI" in match_field_to_value("why_join", "Why do you want to join our engineering team?")
    assert "NTPC" in match_field_to_value("project", "Describe a challenging project you built")


def test_career_autofiller_init_and_resume():
    autofiller = CareerSiteAutofiller(resume_type="python")
    resume_path = autofiller.get_resume_path()
    assert resume_path is not None
    assert resume_path.exists()
    assert resume_path.suffix.lower() == ".pdf"
    assert autofiller.proof_dir.exists()
