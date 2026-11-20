import re
from typing import Dict, List, Tuple
from core.models import MatchResult
from core.vault import vault


class JobMatcher:
    """
    Intelligently inspects Job Descriptions to:
    1. Select the optimal resume (Java vs Python)
    2. Score the compatibility against Sachindra's verified dual stack
    3. Determine role applicability (filters out unrelated tech stacks & senior roles)
    4. Strictly uphold the 'Apply Anyway' CTC policy
    """

    JAVA_KEYWORDS = {
        "java", "spring", "spring boot", "springboot", "microservices", "hibernate",
        "jpa", "kafka", "jvm", "kotlin", "maven", "gradle", "postgresql", "redis",
        "restful", "rest api", "junit", "mockito", "multithreading", "j2ee"
    }

    PYTHON_KEYWORDS = {
        "python", "fastapi", "django", "flask", "asyncio", "pydantic", "pandas",
        "numpy", "ai", "llm", "rag", "pytorch", "tensorflow", "whisper",
        "langchain", "ollama", "nlp", "computer vision", "opencv"
    }

    CONFLICTING_STACKS = {
        "php", "laravel", "wordpress", "ruby", "rails", "golang", "go developer",
        "c#", ".net", "dotnet", "asp.net", "salesforce", "sap", "abap",
        "flutter", "react native", "swift", "ios developer", "objective-c",
        "cobol", "rust developer"
    }

    SENIOR_DISQUALIFIERS = {
        "principal", "director", "architect", "engineering manager",
        "tech lead", "team lead", "vp of", "head of", "sr. manager"
    }

    def match(self, title: str, description: str = "") -> MatchResult:
        content = f"{title.lower()} {description.lower()}"
        title_lower = title.lower()

        java_hits = [kw for kw in self.JAVA_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", content)]
        python_hits = [kw for kw in self.PYTHON_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", content)]

        java_score = len(java_hits)
        python_score = len(python_hits)

        # Title keyword boosting
        if any(k in title_lower for k in ["java", "spring", "springboot", "j2ee"]):
            java_score += 12
        if any(k in title_lower for k in ["python", "fastapi", "django", "flask", "ai"]):
            python_score += 12

        # Decision logic
        if java_score > python_score and java_score > 0:
            selected_type = "java"
            matched_kw = java_hits
            total_hits = java_score
            reasoning = f"Matched Java/Spring stack ({len(java_hits)} keywords: {', '.join(java_hits[:4]) if java_hits else 'Java Title'})"
        elif python_score > java_score and python_score > 0:
            selected_type = "python"
            matched_kw = python_hits
            total_hits = python_score
            reasoning = f"Matched Python/AI stack ({len(python_hits)} keywords: {', '.join(python_hits[:4]) if python_hits else 'Python Title'})"
        elif "java" in title_lower:
            selected_type = "java"
            matched_kw = ["java"]
            total_hits = 10
            reasoning = "Targeted Java Engineering Role"
        elif "python" in title_lower:
            selected_type = "python"
            matched_kw = ["python"]
            total_hits = 10
            reasoning = "Targeted Python Engineering Role"
        else:
            # Generic Backend / SDE role
            selected_type = "python"
            matched_kw = python_hits or java_hits or ["backend"]
            total_hits = max(python_score, java_score, 2)
            reasoning = "General Backend / SDE Role (Routed to Python Resume)"

        norm_score = min(1.0, max(0.4, total_hits / 8.0))
        resume_path = vault.get_resume(selected_type)

        return MatchResult(
            resume_type=selected_type,
            resume_path=str(resume_path) if resume_path else "",
            score=round(norm_score, 2),
            matched_keywords=matched_kw,
            reasoning=reasoning
        )

    def is_applicable(self, title: str, description: str = "", exp_text: str = "", url: str = "") -> Tuple[bool, MatchResult]:
        """
        Evaluates whether a role aligns with Sachindra's verified qualifications.
        Returns: (is_applicable: bool, match_result: MatchResult).
        """
        title_lower = title.lower()
        match_res = self.match(title, description)

        # 1. Fresher / Seniority Check (Candidate is 2026 Batch Fresher)
        from naukri.filters import is_fresher_job, is_valid_software_role
        is_fresh, reason = is_fresher_job(title, exp_text, url=url)
        if not is_fresh:
            match_res.reasoning = f"Filtered Out: {reason}"
            return False, match_res

        # 2. Seniority Check fallback
        if any(term in title_lower for term in self.SENIOR_DISQUALIFIERS):
            return False, match_res

        # 3. Conflicting Tech Stacks Check (if title is specifically for another language/stack)
        for stack in self.CONFLICTING_STACKS:
            if re.search(rf"\b{re.escape(stack)}\b", title_lower):
                # Only reject if neither Python nor Java is mentioned in the title
                if not any(k in title_lower for k in ["python", "java", "spring"]):
                    return False, match_res

        # 4. Basic Software Validation
        if not is_valid_software_role(title):
            return False, match_res

        return True, match_res


matcher = JobMatcher()
