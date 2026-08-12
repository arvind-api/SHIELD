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

import re

from sqlalchemy.orm import Session

from app.core.ai.client import is_mock_mode, scan_text_via_ai
from app.core.text_signals import find_grammar_anomalies, find_suspicious_links
from app.models.scam_scan import ScamScan
from app.schemas.guardian_scanner import ScamScanResult, ScanRequest, ScanResponse

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


def _find_impersonation_signals(text: str) -> list[str]:
    lower = text.lower()
    mentioned_entities = [e for e in IMPERSONATION_ENTITIES if e in lower]
    context_hits = [p for p in IMPERSONATION_CONTEXT_PATTERNS if re.search(p, text, re.IGNORECASE)]
    if mentioned_entities and context_hits:
        return [
            f"claims to be from {', '.join(mentioned_entities)} combined with pressure tactics "
            f"({len(context_hits)} phrase(s))"
        ]
    return []


def _category_hits(text: str) -> dict[str, list[str]]:
    hits = {}
    for category, patterns in CATEGORY_PATTERNS.items():
        matched = [p for p in patterns if re.search(p, text, re.IGNORECASE)]
        if matched:
            hits[category] = matched
    return hits


def _score_and_flag(text: str) -> tuple[int, list[str], dict[str, int]]:
    flags: list[str] = []
    score = 0
    category_scores: dict[str, int] = {}

    urgency_hits = [p for p in URGENCY_PATTERNS if re.search(p, text, re.IGNORECASE)]
    if urgency_hits:
        score += min(20, 6 * len(urgency_hits))
        flags.append(f"urgency/pressure language detected ({len(urgency_hits)} phrase(s))")

    money_hits = [p for p in MONEY_REQUEST_PATTERNS if re.search(p, text, re.IGNORECASE)]
    if money_hits:
        score += min(30, 10 * len(money_hits))
        flags.append(f"requests payment via gift cards/wire transfer/crypto ({len(money_hits)} phrase(s))")

    personal_info_hits = [p for p in PERSONAL_INFO_PATTERNS if re.search(p, text, re.IGNORECASE)]
    if personal_info_hits:
        score += min(25, 9 * len(personal_info_hits))
        flags.append(f"requests personal/financial information ({len(personal_info_hits)} phrase(s))")
        category_scores["phishing"] = category_scores.get("phishing", 0) + 9 * len(personal_info_hits)

    too_good_hits = [p for p in TOO_GOOD_PATTERNS if re.search(p, text, re.IGNORECASE)]
    if too_good_hits:
        score += min(15, 6 * len(too_good_hits))
        flags.append(f"too-good-to-be-true offer language detected ({len(too_good_hits)} phrase(s))")
        category_scores["fake_prize"] = category_scores.get("fake_prize", 0) + 6 * len(too_good_hits)

    link_signals = find_suspicious_links(text)
    if link_signals:
        score += min(25, 10 * len(link_signals))
        flags.extend(link_signals)
        category_scores["phishing"] = category_scores.get("phishing", 0) + 10 * len(link_signals)

    # A request for credentials/financial info *combined with* a suspicious
    # link is a much stronger phishing signature than either alone — score
    # each in isolation and this combo is still capped well under "high"
    # (e.g. urgency + personal_info + one link maxes out around 47), even
    # though it's the single most common shape of real credential phishing.
    if personal_info_hits and link_signals:
        score += 25
        flags.append("combines a request for personal/financial info with a suspicious link — a classic phishing signature")
        category_scores["phishing"] = category_scores.get("phishing", 0) + 25

    impersonation_signals = _find_impersonation_signals(text)
    if impersonation_signals:
        score += 20
        flags.extend(impersonation_signals)
        category_scores["impersonation"] = category_scores.get("impersonation", 0) + 20

    grammar_signals = find_grammar_anomalies(text)
    if grammar_signals:
        score += 6
        flags.extend(grammar_signals)

    for category, matched_patterns in _category_hits(text).items():
        weight = 12 * len(matched_patterns)
        score += min(30, weight)
        category_scores[category] = category_scores.get(category, 0) + weight
        flags.append(f"{category.replace('_', ' ')} language detected ({len(matched_patterns)} phrase(s))")

    return min(score, 100), flags, category_scores


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
    score, flags, category_scores = _score_and_flag(input_text)
    level = _risk_level(score)
    category = _determine_category(category_scores, score)
    reasoning = _build_reasoning(category, level, flags)

    return ScamScanResult(
        risk_level=level,
        risk_score=score,
        category=category,
        red_flags=flags,
        reasoning=reasoning,
    )


# --- Service entry point ----------------------------------------------------


def scan_text(db: Session, user_id: int, request: ScanRequest) -> ScanResponse:
    if is_mock_mode():
        result = _scan_text_mock(request.input_text)
    else:
        result = scan_text_via_ai(request.input_text)

    record = ScamScan(
        user_id=user_id,
        input_text=request.input_text,
        result_json=result.model_dump_json(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return ScanResponse(id=record.id, **result.model_dump())
