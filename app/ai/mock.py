import math

from app.ai.base import AIGenerationError, GenerationResult

FAIL_SENTINEL = "[FAIL]"
FAIL_PARTIAL_SENTINEL = "[FAIL_PARTIAL]"


def estimate_prompt_tokens(prompt: str) -> int:
    return max(1, math.ceil(len(prompt) / 4))


class MockProvider:
    def __init__(self, default_completion_tokens: int = 128):
        self.default_completion_tokens = default_completion_tokens

    def generate(
        self, prompt: str, max_tokens: int | None = None
    ) -> GenerationResult:
        prompt_tokens = estimate_prompt_tokens(prompt)
        completion_tokens = (
            max_tokens if max_tokens is not None else self.default_completion_tokens
        )

        if FAIL_SENTINEL in prompt:
            raise AIGenerationError("mock provider forced failure before usage")
        if FAIL_PARTIAL_SENTINEL in prompt:
            partial = GenerationResult(
                text="", prompt_tokens=prompt_tokens, completion_tokens=0
            )
            raise AIGenerationError(
                "mock provider failed after partial usage", partial_usage=partial
            )

        return GenerationResult(
            text=f"Mock completion for prompt: {prompt[:60]}",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
