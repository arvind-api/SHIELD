"use client";

import { useRef, type PointerEvent, type ReactNode } from "react";

// Pointer-tracked 3D tilt, the trick behind most "interactive card"
// moments on WebGL-heavy sites — no WebGL needed, just a perspective
// transform driven by cursor position relative to the card center.
export default function TiltCard({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);

  function handlePointerMove(event: PointerEvent<HTMLDivElement>) {
    const el = ref.current;
    if (!el || event.pointerType === "touch") return;
    const rect = el.getBoundingClientRect();
    const px = (event.clientX - rect.left) / rect.width - 0.5;
    const py = (event.clientY - rect.top) / rect.height - 0.5;
    el.style.setProperty("--tilt-x", `${(-py * 10).toFixed(2)}deg`);
    el.style.setProperty("--tilt-y", `${(px * 10).toFixed(2)}deg`);
    el.style.setProperty("--glow-x", `${((px + 0.5) * 100).toFixed(1)}%`);
    el.style.setProperty("--glow-y", `${((py + 0.5) * 100).toFixed(1)}%`);
  }

  function handlePointerLeave() {
    const el = ref.current;
    if (!el) return;
    el.style.setProperty("--tilt-x", "0deg");
    el.style.setProperty("--tilt-y", "0deg");
  }

  return (
    <div
      ref={ref}
      onPointerMove={handlePointerMove}
      onPointerLeave={handlePointerLeave}
      className={`tilt-card ${className}`}
      style={{ transformStyle: "preserve-3d" }}
    >
      {children}
    </div>
  );
}
