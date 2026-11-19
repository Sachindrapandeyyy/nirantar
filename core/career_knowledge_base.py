import re
from typing import Dict, Any, Optional
from core.vault import vault

# Base Comprehensive Knowledge Base for Sachindra Shekhar Pandey
BASE_KNOWLEDGE_BASE = {
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

    # Work Experience Base
    "current_company": "NTPC Limited (Fortune 500)",
    "recent_company": "NTPC Limited (Fortune 500)",
    "current_title": "Software Engineer Intern",
    "current_role": "Software Engineer Intern",
    "experience_years": "0.3",
    "total_exp": "0.3",

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
}

# Python Stack Profile Customizations (Matches Python Resume)
PYTHON_PROFILE_DATA = {
    "skills": "Python, FastAPI, Django, Flask, PostgreSQL, Redis, REST APIs, Git, Docker, Microservices, AsyncIO",
    "why_join": "I am passionate about software engineering and eager to contribute my backend and Python development skills to build scalable systems. Having interned at NTPC Limited where I engineered FastAPI and PostgreSQL microservices with Redis caching, I thrive in fast-paced environments solving real problems.",
    "project_description": "At NTPC Limited, I developed an enterprise document approval system with Python FastAPI, PostgreSQL, and Redis. To handle high concurrency, I implemented asynchronous API endpoints and Redis caching, slashing database latency by 30% while securing endpoints with JWT-based RBAC.",
    "technical_strengths": "Python, FastAPI, Django, Flask, PostgreSQL, Redis, RESTful API design, Git, Docker, System Design Fundamentals, Database Optimization, Unit Testing."
}

# Java Stack Profile Customizations (Matches Java Resume)
JAVA_PROFILE_DATA = {
    "skills": "Java 17, Spring Boot 3, Spring Security, Hibernate/JPA, Apache Kafka, PostgreSQL, Redis, RESTful APIs, Microservices, Docker, Maven",
    "why_join": "I am passionate about software engineering and building robust, scalable enterprise systems with Java and Spring Boot. Having interned at NTPC Limited where I worked on enterprise microservices with PostgreSQL and Redis, I thrive in architecting low-latency, event-driven architectures.",
    "project_description": "In my Cloud-Native Enterprise Microservices project and at NTPC Limited, I engineered scalable backend services using Java 17, Spring Boot 3, and Apache Kafka. Integrated Redis caching and HikariCP connection pooling, slashing database query latency by 45% while enforcing Spring Security JWT/RBAC.",
    "technical_strengths": "Java 17, Spring Boot 3, Spring Security, Hibernate/JPA, Apache Kafka, PostgreSQL, Redis, Microservices Architecture, JUnit 5, Mockito, Docker, Maven."
}


def get_career_knowledge_base(resume_type: str = "python") -> Dict[str, Any]:
    """Dynamically builds candidate knowledge base tailored to selected resume stack."""
    kb = dict(BASE_KNOWLEDGE_BASE)
    if str(resume_type).lower() == "java":
        kb.update(JAVA_PROFILE_DATA)
    else:
        kb.update(PYTHON_PROFILE_DATA)
    return kb


# Default instance for backward compatibility
CAREER_KNOWLEDGE_BASE = get_career_knowledge_base("python")


def match_field_to_value(field_key: str, label: str = "", placeholder: str = "", resume_type: str = "python") -> Optional[str]:
    """
    Intelligently maps any form input (name, id, label, placeholder, aria-label)
    to the verified candidate knowledge base in O(1) time without consuming LLM tokens.
    Dynamically routes answers based on selected resume stack (Python vs Java).
    """
    kb = get_career_knowledge_base(resume_type)
    combined = f"{field_key} {label} {placeholder}".lower()

    # 1. Email (Top Priority)
    if "email" in combined:
        return kb["email"]

    # 2. Phone & Mobile
    if any(k in combined for k in ["phone", "mobile", "contact", "cell", "whatsapp"]):
        if "code" in combined:
            return kb["country_code"]
        return kb["phone"]

    # 3. Specific Names
    if any(k in combined for k in ["first_name", "firstname", "first name", "given name", "fname"]):
        return kb["first_name"]
    if any(k in combined for k in ["last_name", "lastname", "last name", "surname", "family name", "lname"]):
        return kb["last_name"]
    if any(k in combined for k in ["full_name", "fullname", "full name", "your name", "candidate name"]):
        return kb["full_name"]
    # Generic name only if not filename/username/company/school/college/university/institution/employer
    if re.search(r"\bname\b", combined) and not any(k in combined for k in ["file", "user", "company", "school", "college", "university", "institution", "org", "employer"]):
        return kb["full_name"]

    # 4. Social Links
    if "linkedin" in combined:
        return kb["linkedin"]
    if "github" in combined:
        return kb["github"]
    if any(k in combined for k in ["portfolio", "website", "personal site", "blog"]):
        return kb["portfolio"]

    # 5. Location & Address
    if any(k in combined for k in ["city", "current city", "current location"]):
        return kb["city"]
    if any(k in combined for k in ["state", "province"]):
        return kb["state"]
    if any(k in combined for k in ["country", "nationality"]):
        return kb["country"]
    if any(k in combined for k in ["pincode", "postal", "zip"]):
        return kb["pincode"]
    if "address" in combined or "street" in combined:
        return kb["address"]

    # 6. Education
    if any(k in combined for k in ["college", "university", "institution", "school name", "institute"]):
        return kb["college"]
    if any(k in combined for k in ["degree", "qualification", "education level", "highest degree"]):
        return kb["degree"]
    if any(k in combined for k in ["major", "discipline", "branch", "department", "stream", "field of study"]):
        return kb["major"]
    if any(k in combined for k in ["graduation year", "passing year", "year of passing", "passout", "batch", "grad year"]):
        return kb["passing_year"]
    if any(k in combined for k in ["cgpa", "gpa", "percentage", "aggregate", "score"]):
        if "12th" in combined or "hsc" in combined or "intermediate" in combined or "senior secondary" in combined:
            return kb["12th_percentage"]
        if "10th" in combined or "ssc" in combined or "matric" in combined or "secondary" in combined:
            return kb["10th_percentage"]
        return kb["cgpa"]
    if any(k in combined for k in ["backlog", "arrear"]):
        return kb["backlogs"]

    # 7. Work Experience & Current Employment
    if any(k in combined for k in ["current company", "current employer", "recent company", "employer", "present employer", "organization", "org"]):
        return kb["current_company"]
    if any(k in combined for k in ["current title", "current designation", "current role", "job title", "designation"]):
        return kb["current_title"]
    if any(k in combined for k in ["years of experience", "total experience", "overall experience", "experience in years", "total exp", "exp (in years)"]):
        return kb["experience_years"]
    if any(k in combined for k in ["skills", "tech stack", "technologies", "key skills", "core competencies", "technical skills"]):
        return kb["skills"]

    # 8. Screening Essays & Long-form Text
    if any(k in combined for k in ["why do you want", "why join", "why interested", "why should we hire", "cover letter", "tell us about yourself", "brief introduction", "about you"]) or (("why" in combined or "interest" in combined) and any(k in combined for k in ["join", "hire", "role", "company", "team"])):
        return kb["why_join"]
    if any(k in combined for k in ["challenging project", "describe a project", "major project", "recent project", "key project"]):
        return kb["project_description"]
    if any(k in combined for k in ["strengths", "core strength", "technical summary"]):
        return kb["technical_strengths"]

    # 9. Compensation & Notice Period
    if any(k in combined for k in ["expected ctc", "expected salary", "salary expectation", "desired salary", "compensation expectation"]):
        if "lpa" in combined or "lac" in combined or "lakh" in combined:
            return kb["expected_ctc_lpa"]
        return kb["expected_ctc"]
    if any(k in combined for k in ["current ctc", "current salary", "present ctc", "present salary"]):
        if "lpa" in combined or "lac" in combined or "lakh" in combined:
            return kb["current_ctc_lpa"]
        return kb["current_ctc"]
    if any(k in combined for k in ["notice period", "notice days", "notice", "availability", "how soon can you join", "earliest start date", "join within", "start date"]):
        return kb["notice_period"]

    # 10. Legal, Work Authorization & Relocation
    if any(k in combined for k in ["authorized", "authorization", "legally authorized", "eligible to work"]):
        return kb["work_authorization"]
    if any(k in combined for k in ["sponsorship", "require visa", "visa sponsorship", "require sponsorship"]):
        return kb["visa_sponsorship"]
    if any(k in combined for k in ["relocate", "relocation", "willing to relocate"]):
        return kb["willing_to_relocate"]
    if any(k in combined for k in ["remote", "hybrid", "in-office", "work from office"]):
        return kb["open_to_hybrid"]
    if any(k in combined for k in ["shift", "rotational", "night shift"]):
        return kb["open_to_shifts"]
    if any(k in combined for k in ["gender", "sex"]):
        return kb["gender"]
    if any(k in combined for k in ["18 years", "above 18", "age 18", "legal age"]):
        return kb["age_18"]
    if any(k in combined for k in ["how did you hear", "hear about", "source", "referral", "where did you find"]):
        return kb["source"]

    return None
