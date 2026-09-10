from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class ClassificationSuggestion:
    suggested_document_type: str | None
    confidence: float | None
    evidence: dict = field(default_factory=dict)
    model_version: str = ""
    generated_at: datetime | None = None


class DocumentClassifier(Protocol):
    """Contrato futuro: una sugerencia nunca equivale a confirmación humana."""

    def suggest(self, *, asset) -> ClassificationSuggestion: ...
