"""Export already-public run files; never include host credentials or logs."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile


def export(source, index, output):
    rows=json.loads(index.read_text())
    entries={}
    allowed={'.json','.stl','.step','.zip','.csv','.md'}
    for row in rows:
        rid=row['id']
        if not re.fullmatch(r'[A-Za-z0-9-]+',rid):raise ValueError('Invalid run ID')
        folder=source/rid
        run=(folder/'run.json').read_bytes()
        if json.loads(run)['id']!=rid:raise ValueError('Run identity mismatch')
        entries[f'recorded/runs/{rid}.json']=run
        for path in sorted(folder.rglob('*')):
            if path.is_symlink():raise ValueError('Symlink in public export')
            if path.is_file() and path.suffix in allowed:
                entries[f'artifacts/{rid}/{path.relative_to(folder).as_posix()}']=path.read_bytes()
    entries['recorded/runs.json']=index.read_bytes()
    entries['recorded/config.json']=json.dumps({'model':'gpt-6-astra','read_only':True,'static_demo':True,'astra_ready':False,'dalus_authorized':False,'store':'Recorded Dalus MCP','fixtures_enabled':False,'busy':False}).encode()
    entries['recorded/read-only.json']=json.dumps({'detail':'This public demo is read-only. Run OpenV locally with your own credentials to create engineering runs.'}).encode()
    manifest={name:{'sha256':hashlib.sha256(data).hexdigest(),'size':len(data)} for name,data in entries.items()}
    entries['recorded/archive-files.json']=json.dumps(manifest,sort_keys=True).encode()
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('wb') as raw, gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0) as compressed, tarfile.open(fileobj=compressed,mode='w') as tar:
        for name,data in sorted(entries.items()):
            info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o644;info.mtime=0
            tar.addfile(info,io.BytesIO(data))
    return {'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'bytes':output.stat().st_size,'file_count':len(entries),'uncompressed_bytes':sum(len(d) for d in entries.values()),'run_count':len(rows)}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True);parser.add_argument('--index',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(export(args.source,args.index,args.output),indent=2))
