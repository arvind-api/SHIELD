import ScanOrb from "@/components/ScanOrb";

// Full-viewport 3D backdrop for the tool/dashboard pages — the same
// draggable glass core and drifting geometry as the hero, fixed behind
// all content, so the whole page carries the 3D language instead of
// going flat past the landing screen.
export default function AmbientCore({ label = "Drag to spin the core" }: { label?: string }) {
  return (
    <div className="fixed inset-0 -z-10">
      <ScanOrb
        className="scan-scene h-full w-full [&>div]:h-full [&>div]:w-full"
        particles={220}
        shardCount={14}
      />
      <span className="eyebrow pointer-events-none absolute bottom-6 right-6 opacity-40">{label}</span>
    </div>
  );
}
