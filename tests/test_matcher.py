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


def test_ctc_apply_anyway_policy():
    # Job mentions lower or higher salary - matcher still scores and approves
    result = matcher.match(
        title="Software Engineer Intern - 3.5 LPA fixed",
        description="Java, SQL, REST APIs"
    )
    assert result.resume_type == "java"
    assert result.score >= 0.4
