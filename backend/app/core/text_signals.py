"""Shared text heuristics used by both the Email Analyzer and Guardian Scam
Scanner rule-based mock engines: suspicious-link detection and common
scam/phishing-style writing anomalies. Kept separate from either service so
the two engines don't duplicate the same regex/domain logic.
"""

import re

URL_RE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
IP_URL_RE = re.compile(r"^https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
SHORTENER_DOMAINS = {
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "goo.gl",
    "is.gd",
    "ow.ly",
    "buff.ly",
    "rebrand.ly",
    "cutt.ly",
}
SUSPICIOUS_TLDS = {"ru", "tk", "top", "xyz", "click", "link", "zip", "work", "gq", "cf", "ml"}

LOOKALIKE_BRANDS = [
    "paypal",
    "amazon",
    "apple",
    "microsoft",
    "google",
    "netflix",
    "chase",
    "wellsfargo",
    "bankofamerica",
    "irs",
    "facebook",
    "instagram",
    "linkedin",
    "usps",
    "fedex",
    "dhl",
]
_LEET_MAP = str.maketrans({"0": "o", "1": "l", "3": "e", "5": "s", "@": "a"})

COMMON_PHISHING_MISSPELLINGS = [
    "recieve",
    "acount",
    "verifiy",
    "immediatly",
    "seperate",
    "occured",
    "untill",
    "informations",
    "beneficiery",
    "securty",
]


def extract_domain(url: str) -> str:
    without_scheme = re.sub(r"^https?://", "", url, flags=re.IGNORECASE)
    domain = without_scheme.split("/")[0].split("?")[0]
    domain = domain.split("@")[-1]  # strip userinfo@ prefix if present
    domain = domain.split(":")[0]  # strip port
    return domain.lower()


def domain_impersonates_brand(domain: str) -> str | None:
    core = domain.split(".")[0]
    normalized = core.translate(_LEET_MAP).replace("-", "")
    for brand in LOOKALIKE_BRANDS:
        if brand == core:
            continue  # exact match to the brand's own name isn't itself a red flag
        if brand in normalized:
            return brand
    return None


def find_suspicious_links(text: str) -> list[str]:
    signals = []
    for url in URL_RE.findall(text):
        domain = extract_domain(url)
        if IP_URL_RE.match(url):
            signals.append(f"link uses a raw IP address instead of a domain ({url})")
        if domain in SHORTENER_DOMAINS:
            signals.append(f"link uses a URL shortener ({domain}) that hides the real destination")
        tld = domain.rsplit(".", 1)[-1] if "." in domain else ""
        if tld in SUSPICIOUS_TLDS:
            signals.append(f"link uses an uncommon/high-risk top-level domain (.{tld})")
        brand_hit = domain_impersonates_brand(domain)
        if brand_hit:
            signals.append(f"link domain '{domain}' looks like it's impersonating {brand_hit}")
    return signals


def find_grammar_anomalies(text: str) -> list[str]:
    signals = []
    lower = text.lower()
    hits = [w for w in COMMON_PHISHING_MISSPELLINGS if w in lower]
    if hits:
        signals.append(f"contains common phishing misspellings: {', '.join(hits)}")
    if re.search(r"!{2,}", text):
        signals.append("excessive exclamation marks")
    if len(re.findall(r"\b[A-Z]{4,}\b", text)) >= 3:
        signals.append("excessive use of ALL CAPS words")
    return signals
