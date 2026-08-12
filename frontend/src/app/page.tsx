import Link from "next/link";

import ScanOrb from "@/components/ScanOrb";
import ThreatMarquee from "@/components/ThreatMarquee";
import TiltCard from "@/components/TiltCard";

const STEPS = [
  {
    index: "01",
    title: "Paste it in",
    body: "Drop in a raw email, a text message, or a suspicious link — whatever landed in front of you.",
  },
  {
    index: "02",
    title: "SHIELD reads it",
    body: "Tone, intent, urgency cues, and known scam patterns get checked against what real fraud looks like.",
  },
  {
    index: "03",
    title: "Get a verdict",
    body: "A risk score, the specific red flags, and a plain-language reason — so you know what to do next.",
  },
];

const TOOLS = [
  {
    href: "/email-analyzer",
    index: "01",
    name: "Email Analyzer",
    body: "Paste a full email to get tone/intent analysis, phishing signals, and a suggested reply.",
  },
  {
    href: "/guardian-scanner",
    index: "02",
    name: "Guardian Scam Scanner",
    body: "Check any message, link, or offer for scam and phishing risk, with the reasoning behind the score.",
  },
];

// Landing page. Once auth state is wired up, this should redirect to
// /dashboard (logged in) or stay here (logged out).
export default function Home() {
  return (
    <main className="flex min-h-screen flex-col">
      <section className="relative flex min-h-screen flex-col items-center justify-center gap-10 overflow-hidden px-6 py-24 text-center">
        <ScanOrb className="scan-scene absolute -inset-x-12 -inset-y-24 -z-10 [&>div]:h-full [&>div]:w-full" shardCount={14} />

        <div className="flex flex-col items-center gap-6">
          <div className="flex flex-col items-center gap-3">
            <h1 className="type-hero text-7xl sm:text-9xl">SHIELD</h1>
            <span className="eyebrow eyebrow-accent">Scam &amp; Harmful Intent Email Logic Detector</span>
          </div>

          <p className="max-w-md text-balance text-base text-muted sm:text-lg">
            See the scam before it sees you. Paste any email, message, or offer — SHIELD reads
            it for phishing signals and social-engineering risk in seconds.
          </p>
        </div>

        <div className="flex gap-3">
          <Link
            href="/login"
            className="btn-primary px-6 py-3 transition-transform duration-[140ms] ease-[var(--ease-out)] motion-safe:active:scale-[0.97]"
          >
            Log in
          </Link>
          <Link
            href="/register"
            className="btn-secondary px-6 py-3 transition-transform duration-[140ms] ease-[var(--ease-out)] motion-safe:active:scale-[0.97]"
          >
            Register
          </Link>
        </div>

        <span className="eyebrow opacity-60">Click or drag the core</span>
      </section>

      <ThreatMarquee />

      <section className="mx-auto flex w-full max-w-4xl flex-col gap-10 px-6 py-24">
        <span className="eyebrow text-center">How it works</span>
        <div className="grid gap-6 sm:grid-cols-3">
          {STEPS.map((step) => (
            <TiltCard key={step.index}>
              <div className="tilt-card-surface panel flex h-full flex-col gap-3 p-6">
                <span className="data-figure eyebrow-accent text-xs">{step.index}</span>
                <h3 className="text-base font-semibold">{step.title}</h3>
                <p className="text-sm text-muted">{step.body}</p>
              </div>
            </TiltCard>
          ))}
        </div>
      </section>

      <section className="mx-auto flex w-full max-w-4xl flex-col gap-10 px-6 pb-28">
        <span className="eyebrow text-center">The tools</span>
        <div className="grid gap-4 sm:grid-cols-2">
          {TOOLS.map((tool) => (
            <TiltCard key={tool.href}>
              <Link
                href={tool.href}
                className="tilt-card-surface panel group flex h-full flex-col gap-4 p-7 text-left transition-[box-shadow,border-color] duration-[140ms] ease-[var(--ease-out)] hover:border-accent hover:shadow-[0_0_32px_var(--accent-glow)]"
              >
                <span className="data-figure text-xs text-border-strong transition-colors group-hover:text-accent">
                  {tool.index}
                </span>
                <span className="type-display text-xl">{tool.name}</span>
                <span className="text-sm text-muted">{tool.body}</span>
              </Link>
            </TiltCard>
          ))}
        </div>
      </section>

      <footer className="border-t border-border px-6 py-8 text-center">
        <span className="eyebrow">SHIELD — built to spot what a rushed reader misses</span>
      </footer>
    </main>
  );
}
