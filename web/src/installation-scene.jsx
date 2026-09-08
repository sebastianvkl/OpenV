import React from "react";
import { Html } from "@react-three/drei";
const point = ([x, y, z]) => [y, z, 0.45 - x];
export function InstallationScene({ data, geometry }) {
  if (!data?.available) return null;
  const failed = new Set(data.static.collisions.flatMap((row) => row.parts));
  data.insertions.forEach((row) =>
    row.collisions.forEach((hit) => hit.parts.forEach((id) => failed.add(id))),
  );
  return (
    <group>
      {geometry.parts
        .filter((part) => failed.has(part.id))
        .map((part) => (
          <mesh key={part.id} position={point(part.centroid_m)}>
            <boxGeometry
              args={[
                part.dimensions_m[1] + 0.002,
                part.dimensions_m[2] + 0.002,
                part.dimensions_m[0] + 0.002,
              ]}
            />
            <meshBasicMaterial color="#fa896e" wireframe depthTest={false} />
          </mesh>
        ))}
      {data.insertions.map((row) => {
        const min = row.bounds_mm.min,
          max = row.bounds_mm.max;
        const center = min.map((n, i) => (n + max[i]) / 2000),
          size = min.map((n, i) => (max[i] - n) / 1000);
        return (
          <group key={row.part_id}>
            <mesh position={point(center)}>
              <boxGeometry args={[size[1], size[2], size[0]]} />
              <meshBasicMaterial
                color={row.collisions.length ? "#fa896e" : "#8eb7c6"}
                wireframe
                transparent
                opacity={0.65}
                depthTest={false}
              />
            </mesh>
            <Html
              position={point([center[0], center[1], max[2] / 1000 + 0.015])}
              center
              style={{ pointerEvents: "none" }}
            >
              <span className="installation-label">{row.part_id} ↑</span>
            </Html>
          </group>
        );
      })}
      <mesh
        position={point(data.propeller.center_m)}
        rotation={[Math.PI / 2, 0, 0]}
      >
        <cylinderGeometry
          args={[
            data.propeller.radius_mm / 1000,
            data.propeller.radius_mm / 1000,
            data.propeller.axial_thickness_mm / 1000,
            64,
            1,
            true,
          ]}
        />
        <meshBasicMaterial
          color={data.propeller.min_clearance_mm >= 2 ? "#8eb7c6" : "#fa896e"}
          wireframe
          transparent
          opacity={0.35}
        />
      </mesh>
    </group>
  );
}
export function InstallationSummary({ data, onSelect, geometry, onEvidence }) {
  if (!data?.available)
    return (
      <p className="small-copy">
        No installed-clearance evidence for this version. New builds include the
        installation checks.
      </p>
    );
  const collisions = [
    ...data.static.collisions,
    ...data.insertions.flatMap((row) => row.collisions),
  ];
  const unique = [
    ...new Map(collisions.map((row) => [row.parts.join(":"), row])).values(),
  ];
  return (
    <div className="installation-summary">
      <p>
        {data.static.checked_pair_count} component/solid pairs checked · full
        propeller rotation · four continuous insertion envelopes.
      </p>
      <small>
        Blue volumes show insertion paths with wing, saddle, spars and hatches
        removed. Red outlines identify interference. Wire routes, tool access
        and joint strength remain UNKNOWN.
      </small>
      {unique.map((row) => (
        <button
          key={row.parts.join(":")}
          className="collision-row"
          onClick={() =>
            onSelect(geometry.parts.find((part) => part.id === row.parts[0]))
          }
        >
          {row.parts.join(" / ")}
          <span>{row.volume_mm3.toFixed(1)} mm³ overlap</span>
        </button>
      ))}
      <button className="text-link" onClick={() => onEvidence("component-fit")}>
        Inspect collision evidence ↗
      </button>
    </div>
  );
}
