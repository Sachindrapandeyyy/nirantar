import re
from typing import Dict, List, Tuple
from core.models import MatchResult
from core.vault import vault


class JobMatcher:
    """
    Intelligently inspects Job Descriptions to:
    1. Select the optimal resume (Java vs Python)
    2. Score the compatibility
    3. Strictly uphold the 'Apply Anyway' CTC policy (never drop a job based on posted salary)
    """

    JAVA_KEYWORDS = {
        "java", "spring", "spring boot", "springboot", "microservices", "hibernate",
        "jpa", "kafka", "jvm", "kotlin", "maven", "gradle", "postgresql", "redis",
        "restful", "rest api", "junit", "mockito", "multithreading"
    }

    PYTHON_KEYWORDS = {
        "python", "fastapi", "django", "flask", "asyncio", "pydantic", "pandas",
        "numpy", "ai", "llm", "rag", "pytorch", "tensorflow", "whisper",
        "langchain", "ollama", "nlp", "computer vision", "opencv"
    }

    def match(self, title: str, description: str = "") -> MatchResult:
        content = f"{title.lower()} {description.lower()}"
        
        java_hits = [kw for kw in self.JAVA_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", content)]
        python_hits = [kw for kw in self.PYTHON_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", content)]

        # Scoring
        java_score = len(java_hits)
        python_score = len(python_hits)

        # Title gets heavy weighting
        title_lower = title.lower()
        if "java" in title_lower or "spring" in title_lower:
            java_score += 10
        elif "python" in title_lower or "ai" in title_lower or "fastapi" in title_lower:
            python_score += 10

        # Choose best resume
        if python_score > java_score:
            selected_type = "python"
            matched_kw = python_hits
            total_hits = python_score
            reasoning = f"Matched {len(python_hits)} Python/AI keywords (e.g., {', '.join(python_hits[:4])})"
        else:
            selected_type = "java"
            matched_kw = java_hits
            total_hits = java_score
            reasoning = f"Matched {len(java_hits)} Java/Spring keywords (e.g., {', '.join(java_hits[:4])})"

        # Normalized compatibility score (0.0 to 1.0)
        norm_score = min(1.0, max(0.4, total_hits / 8.0))
        resume_path = vault.get_resume(selected_type)

        return MatchResult(
            resume_type=selected_type,
            resume_path=str(resume_path) if resume_path else "",
            score=round(norm_score, 2),
            matched_keywords=matched_kw,
            reasoning=reasoning
        )


matcher = JobMatcher()
