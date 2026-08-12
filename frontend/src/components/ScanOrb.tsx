"use client";

import { useEffect, useMemo, useRef, useState, type MutableRefObject } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Environment, Lightformer, MeshTransmissionMaterial } from "@react-three/drei";
import { Bloom, EffectComposer, Vignette } from "@react-three/postprocessing";
import { BlendFunction } from "postprocessing";
import * as THREE from "three";

// The site's signature motif: a glass shield core you can actually pick
// up and spin — drag it and it coasts on inertia like a real object, a
// point light follows the pointer to reveal facets as it passes over
// them (the "mouse reveal" trick from the reference sites), scroll
// nudges its rotation, and clicking fires a bright scan pulse. Fog +
// bloom + a drifting particle field keep it reading as one lit
// atmosphere rather than an object pasted on top of the page.

const VOID = "#07080a";

type Pulse = { id: number; born: number };

type DragState = {
  dragging: boolean;
  lastX: number;
  lastY: number;
  velX: number;
  velY: number;
  rotY: number;
  rotX: number;
};

function GlassCore({
  onPulse,
  drag,
  hovered,
  setHovered,
}: {
  onPulse: (pulse: Pulse) => void;
  drag: MutableRefObject<DragState>;
  hovered: boolean;
  setHovered: (v: boolean) => void;
}) {
  const group = useRef<THREE.Group>(null);
  const wire = useRef<THREE.Mesh>(null);
  const ring = useRef<THREE.Mesh>(null);
  const light = useRef<THREE.PointLight>(null);
  const pointerTarget = useRef({ x: 0, y: 0 });
  const scrollOffset = useRef(0);
  const { viewport } = useThree();

  const geometry = useMemo(() => new THREE.IcosahedronGeometry(1.35, 2), []);

  useFrame((state, delta) => {
    if (typeof window !== "undefined") {
      const max = document.body.scrollHeight - window.innerHeight;
      scrollOffset.current = max > 0 ? window.scrollY / max : 0;
    }

    const target = { x: state.pointer.y * 0.3, y: state.pointer.x * 0.4 };
    pointerTarget.current.x += (target.x - pointerTarget.current.x) * Math.min(delta * 3, 1);
    pointerTarget.current.y += (target.y - pointerTarget.current.y) * Math.min(delta * 3, 1);

    // Drag inertia: while not actively dragging, bleed off velocity into
    // rotation so the core keeps spinning after you let go, like a
    // flicked globe.
    const d = drag.current;
    if (!d.dragging) {
      d.rotY += d.velX;
      d.rotX += d.velY;
      d.velX *= 0.93;
      d.velY *= 0.93;
      d.rotX = THREE.MathUtils.clamp(d.rotX, -1.1, 1.1);
    }

    if (group.current) {
      group.current.rotation.x = pointerTarget.current.x * 0.5 + scrollOffset.current * 0.6 + d.rotX;
      group.current.rotation.y += delta * (hovered ? 0.32 : 0.14) + pointerTarget.current.y * delta;

      // d.rotY is an absolute accumulated drag value, not a per-frame
      // delta — apply only the change since last frame on top of the
      // idle spin above.
      const lastDragY = (group.current.userData.lastDragY as number) ?? 0;
      group.current.rotation.y += d.rotY - lastDragY;
      group.current.userData.lastDragY = d.rotY;

      const s = (hovered ? 1.15 : d.dragging ? 1.1 : 1) * Math.min(viewport.width / 6, 1.05);
      group.current.scale.lerp(new THREE.Vector3(s, s, s), Math.min(delta * 5, 1));
    }
    if (wire.current) wire.current.rotation.y -= delta * 0.05;
    if (ring.current) ring.current.rotation.z -= delta * 0.6;

    // Point light tracks the pointer in world space just in front of the
    // core, so facets light up as the cursor sweeps across them.
    if (light.current) {
      light.current.position.set(state.pointer.x * 2.2, state.pointer.y * 2.2, 1.8);
      light.current.intensity = THREE.MathUtils.lerp(
        light.current.intensity,
        hovered || d.dragging ? 14 : 4.5,
        Math.min(delta * 6, 1)
      );
    }
  });

  return (
    <group
      ref={group}
      onPointerOver={() => setHovered(true)}
      onPointerOut={() => setHovered(false)}
      onClick={() => onPulse({ id: Math.random(), born: performance.now() })}
    >
      <mesh geometry={geometry}>
        <MeshTransmissionMaterial
          color="#bfffdc"
          thickness={1.1}
          roughness={0.08}
          transmission={1}
          ior={1.25}
          chromaticAberration={0.05}
          anisotropy={0.3}
          distortion={0.15}
          distortionScale={0.3}
          temporalDistortion={0.1}
          backside
        />
      </mesh>
      <mesh ref={wire} geometry={geometry} scale={1.008}>
        <meshBasicMaterial
          color={hovered ? "#c8ffe4" : "#66ffb2"}
          wireframe
          transparent
          opacity={hovered ? 0.4 : 0.22}
        />
      </mesh>
      <mesh ref={ring} rotation={[Math.PI / 2.4, 0, 0]}>
        <torusGeometry args={[1.85, 0.006, 8, 96]} />
        <meshBasicMaterial color="#66ffb2" transparent opacity={hovered ? 0.55 : 0.32} />
      </mesh>
      <mesh rotation={[Math.PI / 2.4, 0, 0]}>
        <torusGeometry args={[2.05, 0.003, 8, 96]} />
        <meshBasicMaterial color="#66ffb2" transparent opacity={0.13} />
      </mesh>
      <pointLight ref={light} color="#8fffca" distance={7} decay={2} intensity={4.5} />
    </group>
  );
}

// Expanding rings spawned on click — a visible "scan pulse" so the core
// reads as something you press, not just something you watch.
function ScanPulses({ pulses }: { pulses: Pulse[] }) {
  return (
    <>
      {pulses.map((pulse) => (
        <PulseRing key={pulse.id} born={pulse.born} />
      ))}
    </>
  );
}

function PulseRing({ born }: { born: number }) {
  const mesh = useRef<THREE.Mesh>(null);
  useFrame(() => {
    if (!mesh.current) return;
    const age = (performance.now() - born) / 1000;
    const t = Math.min(age / 1.1, 1);
    const scale = 1.3 + t * 3.8;
    mesh.current.scale.setScalar(scale);
    const material = mesh.current.material as THREE.MeshBasicMaterial;
    material.opacity = 0.75 * (1 - t);
  });
  return (
    <mesh ref={mesh} rotation={[Math.PI / 2.4, 0, 0]}>
      <torusGeometry args={[1, 0.01, 8, 96]} />
      <meshBasicMaterial color="#9dffce" transparent opacity={0.75} />
    </mesh>
  );
}

// Small wireframe fragments scattered through the whole scene, each
// drifting and tumbling on its own independent axis — fills the frame
// with actual geometry so the space around the core doesn't read as
// empty black.
function FloatingShards({ count = 10 }: { count?: number }) {
  const group = useRef<THREE.Group>(null);

  const shards = useMemo(() => {
    return Array.from({ length: count }, (_, i) => {
      const angle = (i / count) * Math.PI * 2 + Math.random() * 0.6;
      const radius = 3.2 + Math.random() * 4.5;
      return {
        position: [
          Math.cos(angle) * radius,
          (Math.random() - 0.5) * 4.5,
          Math.sin(angle) * radius - 1,
        ] as [number, number, number],
        scale: 0.14 + Math.random() * 0.24,
        speed: 0.08 + Math.random() * 0.18,
        axis: new THREE.Vector3(Math.random() - 0.5, Math.random() - 0.5, Math.random() - 0.5).normalize(),
        color: i % 3 === 0 ? "#8b7cff" : "#66ffb2",
        bobOffset: Math.random() * Math.PI * 2,
      };
    });
  }, [count]);

  useFrame((state, delta) => {
    if (!group.current) return;
    group.current.children.forEach((child, i) => {
      const s = shards[i];
      child.rotateOnAxis(s.axis, delta * s.speed);
      child.position.y = s.position[1] + Math.sin(state.clock.elapsedTime * 0.4 + s.bobOffset) * 0.35;
    });
  });

  return (
    <group ref={group}>
      {shards.map((s, i) => (
        <mesh key={i} position={s.position} scale={s.scale}>
          <icosahedronGeometry args={[1, 0]} />
          <meshBasicMaterial color={s.color} wireframe transparent opacity={0.4} />
        </mesh>
      ))}
    </group>
  );
}

// A thin drifting particle field that extends well past the core
// itself, so the "3D layer" fills the whole frame instead of sitting
// as an island in the middle of it — reads as atmosphere, not a prop.
function DriftField({ density = 260 }: { density?: number }) {
  const points = useRef<THREE.Points>(null);

  const positions = useMemo(() => {
    const arr = new Float32Array(density * 3);
    for (let i = 0; i < density; i++) {
      const radius = 3 + Math.random() * 9;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);
      arr[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      arr[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta) * 0.6;
      arr[i * 3 + 2] = radius * Math.cos(phi) * 0.5 - 2;
    }
    return arr;
  }, [density]);

  useFrame((state, delta) => {
    if (points.current) {
      points.current.rotation.y += delta * 0.015;
      points.current.rotation.x = state.pointer.y * 0.03;
    }
  });

  return (
    <points ref={points}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial color="#8fffca" size={0.028} transparent opacity={0.35} sizeAttenuation />
    </points>
  );
}

function Scene({
  drag,
  particles,
  shardCount,
  bloom,
}: {
  drag: MutableRefObject<DragState>;
  particles: number;
  shardCount: number;
  bloom: boolean;
}) {
  const { scene } = useThree();
  const [pulses, setPulses] = useState<Pulse[]>([]);
  const [hovered, setHovered] = useState(false);

  useMemo(() => {
    scene.fog = new THREE.Fog(VOID, 4.5, 12);
  }, [scene]);

  function addPulse(pulse: Pulse) {
    setPulses((prev) => [...prev.filter((p) => performance.now() - p.born < 1200), pulse]);
  }

  return (
    <>
      <ambientLight intensity={0.25} />
      {/* Procedural environment (built from colored panels rather than a
          fetched HDRI) so the glass core has something to refract without
          any external asset dependency. */}
      <Environment resolution={64}>
        <Lightformer form="rect" intensity={2.5} color="#66ffb2" position={[3, 2, 2]} scale={[3, 3, 1]} />
        <Lightformer form="rect" intensity={1.5} color="#8b7cff" position={[-3, -1, 2]} scale={[3, 3, 1]} />
        <Lightformer form="ring" intensity={1} color="#eef1ee" position={[0, 3, -3]} scale={4} />
      </Environment>
      <DriftField density={particles} />
      {shardCount > 0 && <FloatingShards count={shardCount} />}
      <GlassCore onPulse={addPulse} drag={drag} hovered={hovered} setHovered={setHovered} />
      <ScanPulses pulses={pulses} />
      {bloom && (
        <EffectComposer multisampling={0}>
          <Bloom
            intensity={0.65}
            luminanceThreshold={0.05}
            luminanceSmoothing={0.4}
            mipmapBlur
            blendFunction={BlendFunction.SCREEN}
          />
          <Vignette eskil={false} offset={0.15} darkness={0.9} blendFunction={BlendFunction.NORMAL} />
        </EffectComposer>
      )}
    </>
  );
}

export default function ScanOrb({
  className = "",
  interactive = true,
  particles = 260,
  shardCount = 0,
  bloom = true,
}: {
  className?: string;
  interactive?: boolean;
  particles?: number;
  shardCount?: number;
  bloom?: boolean;
}) {
  const wrapperRef = useRef<HTMLDivElement>(null);
  const drag = useRef<DragState>({
    dragging: false,
    lastX: 0,
    lastY: 0,
    velX: 0,
    velY: 0,
    rotY: 0,
    rotX: 0,
  });

  useEffect(() => {
    if (!interactive) return;
    const el = wrapperRef.current;
    if (!el) return;

    function onPointerDown(e: PointerEvent) {
      drag.current.dragging = true;
      drag.current.lastX = e.clientX;
      drag.current.lastY = e.clientY;
      el!.setPointerCapture(e.pointerId);
      el!.style.cursor = "grabbing";
    }
    function onPointerMove(e: PointerEvent) {
      if (!drag.current.dragging) return;
      const dx = e.clientX - drag.current.lastX;
      const dy = e.clientY - drag.current.lastY;
      drag.current.lastX = e.clientX;
      drag.current.lastY = e.clientY;
      const vx = dx * 0.006;
      const vy = dy * 0.006;
      drag.current.rotY += vx;
      drag.current.rotX += vy;
      drag.current.velX = vx;
      drag.current.velY = vy;
    }
    function onPointerUp(e: PointerEvent) {
      drag.current.dragging = false;
      el!.style.cursor = "grab";
      try {
        el!.releasePointerCapture(e.pointerId);
      } catch {
        /* no-op — capture may already be released */
      }
    }

    el.addEventListener("pointerdown", onPointerDown);
    el.addEventListener("pointermove", onPointerMove);
    el.addEventListener("pointerup", onPointerUp);
    el.addEventListener("pointercancel", onPointerUp);
    el.style.cursor = "grab";

    return () => {
      el.removeEventListener("pointerdown", onPointerDown);
      el.removeEventListener("pointermove", onPointerMove);
      el.removeEventListener("pointerup", onPointerUp);
      el.removeEventListener("pointercancel", onPointerUp);
    };
  }, [interactive]);

  return (
    <div
      ref={wrapperRef}
      className={className}
      aria-hidden="true"
      style={{ touchAction: interactive ? "none" : undefined }}
    >
      <Canvas
        camera={{ position: [0, 0, 5], fov: 42 }}
        dpr={[1, 1.75]}
        gl={{ antialias: true, alpha: true }}
        style={{ pointerEvents: interactive ? "auto" : "none" }}
      >
        <Scene drag={drag} particles={particles} shardCount={shardCount} bloom={bloom} />
      </Canvas>
    </div>
  );
}
