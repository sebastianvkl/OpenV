import React, { useEffect, useMemo, useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import { Line, Sky } from "@react-three/drei";
import * as THREE from "three";

// Playback of version-bound solver samples; historical runs retain a labeled cinematic circuit.
const RADIUS = 90;
const HEIGHT = 35;
const palettes = {
  valley: {
    ground: "#71845a",
    trees: "#355e45",
    water: "#438d97",
    sky: "#b6d5df",
    field: "#b0ac6f",
  },
  coast: {
    ground: "#a6a175",
    trees: "#526c48",
    water: "#398f9b",
    sky: "#b9dfe5",
    field: "#d0bd8a",
  },
  ridge: {
    ground: "#7e8a7a",
    trees: "#3c6055",
    water: "#527d89",
    sky: "#bccdd8",
    field: "#a0a892",
  },
};
function random(seed) {
  const x = Math.sin(seed * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
}
function heightAt(x, z, world) {
  const d = Math.hypot(x, z);
  const hills = Math.max(0, d - 145) / 9;
  const base = 3 + 2 * Math.sin(x * 0.027) * Math.cos(z * 0.023);
  return (
    base +
    hills * (0.8 + 0.45 * Math.sin(x * 0.009 + 1.2) * Math.cos(z * 0.011)) +
    (world === "ridge" ? hills * 0.65 : 0)
  );
}
function Terrain({ world, course }) {
  const theme = palettes[world];
  const mesh = useMemo(() => {
    const g = new THREE.PlaneGeometry(2200, 2200, 160, 160);
    g.rotateX(-Math.PI / 2);
    const position = g.attributes.position,
      colors = [];
    for (let i = 0; i < position.count; i++) {
      const x = position.getX(i),
        z = position.getZ(i);
      let y = heightAt(x, z, world);
      if (world === "coast" && x > 170) y -= Math.min(40, (x - 170) * 0.35);
      if (world !== "coast") {
        const lake = ((x + 265) / 95) ** 2 + ((z + 100) / 125) ** 2;
        if (lake < 1.15) y = Math.min(y, 1 + Math.max(0, lake - 0.7) * 32);
      }
      if (course) {
        const blend = Math.min(
          1,
          Math.max(0, Math.abs(x) - 160, -z - 100, z - 500) / 140,
        );
        y = Math.min(y, 5.4) + Math.max(0, y - 5.4) * blend;
      }
      position.setY(i, y);
      const tint = new THREE.Color(theme.ground).lerp(
        new THREE.Color("#c9c5b1"),
        Math.min(0.6, y / 220),
      );
      tint.multiplyScalar(
        0.87 + random(Math.floor(x / 18) + Math.floor(z / 18) * 81) * 0.23,
      );
      colors.push(tint.r, tint.g, tint.b);
    }
    g.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
    g.computeVertexNormals();
    return g;
  }, [world, course]);
  useEffect(() => () => mesh.dispose(), [mesh]);
  const trees = useRef(),
    trunks = useRef();
  useEffect(() => {
    const dummy = new THREE.Object3D(),
      color = new THREE.Color();
    for (let i = 0; i < 650; i++) {
      let x = (random(i * 7 + 1) - 0.5) * 1100,
        z = (random(i * 7 + 2) - 0.5) * 1100;
      // Keep the small airfield and the coastal water clear of scenery trees.
      if (Math.abs(x) < 30 && Math.abs(z) < 135) x += 65;
      if (course && Math.abs(x) < 180) x += x < 0 ? -190 : 190;
      if (world === "coast" && x > 160) x = -Math.abs(x);
      const h = 5 + random(i * 7 + 3) * 10,
        ground = course
          ? Math.min(5.4, heightAt(x, z, world)) +
            Math.max(0, heightAt(x, z, world) - 5.4) *
              Math.min(
                1,
                Math.max(0, Math.abs(x) - 160, -z - 100, z - 500) / 140,
              )
          : heightAt(x, z, world);
      dummy.position.set(x, ground + h * 0.64, z);
      dummy.scale.set(h * 0.26, h, h * 0.26);
      dummy.rotation.set(0, random(i) * 6.28, 0);
      dummy.updateMatrix();
      trees.current.setMatrixAt(i, dummy.matrix);
      color.set(theme.trees).multiplyScalar(0.8 + random(i * 7 + 5) * 0.35);
      trees.current.setColorAt(i, color);
      dummy.position.y = ground + h * 0.23;
      dummy.scale.set(0.3, h * 0.5, 0.3);
      dummy.updateMatrix();
      trunks.current.setMatrixAt(i, dummy.matrix);
    }
    trees.current.instanceMatrix.needsUpdate = true;
    trees.current.instanceColor.needsUpdate = true;
    trunks.current.instanceMatrix.needsUpdate = true;
  }, [world, course]);
  return (
    <group>
      <mesh geometry={mesh} receiveShadow>
        <meshStandardMaterial vertexColors roughness={1} />
      </mesh>
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={world === "coast" ? [610, 1, 0] : [-265, 4, -100]}
      >
        <planeGeometry args={world === "coast" ? [880, 2200] : [180, 240]} />
        <meshPhysicalMaterial
          color={theme.water}
          roughness={0.25}
          metalness={0.15}
          clearcoat={0.6}
        />
      </mesh>
      <instancedMesh frustumCulled={false} ref={trees} args={[null, null, 650]}>
        <latheGeometry
          args={[
            [
              [0, -0.5],
              [0.95, -0.4],
              [0.46, -0.08],
              [0.72, -0.07],
              [0.25, 0.2],
              [0.43, 0.21],
              [0, 0.5],
            ].map((p) => new THREE.Vector2(...p)),
            8,
          ]}
        />
        <meshStandardMaterial color="#ffffff" roughness={0.95} />
      </instancedMesh>
      <instancedMesh
        frustumCulled={false}
        ref={trunks}
        args={[null, null, 650]}
      >
        <cylinderGeometry args={[1, 1, 1, 5]} />
        <meshStandardMaterial color="#665c45" />
      </instancedMesh>
      {/* A fictional airfield provides scale and parallax; it is not a landing analysis. */}
      <group position={[0, 5.4, 0]}>
        <mesh rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[13, 200]} />
          <meshStandardMaterial color="#777c74" />
        </mesh>
        {Array.from({ length: 13 }, (_, i) => (
          <mesh
            key={i}
            rotation={[-Math.PI / 2, 0, 0]}
            position={[0, 0.015, i * 14 - 84]}
          >
            <planeGeometry args={[0.5, 6]} />
            <meshBasicMaterial color="#eee9d2" />
          </mesh>
        ))}
        {[-1, 1].map((s) => (
          <mesh
            key={s}
            rotation={[-Math.PI / 2, 0, 0]}
            position={[s * 5.7, 0.01, 0]}
          >
            <planeGeometry args={[0.2, 194]} />
            <meshBasicMaterial color="#d5d8bf" />
          </mesh>
        ))}
        <mesh position={[25, 3.5, -30]}>
          <boxGeometry args={[17, 7, 24]} />
          <meshStandardMaterial color="#b6b6a4" roughness={0.8} />
        </mesh>
        <mesh position={[25, 7.2, -30]} rotation={[0, 0, 0.03]}>
          <boxGeometry args={[19, 0.6, 26]} />
          <meshStandardMaterial
            color="#60766f"
            metalness={0.3}
            roughness={0.6}
          />
        </mesh>
        <mesh position={[35, 5, 8]}>
          <cylinderGeometry args={[0.12, 0.12, 10, 8]} />
          <meshStandardMaterial color="#d9d8c4" />
        </mesh>
      </group>
      {Array.from({ length: 10 }, (_, i) => {
        const x = -115 - (i % 3) * 70,
          z = Math.floor(i / 3) * 80 - 180;
        return (
          <mesh
            key={i}
            rotation={[-Math.PI / 2, 0, 0.04]}
            position={[x, heightAt(x, z, world) + 0.2, z]}
          >
            <planeGeometry args={[55, 65]} />
            <meshStandardMaterial color={i % 2 ? theme.field : "#8f995e"} />
          </mesh>
        );
      })}
      {Array.from({ length: 12 }, (_, i) => (
        <group
          key={i}
          position={[
            (random(i + 200) - 0.5) * 1400,
            170 + random(i + 400) * 130,
            (random(i + 300) - 0.5) * 1400,
          ]}
          scale={[50, 9, 24]}
        >
          {[
            [-0.6, 0, 0],
            [0, 0.25, 0],
            [0.6, 0, 0.15],
          ].map((p, k) => (
            <mesh key={k} position={p}>
              <sphereGeometry args={[0.8, 12, 8]} />
              <meshStandardMaterial
                color="#f3f5ee"
                roughness={1}
                transparent
                opacity={0.8}
              />
            </mesh>
          ))}
        </group>
      ))}
    </group>
  );
}
export default function FlightWorld({
  children,
  aero,
  playing,
  cameraMode,
  world,
  rate,
  resetKey,
  trajectory,
  onFlightSample,
}) {
  const aircraft = useRef(),
    elapsed = useRef(0),
    body = useRef(),
    reported = useRef(-1);
  const { camera } = useThree();
  const speed = Number.isFinite(aero?.velocity_mps) ? aero.velocity_mps : 0;
  const trail = useMemo(
    () =>
      trajectory
        ? trajectory.samples.map((s) => [s.east_m, s.height_m + 5.4, s.north_m])
        : Array.from({ length: 145 }, (_, i) => {
            const a = (i / 144) * Math.PI * 2;
            return [RADIUS * Math.sin(a), HEIGHT, RADIUS * Math.cos(a)];
          }),
    [trajectory],
  );
  useEffect(() => {
    elapsed.current = 0;
    reported.current = -1;
  }, [resetKey, speed, trajectory]);
  useFrame((_, delta) => {
    if (playing)
      elapsed.current += Math.min(delta, trajectory ? 1 : 0.1) * rate;
    const angle = (elapsed.current * speed) / RADIUS;
    let position = new THREE.Vector3(
      RADIUS * Math.sin(angle),
      HEIGHT,
      RADIUS * Math.cos(angle),
    );
    let yaw = Math.PI / 2 + angle;
    if (trajectory) {
      elapsed.current = Math.min(elapsed.current, trajectory.duration_s);
      const rows = trajectory.samples,
        t = elapsed.current;
      let j = Math.min(rows.length - 1, Math.floor(t * 10));
      while (j + 1 < rows.length && rows[j + 1].time_s <= t) j++;
      const a = rows[j],
        b = rows[Math.min(j + 1, rows.length - 1)];
      const f =
        b.time_s > a.time_s ? (t - a.time_s) / (b.time_s - a.time_s) : 0;
      const sample = Object.fromEntries(
        Object.keys(a).map((k) => [k, a[k] + (b[k] - a[k]) * f]),
      );
      position.set(sample.east_m, sample.height_m + 5.4, sample.north_m);
      yaw = sample.heading_rad;
      body.current.rotation.set(-sample.pitch_rad, 0, -sample.bank_rad);
      if (
        (reported.current !== "done" &&
          Math.floor(t * 5) !== reported.current) ||
        (t === trajectory.duration_s && reported.current !== "done")
      ) {
        reported.current =
          t === trajectory.duration_s ? "done" : Math.floor(t * 5);
        onFlightSample?.(sample);
      }
    }
    aircraft.current.position.copy(position);
    aircraft.current.rotation.set(0, yaw, 0);
    const offset = new THREE.Vector3(
      ...{
        chase: [-1.6, 1.1, -2.2],
        wing: [-2.3, 0.8, 1.6],
        survey: [9, 7, -12],
      }[cameraMode],
    );
    offset.applyAxisAngle(new THREE.Vector3(0, 1, 0), yaw);
    const desired = position.clone().add(offset);
    // Follow captured samples; the browser never integrates or creates engineering evidence.
    if (cameraMode === "survey") {
      camera.position.copy(
        position
          .clone()
          .multiplyScalar(1.45)
          .add(new THREE.Vector3(30, 45, 30)),
      );
      camera.lookAt(
        position
          .clone()
          .multiplyScalar(0.45)
          .add(new THREE.Vector3(0, 6, 0)),
      );
    } else {
      camera.position.copy(desired);
      camera.lookAt(position.clone().add(new THREE.Vector3(0, 0.12, 0)));
    }
  });
  return (
    <>
      <color attach="background" args={[palettes[world].sky]} />
      <fog attach="fog" args={[palettes[world].sky, 250, 1550]} />
      <Sky
        distance={2200}
        sunPosition={[500, 300, -600]}
        turbidity={3.5}
        rayleigh={0.8}
        mieCoefficient={0.004}
        mieDirectionalG={0.85}
      />
      <hemisphereLight args={["#f9f3df", "#6f7e55", 0.8]} />
      <directionalLight position={[400, 600, -300]} intensity={2} />
      <Terrain world={world} course={!!trajectory} />
      <Line
        points={trail}
        color="#e4d6a3"
        transparent
        opacity={0.35}
        lineWidth={1}
        dashed
        dashSize={3}
        gapSize={5}
      />
      <group ref={aircraft}>
        <group
          ref={body}
          rotation={[
            (-(aero?.alpha_deg || 0) * Math.PI) / 180,
            0,
            -Math.atan((speed * speed) / (9.80665 * RADIUS)),
          ]}
        >
          {children}
        </group>
      </group>
    </>
  );
}
