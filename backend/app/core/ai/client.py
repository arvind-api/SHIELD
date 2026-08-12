"""Single entry point for all AI calls.

Nothing outside this module should import the Anthropic SDK — services call
functions defined here, and this module decides whether to hit the real API
or leave that decision to the caller via is_mock_mode().

Real prompts live in email_analysis_prompts.py / scam_scan_prompts.py so
they can be iterated on independently of the call plumbing here.
"""

from anthropic import Anthropic

from app.config import settings
from app.core.ai.email_analysis_prompts import (
    EMAIL_ANALYSIS_SYSTEM_PROMPT,
    build_email_analysis_user_message,
)
from app.core.ai.scam_scan_prompts import (
    SCAM_SCAN_SYSTEM_PROMPT,
    build_scam_scan_user_message,
)
from app.schemas.email_analyzer import EmailAnalysisResult
from app.schemas.guardian_scanner import ScamScanResult

MODEL = "claude-opus-5"


def is_mock_mode() -> bool:
    return settings.use_mock_ai or not settings.anthropic_api_key


def get_ai_client() -> Anthropic | None:
    """Returns an Anthropic client, or None when running in mock mode."""
    if is_mock_mode():
        return None
    return Anthropic(api_key=settings.anthropic_api_key)


def analyze_email_via_ai(raw_email: str) -> EmailAnalysisResult:
    """Calls Claude to analyze an email and returns a validated result.

    Callers are responsible for checking is_mock_mode() first — this
    raises if called without a configured API key.
    """
    client = get_ai_client()
    if client is None:
        raise RuntimeError("analyze_email_via_ai() called while in mock mode")

    response = client.messages.parse(
        model=MODEL,
        max_tokens=1024,
        system=EMAIL_ANALYSIS_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_email_analysis_user_message(raw_email)}],
        output_format=EmailAnalysisResult,
    )

    if response.stop_reason == "refusal":
        raise RuntimeError("Claude declined to analyze this email")

    return response.parsed_output


def scan_text_via_ai(input_text: str) -> ScamScanResult:
    """Calls Claude to assess scam/phishing risk in arbitrary text.

    Callers are responsible for checking is_mock_mode() first — this
    raises if called without a configured API key.
    """
    client = get_ai_client()
    if client is None:
        raise RuntimeError("scan_text_via_ai() called while in mock mode")

    response = client.messages.parse(
        model=MODEL,
        max_tokens=1024,
        system=SCAM_SCAN_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_scam_scan_user_message(input_text)}],
        output_format=ScamScanResult,
    )

    if response.stop_reason == "refusal":
        raise RuntimeError("Claude declined to analyze this text")

    return response.parsed_output
