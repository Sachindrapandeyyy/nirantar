from core.vault import vault


def test_vault_profile_loaded():
    profile = vault.get_profile()
    assert profile.first_name == "Sachindra"
    assert profile.last_name == "Pandey"
    assert profile.email == "sachindrapandey328@gmail.com"
    assert profile.phone == "7905604539"
    assert profile.salary.current_ctc == 600000.0
    assert profile.salary.expected_ctc == 750000.0
    assert profile.salary.apply_anyway_rule is True
    assert profile.salary.volunteer_ctc is False


def test_vault_resume_retrieval():
    java_resume = vault.get_resume("java")
    python_resume = vault.get_resume("python")
    
    assert java_resume is not None
    assert "java" in java_resume.name.lower()
    assert python_resume is not None
    assert "python" in python_resume.name.lower()
