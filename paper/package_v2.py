"""Package inspectable study artifacts; omit raw vendor feeds and local caches."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
files=[]
for folder in ['src','tests','research','results','paper','portfolio']:
    for p in (ROOT/folder).rglob('*'):
        if p.is_file() and not any(part.startswith('.') or part=='__pycache__' for part in p.relative_to(ROOT).parts) and p.suffix not in ['.pyc','.log']:
            files.append(p)
files += [ROOT/p for p in ['README.md','pyproject.toml','requirements-research.txt','output/pdf/value-of-information-f1-paper-v2.pdf','output/docx/value-of-information-f1-paper-v2.docx']]
files=sorted(set(files))
manifest={'version':'2.0','date':'2026-09-22','scope':'Completed local research manuscript and evidence; no public publication or acceptance claimed','omitted':'Raw and processed vendor input snapshots, caches, environments, temporary renders; see reproduction guide','files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
m=ROOT/'output/release-manifest-v2.json'; m.write_text(json.dumps(manifest,indent=2)+'\n')
out=ROOT/'output/f1-research-v2-source.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
    for p in files+[m]:z.write(p,p.relative_to(ROOT))
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None
    for n,h in manifest['files'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
print(f'{len(files)} hashed files; archive {out.stat().st_size/1e6:.1f} MB; every archived hash verified')
