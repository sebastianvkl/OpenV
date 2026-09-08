// Identity/scale checks prevent attaching one component's specs to another STEP mesh.
// These display checks never create engineering PASS or replace the source evidence.
export function meshBounds(part) {
  const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
  const points = part.mesh.positions;
  if (!points.length || points.length % 3) throw new Error("Incomplete CAD coordinates");
  for (let i = 0; i < points.length; i++) {
    if (!Number.isFinite(points[i])) throw new Error("Nonfinite CAD coordinate");
    min[i % 3] = Math.min(min[i % 3], points[i]);
    max[i % 3] = Math.max(max[i % 3], points[i]);
  }
  return { min, max, size: max.map((v, i) => v - min[i]), center: max.map((v, i) => (v + min[i]) / 2) };
}

export function stepPartNames(root, count) {
  const names = new Array(count);
  function visit(node) {
    for (const index of node.meshes || []) {
      if (!Number.isInteger(index) || index < 0 || index >= count || names[index])
        throw new Error("Ambiguous STEP assembly instance");
      if (!node.name || node.meshes.length !== 1)
        throw new Error("Unsupported STEP part hierarchy");
      names[index] = node.name;
    }
    for (const child of node.children || []) visit(child);
  }
  visit(root);
  if (Array.from(names).some((name) => !name))
    throw new Error("Missing STEP assembly identity");
  return names;
}

export function attachStepMeshes(geometry, imported) {
  if (imported.length !== geometry.parts.length)
    throw new Error(
      `STEP has ${imported.length} meshes; the captured assembly has ${geometry.parts.length} parts`,
    );
  const byId = new Map(imported.map((m) => [m.name, m]));
  if (byId.size !== imported.length)
    throw new Error("Ambiguous STEP part names");
  let triangles = 0,
    faces = 0;
  const parts = geometry.parts.map((part) => {
    const mesh = byId.get(part.id);
    if (!mesh) throw new Error(`STEP identity missing: ${part.id}`);
    if (
      !mesh.positions.length ||
      mesh.positions.length % 3 ||
      mesh.indices.length % 3 ||
      !mesh.indices.length
    )
      throw new Error(`Incomplete STEP mesh: ${part.id}`);
    const lo = [Infinity, Infinity, Infinity],
      hi = [-Infinity, -Infinity, -Infinity];
    for (let i = 0; i < mesh.positions.length; i++) {
      const n = mesh.positions[i];
      if (!Number.isFinite(n)) throw new Error("Nonfinite STEP coordinate");
      lo[i % 3] = Math.min(lo[i % 3], n);
      hi[i % 3] = Math.max(hi[i % 3], n);
    }
    if (
      Array.from(mesh.indices).some(
        (i) => !Number.isInteger(i) || i < 0 || i >= mesh.positions.length / 3,
      )
    )
      throw new Error("Invalid STEP face index");
    // Compare tessellated bounds against the captured CAD mesh, including placement.
    const oldLo = [Infinity, Infinity, Infinity],
      oldHi = [-Infinity, -Infinity, -Infinity];
    part.mesh.positions.forEach((n, i) => {
      oldLo[i % 3] = Math.min(oldLo[i % 3], n);
      oldHi[i % 3] = Math.max(oldHi[i % 3], n);
    });
    if (
      lo.some((n, i) => Math.abs(n - oldLo[i]) > 0.001) ||
      hi.some((n, i) => Math.abs(n - oldHi[i]) > 0.001)
    )
      throw new Error(`STEP scale or placement differs: ${part.id}`);
    if (
      mesh.normals &&
      (mesh.normals.length !== mesh.positions.length ||
        Array.from(mesh.normals).some((n) => !Number.isFinite(n)))
    )
      throw new Error("Invalid STEP normals");
    triangles += mesh.indices.length / 3;
    faces += mesh.faceCount;
    return {
      ...part,
      mesh: {
        positions: mesh.positions,
        indices: mesh.indices,
        normals: mesh.normals,
      },
      stepFaceCount: mesh.faceCount,
    };
  });
  return { geometry: { ...geometry, parts }, triangles, faces };
}
