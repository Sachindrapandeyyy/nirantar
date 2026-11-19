import asyncio
import json
from typing import List, Optional
from loguru import logger
from brain.gemini_provider import GeminiProvider
from core.models import UserProfile
from core.vault import vault

SYSTEM_PROMPT = """You are Nirantar's AI Recruiter Question Solver, acting strictly on behalf of the candidate:
Candidate Profile:
- Name: Sachindra Shekhar Pandey
- Email: sachindrapandey328@gmail.com | Phone: 7905604539
- Education: B.Tech in Computer Science & Engineering (2022-2026), CGPA 8.0+
- Key Expertise: Python, FastAPI, Django, PostgreSQL, Redis, RESTful APIs, Git, Docker, AI/ML
- Experience: 0.3 years (Software Engineer Intern @ NTPC Limited building FastAPI/React apps)
- Current CTC: 6,00,000 (6 LPA)
- Expected CTC: 7,50,000 (7.5 LPA)
- Notice Period: Immediate (0 days)
- Current Location: Noida, Uttar Pradesh (open to Delhi NCR, Bengaluru, Remote, Relocation: Yes)
- Work Authorization: Authorized to work in India, No sponsorship needed

Rules:
1. STRICT ZERO HALLUCINATION: Ground every answer in the candidate's real resume.
2. Return ONLY the direct answer. No pleasantries, no markdown explanations, no quotes.
3. If choices/options are given, choose the EXACT string from the options.
4. For yes/no questions (e.g., immediate joiner, willing to relocate, comfortable with shifts): answer 'Yes'.
5. For notice period: always 'Immediate'.
6. Keep single-input answers short (e.g. 'Immediate', '0.3', '750000', 'Python, FastAPI, PostgreSQL').
"""


class QuestionSolver:
    def __init__(self):
        self.llm = GeminiProvider()

    async def solve_question(self, question: str, options: Optional[List[str]] = None, profile: Optional[UserProfile] = None) -> str:
        """Solves a recruiter questionnaire or chatbot question using LLM with resume context."""
        profile = profile or vault.get_profile()
        q_clean = question.strip()

        # Quick rule check for common standard fields to maximize speed
        q_lower = q_clean.lower()
        if any(w in q_lower for w in ["notice", "joining", "join within", "how soon", "available"]):
            return "Immediate"
        if any(w in q_lower for w in ["relocate", "comfortable", "immediate joiner", "willing"]):
            return "Yes"
        if "expected ctc" in q_lower or "expected salary" in q_lower:
            return "750000"
        if "current ctc" in q_lower or "current salary" in q_lower:
            return "600000"

        # Ask LLM with resume grounding
        prompt = f"Recruiter Question:\n{q_clean}\n"
        if options:
            prompt += f"\nAvailable Options (choose strictly one):\n{json.dumps(options)}\n"
        prompt += "\nProvide the single most accurate, professional answer for Sachindra's application:"

        try:
            resp = await self.llm.generate_response(prompt, system_instruction=SYSTEM_PROMPT)
            answer = resp.strip().strip('"').strip("'")
            if answer:
                logger.info(f"LLM Solved Q: '{q_clean[:50]}...' -> '{answer}'")
                return answer
        except Exception as e:
            logger.warning(f"LLM question solve fallback triggered: {e}")

        # Intelligent fallback if LLM is unreachable
        if "experience" in q_lower or "exp" in q_lower:
            return "0.3"
        if "python" in q_lower or "skill" in q_lower:
            return "Python, FastAPI, Django, PostgreSQL, Git"
        return "Immediate"


solver = QuestionSolver()
