const VECTORS = [
  "PHISHING",
  "CREDENTIAL THEFT",
  "INVOICE FRAUD",
  "IMPERSONATION",
  "SOCIAL ENGINEERING",
  "ROMANCE SCAMS",
  "ACCOUNT TAKEOVER",
  "LINK SPOOFING",
  "URGENCY BAIT",
  "GIFT CARD SCAMS",
];

export default function ThreatMarquee() {
  return (
    <div className="marquee border-y border-border py-3">
      <div className="marquee-track">
        {[...VECTORS, ...VECTORS].map((vector, i) => (
          <span key={i} className="flex items-center gap-2.5">
            <span className="eyebrow whitespace-nowrap">{vector}</span>
            <span aria-hidden="true" className="h-1 w-1 rounded-full bg-border-strong" />
          </span>
        ))}
      </div>
    </div>
  );
}
