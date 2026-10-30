"""Service-level tests for the AI path (app/core/ai/client.py is stubbed —
no network). Covers: a failed Claude call falls back to the rule engine
instead of a 500, and AI evidence quotes that aren't verbatim in the input
are dropped before they reach the UI.
"""

import pytest

from app.core.ai.client import AIUnavailableError
from app.schemas.email_analyzer import EmailAnalysisResult, EmailAnalyzeRequest
from app.schemas.evidence import Evidence
from app.schemas.guardian_scanner import ScamScanResult, ScanRequest
from app.models.user import User
from app.services import email_analyzer_service, guardian_scanner_service

EMAIL = """From: hr-team@company-payroll-update.com
Subject: Action required

Please confirm your bank account number by replying to this email before end of day today."""


@pytest.fixture()
def user_id(db_session) -> int:
    user = User(email="tester@example.com", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    return user.id


def _raise(_text: str):
    raise AIUnavailableError("simulated outage")


def test_email_falls_back_to_rules_when_ai_fails(monkeypatch, db_session, user_id) -> None:
    monkeypatch.setattr(email_analyzer_service, "is_mock_mode", lambda: False)
    monkeypatch.setattr(email_analyzer_service, "analyze_email_via_ai", _raise)

    response = email_analyzer_service.analyze_email(db_session, user_id, EmailAnalyzeRequest(raw_email=EMAIL))

    assert response.analysis_mode == "rules_fallback"
    assert response.phishing_signals, "fallback should still produce a real rule-engine analysis"


def test_scan_falls_back_to_rules_when_ai_fails(monkeypatch, db_session, user_id) -> None:
    monkeypatch.setattr(guardian_scanner_service, "is_mock_mode", lambda: False)
    monkeypatch.setattr(guardian_scanner_service, "scan_text_via_ai", _raise)

    response = guardian_scanner_service.scan_text(db_session, user_id, ScanRequest(input_text=EMAIL))

    assert response.analysis_mode == "rules_fallback"


def test_ai_evidence_keeps_only_verbatim_quotes(monkeypatch, db_session, user_id) -> None:
    ai_result = EmailAnalysisResult(
        tone="urgent",
        intent="phishing_attempt",
        phishing_signals=["asks for bank details"],
        risk_score=88,
        risk_level="high",
        suggested_reply="Do not reply.",
        evidence=[
            Evidence(quote="bank account number", reason="asks for bank details"),
            Evidence(quote="send us your SSN", reason="paraphrase that isn't in the email"),
            Evidence(quote="BANK ACCOUNT NUMBER", reason="duplicate in another case"),
        ],
    )
    monkeypatch.setattr(email_analyzer_service, "is_mock_mode", lambda: False)
    monkeypatch.setattr(email_analyzer_service, "analyze_email_via_ai", lambda _text: ai_result)

    response = email_analyzer_service.analyze_email(db_session, user_id, EmailAnalyzeRequest(raw_email=EMAIL))

    assert response.analysis_mode == "ai"
    assert [item.quote for item in response.evidence] == ["bank account number"]


def test_scan_ai_result_passes_through(monkeypatch, db_session, user_id) -> None:
    ai_result = ScamScanResult(
        risk_level="low", risk_score=5, category="not_a_scam", red_flags=[], reasoning="Looks fine."
    )
    monkeypatch.setattr(guardian_scanner_service, "is_mock_mode", lambda: False)
    monkeypatch.setattr(guardian_scanner_service, "scan_text_via_ai", lambda _text: ai_result)

    response = guardian_scanner_service.scan_text(db_session, user_id, ScanRequest(input_text="hello"))

    assert response.analysis_mode == "ai"
    assert response.category == "not_a_scam"
