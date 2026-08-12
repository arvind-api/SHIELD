"""Regression tests for the Guardian Scam Scanner's rule-based mock engine
(app/services/guardian_scanner_service.py::_scan_text_mock).

These assert on risk_level, not exact risk_score — risk_level is the actual
contract the rest of the app and the UI rely on, and exact scores are
expected to shift as the scoring rules get tuned over time. The legitimate
samples additionally assert risk_score stays under a ceiling so a future
change can't silently creep them from "low" toward "medium" while the
level assertion alone would still pass right up until it flips.

Sample texts and expected levels came from a manual before/after diagnostic
run: see the conversation history for the original comparison. A1/A3 already
scored high before scoring was tuned; A2/A4 were the ones that motivated the
"personal-info request + suspicious link" combo bonus in the scorer.
"""

import pytest

from app.services.guardian_scanner_service import _scan_text_mock

PHISHING_SAMPLES = {
    "A1_fake_bank_of_america": """From: "Bank of America Security" <alert@bankofamerica-secure.net>
Subject: URGENT: Your Bank of America account has been suspended

Dear Customer,

We have detected suspicious activity on your account. Your account has been suspended immediately and will remain locked until you verify your identity.

Click here to confirm your password and account number: http://bankofamerica-secure.net/verify

You must respond within 24 hours or your account will be permanently closed and legal action may be taken.

Bank of America Security Team""",
    "A2_fake_apple_id_locked": """From: "Apple Support" <support@apple-id-verify.com>
Subject: Your Apple ID has been locked

Dear Customer,

Your Apple ID has been locked due to unusual sign-in activity. To avoid permanent suspension, you must verify your identity immediately by confirming your password and credit card details.

Verify now: http://apple-id-verify.com/unlock

Failure to respond within 24 hours will result in permanent account closure.""",
    "A3_fake_irs_tax_debt": """From: "Internal Revenue Service" <notice@irs-taxrefund.info>
Subject: FINAL NOTICE: Immediate action required regarding your tax debt

This is your final notice. The IRS has determined that you owe back taxes. Failure to respond within 24 hours will result in legal action and an arrest warrant.

To resolve this immediately, call this number and provide your social security number and bank account details, or pay via gift cards to avoid penalty.

http://irs-taxrefund.info/pay-now""",
    "A4_fake_amazon_verification": """From: "Amazon Support" <support@amaz0n-account.com>
Subject: Action Required: Your Amazon account will be suspended

Dear Customer,

We were unable to verify your billing information. Your account will be suspended within 24 hours unless you confirm your password and credit card number immediately.

Verify your account now: http://amaz0n-account.com/billing

Thank you,
Amazon Account Services""",
}

LEGITIMATE_SAMPLES = {
    "B1_real_chase_fraud_alert": """From: "Chase" <alerts@chase.com>
Subject: Fraud Alert: Unusual activity detected on your card ending in 4471

We noticed an unusual purchase on your Chase Freedom card ending in 4471: $412.00 at an electronics store in Miami, FL.

If this was you, no action is needed. If you did not make this purchase, please call the number on the back of your card immediately, or sign in to the Chase Mobile app to review recent transactions.

This is an automated alert. Please do not reply to this email.

Chase Card Services""",
    "B2_real_fedex_delivery_notice": """From: "FedEx" <tracking@fedex.com>
Subject: Delivery Attempt Failed - Action Required Today

Your package (tracking #798234651) could not be delivered today because no one was available to sign for it. This is your final delivery attempt.

To schedule redelivery or arrange pickup at a FedEx location, visit https://fedex.com/redeliver and enter your tracking number. No payment is required to reschedule delivery.

FedEx Customer Service""",
    "B3_real_github_password_reset": """From: "GitHub" <noreply@github.com>
Subject: Your password reset request

We received a request to reset the password for your GitHub account. If you made this request, click the link below to reset your password. This link will expire in 1 hour.

Reset your password: https://github.com/password_reset/confirm?token=abc123xyz

If you didn't request a password reset, you can safely ignore this email. Your password will not be changed.

The GitHub Team""",
    "B4_real_google_security_alert": """From: "Google" <no-reply@accounts.google.com>
Subject: Security alert: New sign-in on Windows

We noticed a new sign-in to your Google Account on a Windows device. If this was you, you don't need to do anything. If not, we'll help you secure your account right away.

Check activity: https://myaccount.google.com/notifications

You received this email to let you know about important changes to your Google Account.""",
}

# Legitimate samples must stay strictly below the "medium" threshold used by
# _risk_level() in guardian_scanner_service.py (score >= 30 -> "medium").
LEGITIMATE_RISK_SCORE_CEILING = 30


@pytest.mark.parametrize("text", PHISHING_SAMPLES.values(), ids=PHISHING_SAMPLES.keys())
def test_phishing_samples_score_high(text: str) -> None:
    result = _scan_text_mock(text)
    assert result.risk_level == "high", (
        f"expected high risk, got {result.risk_level} "
        f"(score={result.risk_score}, flags={result.red_flags})"
    )


@pytest.mark.parametrize("text", LEGITIMATE_SAMPLES.values(), ids=LEGITIMATE_SAMPLES.keys())
def test_legitimate_samples_score_low(text: str) -> None:
    result = _scan_text_mock(text)
    assert result.risk_level == "low", (
        f"expected low risk, got {result.risk_level} "
        f"(score={result.risk_score}, flags={result.red_flags})"
    )
    assert result.risk_score < LEGITIMATE_RISK_SCORE_CEILING, (
        f"risk_score {result.risk_score} crept toward the medium threshold "
        f"(ceiling={LEGITIMATE_RISK_SCORE_CEILING}, flags={result.red_flags})"
    )
