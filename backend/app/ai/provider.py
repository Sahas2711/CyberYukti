from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    def analyze(self, case: dict) -> str:
        """Return raw JSON string of AIAnalysis."""
        ...
