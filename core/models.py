from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


class JobPortalType(str, Enum):
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    WORKDAY = "workday"
    LINKEDIN = "linkedin"
    NAUKRI = "naukri"
    GENERIC = "generic"


class ApplicationStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    QUEUED = "QUEUED"
    APPLYING = "APPLYING"
    APPLIED = "APPLIED"
    FAILED = "FAILED"
    INTERVIEW = "INTERVIEW"
    REJECTED = "REJECTED"
    NEEDS_INPUT = "NEEDS_INPUT"


class EducationRecord(BaseModel):
    institution: str
    degree: str
    field_of_study: str
    start_year: int
    end_year: int
    location: str


class ExperienceRecord(BaseModel):
    company: str
    role: str
    start_date: str
    end_date: str
    location: str
    description: List[str] = Field(default_factory=list)


class SalaryDetails(BaseModel):
    current_ctc: float = 600000.0  # 6 LPA
    expected_ctc: float = 750000.0  # 7.5 LPA
    currency: str = "INR"
    notice_period_days: int = 0
    notice_period_text: str = "Immediate"
    apply_anyway_rule: bool = True  # Always apply regardless of company's posted CTC
    volunteer_ctc: bool = False  # NEVER volunteer CTC unless explicitly asked


class WorkAuthorization(BaseModel):
    authorized_in_india: bool = True
    requires_sponsorship: bool = False
    willing_to_relocate: bool = True
    open_to_remote: bool = True


class UserProfile(BaseModel):
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    email: str
    phone: str
    city: str
    state: str = "Uttar Pradesh"
    country: str = "India"
    linkedin_url: str
    github_url: str
    portfolio_url: Optional[str] = None
    education: List[EducationRecord] = Field(default_factory=list)
    experience: List[ExperienceRecord] = Field(default_factory=list)
    total_experience_years: float = 0.3
    salary: SalaryDetails = Field(default_factory=SalaryDetails)
    authorization: WorkAuthorization = Field(default_factory=WorkAuthorization)
    skills: List[str] = Field(default_factory=list)
    custom_qa: Dict[str, str] = Field(default_factory=dict)

    @property
    def full_name(self) -> str:
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"


class MatchResult(BaseModel):
    resume_type: str  # "java" or "python"
    resume_path: str
    score: float  # 0.0 to 1.0
    matched_keywords: List[str] = Field(default_factory=list)
    reasoning: str


class JobListing(BaseModel):
    id: Optional[str] = None
    title: str
    company: str
    url: str
    portal_type: JobPortalType = JobPortalType.GENERIC
    location: Optional[str] = None
    description: Optional[str] = None
    posted_salary: Optional[str] = None
    match_result: Optional[MatchResult] = None
    status: ApplicationStatus = ApplicationStatus.DISCOVERED
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    applied_at: Optional[datetime] = None


class ApplicationResult(BaseModel):
    job_id: Optional[str] = None
    url: str
    success: bool
    status: ApplicationStatus
    message: str
    screenshot_path: Optional[str] = None
    applied_at: datetime = Field(default_factory=datetime.utcnow)
    fields_filled: Dict[str, str] = Field(default_factory=dict)
