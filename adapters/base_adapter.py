from abc import ABC, abstractmethod
from typing import Optional
from playwright.async_api import Page
from core.models import JobListing, ApplicationResult
from brain.base import BaseLLMProvider


class BaseAdapter(ABC):
    """Abstract interface for career portal application adapters."""

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Determines if this adapter can process the given job application URL."""
        pass

    @abstractmethod
    async def apply(self, job: JobListing, page: Page, brain: BaseLLMProvider) -> ApplicationResult:
        """Executes the autonomous application flow on the page."""
        pass
