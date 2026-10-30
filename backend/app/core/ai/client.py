"""Single entry point for all AI calls.

Nothing outside this module should import the Anthropic SDK — services call
functions defined here, and this module decides whether to hit the real API
or leave that decision to the caller via is_mock_mode().

Real prompts live in email_analysis_prompts.py / scam_scan_prompts.py so
they can be iterated on independently of the call plumbing here.
"""

import logging
from typing import TypeVar

import anthropic
from pydantic import BaseModel

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

logger = logging.getLogger("shield.ai")

# On a safety-classifier decline the API re-runs the request on a fallback
# model chosen by refusal category, inside the same call.
FALLBACK_BETA = "server-side-fallback-2026-07-01"

ResultT = TypeVar("ResultT", bound=BaseModel)


class AIUnavailableError(RuntimeError):
    """The AI call failed or declined. Services catch this and fall back to
    the rule-based engine rather than surfacing a 500 to the user."""


def is_mock_mode() -> bool:
    return settings.use_mock_ai or not settings.anthropic_api_key


def get_ai_client() -> anthropic.Anthropic | None:
    """Returns an Anthropic client, or None when running in mock mode."""
    if is_mock_mode():
        return None
    return anthropic.Anthropic(api_key=settings.anthropic_api_key, timeout=60.0)


def _parse(system: str, user_message: str, output_format: type[ResultT]) -> ResultT:
    client = get_ai_client()
    if client is None:
        raise RuntimeError("AI analysis called while in mock mode")

    try:
        response = client.beta.messages.parse(
            model=settings.anthropic_model,
            max_tokens=16000,
            system=system,
            messages=[{"role": "user", "content": user_message}],
            output_format=output_format,
            output_config={"effort": settings.anthropic_effort},
            betas=[FALLBACK_BETA],
            fallbacks="default",
        )
    except anthropic.RateLimitError as e:
        raise AIUnavailableError("rate limited") from e
    except anthropic.APIStatusError as e:
        logger.warning("Claude API error %s (request %s): %s", e.status_code, e.request_id, e.message)
        raise AIUnavailableError(f"API error {e.status_code}") from e
    except anthropic.APIConnectionError as e:
        raise AIUnavailableError("could not reach the Claude API") from e

    if response.stop_reason == "refusal":
        raise AIUnavailableError("Claude declined to analyze this text")
    if response.parsed_output is None:
        raise AIUnavailableError(f"no structured output (stop_reason={response.stop_reason})")

    return response.parsed_output


def analyze_email_via_ai(raw_email: str) -> EmailAnalysisResult:
    """Calls Claude to analyze an email. Raises AIUnavailableError on any
    failure; callers check is_mock_mode() first."""
    return _parse(EMAIL_ANALYSIS_SYSTEM_PROMPT, build_email_analysis_user_message(raw_email), EmailAnalysisResult)


def scan_text_via_ai(input_text: str) -> ScamScanResult:
    """Calls Claude to assess scam/phishing risk in arbitrary text. Raises
    AIUnavailableError on any failure; callers check is_mock_mode() first."""
    return _parse(SCAM_SCAN_SYSTEM_PROMPT, build_scam_scan_user_message(input_text), ScamScanResult)
