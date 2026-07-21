# ============================================================
# ORZYN AI m2.0
# Notebook 08
# AI Models
# ============================================================

from __future__ import annotations

from pathlib import Path
import sys

BACKEND_DIR = Path.cwd().parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from dataclasses import dataclass
from typing import Any

from huggingface_hub import InferenceClient

from orzyn import (
    HF_TOKEN,
    get_active_model,
    get_active_repository,
)

model_config = get_active_model()


@dataclass(slots=True)
class AIResponse:

    model: str

    prompt: str

    response: str

    raw: Any

class AIInference:

    def __init__(
        self,
        model: str | None = None,
    ):

        config = get_active_model()

        self.provider = config.provider

        self.model = model or config.model

        self.client = InferenceClient(
            api_key=HF_TOKEN,
        )

    def _huggingface(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> AIResponse:

        completion = self.client.chat.completions.create(

            model=self.model,

            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],

            **kwargs,
        )

        text = completion.choices[0].message.content

        return AIResponse(

           model=self.model,

            prompt=prompt,

            response=text,

            raw=completion,
        )

    def generate(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> AIResponse:

        if self.provider == "huggingface":

            return self._huggingface(

                prompt,

                **kwargs,
            )

        raise ValueError(

            f"Unsupported provider: {self.provider}"

        )

ai = AIInference()

repo = get_active_repository()

prompt = f"""
You are an expert software architect.

The active GitHub repository is:

Owner: {repo.owner}
Repository: {repo.repository}
URL: {repo.url}

At this stage you only know the repository identity.
Do not invent implementation details.
Explain what additional repository data (commits, pull requests, issues, files, contributors, languages, etc.) would allow you to produce a comprehensive analysis.
"""

answer = ai.generate(
    prompt,
    max_tokens=1000,
    temperature=0.2,
)

print(answer.response)