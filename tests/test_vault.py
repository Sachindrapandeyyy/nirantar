import os
from pathlib import Path
from core.vault import vault, VaultManager


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


def test_vault_resume_retrieval(tmp_path):
    # If running locally on Sachindra's laptop
    if vault.vault_dir.exists() and vault.get_resume("java"):
        java_resume = vault.get_resume("java")
        python_resume = vault.get_resume("python")
        assert java_resume is not None
        assert "java" in java_resume.name.lower()
        assert python_resume is not None
        assert "python" in python_resume.name.lower()
    else:
        # Running in GitHub CI Linux runner
        dummy_java = tmp_path / "test_java_resume.pdf"
        dummy_java.write_text("dummy java resume")
        dummy_py = tmp_path / "test_python_resume.pdf"
        dummy_py.write_text("dummy python resume")
        vm = VaultManager(vault_dir=tmp_path)
        assert vm.get_resume("java") is not None
        assert vm.get_resume("python") is not None
