from typing import Literal

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """One exact excerpt from the analyzed text and why it's suspicious —
    the frontend highlights `quote` in place in the original input."""

    quote: str = Field(description="Exact, verbatim excerpt copied from the analyzed text (a few words)")
    reason: str = Field(description="Short reason this excerpt is a red flag")


# Which engine produced a result: Claude, the rule engine (no API key / mock
# mode forced), or the rule engine because the Claude call failed.
AnalysisMode = Literal["ai", "rules", "rules_fallback"]
