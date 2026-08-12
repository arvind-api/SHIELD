import Link from "next/link";

import AmbientCore from "@/components/AmbientCore";
import LogoutButton from "@/components/LogoutButton";
import PageHeader from "@/components/PageHeader";
import TiltCard from "@/components/TiltCard";

const TOOLS = [
  {
    href: "/email-analyzer",
    index: "01",
    name: "Email Analyzer",
    body: "Tone/intent analysis, phishing signals, and a reply suggestion.",
    icon: (
      <>
        <rect x="3" y="5" width="18" height="14" rx="2" />
        <path d="M4 7l8 6 8-6" strokeLinecap="round" strokeLinejoin="round" />
      </>
    ),
  },
  {
    href: "/guardian-scanner",
    index: "02",
    name: "Guardian Scam Scanner",
    body: "Scam/phishing risk assessment for any message, link, or offer.",
    icon: (
      <path
        d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6l7-3z"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    ),
  },
];

// Placeholder dashboard. Should eventually show recent analyses/scans and
// require authentication.
export default function DashboardPage() {
  return (
    <main className="relative flex min-h-screen flex-col items-center gap-10 px-6 py-16">
      <AmbientCore />
      <LogoutButton />
      <PageHeader
        eyebrow="SHIELD"
        title="Dashboard"
        description="Choose a tool to analyze a message or email."
      />

      <div className="grid w-full max-w-2xl gap-4 sm:grid-cols-2">
        {TOOLS.map((tool) => (
          <TiltCard key={tool.href}>
            <Link
              href={tool.href}
              className="tilt-card-surface panel group flex h-full flex-col gap-3 p-6 text-left transition-[box-shadow,border-color] duration-[140ms] ease-[var(--ease-out)] hover:border-accent hover:shadow-[0_0_32px_var(--accent-glow)]"
            >
              <div className="flex items-center justify-between">
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={1.5}
                  className="h-6 w-6 text-accent"
                  aria-hidden="true"
                >
                  {tool.icon}
                </svg>
                <span className="data-figure text-xs text-border-strong transition-colors group-hover:text-accent">
                  {tool.index}
                </span>
              </div>
              <span className="text-base font-semibold">{tool.name}</span>
              <span className="text-sm text-muted">{tool.body}</span>
            </Link>
          </TiltCard>
        ))}
      </div>
    </main>
  );
}
