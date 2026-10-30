"use client";

import { useEffect, useMemo, useState } from "react";

import type { AnalysisMode, Evidence, EmailAnalysisResult } from "@/types";

type Risk = EmailAnalysisResult["risk_level"];

const RISK_BAND_CLASSES: Record<Risk, string> = {
  low: "border-b border-risk-low bg-risk-low-bg text-risk-low",
  medium: "border-b border-risk-medium bg-risk-medium-bg text-risk-medium",
  high: "border-b border-risk-high bg-risk-high-bg text-risk-high",
};

const MODE_LABELS: Record<AnalysisMode, { label: string; title: string }> = {
  ai: { label: "Claude AI", title: "Analyzed by Claude" },
  rules: { label: "Rule engine", title: "Analyzed by SHIELD's built-in rule engine (no AI key configured)" },
  rules_fallback: {
    label: "Rule engine · AI offline",
    title: "Claude was unavailable for this request, so SHIELD's rule engine analyzed it instead",
  },
};

function usePrefersReducedMotion() {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    setReduced(window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  }, []);
  return reduced;
}

// Counts the score up from 0 so the number lands with the 3D verdict
// shockwave instead of just appearing.
function CountUp({ value, durationMs = 800 }: { value: number; durationMs?: number }) {
  const reduced = usePrefersReducedMotion();
  const [shown, setShown] = useState(reduced ? value : 0);

  useEffect(() => {
    if (reduced) {
      setShown(value);
      return;
    }
    let frame = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min((now - start) / durationMs, 1);
      setShown(Math.round(value * (1 - (1 - t) ** 3)));
      if (t < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value, durationMs, reduced]);

  return <>{shown}</>;
}

export function RiskHeader({ risk, score, mode }: { risk: Risk; score: number; mode: AnalysisMode }) {
  const modeInfo = MODE_LABELS[mode];
  return (
    <div className={`flex items-center justify-between gap-4 px-6 py-4 ${RISK_BAND_CLASSES[risk]}`}>
      <div className="flex flex-col gap-1.5">
        <span className="eyebrow text-current">{risk} risk</span>
        <span
          title={modeInfo.title}
          className="eyebrow w-fit rounded-full border border-white/20 px-2 py-0.5 text-[0.6rem] tracking-[0.18em] text-muted"
        >
          {modeInfo.label}
        </span>
      </div>
      <span className="data-figure text-3xl font-bold" aria-label={`Risk score ${score} out of 100`}>
        <CountUp value={score} />
        <span className="text-sm font-normal opacity-70">/100</span>
      </span>
    </div>
  );
}

type Segment = { text: string; indices: number[] };

// Splits `text` into plain and highlighted runs. Every occurrence of every
// quote is marked (case-insensitive); overlapping quotes ("bank account" /
// "account has been locked") merge into one mark tagged with both numbers,
// so marks never nest and no quote goes unhighlighted.
function segment(text: string, evidence: Evidence[]): Segment[] {
  const lower = text.toLowerCase();
  const ranges: { start: number; end: number; index: number }[] = [];
  evidence.forEach((item, index) => {
    const needle = item.quote.toLowerCase();
    if (!needle) return;
    let from = 0;
    while (true) {
      const start = lower.indexOf(needle, from);
      if (start === -1) break;
      ranges.push({ start, end: start + needle.length, index });
      from = start + needle.length;
    }
  });
  ranges.sort((a, b) => a.start - b.start || b.end - a.end);

  const merged: { start: number; end: number; indices: number[] }[] = [];
  for (const range of ranges) {
    const last = merged[merged.length - 1];
    if (last && range.start < last.end) {
      last.end = Math.max(last.end, range.end);
      if (!last.indices.includes(range.index)) last.indices.push(range.index);
    } else {
      merged.push({ start: range.start, end: range.end, indices: [range.index] });
    }
  }

  const segments: Segment[] = [];
  let cursor = 0;
  for (const range of merged) {
    if (range.start > cursor) segments.push({ text: text.slice(cursor, range.start), indices: [] });
    segments.push({ text: text.slice(range.start, range.end), indices: range.indices.sort((a, b) => a - b) });
    cursor = range.end;
  }
  if (cursor < text.length) segments.push({ text: text.slice(cursor), indices: [] });
  return segments;
}

/**
 * The analyzed text with each piece of evidence highlighted in place,
 * plus a numbered list of why. Hovering a list item lights up its marks.
 */
export function EvidenceView({ text, evidence, risk }: { text: string; evidence: Evidence[]; risk: Risk }) {
  const [active, setActive] = useState<number | null>(null);
  const segments = useMemo(() => segment(text, evidence), [text, evidence]);

  if (evidence.length === 0) return null;

  return (
    <div className="flex flex-col gap-3">
      <div className="eyebrow">Evidence in your text</div>
      <div
        className="evidence-text max-h-56 overflow-y-auto whitespace-pre-wrap break-words rounded-lg border border-border bg-black/25 p-3 text-sm leading-relaxed text-muted"
        data-risk={risk}
      >
        {segments.map((seg, i) =>
          seg.indices.length === 0 ? (
            <span key={i}>{seg.text}</span>
          ) : (
            <mark
              key={i}
              title={seg.indices.map((n) => evidence[n].reason).join(" · ")}
              data-active={active !== null && seg.indices.includes(active)}
              className="evidence-mark"
            >
              {seg.text}
              <sup className="evidence-tag">{seg.indices.map((n) => n + 1).join(",")}</sup>
            </mark>
          )
        )}
      </div>
      <ol className="flex flex-col gap-1.5 text-sm">
        {evidence.map((item, i) => (
          <li
            key={i}
            onMouseEnter={() => setActive(i)}
            onMouseLeave={() => setActive(null)}
            className="flex gap-2 rounded-md px-2 py-1 transition-colors hover:bg-white/5"
          >
            <span className="data-figure evidence-index shrink-0 text-xs">{i + 1}</span>
            <span>
              <span className="text-foreground">&ldquo;{item.quote}&rdquo;</span>
              <span className="text-[#b4bac2]"> — {item.reason}</span>
            </span>
          </li>
        ))}
      </ol>
    </div>
  );
}
