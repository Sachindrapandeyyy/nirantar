import pytest
from core.matcher import matcher
from core.vault import vault
from core.career_knowledge_base import match_field_to_value, get_career_knowledge_base
from career_site.autofiller import CareerSiteAutofiller
from naukri.filters import is_fresher_job


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


def test_fresher_experience_gatekeeping():
    # Acceptable fresher & junior brackets
    assert is_fresher_job("Python Developer", "0-2 Yrs")[0] is True
    assert is_fresher_job("Java Backend Engineer", "0-1 Yrs")[0] is True
    assert is_fresher_job("Software Engineer", "Fresher")[0] is True
    assert is_fresher_job("Graduate Engineer Trainee", "")[0] is True
    assert is_fresher_job("Junior Backend Developer", "")[0] is True

    # Reject senior brackets & senior titles
    assert is_fresher_job("Senior Python Developer", "0-2 Yrs")[0] is False
    assert is_fresher_job("Tech Lead - Java", "0-1 Yrs")[0] is False
    assert is_fresher_job("Principal Architect", "0-1 Yrs")[0] is False
    assert is_fresher_job("Python Developer", "3-5 Yrs")[0] is False
    assert is_fresher_job("Java Developer", "4-7 Yrs")[0] is False
    assert is_fresher_job("Backend Engineer", "5+ Yrs")[0] is False
    assert is_fresher_job("Python Engineer (4+ Years)", "")[0] is False


def test_matcher_with_experience_bracket():
    # Junior / Fresher: Accepted
    ok_py, res_py = matcher.is_applicable("Python Developer", exp_text="0-2 Yrs")
    assert ok_py is True
    assert res_py.resume_type == "python"

    ok_java, res_java = matcher.is_applicable("Java Developer", exp_text="0-1 Yrs")
    assert ok_java is True
    assert res_java.resume_type == "java"

    # Senior Experience: Rejected
    rej_py, _ = matcher.is_applicable("Python Developer", exp_text="3-6 Yrs")
    assert rej_py is False

    rej_java, _ = matcher.is_applicable("Java Developer", exp_text="4-8 Yrs")
    assert rej_java is False

    rej_lead, _ = matcher.is_applicable("Lead Software Engineer", exp_text="0-2 Yrs")
    assert rej_lead is False


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
