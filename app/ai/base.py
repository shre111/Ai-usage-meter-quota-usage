from dataclasses import dataclass
from typing import Protocol


@dataclass
class GenerationResult:
    text: str
    prompt_tokens: int
    completion_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class AIGenerationError(Exception):
    def __init__(self, message: str, partial_usage: GenerationResult | None = None):
        super().__init__(message)
        self.partial_usage = partial_usage


class AIProvider(Protocol):
    def generate(self, prompt: str, max_tokens: int | None = None) -> GenerationResult:
        ...
