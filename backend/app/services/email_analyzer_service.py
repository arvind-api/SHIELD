"""Email Analyzer business logic.

analyze_email() branches on mock vs. real AI mode, then persists the result
to the EmailAnalysis table linked to the requesting user before returning.

The rule-based mock engine below is a real (if simple) heuristic analyzer —
not canned output — so the app is genuinely usable without an Anthropic API
key. It looks for: urgency/pressure language, requests for credentials or
payment info, suspicious links (raw IPs, shorteners, risky TLDs, brand
lookalike domains), sender/display-name mismatches, generic greetings, and
common phishing misspellings — then scores and flags based on what actually
matched in the input.
"""

import re

from sqlalchemy.orm import Session

from app.core.ai.client import analyze_email_via_ai, is_mock_mode
from app.core.text_signals import (
    LOOKALIKE_BRANDS,
    find_grammar_anomalies,
    find_suspicious_links,
)
from app.models.email_analysis import EmailAnalysis
from app.schemas.email_analyzer import EmailAnalysisResult, EmailAnalyzeRequest, EmailAnalyzeResponse

# --- Rule-based mock engine ------------------------------------------------

URGENCY_PATTERNS = [
    r"\burgent\b",
    r"\bimmediately\b",
    r"\bact now\b",
    r"\bright away\b",
    r"\bwithin 24 hours\b",
    r"\bfinal notice\b",
    r"\blast chance\b",
    r"\baccount (will be|has been) (suspended|locked|closed|terminated)\b",
    r"\bverify (your )?account\b",
    r"\bconfirm (your )?identity\b",
    r"\btime[- ]sensitive\b",
    r"\bexpires? (today|soon|in \d+ hours?)\b",
    r"\blegal action\b",
    r"\bfailure to (respond|comply)\b",
]

CREDENTIAL_PAYMENT_PATTERNS = [
    r"\bpassword\b",
    r"\bsocial security( number)?\b",
    r"\bssn\b",
    r"\bcredit card( number)?\b",
    r"\bcvv\b",
    r"\bbank (account|details|routing)\b",
    r"\bwire (transfer|funds|money)\b",
    r"\bgift card(s)?\b",
    r"\bbitcoin\b",
    r"\bcrypto(currency)?\b",
    r"\bverify your (account|identity|payment)\b",
    r"\bupdate your (payment|billing) information\b",
    r"\bconfirm your (password|pin|account number)\b",
]

GENERIC_GREETING_RE = re.compile(
    r"dear (customer|user|sir|madam|sir/madam|valued customer|account holder|member)\b",
    re.IGNORECASE,
)

FREE_EMAIL_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "aol.com", "icloud.com"}

FROM_HEADER_RE = re.compile(r'^From:\s*"?([^"<]*)"?\s*<([^<>]+)>', re.IGNORECASE | re.MULTILINE)

FRIENDLY_MARKERS = ["hope you're well", "hope you are well", "thanks so much", "looking forward", "cheers", "hi there"]
THREAT_MARKERS = ["suspended", "legal action", "terminated", "locked", "will be closed", "penalty", "unauthorized"]
MARKETING_MARKERS = ["unsubscribe", "% off", "shop now", "limited time offer", "sale", "discount code", "newsletter"]
REQUEST_MARKERS = ["please review", "could you", "can you", "attached", "let me know", "please send", "requesting"]


def _find_sender_mismatch(text: str) -> list[str]:
    signals = []
    match = FROM_HEADER_RE.search(text)
    if not match:
        return signals

    display_name, email_addr = match.groups()
    domain = email_addr.split("@")[-1].lower() if "@" in email_addr else ""
    display_lower = display_name.lower()

    for brand in LOOKALIKE_BRANDS:
        if brand in display_lower and brand not in domain.replace("-", ""):
            signals.append(f"sender display name claims '{brand}' but the email domain is '{domain}'")
            break

    if domain in FREE_EMAIL_DOMAINS and any(
        word in display_lower for word in ["support", "security", "billing", "accounts", "service", "team"]
    ):
        signals.append(f"claims to be an official department but was sent from a free email domain ({domain})")

    return signals


def _score_and_flag(text: str) -> tuple[int, list[str], int]:
    signals: list[str] = []
    score = 0

    urgency_hits = [p for p in URGENCY_PATTERNS if re.search(p, text, re.IGNORECASE)]
    if urgency_hits:
        score += min(25, 8 * len(urgency_hits))
        signals.append(f"urgency/pressure language detected ({len(urgency_hits)} phrase(s))")

    cred_hits = [p for p in CREDENTIAL_PAYMENT_PATTERNS if re.search(p, text, re.IGNORECASE)]
    if cred_hits:
        score += min(30, 10 * len(cred_hits))
        signals.append(f"requests for credentials/payment/personal info detected ({len(cred_hits)} phrase(s))")

    link_signals = find_suspicious_links(text)
    if link_signals:
        score += min(30, 12 * len(link_signals))
        signals.extend(link_signals)

    # A request for credentials/payment combined with a suspicious link is a
    # much stronger phishing signature than either alone — same fix applied
    # to guardian_scanner_service.py's mock engine (see that module for the
    # original diagnosis: this combo was landing genuine credential-phishing
    # emails at ~medium instead of high).
    if cred_hits and link_signals:
        score += 25
        signals.append(
            "combines a request for credentials/payment with a suspicious link — a classic phishing signature"
        )

    sender_signals = _find_sender_mismatch(text)
    if sender_signals:
        score += 20
        signals.extend(sender_signals)

    if GENERIC_GREETING_RE.search(text):
        score += 8
        signals.append("uses a generic greeting instead of the recipient's name")

    grammar_signals = find_grammar_anomalies(text)
    if grammar_signals:
        score += 7
        signals.extend(grammar_signals)

    return min(score, 100), signals, len(urgency_hits)


def _determine_tone(text: str, urgency_hit_count: int) -> str:
    lower = text.lower()
    if urgency_hit_count and any(m in lower for m in THREAT_MARKERS):
        return "threatening"
    if urgency_hit_count:
        return "urgent"
    if any(m in lower for m in FRIENDLY_MARKERS):
        return "friendly"
    return "neutral"


def _determine_intent(text: str, risk_score: int) -> str:
    lower = text.lower()
    if risk_score >= 55:
        return "phishing_attempt"
    if any(m in lower for m in MARKETING_MARKERS):
        return "marketing"
    if any(m in lower for m in REQUEST_MARKERS):
        return "request"
    return "notification"


def _risk_level(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 30:
        return "medium"
    return "low"


def _suggested_reply(risk_level: str, intent: str) -> str:
    if risk_level == "high":
        return (
            "Do not click any links, reply with personal information, or download attachments. "
            "This message shows strong signs of phishing — verify the sender through a separate, "
            "trusted channel (e.g. calling the organization directly), then report and delete it."
        )
    if risk_level == "medium":
        return (
            "Treat this email with caution. Before responding or clicking anything, verify the "
            "sender's identity through a channel you already trust."
        )
    if intent == "marketing":
        return "No reply needed — unsubscribe if you no longer want these emails."
    if intent == "request":
        return "Thanks for reaching out — I'll review this and get back to you shortly."
    return "No action needed; this appears to be a routine notification."


def _analyze_email_mock(raw_email: str) -> EmailAnalysisResult:
    score, signals, urgency_hit_count = _score_and_flag(raw_email)
    level = _risk_level(score)
    tone = _determine_tone(raw_email, urgency_hit_count)
    intent = _determine_intent(raw_email, score)
    reply = _suggested_reply(level, intent)

    return EmailAnalysisResult(
        tone=tone,
        intent=intent,
        phishing_signals=signals,
        risk_score=score,
        risk_level=level,
        suggested_reply=reply,
    )


# --- Service entry point ----------------------------------------------------


def analyze_email(db: Session, user_id: int, request: EmailAnalyzeRequest) -> EmailAnalyzeResponse:
    if is_mock_mode():
        result = _analyze_email_mock(request.raw_email)
    else:
        result = analyze_email_via_ai(request.raw_email)

    record = EmailAnalysis(
        user_id=user_id,
        raw_email=request.raw_email,
        result_json=result.model_dump_json(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return EmailAnalyzeResponse(id=record.id, **result.model_dump())
