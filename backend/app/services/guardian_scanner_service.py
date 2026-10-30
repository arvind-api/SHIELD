"""Guardian Scam Scanner business logic.

scan_text() branches on mock vs. real AI mode, then persists the result to
the ScamScan table linked to the requesting user before returning.

The rule-based mock engine below is a real heuristic analyzer — not canned
output — so the app is genuinely usable without an Anthropic API key. It
looks for: urgency/pressure tactics, requests for money (gift cards, wire
transfer, crypto), requests for personal/financial info, too-good-to-be-true
offers, impersonation of known entities (banks, government agencies,
delivery services) paired with pressure tactics, suspicious links, and
scam-category-specific language (fake prizes, advance-fee/inheritance
scams, romance scams, investment scams) — then scores and categorizes
based on what actually matched in the input.
"""

import json
import logging

from sqlalchemy.orm import Session

from app.core.ai.client import AIUnavailableError, is_mock_mode, scan_text_via_ai
from app.core.text_signals import build_evidence, find_grammar_anomalies, matched_phrases, scan_links
from app.models.scam_scan import ScamScan
from app.schemas.evidence import AnalysisMode
from app.schemas.guardian_scanner import ScamScanResult, ScanRequest, ScanResponse

logger = logging.getLogger("shield.guardian_scanner")

# --- Rule-based mock engine ------------------------------------------------

URGENCY_PATTERNS = [
    r"\burgent\b",
    r"\bact now\b",
    r"\bimmediately\b",
    r"\bright away\b",
    r"\bwithin 24 hours\b",
    r"\blimited time\b",
    r"\bexpires? (today|soon|in \d+ hours?)\b",
    r"\bdo not (ignore|delay)\b",
    r"\btime[- ]sensitive\b",
    r"\blast chance\b",
    r"\bfinal (notice|warning)\b",
    r"\bact fast\b",
    r"\b(by|before) (the )?end of (the )?(day|business)\b",
    r"\b(otherwise|or) (your|it|the)\b[^.]{0,60}\bwill be (closed|suspended|locked|blocked|frozen|cancell?ed|delayed)\b",
]

# The subset of pressure that threatens a consequence on a deadline. Plain
# expiry notices ("this reset link will expire in 1 hour") are deliberately
# not here — legit password resets say that, and they mention passwords.
DEADLINE_THREAT_PATTERNS = [
    r"\bwithin 24 hours\b",
    r"\bfinal (notice|warning)\b",
    r"\bdo not (ignore|delay)\b",
    r"\b(by|before) (the )?end of (the )?(day|business)\b",
    r"\b(otherwise|or) (your|it|the)\b[^.]{0,60}\bwill be (closed|suspended|locked|blocked|frozen|cancell?ed|delayed)\b",
]

MONEY_REQUEST_PATTERNS = [
    r"\bgift card(s)?\b",
    r"\bwire (transfer|money|funds)\b",
    r"\bwestern union\b",
    r"\bmoneygram\b",
    r"\bbitcoin\b",
    r"\bcrypto(currency)?\b",
    r"\bprocessing fee\b",
    r"\bclearance fee\b",
    r"\bcustoms fee\b",
    r"\bshipping fee\b",
    r"\bsend (money|cash|funds)\b",
    r"\bpay(ment)? (upfront|in advance)\b",
    r"\bactivation fee\b",
]

PERSONAL_INFO_PATTERNS = [
    r"\bpassword\b",
    r"\bsocial security( number)?\b",
    r"\bssn\b",
    r"\bcredit card( number)?\b",
    r"\bcvv\b",
    r"\bbank (account|details|routing)\b",
    r"\bverify your (account|identity|payment)\b",
    r"\bconfirm your (password|pin|account number)\b",
    r"\bdate of birth\b",
    r"\bpin number\b",
    r"\b(login|log-in|sign[- ]in|account) (credentials|details)\b",
    r"\baccount number\b",
    r"\b(otp|one[- ]time (pass)?code)\b",
]

TOO_GOOD_PATTERNS = [
    r"\b100% (free|guaranteed)\b",
    r"\bno risk\b",
    r"\btoo good to be true\b",
    r"\bno purchase necessary\b",
    r"\byou don'?t need to pay\b",
    r"\bdouble your money\b",
    r"\bfree (money|cash)\b",
]

CATEGORY_PATTERNS: dict[str, list[str]] = {
    "fake_prize": [
        r"\byou('| ha)ve (been selected|won)\b",
        r"\bcongratulations,? you\b",
        r"\bclaim your prize\b",
        r"\blottery\b",
        r"\bsweepstakes\b",
        r"\bselected winner\b",
        r"\bfree gift\b",
        r"\byou are a winner\b",
        r"\bcash prize\b",
    ],
    "advance_fee_scam": [
        r"\bnext of kin\b",
        r"\binheritance\b",
        r"\bbeneficiary\b",
        r"\bunclaimed funds\b",
        r"\brelease (your|the) funds\b",
        r"\btransfer (the|your) (money|funds)\b",
    ],
    "romance_scam": [
        r"\bmy love\b",
        r"\bfallen (in love )?for you\b",
        r"\bstranded\b",
        r"\bdeployed (overseas|to)\b",
        r"\bneed (your )?help to (get home|come home)\b",
        r"\bhospital bill(s)?\b",
        r"\bwidow(er)?\b",
        r"\bmeet (you )?in person\b",
        r"\bmilitary (base|deployment)\b",
    ],
    "investment_scam": [
        r"\bguaranteed returns?\b",
        r"\bdouble your (money|investment)\b",
        r"\brisk[- ]free investment\b",
        r"\bhigh returns? guaranteed\b",
        r"\binvestment opportunity\b",
        r"\bforex trading\b",
        r"\blimited slots\b",
        r"\bact now to invest\b",
    ],
}

IMPERSONATION_ENTITIES = [
    "irs",
    "social security administration",
    "ssa",
    "paypal",
    "amazon",
    "microsoft",
    "apple",
    "usps",
    "fedex",
    "dhl",
    "ups",
    "your bank",
    "tech support",
    "netflix",
]

IMPERSONATION_CONTEXT_PATTERNS = [
    r"\bpackage could not be delivered\b",
    r"\bverify your delivery address\b",
    r"\bcomputer has a virus\b",
    r"\bcall this number\b",
    r"\baccount has been (compromised|locked|suspended)\b",
    r"\btax (refund|debt)\b",
    r"\blegal action\b",
    r"\barrest warrant\b",
]


def _find_impersonation_signals(text: str) -> tuple[list[str], list[str]]:
    """(flags, matched context phrases)."""
    lower = text.lower()
    mentioned_entities = [e for e in IMPERSONATION_ENTITIES if e in lower]
    context_hits = matched_phrases(text, IMPERSONATION_CONTEXT_PATTERNS)
    if mentioned_entities and context_hits:
        flags = [
            f"claims to be from {', '.join(mentioned_entities)} combined with pressure tactics "
            f"({len(context_hits)} phrase(s))"
        ]
        return flags, context_hits
    return [], []


def _category_hits(text: str) -> dict[str, list[str]]:
    hits = {}
    for category, patterns in CATEGORY_PATTERNS.items():
        matched = matched_phrases(text, patterns)
        if matched:
            hits[category] = matched
    return hits


def _score_and_flag(text: str) -> tuple[int, list[str], dict[str, int], list[tuple[str, str]]]:
    flags: list[str] = []
    # (exact excerpt, reason) pairs for the UI to highlight in the input.
    evidence: list[tuple[str, str]] = []
    score = 0
    category_scores: dict[str, int] = {}

    urgency_hits = matched_phrases(text, URGENCY_PATTERNS)
    if urgency_hits:
        score += min(20, 6 * len(urgency_hits))
        flags.append(f"urgency/pressure language detected ({len(urgency_hits)} phrase(s))")
        evidence += [(phrase, "pressure or deadline") for phrase in urgency_hits]

    money_hits = matched_phrases(text, MONEY_REQUEST_PATTERNS)
    if money_hits:
        score += min(30, 10 * len(money_hits))
        flags.append(f"requests payment via gift cards/wire transfer/crypto ({len(money_hits)} phrase(s))")
        evidence += [(phrase, "hard-to-reverse payment method or fee") for phrase in money_hits]

    personal_info_hits = matched_phrases(text, PERSONAL_INFO_PATTERNS)
    if personal_info_hits:
        score += min(25, 9 * len(personal_info_hits))
        flags.append(f"requests personal/financial information ({len(personal_info_hits)} phrase(s))")
        category_scores["phishing"] = category_scores.get("phishing", 0) + 9 * len(personal_info_hits)
        evidence += [(phrase, "asks for personal or financial info") for phrase in personal_info_hits]

    # Link-free credential phishing ("reply with your account number and
    # PIN within 24 hours or it will be closed") never reaches the link
    # combo below — the info request under a deadline is the signature.
    if personal_info_hits and matched_phrases(text, DEADLINE_THREAT_PATTERNS):
        score += 20
        flags.append("pairs a request for personal info with a deadline or threat")
        category_scores["phishing"] = category_scores.get("phishing", 0) + 20

    too_good_hits = matched_phrases(text, TOO_GOOD_PATTERNS)
    if too_good_hits:
        score += min(15, 6 * len(too_good_hits))
        flags.append(f"too-good-to-be-true offer language detected ({len(too_good_hits)} phrase(s))")
        category_scores["fake_prize"] = category_scores.get("fake_prize", 0) + 6 * len(too_good_hits)
        evidence += [(phrase, "too good to be true") for phrase in too_good_hits]

    link_hits = scan_links(text)
    link_signals = [signal for _, signal in link_hits]
    if link_signals:
        score += min(25, 10 * len(link_signals))
        flags.extend(link_signals)
        category_scores["phishing"] = category_scores.get("phishing", 0) + 10 * len(link_signals)
        evidence += link_hits

    # A request for credentials/financial info *combined with* a suspicious
    # link is a much stronger phishing signature than either alone — score
    # each in isolation and this combo is still capped well under "high"
    # (e.g. urgency + personal_info + one link maxes out around 47), even
    # though it's the single most common shape of real credential phishing.
    if personal_info_hits and link_signals:
        score += 25
        flags.append("combines a request for personal/financial info with a suspicious link — a classic phishing signature")
        category_scores["phishing"] = category_scores.get("phishing", 0) + 25

    impersonation_signals, impersonation_phrases = _find_impersonation_signals(text)
    if impersonation_signals:
        score += 20
        flags.extend(impersonation_signals)
        category_scores["impersonation"] = category_scores.get("impersonation", 0) + 20
        evidence += [(phrase, "impersonation pressure tactic") for phrase in impersonation_phrases]

    grammar_signals = find_grammar_anomalies(text)
    if grammar_signals:
        score += 6
        flags.extend(grammar_signals)

    for category, phrases in _category_hits(text).items():
        weight = 12 * len(phrases)
        score += min(30, weight)
        category_scores[category] = category_scores.get(category, 0) + weight
        label = category.replace("_", " ")
        flags.append(f"{label} language detected ({len(phrases)} phrase(s))")
        evidence += [(phrase, f"typical of a {label}") for phrase in phrases]

    return min(score, 100), flags, category_scores, evidence


def _risk_level(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 30:
        return "medium"
    return "low"


def _determine_category(category_scores: dict[str, int], score: int) -> str:
    if score < 15:
        return "not_a_scam"
    if category_scores:
        return max(category_scores, key=category_scores.get)
    return "phishing"


def _build_reasoning(category: str, risk_level: str, flags: list[str]) -> str:
    if not flags:
        return "No significant scam indicators were found in this text."
    category_label = category.replace("_", " ")
    flag_summary = "; ".join(flags)
    return (
        f"This text was flagged as {risk_level} risk, most consistent with a {category_label} pattern. "
        f"Specific indicators: {flag_summary}."
    )


def _scan_text_mock(input_text: str) -> ScamScanResult:
    score, flags, category_scores, evidence = _score_and_flag(input_text)
    level = _risk_level(score)
    category = _determine_category(category_scores, score)
    reasoning = _build_reasoning(category, level, flags)

    return ScamScanResult(
        risk_level=level,
        risk_score=score,
        category=category,
        red_flags=flags,
        reasoning=reasoning,
        evidence=build_evidence(input_text, evidence),
    )


# --- Service entry point ----------------------------------------------------


def _run_scan(input_text: str) -> tuple[ScamScanResult, AnalysisMode]:
    if is_mock_mode():
        return _scan_text_mock(input_text), "rules"
    try:
        result = scan_text_via_ai(input_text)
    except AIUnavailableError as e:
        logger.warning("AI scan unavailable (%s); falling back to rule engine", e)
        return _scan_text_mock(input_text), "rules_fallback"
    result.evidence = build_evidence(input_text, [(item.quote, item.reason) for item in result.evidence])
    return result, "ai"


def scan_text(db: Session, user_id: int, request: ScanRequest) -> ScanResponse:
    result, mode = _run_scan(request.input_text)

    record = ScamScan(
        user_id=user_id,
        input_text=request.input_text,
        result_json=json.dumps({**result.model_dump(), "analysis_mode": mode}),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return ScanResponse(id=record.id, analysis_mode=mode, **result.model_dump())
