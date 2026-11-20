import re
from typing import Tuple


def is_fresher_job(title: str, exp_text: str = "", url: str = "") -> Tuple[bool, str]:
    """
    Strictly verifies if a job is suited for a Fresher / 2026 Batch Graduate (0-2 Years).
    Filters out Senior, Lead, Architect, and jobs requiring 3+ years of experience.
    Strictly rejects any upper experience bracket >= 4 years (e.g. 0-5, 0-7, 1-4, 2-5).
    Returns: (is_fresher: bool, reason: str).
    """
    title_lower = title.lower()
    exp_lower = exp_text.lower().strip()
    url_lower = url.lower().strip()

    # 1. Seniority Titles & High-Level Roles in Title
    senior_titles = [
        "senior", "sr.", "sr ", "lead", "principal", "staff", "architect",
        "engineering manager", "tech lead", "team lead", "director", "head of",
        "vp of", "vice president", "associate manager", "project manager",
        "specialist", "expert"
    ]
    for st in senior_titles:
        if st in title_lower:
            return False, f"Senior title detected ('{st}')"

    # 2. Seniority & Experience slugs in Job URL (e.g. -0-to-5-years, -0-to-7-years, -senior-)
    if url_lower:
        url_senior_slugs = ["-senior-", "-lead-", "-architect-", "-tech-lead-", "-manager-"]
        for us in url_senior_slugs:
            if us in url_lower:
                return False, f"Senior slug in URL ('{us}')"

        url_exp_match = re.search(r"(\d+)-to-(\d+)-years?", url_lower)
        if url_exp_match:
            u_min = int(url_exp_match.group(1))
            u_max = int(url_exp_match.group(2))
            if u_max >= 4:
                return False, f"URL experience bracket {u_min}-to-{u_max} years exceeds entry level"
            if u_min >= 3:
                return False, f"URL experience bracket {u_min}-to-{u_max} years requires >= 3 yrs"

    # 3. Explicit High Years in Title (e.g. 'Python Dev (3+ Years)', 'Java 4-8 Yrs', '0-5 Yrs')
    title_exp_match = re.search(r"(\d+)\s*(?:\+|-\s*(\d+))\s*(?:yrs?|years?)", title_lower)
    if title_exp_match:
        min_yrs = int(title_exp_match.group(1))
        max_yrs = int(title_exp_match.group(2)) if title_exp_match.group(2) else None
        if max_yrs is not None and max_yrs >= 4:
            return False, f"Title experience bracket {min_yrs}-{max_yrs} Yrs exceeds entry level"
        if min_yrs >= 3:
            return False, f"Title requires {min_yrs}+ years experience"

    # 4. Experience Range on Job Card / Tuple (e.g. '0-1 Yrs', '0-5 Yrs', '0-7 Yrs', '3-5 Yrs')
    if exp_lower:
        range_match = re.search(r"(\d+)\s*-\s*(\d+)", exp_lower)
        if range_match:
            min_exp = int(range_match.group(1))
            max_exp = int(range_match.group(2))
            # Any job with upper bracket >= 4 (0-4, 0-5, 0-7, 1-4, 2-5, 3-5) is NOT for freshers!
            if max_exp >= 4:
                return False, f"Experience bracket {min_exp}-{max_exp} Yrs exceeds entry level (max allowed: 3 yrs)"
            if min_exp >= 3:
                return False, f"Experience bracket {min_exp}-{max_exp} Yrs is senior level (requires >= 3 yrs)"

        plus_match = re.search(r"(\d+)\+", exp_lower)
        if plus_match:
            min_exp = int(plus_match.group(1))
            if min_exp >= 3:
                return False, f"Experience requires {min_exp}+ Yrs"

    return True, "Valid Fresher / Junior role (0-2 Yrs)"


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
