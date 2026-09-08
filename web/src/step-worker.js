/* Browser-only CAD reader. No model state or verification statuses are written. */
import { stepPartNames } from "./step-model.mjs";
import { cachedStep, rememberStep } from "./step-cache.js";
function send(value, cached) {
  self.postMessage({ done: true, ...value, cached }, value.meshes.flatMap((m) => [
    m.positions.buffer, m.indices.buffer, ...(m.normals ? [m.normals.buffer] : []),
  ]));
}
self.onmessage = async ({ data: { url, base, bypassCache } }) => {
  try {
    self.postMessage({ stage: "Downloading assembly STEP" });
    const response = await fetch(url);
    if (!response.ok)
      throw new Error(`STEP download failed (${response.status})`);
    const bytes = new Uint8Array(await response.arrayBuffer());
    if (bytes.length > 64 * 1024 * 1024)
      throw new Error("STEP exceeds the 64 MB browser-view limit");
    const hash = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)))
      .map((n) => n.toString(16).padStart(2, "0")).join("");
    self.postMessage({ stage: "Checking saved geometry against the STEP file" });
    const saved = !bypassCache && await cachedStep(hash);
    if (saved && saved.hash === hash && saved.bytes === bytes.length) {
      send(saved, true);
      return;
    }
    self.postMessage({ stage: "Loading CAD reader" });
    importScripts(`${base}/cad-kernel/occt-import-js.js`);
    const occt = await self.occtimportjs({
      locateFile: (name) => `${base}/cad-kernel/${name}`,
    });
    self.postMessage({
      stage: "Reading solid geometry and tessellating faces",
    });
    const result = occt.ReadStepFile(bytes, {
      linearUnit: "meter",
      linearDeflectionType: "absolute_value",
      linearDeflection: 0.00015,
      angularDeflection: 0.15,
    });
    if (!result.success || !result.meshes?.length)
      throw new Error("The STEP reader returned no displayable geometry");
    const names = stepPartNames(result.root, result.meshes.length);
    const meshes = result.meshes.map((m, index) => ({
      name: names[index],
      color: m.color,
      faceCount: m.brep_faces?.length || 0,
      positions: new Float32Array(m.attributes.position.array),
      normals: m.attributes.normal
        ? new Float32Array(m.attributes.normal.array)
        : null,
      indices: new Uint32Array(m.index.array),
    }));
    const value = { meshes, root: result.root, bytes: bytes.length, hash };
    await rememberStep(hash, value);
    send(value, false);
  } catch (error) {
    self.postMessage({ error: error.message || String(error) });
  }
};
