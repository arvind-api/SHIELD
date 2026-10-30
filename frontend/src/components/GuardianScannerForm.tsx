"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

import { scanText, ApiError } from "@/lib/api";
import { finishScan, pulseTyping, resetScan, startScan, waitForMinimumScan } from "@/lib/scanSignal";
import { EvidenceView, RiskHeader } from "@/components/AnalysisReadout";
import TiltCard from "@/components/TiltCard";
import type { ScanResponse } from "@/types";

type Status = "idle" | "loading" | "success" | "error";

export default function GuardianScannerForm() {
  const router = useRouter();
  const [inputText, setInputText] = useState("");
  const [scannedText, setScannedText] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<ScanResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Leave the shared 3D scene neutral for whichever page mounts next.
  useEffect(() => resetScan, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus("loading");
    setErrorMessage(null);
    setResult(null);
    setScannedText(inputText);
    const startedAt = performance.now();
    startScan();

    try {
      const response = await scanText({ input_text: inputText });
      await waitForMinimumScan(startedAt);
      setResult(response);
      setStatus("success");
      finishScan(response.risk_level, response.risk_score);
    } catch (err) {
      resetScan();
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
          placeholder="Paste a message, link, or offer here..."
          value={inputText}
          onChange={(event) => {
            setInputText(event.target.value);
            pulseTyping();
          }}
          disabled={status === "loading"}
          required
        />
        <button
          type="submit"
          disabled={status === "loading" || inputText.trim().length === 0}
          className="btn-primary self-start px-5 py-2.5 transition-transform duration-[140ms] ease-[var(--ease-out)] motion-safe:active:scale-[0.97]"
        >
          <span className="inline-flex items-center gap-2">
            {status === "loading" && (
              <span
                aria-hidden="true"
                className="h-3.5 w-3.5 rounded-full border-2 border-border border-t-foreground motion-safe:animate-spin"
              />
            )}
            {status === "loading" ? "Scanning..." : "Scan"}
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
            <RiskHeader risk={result.risk_level} score={result.risk_score} mode={result.analysis_mode} />

            <div className="flex flex-col gap-6 p-6">
              <div>
                <div className="eyebrow">Category</div>
                <div className="mt-1 text-sm">{result.category}</div>
              </div>

              {result.red_flags.length > 0 && (
                <div>
                  <div className="eyebrow">Red flags</div>
                  <ul className="mt-2 list-inside list-disc space-y-1 text-sm">
                    {result.red_flags.map((flag, i) => (
                      <li key={i}>{flag}</li>
                    ))}
                  </ul>
                </div>
              )}

              <EvidenceView text={scannedText} evidence={result.evidence} risk={result.risk_level} />

              <div className="border-t border-border pt-4">
                <div className="eyebrow">Reasoning</div>
                <p className="mt-1 text-sm">{result.reasoning}</p>
              </div>
            </div>
          </div>
        </TiltCard>
      )}
    </div>
  );
}
