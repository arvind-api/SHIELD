from typing import Literal

from pydantic import BaseModel, Field


class EmailAnalyzeRequest(BaseModel):
    # 20,000 chars comfortably covers a real email (headers + body) while
    # bounding request size and mock-engine/AI-call cost per request.
    raw_email: str = Field(min_length=1, max_length=20_000)


class EmailAnalysisResult(BaseModel):
    """The analysis fields themselves, independent of persistence — produced
    by either the mock rule engine or the Claude API."""

    tone: str
    intent: str
    phishing_signals: list[str] = []
    risk_score: int = Field(ge=0, le=100)
    risk_level: Literal["low", "medium", "high"]
    suggested_reply: str


class EmailAnalyzeResponse(EmailAnalysisResult):
    id: int
