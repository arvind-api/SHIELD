from typing import Literal

from pydantic import BaseModel, Field


class ScanRequest(BaseModel):
    # Same bound as EmailAnalyzeRequest — comfortably covers any real
    # message/link/offer while bounding request size and analysis cost.
    input_text: str = Field(min_length=1, max_length=20_000)


class ScamScanResult(BaseModel):
    """The analysis fields themselves, independent of persistence — produced
    by either the mock rule engine or the Claude API."""

    risk_level: Literal["low", "medium", "high"]
    risk_score: int = Field(ge=0, le=100)
    category: str
    red_flags: list[str] = []
    reasoning: str


class ScanResponse(ScamScanResult):
    id: int
