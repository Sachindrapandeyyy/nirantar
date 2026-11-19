import json
from pathlib import Path
from typing import Dict, Optional, Tuple
from loguru import logger
from config.settings import settings
from core.models import (
    UserProfile,
    EducationRecord,
    ExperienceRecord,
    SalaryDetails,
    WorkAuthorization
)


class VaultManager:
    """
    Manages user identity documents, resumes, and verified profile data.
    Ensures ZERO hallucination by strictly drawing from the vault.
    """

    def __init__(self, vault_dir: Optional[Path] = None):
        self.vault_dir = vault_dir or settings.VAULT_DIR
        self.profile: Optional[UserProfile] = None
        self._doc_map: Dict[str, Path] = {}
        self.scan_documents()
        self.load_profile()

    def scan_documents(self):
        """Scans the vault directory for resumes and verification credentials."""
        if not self.vault_dir.exists():
            logger.warning(f"Vault directory not found: {self.vault_dir}")
            return

        for file_path in self.vault_dir.iterdir():
            if file_path.is_file():
                name_lower = file_path.name.lower()
                if "java" in name_lower and file_path.suffix == ".pdf":
                    self._doc_map["resume_java"] = file_path
                elif "python" in name_lower and file_path.suffix == ".pdf":
                    self._doc_map["resume_python"] = file_path
                elif "pan" in name_lower and file_path.suffix in [".pdf", ".jpeg", ".jpg"]:
                    self._doc_map["pan"] = file_path
                elif ("adhar" in name_lower or "aadhaar" in name_lower) and file_path.suffix == ".pdf":
                    self._doc_map["aadhaar"] = file_path
                elif ("marksheet" in name_lower or "10th" in name_lower) and file_path.suffix == ".pdf":
                    self._doc_map["marksheet"] = file_path
                elif "image" in name_lower or "photo" in name_lower:
                    self._doc_map["photo"] = file_path

        logger.info(f"Vault scanned {len(self._doc_map)} key documents: {list(self._doc_map.keys())}")

    def load_profile(self) -> UserProfile:
        """Loads profile from profile.json or initializes Sachindra's verified master profile."""
        profile_file = self.vault_dir / "profile.json"
        
        if profile_file.exists():
            try:
                data = json.loads(profile_file.read_text(encoding="utf-8"))
                self.profile = UserProfile(**data)
                return self.profile
            except Exception as e:
                logger.error(f"Failed to read {profile_file}: {e}. Initializing verified default.")

        # Default Verified Profile
        self.profile = UserProfile(
            first_name="Sachindra",
            middle_name="Shekhar",
            last_name="Pandey",
            email="sachindrapandey328@gmail.com",
            phone="7905604539",
            city="Noida",
            state="Uttar Pradesh",
            country="India",
            linkedin_url="https://www.linkedin.com/in/sachindra-shekhar-pandey-73b45427b/",
            github_url="https://github.com/Sachindrapandeyyy",
            portfolio_url="https://sachindraos-portfolio.vercel.app",
            total_experience_years=0.3,
            education=[
                EducationRecord(
                    institution="Shri Ramswaroop Memorial University",
                    degree="B.Tech",
                    field_of_study="Computer Science & Engineering",
                    start_year=2022,
                    end_year=2026,
                    location="Lucknow, India"
                )
            ],
            experience=[
                ExperienceRecord(
                    company="NTPC Limited (Fortune 500)",
                    role="Software Engineer Intern",
                    start_date="Jun 2025",
                    end_date="Jul 2025",
                    location="Shakti Nagar, India",
                    description=[
                        "Engineered enterprise core administrative applications with Python FastAPI/React and PostgreSQL.",
                        "Optimized database performance with Redis caching and B-tree indexing, slashing latency by 30%.",
                        "Architected secure RESTful endpoints with JWT & RBAC for document approval pipelines."
                    ]
                ),
                ExperienceRecord(
                    company="Skillzee (EdTech Startup)",
                    role="Software Engineer Intern",
                    start_date="Dec 2023",
                    end_date="Jan 2024",
                    location="Remote",
                    description=[
                        "Constructed scalable REST backend endpoints under 1,000+ concurrent request loads.",
                        "Configured GitHub Actions CI/CD pipelines achieving 80% code coverage."
                    ]
                )
            ],
            salary=SalaryDetails(
                current_ctc=600000.0,
                expected_ctc=750000.0,
                notice_period_days=0,
                notice_period_text="Immediate",
                apply_anyway_rule=True,
                volunteer_ctc=False
            ),
            authorization=WorkAuthorization(
                authorized_in_india=True,
                requires_sponsorship=False,
                willing_to_relocate=True,
                open_to_remote=True
            ),
            skills=[
                "Java", "Spring Boot", "Microservices", "REST APIs", "PostgreSQL",
                "Redis", "Kafka", "Docker", "Python", "FastAPI", "AsyncIO",
                "Git", "CI/CD", "Linux", "SQL", "JUnit", "Pytest"
            ],
            custom_qa={
                "notice_period": "Immediate",
                "current_ctc": "600000",
                "expected_ctc": "750000",
                "reason_for_change": "Seeking high-growth backend/systems engineering opportunities to apply distributed systems, cloud microservices, and AI integrations.",
                "relocation": "Yes, completely willing to relocate.",
                "work_authorization": "Yes, I am a citizen of India and legally authorized to work."
            }
        )

        # Save to vault for user reference
        try:
            profile_file.write_text(self.profile.model_dump_json(indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Could not save profile.json to vault: {e}")

        return self.profile

    def get_profile(self) -> UserProfile:
        """Returns the loaded verified profile."""
        if self.profile:
            return self.profile
        return self.load_profile()

    def get_resume(self, resume_type: str = "java") -> Optional[Path]:
        """Returns the absolute path to the requested resume PDF."""
        key = "resume_python" if resume_type.lower() == "python" else "resume_java"
        if key in self._doc_map and self._doc_map[key].exists():
            return self._doc_map[key]
        
        # Fallback search
        for k, p in self._doc_map.items():
            if "resume" in k:
                return p
        return None

    def get_document(self, doc_type: str) -> Optional[Path]:
        """Retrieves path for government IDs, marksheets, or profile pictures."""
        doc_type_lower = doc_type.lower()
        for key, path in self._doc_map.items():
            if doc_type_lower in key:
                return path
        return None


vault = VaultManager()
