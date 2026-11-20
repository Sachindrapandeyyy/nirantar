from core.matcher import matcher


def test_java_matching():
    result = matcher.match(
        title="Senior Java Backend Engineer",
        description="Looking for Spring Boot, Microservices, Kafka, Redis, and PostgreSQL experience."
    )
    assert result.resume_type == "java"
    assert result.score >= 0.7
    assert "spring boot" in result.matched_keywords or "spring" in result.matched_keywords


def test_python_matching():
    result = matcher.match(
        title="AI Backend Engineer",
        description="Experience with Python, FastAPI, AsyncIO, PyTorch, and LLM integrations required."
    )
    assert result.resume_type == "python"
    assert result.score >= 0.7
    assert "fastapi" in result.matched_keywords or "python" in result.matched_keywords


def test_fresher_experience_filters():
    from naukri.filters import is_fresher_job

    # 1. Real freshers & junior brackets must pass
    is_f, _ = is_fresher_job("Python Developer", "0-1 Yrs")
    assert is_f is True

    is_f, _ = is_fresher_job("Software Engineer Fresher", "0-2 Yrs")
    assert is_f is True

    is_f, _ = is_fresher_job("Junior Java Developer", "Fresher")
    assert is_f is True

    # 2. Upper experience brackets >= 4 years MUST be rejected (No 0-5 or 0-7 leaks)
    is_f, reason = is_fresher_job("Python Developer", "0-5 Yrs")
    assert is_f is False
    assert "exceeds entry level" in reason

    is_f, reason = is_fresher_job("Python Developer", "0-7 Yrs")
    assert is_f is False
    assert "exceeds entry level" in reason

    is_f, reason = is_fresher_job("Backend Developer", "1-4 Yrs")
    assert is_f is False
    assert "exceeds entry level" in reason

    is_f, reason = is_fresher_job("Java Engineer", "3-5 Yrs")
    assert is_f is False
    assert ("exceeds entry level" in reason or "senior level" in reason)

    # 3. URL slug experience detection
    is_f, reason = is_fresher_job("Python Dev", "0-1 Yrs", url="https://naukri.com/job-listings-python-dev-0-to-5-years-12345")
    assert is_f is False
    assert "URL experience bracket" in reason

    is_f, reason = is_fresher_job("Python Dev", "0-1 Yrs", url="https://naukri.com/job-listings-senior-developer-12345")
    assert is_f is False
    assert "Senior slug in URL" in reason


def test_ctc_apply_anyway_policy():
    # Job mentions lower or higher salary - matcher still scores and approves
    result = matcher.match(
        title="Software Engineer Intern - 3.5 LPA fixed",
        description="Java, SQL, REST APIs"
    )
    assert result.resume_type == "java"
    assert result.score >= 0.4
