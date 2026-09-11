import json
import logging
import os
from pathlib import Path

from ..provider import LLMProvider
from .mock_provider import MockProvider

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def _load_prompt(name: str) -> str:
    path = PROMPTS_DIR / name
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return ""


class OpenAIProvider(LLMProvider):
    def __init__(self) -> None:
        self._fallback = MockProvider()
        self._api_key = os.environ.get("OPENAI_API_KEY", "")
        self._model = os.environ.get("OPENAI_MODEL", "gpt-4o")
        self._system_prompt = _load_prompt("system_prompt.txt")
        self._case_prompt = _load_prompt("case_analysis.txt")

    def analyze(self, case: dict) -> str:
        if not self._api_key:
            logger.warning("OPENAI_API_KEY not set, falling back to mock provider")
            return self._fallback.analyze(case)

        try:
            import openai
        except ImportError:
            logger.warning("openai package not installed, falling back to mock provider")
            return self._fallback.analyze(case)

        try:
            client = openai.OpenAI(api_key=self._api_key)

            user_content = self._case_prompt + "\n\n" + json.dumps(case, indent=2, default=str)

            response = client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": self._system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.3,
                max_tokens=2000,
            )

            raw = response.choices[0].message.content or ""
            return raw.strip()

        except Exception as e:
            logger.error("OpenAI API call failed: %s — falling back to mock", e)
            return self._fallback.analyze(case)
