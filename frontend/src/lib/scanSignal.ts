import type { EmailAnalysisResult } from "@/types";

export type Risk = EmailAnalysisResult["risk_level"];
export type ScanPhase = "idle" | "scanning" | "result";

/**
 * Shared, mutable state the analyzer forms write and the 3D scene reads
 * every frame (in useFrame) — deliberately not React state, so typing and
 * scanning never re-render the WebGL tree. `version` bumps on every phase
 * change so the scene can detect one-shot events (e.g. the verdict
 * shockwave) without subscriptions.
 */
export const scanSignal = {
  phase: "idle" as ScanPhase,
  risk: null as Risk | null,
  score: 0,
  /** 0..1, bumped by keystrokes and decayed by the scene. */
  energy: 0,
  version: 0,
};

export function startScan() {
  scanSignal.phase = "scanning";
  scanSignal.risk = null;
  scanSignal.version++;
}

export function finishScan(risk: Risk, score: number) {
  scanSignal.phase = "result";
  scanSignal.risk = risk;
  scanSignal.score = score;
  scanSignal.version++;
}

export function resetScan() {
  scanSignal.phase = "idle";
  scanSignal.risk = null;
  scanSignal.score = 0;
  scanSignal.version++;
}

export function pulseTyping() {
  scanSignal.energy = Math.min(1, scanSignal.energy + 0.12);
}

/** Keep the scan animation on screen long enough to read as a scan, even
 * when the rule engine answers in a few milliseconds. */
export const MIN_SCAN_MS = 900;

export function waitForMinimumScan(startedAt: number): Promise<void> {
  const remaining = MIN_SCAN_MS - (performance.now() - startedAt);
  return remaining > 0 ? new Promise((resolve) => setTimeout(resolve, remaining)) : Promise.resolve();
}
