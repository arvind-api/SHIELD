"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

import { analyzeEmail, ApiError } from "@/lib/api";
import TiltCard from "@/components/TiltCard";
import type { EmailAnalyzeResponse } from "@/types";

type Status = "idle" | "loading" | "success" | "error";

const RISK_BAND_CLASSES: Record<EmailAnalyzeResponse["risk_level"], string> = {
  low: "border-b border-risk-low bg-risk-low-bg text-risk-low",
  medium: "border-b border-risk-medium bg-risk-medium-bg text-risk-medium",
  high: "border-b border-risk-high bg-risk-high-bg text-risk-high",
};

export default function EmailAnalyzerForm() {
  const router = useRouter();
  const [rawEmail, setRawEmail] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<EmailAnalyzeResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus("loading");
    setErrorMessage(null);
    setResult(null);

    try {
      const response = await analyzeEmail({ raw_email: rawEmail });
      setResult(response);
      setStatus("success");
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        router.push("/login");
        return;
      }
      setErrorMessage(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
      setStatus("error");
    }
  }

  return (
    <div className="flex w-full max-w-xl flex-col gap-6">
      <form onSubmit={handleSubmit} className="panel flex flex-col gap-4 p-6">
        <textarea
          className="min-h-[200px] rounded-lg border border-border bg-black/20 p-3 text-sm text-foreground outline-none transition-colors focus:border-accent focus:shadow-[0_0_0_3px_var(--accent-glow)]"
          placeholder="Paste an email here..."
          value={rawEmail}
          onChange={(event) => setRawEmail(event.target.value)}
          disabled={status === "loading"}
          required
        />
        <button
          type="submit"
          disabled={status === "loading" || rawEmail.trim().length === 0}
          className="btn-primary self-start px-5 py-2.5 transition-transform duration-[140ms] ease-[var(--ease-out)] motion-safe:active:scale-[0.97]"
        >
          <span className="inline-flex items-center gap-2">
            {status === "loading" && (
              <span
                aria-hidden="true"
                className="h-3.5 w-3.5 rounded-full border-2 border-border border-t-foreground motion-safe:animate-spin"
              />
            )}
            {status === "loading" ? "Analyzing..." : "Analyze"}
          </span>
        </button>
      </form>

      {status === "error" && errorMessage && (
        <p
          role="alert"
          className="error-message-enter rounded-lg border border-risk-high bg-risk-high-bg px-4 py-3 text-sm text-risk-high"
        >
          {errorMessage}
        </p>
      )}

      {status === "success" && result && (
        <TiltCard className="result-panel-enter">
          <div className="tilt-card-surface panel overflow-hidden">
            <div
              className={`flex items-center justify-between px-6 py-4 ${RISK_BAND_CLASSES[result.risk_level]}`}
            >
              <span className="eyebrow text-current">{result.risk_level} risk</span>
              <span className="data-figure text-2xl font-bold">
                {result.risk_score}
                <span className="text-sm font-normal opacity-70">/100</span>
              </span>
            </div>

            <div className="flex flex-col gap-6 p-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="eyebrow">Tone</div>
                  <div className="mt-1 text-sm">{result.tone}</div>
                </div>
                <div>
                  <div className="eyebrow">Intent</div>
                  <div className="mt-1 text-sm">{result.intent}</div>
                </div>
              </div>

              {result.phishing_signals.length > 0 && (
                <div>
                  <div className="eyebrow">
                    Phishing signals
                  </div>
                  <ul className="mt-2 list-inside list-disc space-y-1 text-sm">
                    {result.phishing_signals.map((signal, i) => (
                      <li key={i}>{signal}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="border-t border-border pt-4">
                <div className="eyebrow">Suggested reply</div>
                <p className="mt-1 text-sm">{result.suggested_reply}</p>
              </div>
            </div>
          </div>
        </TiltCard>
      )}
    </div>
  );
}
