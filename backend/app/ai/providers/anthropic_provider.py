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


class AnthropicProvider(LLMProvider):
    def __init__(self) -> None:
        self._fallback = MockProvider()
        self._api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self._model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        self._system_prompt = _load_prompt("system_prompt.txt")
        self._case_prompt = _load_prompt("case_analysis.txt")

    def analyze(self, case: dict) -> str:
        if not self._api_key:
            logger.warning("ANTHROPIC_API_KEY not set, falling back to mock provider")
            return self._fallback.analyze(case)

        try:
            import anthropic
        except ImportError:
            logger.warning("anthropic package not installed, falling back to mock provider")
            return self._fallback.analyze(case)

        try:
            client = anthropic.Anthropic(api_key=self._api_key)

            user_content = self._case_prompt + "\n\n" + json.dumps(case, indent=2, default=str)

            response = client.messages.create(
                model=self._model,
                max_tokens=2000,
                system=self._system_prompt,
                messages=[
                    {"role": "user", "content": user_content},
                ],
            )

            raw = ""
            for block in response.content:
                if hasattr(block, "text"):
                    raw += block.text

            return raw.strip()

        except Exception as e:
            logger.error("Anthropic API call failed: %s — falling back to mock", e)
            return self._fallback.analyze(case)
