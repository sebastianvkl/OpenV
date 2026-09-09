import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root=fileURLToPath(new URL('../../',import.meta.url));
const spec=JSON.parse(await readFile(path.join(root,'deploy/static-demo.json'),'utf8'));
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const cache=path.join(root,'web/node_modules/.cache/openv');
await mkdir(cache,{recursive:true});
const archive=process.env.OPENV_STATIC_ARCHIVE || path.join(cache,`${spec.sha256}.tar.gz`);
let bytes;
try { bytes=await readFile(archive); } catch {}
if (!bytes || hash(bytes)!==spec.sha256) {
  if(process.env.OPENV_STATIC_ARCHIVE)throw new Error('Local static archive is missing or has the wrong hash');
  const response=await fetch(spec.url,{signal:AbortSignal.timeout(180000)});
  if(!response.ok)throw new Error(`Static demo archive download failed: ${response.status}`);
  bytes=Buffer.from(await response.arrayBuffer());
  if(hash(bytes)!==spec.sha256)throw new Error('Static demo archive hash mismatch');
  await writeFile(archive,bytes);
}
if(bytes.length!==spec.bytes)throw new Error('Static archive size mismatch');
const names=execFileSync('tar',['-tzf',archive],{encoding:'utf8',maxBuffer:4*1024*1024}).trim().split('\n');
if(names.some(name=>!name.startsWith('artifacts/')&&!name.startsWith('recorded/') || name.split('/').includes('..') || name.includes('\\')))throw new Error('Unsafe static archive path');
const dist=path.join(root,'web/dist');
execFileSync('tar',['-xzf',archive,'-C',dist]);
const files=JSON.parse(await readFile(path.join(dist,'recorded/archive-files.json'),'utf8'));
for(const [name,info] of Object.entries(files)){
  if(!names.includes(name))throw new Error(`Missing static file: ${name}`);
  const data=await readFile(path.join(dist,name));
  if(data.length!==info.size||hash(data)!==info.sha256)throw new Error(`Static file hash mismatch: ${name}`);
}
const config=JSON.parse(await readFile(path.join(dist,'recorded/config.json'),'utf8'));
if(!config.read_only||!config.static_demo||config.astra_ready)throw new Error('Static demo must never enable engineering runs');
console.log(`Prepared ${spec.run_count} recorded runs; verified ${Object.keys(files).length} static file hashes. No backend or credentials required.`);
