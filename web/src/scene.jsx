import React, { Suspense, useEffect, useMemo, useRef } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import {
  ContactShadows,
  Environment,
  Html,
  Lightformer,
  Line,
  OrbitControls,
} from "@react-three/drei";
import * as THREE from "three";

export const point = ([x, y, z]) => [y, z, 0.45 - x];
const offsets = (part) =>
  ({
    wing: [Math.sign(part.centroid_m[1]) * 0.28, 0.13, 0],
    tail: [Math.sign(part.centroid_m[1]) * 0.17, 0.2, -0.16],
    fuselage: [0, -0.1, 0],
    structure: [0, 0.08, 0],
    power: [0.2, 0.28, 0.02],
    payload: [-0.2, 0.22, 0.1],
    controls: [Math.sign(part.centroid_m[1]) * 0.2, 0.3, 0],
  })[part.group] || [0, 0, 0];
const colors = {
  print: "#e4e5d9",
  "cut-carbon": "#292e2d",
  "cut-plywood": "#ba8c54",
  purchase: "#343c39",
  provided: "#576365",
};
function surfaceTexture(kind) {
  const c = document.createElement("canvas");
  c.width = c.height = 256;
  const ctx = c.getContext("2d");
  ctx.fillStyle = "#cccccc";
  ctx.fillRect(0, 0, 256, 256);
  if (kind === "cut-carbon") {
    for (let y = 0; y < 256; y += 16)
      for (let x = 0; x < 256; x += 16) {
        ctx.fillStyle = ((x + y) / 16) % 2 ? "#969a98" : "#dddddd";
        ctx.fillRect(x, y, 16, 16);
        ctx.strokeStyle = "#b5b7b6";
        ctx.lineWidth = 1;
        for (let k = 2; k < 16; k += 3) {
          ctx.beginPath();
          if (((x + y) / 16) % 2) {
            ctx.moveTo(x + k, y);
            ctx.lineTo(x + k, y + 16);
          } else {
            ctx.moveTo(x, y + k);
            ctx.lineTo(x + 16, y + k);
          }
          ctx.stroke();
        }
      }
  } else {
    for (let y = 0; y < 256; y += kind === "print" ? 4 : 3) {
      ctx.strokeStyle =
        kind === "print"
          ? "#bfc1bb"
          : `rgb(${170 + (y % 45)},${170 + (y % 45)},${170 + (y % 45)})`;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.bezierCurveTo(75, y + 1, 160, y - 1, 256, y);
      ctx.stroke();
    }
  }
  const texture = new THREE.CanvasTexture(c);
  texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
  texture.anisotropy = 8;
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

// Cosmetic labels on the existing component envelopes, not vendor CAD.
function componentTexture(part) {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 256;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = part.id === "battery" ? "#344939" : "#293231";
  ctx.fillRect(0, 0, 512, 256);
  ctx.fillStyle = "#cf9b54";
  ctx.fillRect(0, 0, 512, 24);
  ctx.fillRect(0, 228, 512, 28);
  if (part.id === "motor") {
    ctx.fillStyle = "#889193";
    ctx.fillRect(0, 28, 512, 194);
    for (let x = 0; x < 512; x += 16) {
      ctx.fillStyle = x % 32 ? "#738083" : "#aeb5b4";
      ctx.fillRect(x, 35, 2, 180);
    }
  } else {
    ctx.fillStyle = "#f0f0db";
    ctx.font = "bold 55px sans-serif";
    ctx.fillText(
      part.id === "battery"
        ? "1300 mAh"
        : part.id === "esc"
          ? "20A ESC"
          : "CONTROL",
      24,
      105,
    );
    ctx.font = "25px sans-serif";
    ctx.fillText(
      part.id === "battery" ? "3S / 11.1V   LiPo" : "COMPONENT ENVELOPE",
      24,
      155,
    );
    for (let x = 360; x < 480; x += 5) ctx.fillRect(x, 175, (x % 3) + 1, 30);
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 8;
  return texture;
}
function Part({
  part,
  explode,
  inside,
  selected,
  onSelect,
  stepGroups,
  analysis,
}) {
  const ref = useRef();
  const texture = useMemo(
    () =>
      ["print", "cut-carbon", "cut-plywood"].includes(part.process)
        ? surfaceTexture(part.process)
        : ["battery", "esc", "motor", "receiver"].includes(part.id)
          ? componentTexture(part)
          : null,
    [part],
  );
  const geometry = useMemo(() => {
    const g = new THREE.BufferGeometry(),
      p = [],
      uv = [];
    for (let i = 0; i < part.mesh.positions.length; i += 3) {
      const a = part.mesh.positions.slice(i, i + 3);
      p.push(...point(a));
      if (part.process === "purchase") {
        uv.push(
          (a[0] - part.centroid_m[0]) / part.dimensions_m[0] + 0.5,
          part.id === "motor"
            ? Math.atan2(a[2] - part.centroid_m[2], a[1] - part.centroid_m[1]) /
                (2 * Math.PI) +
                0.5
            : (a[1] - part.centroid_m[1]) / part.dimensions_m[1] + 0.5,
        );
      } else {
        uv.push(
          (a[0] + a[1]) * (part.process === "cut-carbon" ? 35 : 7),
          a[2] * 25 + a[1] * 3,
        );
      }
    }
    g.setAttribute("position", new THREE.Float32BufferAttribute(p, 3));
    g.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2));
    g.setIndex(part.mesh.indices);
    g.computeVertexNormals();
    return g;
  }, [part]);
  useEffect(
    () => () => {
      geometry.dispose();
      texture?.dispose();
    },
    [geometry, texture],
  );
  const offset = offsets(part);
  useFrame((_, delta) =>
    ref.current?.position.lerp(
      new THREE.Vector3(...offset.map((v) => v * explode)),
      1 - Math.exp(-8 * delta),
    ),
  );
  const shell =
    ["wing", "fuselage", "tail"].includes(part.group) ||
    (part.process === "print" && part.group === "controls");
  const faded =
    (inside && shell) ||
    analysis === "airflow" ||
    (analysis === "structure" && part.process !== "cut-carbon");
  const inactive = stepGroups && !stepGroups.includes(part.group);
  const color =
    selected === part.id
      ? "#df9050"
      : part.id === "propeller"
        ? "#cc8747"
        : part.id === "motor"
          ? "#a7aeb0"
          : part.id === "battery"
            ? "#384a3c"
            : part.id.startsWith("servo")
              ? "#2b343c"
              : part.id.startsWith("aileron") ||
                  part.id.startsWith("elevator") ||
                  part.id === "rudder"
                ? "#637769"
                : colors[part.process] || part.color;
  return (
    <mesh
      ref={ref}
      geometry={geometry}
      castShadow
      receiveShadow
      onClick={(e) => {
        e.stopPropagation();
        onSelect(part);
      }}
    >
      <meshPhysicalMaterial
        color={
          part.process === "purchase" && texture && selected !== part.id
            ? "#ffffff"
            : color
        }
        map={texture}
        bumpMap={part.process === "purchase" ? null : texture}
        bumpScale={part.process === "print" ? 0.00012 : 0.00035}
        roughness={
          part.process === "cut-carbon"
            ? 0.35
            : part.id === "motor"
              ? 0.27
              : 0.55
        }
        metalness={
          part.id === "motor"
            ? 0.88
            : part.process === "cut-carbon"
              ? 0.32
              : 0.03
        }
        clearcoat={part.process === "cut-carbon" ? 0.55 : 0.12}
        clearcoatRoughness={0.35}
        transparent={faded || inactive}
        opacity={
          inactive ? 0.1 : faded ? (analysis === "airflow" ? 0.16 : 0.1) : 1
        }
        depthWrite={!faded && !inactive}
        side={THREE.DoubleSide}
      />
    </mesh>
  );
}
function Camera({ preset, controls }) {
  const { camera } = useThree();
  useEffect(() => {
    const positions = {
      perspective: [1.75, 1.2, 2],
      top: [0, 2.9, 0.001],
      side: [2.8, 0.3, 0],
      detail: [0.52, 0.45, 0.72],
    };
    const target = preset === "detail" ? [0, 0.05, 0.12] : [0, 0.07, 0];
    camera.position.set(...positions[preset]);
    camera.lookAt(...target);
    controls.current?.target.set(...target);
    controls.current?.update();
  }, [preset]);
  return null;
}
function Label({ position, children, dark = false }) {
  return (
    <Html position={position} center style={{ pointerEvents: "none" }}>
      <span className={`scene-label ${dark ? "dark-label" : ""}`}>
        {children}
      </span>
    </Html>
  );
}
function Details({ geometry, explode, labels, wiring, inside }) {
  const parts = Object.fromEntries(geometry.parts.map((p) => [p.id, p]));
  const anchor = (id) => {
    const part = parts[id];
    if (!part) return null;
    return point(part.centroid_m).map((v, i) => v + offsets(part)[i] * explode);
  };
  const routes = [
    ["battery", "esc", "#dc654e"],
    ["esc", "motor", "#d8af60"],
    ["esc", "receiver", "#e6be75"],
    ["receiver", "servo-1", "#769da6"],
    ["receiver", "servo-2", "#769da6"],
    ["receiver", "servo-3", "#769da6"],
    ["receiver", "servo-4", "#769da6"],
  ];
  return (
    <group>
      {wiring &&
        (inside || explode > 0) &&
        routes.map(([a, b, color]) => {
          const start = anchor(a),
            end = anchor(b);
          if (!start || !end) return null;
          const middle = start.map(
            (v, i) => (v + end[i]) / 2 + (i === 1 ? 0.045 : 0),
          );
          const curve = new THREE.CatmullRomCurve3([
            new THREE.Vector3(...start),
            new THREE.Vector3(...middle),
            new THREE.Vector3(...end),
          ]);
          return (
            <Line
              key={b}
              points={curve.getPoints(24)}
              color={color}
              lineWidth={2}
            />
          );
        })}
      {labels &&
        [
          ["motor", "BRUSHLESS MOTOR", [0.2, 0.1, 0]],
          ["battery", "3S / 1300 mAh", [-0.2, 0.06, 0.06]],
          ["payload", "MISSION PAYLOAD", [-0.26, 0.13, 0.12]],
          ["servo-2", "AILERON SERVO", [0.05, 0.16, 0]],
          ["receiver", "RADIO / CONTROL", [0.2, 0.07, 0.17]],
        ].map(([id, title, offset]) => {
          const p = anchor(id);
          if (
            !p ||
            (!inside &&
              explode === 0 &&
              ["battery", "receiver", "payload"].includes(id))
          )
            return null;
          const end = p.map((v, i) => v + offset[i]);
          return (
            <group key={id}>
              <Line points={[p, end]} color="#8a978b" lineWidth={0.7} />
              <mesh position={p}>
                <sphereGeometry args={[0.003, 8, 8]} />
                <meshBasicMaterial color="#536e60" />
              </mesh>
              <Label position={end}>{title}</Label>
            </group>
          );
        })}
    </group>
  );
}
function Tracers({ lines }) {
  const ref = useRef();
  const position = useMemo(() => new Float32Array(lines.length * 3), [lines]);
  useFrame(({ clock }) => {
    lines.forEach((line, i) => {
      const p = point(
        line[
          Math.floor(
            ((clock.elapsedTime * 0.16 + i * 0.071) % 1) * (line.length - 1),
          )
        ],
      );
      position.set(p, i * 3);
    });
    if (ref.current)
      ref.current.geometry.attributes.position.needsUpdate = true;
  });
  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[position, 3]} />
      </bufferGeometry>
      <pointsMaterial
        size={0.008}
        color="#ddf9f7"
        transparent
        opacity={0.85}
        sizeAttenuation
      />
    </points>
  );
}
function Flow({ flow }) {
  const mesh = useMemo(() => {
    if (flow?.status !== "COMPUTED") return null;
    const g = new THREE.BufferGeometry(),
      p = [],
      c = [];
    const scale = Math.max(
      1,
      ...flow.panels.map((p) => Math.abs(p.normal_load_pa)),
    );
    flow.panels.forEach((panel) => {
      const t = panel.normal_load_pa / scale;
      const color = new THREE.Color("#53b7bd").lerp(
        new THREE.Color(t < 0 ? "#617bd0" : "#efae52"),
        Math.abs(t),
      );
      for (const k of [0, 1, 2, 0, 2, 3]) {
        p.push(...point(panel.vertices_m[k]));
        c.push(color.r, color.g, color.b);
      }
    });
    g.setAttribute("position", new THREE.Float32BufferAttribute(p, 3));
    g.setAttribute("color", new THREE.Float32BufferAttribute(c, 3));
    g.computeVertexNormals();
    return g;
  }, [flow]);
  useEffect(() => () => mesh?.dispose(), [mesh]);
  if (!mesh) return null;
  return (
    <group>
      <mesh geometry={mesh}>
        <meshBasicMaterial
          vertexColors
          side={THREE.DoubleSide}
          transparent
          opacity={0.86}
        />
      </mesh>
      {flow.streamlines_m.map((line, i) => (
        <Line
          key={i}
          points={line.map(point)}
          color={i % 3 === 0 ? "#6ecaca" : "#719baa"}
          transparent
          opacity={0.6}
          lineWidth={1.1}
        />
      ))}
      <Tracers lines={flow.streamlines_m} />
    </group>
  );
}
function Structure({ raw, parameters }) {
  if (!raw?.spanwise) return null;
  const z = 0.45 - (0.28 + 0.3 * parameters.chord_m),
    half = parameters.span_m / 2;
  return (
    <group>
      <mesh position={[0, 0.015, z]} castShadow>
        <boxGeometry args={[0.09, 0.16, 0.13]} />
        <meshStandardMaterial
          color="#596970"
          metalness={0.65}
          roughness={0.33}
        />
      </mesh>
      <mesh position={[0, -0.065, z]} receiveShadow>
        <boxGeometry args={[0.36, 0.025, 0.35]} />
        <meshStandardMaterial
          color="#a4abad"
          metalness={0.55}
          roughness={0.5}
        />
      </mesh>
      {[-1, 1].map((sign) => (
        <group key={sign}>
          {raw.spanwise.slice(0, -1).map((s, i) => {
            const next = raw.spanwise[i + 1];
            const ratio = s.moment_nm / raw.root_moment_nm;
            const color = new THREE.Color("#59b6bb").lerp(
              new THREE.Color("#df7754"),
              ratio,
            );
            return (
              <Line
                key={i}
                points={[s, next].map((v) => [
                  sign * v.y_m,
                  0.115 + 0.05 * v.y_m + v.deflection_m * 4,
                  z,
                ])}
                color={color}
                lineWidth={5}
              />
            );
          })}
          <Line
            points={[
              [0, 0.115, z],
              [sign * half, 0.115 + 0.05 * half, z],
            ]}
            color="#929f9f"
            lineWidth={1}
            dashed
            dashSize={0.02}
            gapSize={0.015}
          />
          {[0.2, 0.4, 0.6, 0.8, 1].map((t) => (
            <group key={t}>
              <Line
                points={[
                  [sign * half * t, 0.24 + 0.05 * half * t, z],
                  [sign * half * t, 0.34 + 0.05 * half * t, z],
                ]}
                color="#6ab2b0"
                lineWidth={1.5}
              />
              <mesh position={[sign * half * t, 0.35 + 0.05 * half * t, z]}>
                <coneGeometry args={[0.009, 0.02, 8]} />
                <meshBasicMaterial color="#6ab2b0" />
              </mesh>
            </group>
          ))}
        </group>
      ))}
      <Label position={[0, 0.48, z]} dark>
        UNIFORM LOAD · {raw.total_lift_n.toFixed(1)} N TOTAL
      </Label>
      <Label position={[-half, 0.14 + raw.tip_deflection_m * 4, z]} dark>
        {(raw.tip_deflection_m * 1000).toFixed(1)} mm TIP · DISPLAY 4×
      </Label>
    </group>
  );
}
function Trim({ aero }) {
  if (!aero?.cg_m) return null;
  const cg = point(aero.cg_m),
    np = point([aero.x_np, 0, aero.cg_m[2]]);
  return (
    <group>
      <mesh position={cg}>
        <sphereGeometry args={[0.008, 16, 16]} />
        <meshBasicMaterial color="#d98b53" depthTest={false} />
      </mesh>
      <Line
        points={[
          [np[0] - 0.18, np[1] + 0.04, np[2]],
          [np[0] + 0.18, np[1] + 0.04, np[2]],
        ]}
        color="#6bad92"
        dashed
        dashSize={0.015}
        gapSize={0.012}
      />
      <Line
        points={[cg, [cg[0], cg[1] + 0.3, cg[2]]]}
        color="#458b73"
        lineWidth={2}
      />
      <Label position={[cg[0] + 0.1, cg[1] + 0.32, cg[2]]}>
        LIFT {aero.L.toFixed(1)} N
      </Label>
      <Label position={[cg[0] - 0.1, cg[1] + 0.07, cg[2]]}>CG</Label>
    </group>
  );
}
function Setting({ environment }) {
  if (environment === "airflow")
    return (
      <group>
        {[-0.6, 0.7].map((z) => (
          <Line
            key={z}
            points={[
              [-1.12, -0.12, z],
              [-1.12, 0.65, z],
              [1.12, 0.65, z],
              [1.12, -0.12, z],
            ]}
            color="#3c626e"
            lineWidth={1}
          />
        ))}
        {[-1.12, 1.12].map((x) => (
          <Line
            key={x}
            points={[
              [x, 0.65, -0.6],
              [x, 0.65, 0.7],
            ]}
            color="#3c626e"
            lineWidth={1}
          />
        ))}
      </group>
    );
  if (environment === "flight")
    return (
      <group position={[0, -0.75, 0]}>
        <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
          <planeGeometry args={[100, 100]} />
          <meshStandardMaterial color="#b4b99a" roughness={1} />
        </mesh>
        {Array.from({ length: 24 }, (_, i) => (
          <mesh
            key={i}
            rotation={[-Math.PI / 2, 0, (i % 3) * 0.15]}
            position={[((i % 6) - 2.5) * 2, 0.002, Math.floor(i / 6) * 2 - 4]}
          >
            <planeGeometry args={[1.85, 1.85]} />
            <meshStandardMaterial
              color={["#a4ad8c", "#c2bc98", "#b1b28c", "#a7b49a"][i % 4]}
            />
          </mesh>
        ))}
        <mesh position={[0, 0.005, -2]} rotation={[-Math.PI / 2, 0, 0.23]}>
          <planeGeometry args={[12, 0.1]} />
          <meshStandardMaterial color="#d1c7ac" />
        </mesh>
      </group>
    );
  return null;
}
export default function Scene({
  geometry,
  explode,
  inside,
  selected,
  onSelect,
  mode,
  evidence,
  preset,
  autoRotate,
  stepGroups,
  labels,
  wiring,
  environment,
  flow,
}) {
  const controls = useRef();
  const sim = mode === "Simulate";
  const dark = sim && environment !== "flight";
  const aero = evidence.find((e) => e.method === "aero")?.output.raw,
    structure = evidence.find((e) => e.method === "structure")?.output.raw;
  return (
    <Canvas
      shadows
      camera={{ position: [1.75, 1.2, 2], fov: 36, near: 0.01, far: 150 }}
      dpr={[1, 2]}
      onPointerMissed={() => onSelect(null)}
      gl={{
        antialias: true,
        toneMapping: THREE.ACESFilmicToneMapping,
        toneMappingExposure: 0.95,
      }}
    >
      <color
        attach="background"
        args={[dark ? "#182c35" : sim ? "#dce6df" : "#edf0e8"]}
      />
      <fog
        attach="fog"
        args={[dark ? "#182c35" : sim ? "#dce6df" : "#edf0e8", 5, 20]}
      />
      <ambientLight intensity={dark ? 0.45 : 0.65} />
      <hemisphereLight args={["#fff9e9", "#768879", 1.2]} />
      <directionalLight
        position={[-2, 4, 3]}
        intensity={2}
        castShadow
        shadow-mapSize={[2048, 2048]}
        shadow-camera-left={-2}
        shadow-camera-right={2}
        shadow-camera-top={2}
        shadow-camera-bottom={-2}
        shadow-bias={-0.0002}
      />
      <directionalLight position={[2, 1, -2]} intensity={1.2} color="#c9e8ec" />
      <Suspense fallback={null}>
        <Environment resolution={128} frames={1}>
          <Lightformer
            position={[0, 3, 0]}
            rotation={[Math.PI / 2, 0, 0]}
            scale={[5, 5, 1]}
            intensity={2}
          />
          <Lightformer
            position={[-3, 1, 1]}
            rotation={[0, Math.PI / 2, 0]}
            scale={[2, 5, 1]}
            intensity={3}
          />
          <Lightformer position={[2, 2, -3]} scale={[4, 2, 1]} intensity={2} />
        </Environment>
        {geometry.parts.map((part) => (
          <Part
            key={part.id}
            {...{ part, explode, inside, onSelect, stepGroups }}
            selected={selected?.id}
            analysis={sim ? environment : null}
          />
        ))}
        {!sim && <Details {...{ geometry, explode, labels, wiring, inside }} />}
        {sim && (
          <>
            <Setting environment={environment} />
            {environment === "airflow" ? (
              <Flow flow={flow} />
            ) : environment === "structure" ? (
              <Structure raw={structure} parameters={geometry.parameters} />
            ) : (
              <Trim aero={aero} />
            )}
          </>
        )}
        {(!sim || environment === "structure") && (
          <ContactShadows
            position={[0, -0.1, 0]}
            opacity={inside ? 0.12 : 0.32}
            scale={5}
            blur={2.5}
            far={2}
            resolution={512}
          />
        )}
      </Suspense>
      {sim && environment === "structure" && (
        <gridHelper
          args={[
            5,
            50,
            dark ? "#2e4650" : "#dde3d8",
            dark ? "#243b45" : "#e4e9df",
          ]}
          position={[0, -0.115, 0]}
        />
      )}
      <OrbitControls
        ref={controls}
        target={[0, 0.07, 0]}
        minDistance={0.25}
        maxDistance={5}
        autoRotate={autoRotate}
        autoRotateSpeed={0.5}
        maxPolarAngle={Math.PI * 0.49}
      />
      <Camera preset={preset} controls={controls} />
    </Canvas>
  );
}
