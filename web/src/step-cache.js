// Display-only cache. Keys include the downloaded STEP hash and reader settings.
export const STEP_READER_REVISION = "occt-0.0.23-meter-0.00015-0.15-hierarchy-v1";
const request = (req) => new Promise((resolve, reject) => {
  req.onsuccess = () => resolve(req.result);
  req.onerror = () => reject(req.error);
});
async function database() {
  const req = indexedDB.open("openv-step-display", 1);
  req.onupgradeneeded = () => req.result.createObjectStore("models", { keyPath: "key" });
  return request(req);
}
export async function cachedStep(hash) {
  let db;
  try {
    db = await database();
    const row = await request(db.transaction("models").objectStore("models").get(`${STEP_READER_REVISION}:${hash}`));
    return row?.value || null;
  } catch { return null; } finally { db?.close(); }
}
export async function rememberStep(hash, value) {
  let db;
  try {
    db = await database();
    const tx = db.transaction("models", "readwrite"), store = tx.objectStore("models");
    const complete = new Promise((resolve, reject) => {
      tx.oncomplete = resolve;
      tx.onerror = tx.onabort = () => reject(tx.error);
    });
    const key = `${STEP_READER_REVISION}:${hash}`;
    store.put({ key, saved: Date.now(), value });
    const all = store.getAll();
    all.onsuccess = () => {
      for (const row of all.result.sort((a, b) => b.saved - a.saved).slice(2)) store.delete(row.key);
    };
    await complete;
  } catch { /* Storage denial/quota must not prevent STEP inspection. */ }
  finally { db?.close(); }
}
