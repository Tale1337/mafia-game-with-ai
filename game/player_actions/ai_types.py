from dataclasses import dataclass


@dataclass(frozen=True)
class AIResponse:
    content: str
    reasoning: str | None = None
