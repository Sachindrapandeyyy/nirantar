import pytest
from core.matcher import matcher
from core.vault import vault
from core.career_knowledge_base import match_field_to_value, get_career_knowledge_base
from career_site.autofiller import CareerSiteAutofiller


def test_dual_resume_vault_files_exist():
    py_resume = vault.get_resume("python")
    java_resume = vault.get_resume("java")

    assert py_resume is not None and py_resume.exists()
    assert java_resume is not None and java_resume.exists()
    assert "python" in py_resume.name.lower()
    assert "java" in java_resume.name.lower()


def test_matcher_stack_routing():
    # 1. Java Stack Routing
    java_roles = [
        "Java Developer",
        "Junior Java Backend Engineer",
        "Spring Boot Developer",
        "Java / Microservices Engineer"
    ]
    for r in java_roles:
        app, res = matcher.is_applicable(r)
        assert app is True, f"Failed for {r}"
        assert res.resume_type == "java", f"Expected java for {r}, got {res.resume_type}"
        assert "java" in res.resume_path.lower()

    # 2. Python Stack Routing
    python_roles = [
        "Python Developer",
        "FastAPI Backend Engineer",
        "Django Developer",
        "AI / Machine Learning Engineer",
        "Python Software Engineer"
    ]
    for r in python_roles:
        app, res = matcher.is_applicable(r)
        assert app is True, f"Failed for {r}"
        assert res.resume_type == "python", f"Expected python for {r}, got {res.resume_type}"
        assert "python" in res.resume_path.lower()


def test_matcher_non_applicable_filtering():
    non_applicable = [
        "PHP Laravel Developer",
        "Ruby on Rails Developer",
        "Flutter Mobile App Engineer",
        "iOS Swift Developer",
        "Principal Architect",
        "Engineering Director",
        "Telecaller Support Executive",
        "Insurance Claim Analyst"
    ]
    for r in non_applicable:
        app, res = matcher.is_applicable(r)
        assert app is False, f"Expected False for {r}, got True"


def test_knowledge_base_dynamic_stack():
    py_skills = match_field_to_value("skills", resume_type="python")
    java_skills = match_field_to_value("skills", resume_type="java")

    assert "Python" in py_skills and "FastAPI" in py_skills
    assert "Java" in java_skills and "Spring Boot" in java_skills

    py_essay = match_field_to_value("why_join", resume_type="python")
    java_essay = match_field_to_value("why_join", resume_type="java")

    assert "Python" in py_essay
    assert "Java" in java_essay


def test_autofiller_resume_selection():
    py_filler = CareerSiteAutofiller(resume_type="python")
    java_filler = CareerSiteAutofiller(resume_type="java")

    assert "python" in py_filler.get_resume_path().name.lower()
    assert "java" in java_filler.get_resume_path().name.lower()
