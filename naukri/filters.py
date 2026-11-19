def is_valid_software_role(title: str) -> bool:
    """
    Strictly validates software engineering roles on Naukri.com,
    eliminating non-tech noise, telecaller, sales, claims, and non-developer roles.
    """
    title_lower = title.lower()

    # Blacklist non-tech and non-engineering jobs
    blacklist = [
        "claim", "kyc", "aml", "analyst 3", "insurance", "video editor", "video creator",
        "civil", "structural", "mechanical", "electrical", "chemical", "site engineer",
        "telecaller", "tele-caller", "bpo", "sales", "executive", "field", "counselor",
        "receptionist", "content writer", "digital marketing", "seo", "graphic designer",
        "data entry", "voice process", "bde", "accountant", "hr recruiter", "operations analyst",
        "finance domain"
    ]
    for term in blacklist:
        if term in title_lower:
            return False

    # Positive whitelist for core software & Python engineering roles
    whitelist = [
        "python", "django", "fastapi", "flask", "backend", "back-end",
        "software engineer", "software developer", "full stack", "fullstack",
        "data engineer", "developer", "programmer", "ai engineer", "sde"
    ]
    return any(term in title_lower for term in whitelist)
