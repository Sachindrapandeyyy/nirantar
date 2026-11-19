import re

def is_valid_software_role(title: str) -> bool:
    """
    Strictly validates software engineering roles on Naukri.com,
    eliminating non-tech noise, telecaller, sales, claims, and non-developer roles.
    """
    title_lower = title.lower()

    # Blacklist non-tech and non-engineering jobs, and high-seniority roles
    blacklist = [
        "claim", "kyc", "aml", "analyst 3", "insurance", "video editor", "video creator",
        "civil", "structural", "mechanical", "electrical", "chemical", "site engineer",
        "telecaller", "tele-caller", "bpo", "sales", "executive", "field", "counselor",
        "receptionist", "content writer", "digital marketing", "seo", "graphic designer",
        "data entry", "voice process", "bde", "accountant", "hr recruiter", "operations analyst",
        "finance domain", "principal architect", "director of", "engineering manager",
        "vice president", "head of engineering"
    ]
    for term in blacklist:
        if term in title_lower:
            return False

    # Positive whitelist for core software engineering roles (Python & Java stacks)
    whitelist = [
        "python", "django", "fastapi", "flask",
        "java", "spring", "springboot", "spring boot", "j2ee", "jvm",
        "backend", "back-end", "software engineer", "software developer",
        "full stack", "fullstack", "data engineer", "developer", "programmer",
        "ai engineer", "ai developer", "machine learning", "ml engineer", "sde", "ai"
    ]
    for term in whitelist:
        if len(term) <= 3:
            if re.search(rf"\b{re.escape(term)}\b", title_lower):
                return True
        else:
            if term in title_lower:
                return True

    return False
