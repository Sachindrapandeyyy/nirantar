import re
from typing import Dict, Any, Optional
from core.vault import vault

# Pre-computed Comprehensive Knowledge Base for Sachindra Shekhar Pandey
CAREER_KNOWLEDGE_BASE = {
    # Identity & Contact
    "first_name": "Sachindra",
    "last_name": "Pandey",
    "full_name": "Sachindra Shekhar Pandey",
    "email": "sachindrapandey328@gmail.com",
    "phone": "7905604539",
    "country_code": "+91",
    "full_phone": "+917905604539",
    "address": "Noida, Uttar Pradesh, India",
    "city": "Noida",
    "state": "Uttar Pradesh",
    "country": "India",
    "pincode": "201301",
    "postal_code": "201301",
    "zip": "201301",

    # Links
    "linkedin": "https://www.linkedin.com/in/sachindra-shekhar-pandey-73b45427b/",
    "github": "https://github.com/Sachindrapandeyyy",
    "portfolio": "https://sachindraos-portfolio.vercel.app",
    "website": "https://sachindraos-portfolio.vercel.app",

    # Education (Graduation / College)
    "college": "Shri Ramswaroop Memorial University",
    "university": "Shri Ramswaroop Memorial University",
    "school": "Shri Ramswaroop Memorial University",
    "degree": "B.Tech",
    "full_degree": "Bachelor of Technology",
    "major": "Computer Science & Engineering",
    "discipline": "Computer Science & Engineering",
    "branch": "Computer Science & Engineering",
    "field_of_study": "Computer Science & Engineering",
    "grad_year": "2026",
    "passing_year": "2026",
    "college_start_year": "2022",
    "college_end_year": "2026",
    "cgpa": "8.2",
    "gpa": "8.2",
    "backlogs": "0",
    "active_backlogs": "No",

    # Secondary & Higher Secondary Education
    "12th_percentage": "82.4",
    "12th_marks": "82.4%",
    "12th_board": "CBSE",
    "12th_year": "2022",
    "10th_percentage": "84.6",
    "10th_marks": "84.6%",
    "10th_board": "CBSE",
    "10th_year": "2020",

    # Work Experience
    "current_company": "NTPC Limited (Fortune 500)",
    "recent_company": "NTPC Limited (Fortune 500)",
    "current_title": "Software Engineer Intern",
    "current_role": "Software Engineer Intern",
    "experience_years": "0.3",
    "total_exp": "0.3",
    "skills": "Python, FastAPI, Django, PostgreSQL, Redis, REST APIs, Git, Docker, Microservices",

    # Compensation & Availability
    "current_ctc": "600000",
    "current_ctc_lpa": "6 LPA",
    "expected_ctc": "750000",
    "expected_ctc_lpa": "7.5 LPA",
    "notice_period": "Immediate",
    "notice_days": "0",
    "joining_date": "Immediate",
    "earliest_start_date": "Immediate",

    # Legal & Compliance
    "authorized_in_india": "Yes",
    "work_authorization": "Yes",
    "visa_sponsorship": "No",
    "require_sponsorship": "No",
    "willing_to_relocate": "Yes",
    "relocate": "Yes",
    "open_to_remote": "Yes",
    "open_to_hybrid": "Yes",
    "open_to_shifts": "Yes",
    "rotational_shifts": "Yes",
    "gender": "Male",
    "age_18": "Yes",
    "source": "Job Board",

    # Pre-computed Screening Essays
    "why_join": "I am passionate about software engineering and eager to contribute my backend and Python development skills to build scalable systems. Having interned at NTPC Limited where I engineered FastAPI and PostgreSQL microservices with Redis caching, I thrive in fast-paced environments solving real problems.",
    "project_description": "At NTPC Limited, I developed an enterprise document approval system with Python FastAPI, PostgreSQL, and Redis. To handle high concurrency, I implemented asynchronous API endpoints and Redis caching, slashing database latency by 30% while securing endpoints with JWT-based RBAC.",
    "technical_strengths": "Python, FastAPI, Django, PostgreSQL, Redis, RESTful API design, Git, Docker, System Design Fundamentals, Database Optimization, Unit Testing."
}


def match_field_to_value(field_key: str, label: str = "", placeholder: str = "") -> Optional[str]:
    """
    Intelligently maps any form input (name, id, label, placeholder, aria-label)
    to the verified candidate knowledge base in O(1) time without consuming LLM tokens.
    """
    combined = f"{field_key} {label} {placeholder}".lower()

    # 1. Email (Top Priority)
    if "email" in combined:
        return CAREER_KNOWLEDGE_BASE["email"]

    # 2. Phone & Mobile
    if any(k in combined for k in ["phone", "mobile", "contact", "cell", "whatsapp"]):
        if "code" in combined:
            return CAREER_KNOWLEDGE_BASE["country_code"]
        return CAREER_KNOWLEDGE_BASE["phone"]

    # 3. Specific Names
    if any(k in combined for k in ["first_name", "firstname", "first name", "given name", "fname"]):
        return CAREER_KNOWLEDGE_BASE["first_name"]
    if any(k in combined for k in ["last_name", "lastname", "last name", "surname", "family name", "lname"]):
        return CAREER_KNOWLEDGE_BASE["last_name"]
    if any(k in combined for k in ["full_name", "fullname", "full name", "your name", "candidate name"]):
        return CAREER_KNOWLEDGE_BASE["full_name"]
    # Generic name only if not filename/username/company/school/college/university/institution/employer
    if re.search(r"\bname\b", combined) and not any(k in combined for k in ["file", "user", "company", "school", "college", "university", "institution", "org", "employer"]):
        return CAREER_KNOWLEDGE_BASE["full_name"]

    # 4. Social Links
    if "linkedin" in combined:
        return CAREER_KNOWLEDGE_BASE["linkedin"]
    if "github" in combined:
        return CAREER_KNOWLEDGE_BASE["github"]
    if any(k in combined for k in ["portfolio", "website", "personal site", "blog"]):
        return CAREER_KNOWLEDGE_BASE["portfolio"]

    # 5. Location & Address
    if any(k in combined for k in ["city", "current city", "current location"]):
        return CAREER_KNOWLEDGE_BASE["city"]
    if any(k in combined for k in ["state", "province"]):
        return CAREER_KNOWLEDGE_BASE["state"]
    if any(k in combined for k in ["country", "nationality"]):
        return CAREER_KNOWLEDGE_BASE["country"]
    if any(k in combined for k in ["pincode", "postal", "zip"]):
        return CAREER_KNOWLEDGE_BASE["pincode"]
    if "address" in combined or "street" in combined:
        return CAREER_KNOWLEDGE_BASE["address"]

    # 6. Education
    if any(k in combined for k in ["college", "university", "institution", "school name", "institute"]):
        return CAREER_KNOWLEDGE_BASE["college"]
    if any(k in combined for k in ["degree", "qualification", "education level", "highest degree"]):
        return CAREER_KNOWLEDGE_BASE["degree"]
    if any(k in combined for k in ["major", "discipline", "branch", "department", "stream", "field of study"]):
        return CAREER_KNOWLEDGE_BASE["major"]
    if any(k in combined for k in ["graduation year", "passing year", "year of passing", "passout", "batch", "grad year"]):
        return CAREER_KNOWLEDGE_BASE["passing_year"]
    if any(k in combined for k in ["cgpa", "gpa", "percentage", "aggregate", "score"]):
        if "12th" in combined or "hsc" in combined or "intermediate" in combined or "senior secondary" in combined:
            return CAREER_KNOWLEDGE_BASE["12th_percentage"]
        if "10th" in combined or "ssc" in combined or "matric" in combined or "secondary" in combined:
            return CAREER_KNOWLEDGE_BASE["10th_percentage"]
        return CAREER_KNOWLEDGE_BASE["cgpa"]
    if any(k in combined for k in ["backlog", "arrear"]):
        return CAREER_KNOWLEDGE_BASE["backlogs"]

    # 7. Work Experience & Current Employment
    if any(k in combined for k in ["current company", "current employer", "recent company", "employer", "present employer", "organization", "org"]):
        return CAREER_KNOWLEDGE_BASE["current_company"]
    if any(k in combined for k in ["current title", "current designation", "current role", "job title", "designation"]):
        return CAREER_KNOWLEDGE_BASE["current_title"]
    if any(k in combined for k in ["years of experience", "total experience", "overall experience", "experience in years", "total exp", "exp (in years)"]):
        return CAREER_KNOWLEDGE_BASE["experience_years"]
    if any(k in combined for k in ["skills", "tech stack", "technologies", "key skills", "core competencies", "technical skills"]):
        return CAREER_KNOWLEDGE_BASE["skills"]

    # 8. Screening Essays & Long-form Text
    if any(k in combined for k in ["why do you want", "why join", "why interested", "why should we hire", "cover letter", "tell us about yourself", "brief introduction", "about you"]) or (("why" in combined or "interest" in combined) and any(k in combined for k in ["join", "hire", "role", "company", "team"])):
        return CAREER_KNOWLEDGE_BASE["why_join"]
    if any(k in combined for k in ["challenging project", "describe a project", "major project", "recent project", "key project"]):
        return CAREER_KNOWLEDGE_BASE["project_description"]
    if any(k in combined for k in ["strengths", "core strength", "technical summary"]):
        return CAREER_KNOWLEDGE_BASE["technical_strengths"]

    # 9. Compensation & Notice Period
    if any(k in combined for k in ["expected ctc", "expected salary", "salary expectation", "desired salary", "compensation expectation"]):
        if "lpa" in combined or "lac" in combined or "lakh" in combined:
            return CAREER_KNOWLEDGE_BASE["expected_ctc_lpa"]
        return CAREER_KNOWLEDGE_BASE["expected_ctc"]
    if any(k in combined for k in ["current ctc", "current salary", "present ctc", "present salary"]):
        if "lpa" in combined or "lac" in combined or "lakh" in combined:
            return CAREER_KNOWLEDGE_BASE["current_ctc_lpa"]
        return CAREER_KNOWLEDGE_BASE["current_ctc"]
    if any(k in combined for k in ["notice period", "notice days", "notice", "availability", "how soon can you join", "earliest start date", "join within", "start date"]):
        return CAREER_KNOWLEDGE_BASE["notice_period"]

    # 10. Legal, Work Authorization & Relocation
    if any(k in combined for k in ["authorized", "authorization", "legally authorized", "eligible to work"]):
        return CAREER_KNOWLEDGE_BASE["work_authorization"]
    if any(k in combined for k in ["sponsorship", "require visa", "visa sponsorship", "require sponsorship"]):
        return CAREER_KNOWLEDGE_BASE["visa_sponsorship"]
    if any(k in combined for k in ["relocate", "relocation", "willing to relocate"]):
        return CAREER_KNOWLEDGE_BASE["willing_to_relocate"]
    if any(k in combined for k in ["remote", "hybrid", "in-office", "work from office"]):
        return CAREER_KNOWLEDGE_BASE["open_to_hybrid"]
    if any(k in combined for k in ["shift", "rotational", "night shift"]):
        return CAREER_KNOWLEDGE_BASE["open_to_shifts"]
    if any(k in combined for k in ["gender", "sex"]):
        return CAREER_KNOWLEDGE_BASE["gender"]
    if any(k in combined for k in ["18 years", "above 18", "age 18", "legal age"]):
        return CAREER_KNOWLEDGE_BASE["age_18"]
    if any(k in combined for k in ["how did you hear", "hear about", "source", "referral", "where did you find"]):
        return CAREER_KNOWLEDGE_BASE["source"]

    return None
