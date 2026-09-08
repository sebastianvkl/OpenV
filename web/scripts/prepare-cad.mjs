import { mkdir, copyFile, writeFile } from "node:fs/promises";
const root = new URL("../", import.meta.url),
  source = new URL("node_modules/occt-import-js/", root),
  target = new URL("public/cad-kernel/", root);
await mkdir(target, { recursive: true });
for (const name of ["occt-import-js.js", "occt-import-js.wasm"])
  await copyFile(new URL("dist/" + name, source), new URL(name, target));
await copyFile(new URL("LICENSE.md", source), new URL("LICENSE.md", target));
await copyFile(
  new URL("README.md", source),
  new URL("BUILD-SOURCE.md", target),
);
await writeFile(
  new URL("NOTICE.txt", target),
  "occt-import-js 0.0.23, unmodified npm distribution. LGPL-2.1.\nSource and build instructions: https://github.com/kovacsv/occt-import-js/tree/0.0.23\nLicense: /cad-kernel/LICENSE.md\nThis separately loaded library can be replaced by compatible JS/WASM builds in this directory. OpenV application code remains MIT licensed.\n",
);
console.log("Prepared local STEP import kernel assets");
