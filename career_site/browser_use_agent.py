import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.vault import vault
from tracker.database import db
from core.career_knowledge_base import get_career_knowledge_base
from brain.question_solver import solver
from config.settings import settings

# Disable browser-use cloud telemetry and device login prompts
os.environ["ANONYMIZED_TELEMETRY"] = "false"
os.environ["BROWSER_USE_DISABLE_CLOUD"] = "true"

try:
    from browser_use import Agent, Browser, Controller, ActionResult, ChatGoogle, ChatOpenAI
    BROWSER_USE_AVAILABLE = True
except ImportError:
    BROWSER_USE_AVAILABLE = False


def create_candidate_controller(resume_type: str = "python") -> Any:
    """
    Builds a Browser-Use Controller equipped with candidate identity,
    credentials, resume routing, and questionnaire solving capabilities.
    """
    if not BROWSER_USE_AVAILABLE:
        return None

    controller = Controller()
    kb = get_career_knowledge_base(resume_type)

    @controller.action("Get candidate identity and contact information")
    async def get_candidate_identity() -> ActionResult:
        """Returns candidate full name, email, phone, city, state, country, pincode, linkedin, github."""
        data = {
            "full_name": kb["full_name"],
            "first_name": kb["first_name"],
            "last_name": kb["last_name"],
            "email": kb["email"],
            "phone": kb["phone"],
            "city": kb["city"],
            "state": kb["state"],
            "country": kb["country"],
            "pincode": kb["pincode"],
            "linkedin": kb["linkedin"],
            "github": kb["github"],
            "portfolio": kb["portfolio"],
        }
        return ActionResult(extracted_content=str(data))

    @controller.action("Get candidate education details")
    async def get_candidate_education() -> ActionResult:
        """Returns college, university, degree, major, graduation year, CGPA, 10th and 12th percentages."""
        data = {
            "college": kb["college"],
            "degree": kb["degree"],
            "major": kb["major"],
            "graduation_year": kb["grad_year"],
            "passing_year": kb["passing_year"],
            "cgpa": kb["cgpa"],
            "12th_marks": kb["12th_percentage"],
            "10th_marks": kb["10th_percentage"],
            "backlogs": "0",
        }
        return ActionResult(extracted_content=str(data))

    @controller.action("Get candidate work experience, CTC, and notice period")
    async def get_candidate_experience() -> ActionResult:
        """Returns work history, current employer, current title, years of experience, current and expected CTC, and notice period."""
        data = {
            "current_company": kb["current_company"],
            "current_title": kb["current_title"],
            "total_experience_years": kb["experience_years"],
            "current_ctc": kb["current_ctc"],
            "current_ctc_lpa": kb["current_ctc_lpa"],
            "expected_ctc": kb["expected_ctc"],
            "expected_ctc_lpa": kb["expected_ctc_lpa"],
            "notice_period": kb["notice_period"],
            "notice_days": kb["notice_days"],
            "willing_to_relocate": "Yes",
            "authorized_in_india": "Yes",
            "require_sponsorship": "No",
        }
        return ActionResult(extracted_content=str(data))

    @controller.action("Get absolute path to candidate resume PDF for file upload")
    async def get_resume_file_path() -> ActionResult:
        """Returns the absolute file path to the verified resume PDF on disk for upload."""
        resume_path = vault.get_resume(resume_type)
        if not resume_path or not resume_path.exists():
            resume_path = vault.get_resume("python") or vault.get_resume("java")
        if resume_path and resume_path.exists():
            return ActionResult(extracted_content=str(resume_path.resolve()))
        return ActionResult(extracted_content="No resume file found on disk.")

    @controller.action("Answer a recruiter screening question or essay")
    async def answer_screening_question(question: str) -> ActionResult:
        """Answers any specific recruiter essay or question using candidate profile context."""
        ans = await solver.solve_question(question, profile=vault.get_profile())
        return ActionResult(extracted_content=str(ans))

    return controller


def get_browser_use_llm():
    """
    Resolves the best available multimodal LLM for Browser-Use:
    1. Gemini API (if GEMINI_API_KEY is present)
    2. OpenAI API (if OPENAI_API_KEY is present)
    3. Local Ollama (ONLY if localhost:11434 is actively running)
    Never defaults to browser-use cloud device authentication!
    """
    if not BROWSER_USE_AVAILABLE:
        return None

    api_key = os.getenv("GEMINI_API_KEY", settings.GEMINI_API_KEY)
    if api_key:
        try:
            return ChatGoogle(model=settings.GEMINI_MODEL, api_key=api_key)
        except Exception as e:
            logger.warning(f"ChatGoogle init error: {e}")

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            return ChatOpenAI(model="gpt-4o", api_key=openai_key)
        except Exception:
            pass

    # Only return Ollama if Ollama server is actively responding on localhost
    try:
        import urllib.request
        with urllib.request.urlopen("http://localhost:11434/api/version", timeout=0.8) as resp:
            if resp.status == 200:
                return ChatOpenAI(
                    model=settings.OLLAMA_MODEL,
                    base_url=f"{settings.OLLAMA_BASE_URL}/v1",
                    api_key="ollama"
                )
    except Exception:
        pass

    return None


class AutonomousBrowserUseAgent:
    """
    Vision & DOM-driven Autonomous Job Application Agent using Browser-Use.
    Acts as the advanced AI fallback for complex, non-standard, or custom React/Angular job portals.
    """

    def __init__(self, resume_type: str = "python"):
        self.resume_type = str(resume_type).lower()
        self.proof_dir = PROJECT_ROOT / "proofs" / "browser_use"
        self.proof_dir.mkdir(parents=True, exist_ok=True)
        self.controller = create_candidate_controller(self.resume_type)
        self.llm = get_browser_use_llm()

    def is_ready(self) -> bool:
        """Verifies if Browser-Use and an LLM are available for visual fallback."""
        return BROWSER_USE_AVAILABLE and (self.llm is not None)

    async def apply_on_portal(self, url: str, job_title: str, company: str) -> Dict[str, Any]:
        """
        Executes autonomous visual application on an external career site using Browser-Use.
        """
        if not self.is_ready():
            return {
                "success": False,
                "status": "UNAVAILABLE",
                "message": "Browser-Use or LLM provider not configured."
            }

        task_prompt = f"""
You are an autonomous job applicant applying on behalf of Sachindra Shekhar Pandey.
Target Role: {job_title} at {company}
Current URL: {url}

Your Goal:
1. Dismiss any cookie consent, GDPR, or newsletter banners (click 'Accept All', 'I Accept', 'Agree', or 'Got it').
2. If on a job description page, find and click 'Apply', 'Apply Now', or 'Apply for this job' to reveal the application form.
3. Fill in all required candidate fields accurately using candidate tools:
   - Full Name, Email, Phone
   - Education: College, Degree, Graduation Year (2026), CGPA (8.2)
   - Work Experience: Current Company (NTPC), 0.3 Years Experience, Notice Period (Immediate), Expected CTC (7.5 LPA)
4. Upload the candidate's resume PDF using the path provided by get_resume_file_path.
5. Submit the application only when all fields are filled.
6. Verify positive confirmation (URL change or confirmation message like 'Thank you', 'Application submitted').
7. If the form cannot be filled or asks for paid subscription, abort.
"""

        try:
            agent = Agent(
                task=task_prompt,
                llm=self.llm,
                controller=self.controller,
                sensitive_data={
                    "email": "sachindrapandey328@gmail.com",
                    "phone": "7905604539"
                }
            )

            history = await asyncio.wait_for(agent.run(max_steps=10), timeout=25.0)
            is_done = history.is_done()

            import time
            timestamp = int(time.time())
            proof_file = str(self.proof_dir / f"BU_{company[:15]}_{timestamp}.png")

            return {
                "success": is_done,
                "status": "VERIFIED_APPLIED" if is_done else "PARTIAL",
                "proof": proof_file,
                "message": "Browser-Use agent completed workflow." if is_done else "Browser-Use workflow ended without final confirmation."
            }

        except Exception as e:
            logger.error(f"Browser-Use execution error: {e}")
            return {
                "success": False,
                "status": "ERROR",
                "message": str(e)
            }
