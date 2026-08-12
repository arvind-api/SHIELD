"""Regression tests for the Email Analyzer's rule-based mock engine
(app/services/email_analyzer_service.py::_analyze_email_mock).

Mirrors tests/test_guardian_scanner_mock.py — same structure, same
risk_level-not-risk_score assertion philosophy. Sample texts came from a
diagnostic run against the live engine (see the "combines a request for
credentials/payment with a suspicious link" combo-bonus fix in
email_analyzer_service.py, applied here for the same reason it was applied
to guardian_scanner_service.py: genuine credential-phishing samples were
landing at medium instead of high).
"""

import pytest

from app.services.email_analyzer_service import _analyze_email_mock

PHISHING_SAMPLES = {
    "A1_fake_paypal": """From: "PayPal Security" <security@paypa1-verify.com>
Subject: URGENT: Your account will be suspended in 24 hours

Dear Customer,

We detected unusual activity on your account. Your account will be suspended immediately unless you verify your identity.

Please click here to confirm your password and billing information: http://paypa1-verify.com/login

Failure to respond within 24 hours will result in permanent account closure.

Thank you,
PayPal Security Team""",
    "A2_fake_netflix": """From: "Netflix" <billing@netflix-account-verify.com>
Subject: Your payment failed - update immediately

Dear Customer,

Your last payment failed. Your account will be suspended within 24 hours unless you update your billing information and confirm your password.

Update now: http://netflix-account-verify.com/billing

Netflix Billing Team""",
    "A3_fake_irs": """From: "Internal Revenue Service" <notice@irs-taxrefund.info>
Subject: FINAL NOTICE: Immediate action required regarding your tax debt

This is your final notice. The IRS has determined that you owe back taxes. Failure to respond within 24 hours will result in legal action.

To resolve this immediately, provide your social security number and bank account details, or pay via gift cards to avoid penalty.

http://irs-taxrefund.info/pay-now""",
    "A4_fake_amazon": """From: "Amazon Support" <support@amaz0n-account.com>
Subject: Action Required: Your Amazon account will be suspended

Dear Customer,

We were unable to verify your billing information. Your account will be suspended within 24 hours unless you confirm your password and credit card number immediately.

Verify your account now: http://amaz0n-account.com/billing

Thank you,
Amazon Account Services""",
}

LEGITIMATE_SAMPLES = {
    "B1_real_coworker": """From: "Sarah Chen" <sarah.chen@acmecorp.com>
Subject: Follow-up on tomorrow's meeting

Hi Alex,

Hope you're doing well! Just wanted to confirm we're still on for our 2pm meeting tomorrow to discuss the Q3 roadmap. I've attached the agenda for reference.

Let me know if you need to reschedule.

Best,
Sarah""",
    "B2_real_receipt": """From: "Order Confirmation" <orders@bookstore-example.com>
Subject: Your order has shipped

Hi there,

Good news — your recent order (#48213) has shipped and is on its way. You can track it using the carrier's tracking number in your account.

Thanks for shopping with us!""",
    "B3_real_newsletter": """From: "Weekly Digest" <newsletter@techblog-example.com>
Subject: This week's top 5 articles

Hi there,

Here's what our readers loved this week: a deep dive on caching strategies, a tutorial on async Python, and three more picks from the team.

Read them all on the blog. Unsubscribe anytime from the link below.""",
    "B4_real_calendar": """From: "Calendar" <no-reply@calendar-example.com>
Subject: Reminder: Dentist appointment tomorrow at 10am

This is a reminder that you have an appointment tomorrow at 10:00 AM with Dr. Patel.

Reply to this email if you need to reschedule.""",
}

# Legitimate samples must stay strictly below the "medium" threshold used by
# _risk_level() in email_analyzer_service.py (score >= 30 -> "medium").
LEGITIMATE_RISK_SCORE_CEILING = 30


@pytest.mark.parametrize("text", PHISHING_SAMPLES.values(), ids=PHISHING_SAMPLES.keys())
def test_phishing_samples_score_high(text: str) -> None:
    result = _analyze_email_mock(text)
    assert result.risk_level == "high", (
        f"expected high risk, got {result.risk_level} "
        f"(score={result.risk_score}, signals={result.phishing_signals})"
    )


@pytest.mark.parametrize("text", LEGITIMATE_SAMPLES.values(), ids=LEGITIMATE_SAMPLES.keys())
def test_legitimate_samples_score_low(text: str) -> None:
    result = _analyze_email_mock(text)
    assert result.risk_level == "low", (
        f"expected low risk, got {result.risk_level} "
        f"(score={result.risk_score}, signals={result.phishing_signals})"
    )
    assert result.risk_score < LEGITIMATE_RISK_SCORE_CEILING, (
        f"risk_score {result.risk_score} crept toward the medium threshold "
        f"(ceiling={LEGITIMATE_RISK_SCORE_CEILING}, signals={result.phishing_signals})"
    )
