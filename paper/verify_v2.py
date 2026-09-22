"""Verify archived version-2 evidence without requiring external timing feeds."""
from pathlib import Path
import hashlib, json, re, zipfile
from xml.etree import ElementTree as ET
from statistics import mean
from datetime import datetime
import fitz
ROOT=Path(__file__).resolve().parents[1]
def read(p): return json.loads((ROOT/p).read_text())
def digest(p): return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def hashes(d):
    for p,h in d.items(): assert digest(p)==h,p
def close(a,b): assert abs(a-b)<1e-8,(a,b)
s=read('results/segmented-study.json'); p=read('research/segmented-study-protocol.json')
assert s['protocol']==p and s['protocol_sha256']==digest('research/segmented-study-protocol.json'); hashes(p['source_sha256'])
rows=s['states']; assert len(rows)==2187 and len({r['index'] for r in rows})==2187
assert sum(r['adaptive_action']!=r['frozen_action'] for r in rows)==319
assert sum(r['policy_gain']>.05 for r in rows)==474
close(mean(r['policy_gain'] for r in rows),.37654348833161483)
for r in rows:
    close(r['frozen_policy_cost']-r['adaptive_cost'],r['policy_gain'])
    assert r['joint_oracle_cost']<=r['adaptive_cost']+1e-7
    assert r['adaptive_cost']<=r['frozen_policy_cost']+1e-7
    assert r['frozen_policy_cost']<=r['fixed_prior_cost']+1e-7
assert [v['index'] for v in s['validations']]==p['validation_indices']
assert sum(v['rollout']['trials'] for v in s['validations'])==1200000
for v in s['validations']:
    lo,hi=v['rollout']['gain_95_ci']; assert lo-1e-9<=v['refined']['policy_gain']<=hi+1e-9
    for a in ['adaptive_action','frozen_action']: assert rows[v['index']][a]==v['refined'][a]
h=read('results/historical-decisions.json'); hp=read('research/historical-decisions-frozen.json')
assert h['protocol']==hp and h['protocol_sha256']==digest('research/historical-decisions-frozen.json'); hashes(hp['source_sha256'])
hashes(read('research/replay-ingestion-amendment.json')['files'])
assert len(hp['development_sha256'])==11
assert min(hp['candidates'],key=lambda x:x['equal_event_nll'])['noise_sd']==hp['noise_sd']==1.2
counts=[]; changes=[]; forecasts=[]
for e,round_no,title in zip(h['events'],[12,13,14],['British Grand Prix','Hungarian Grand Prix','Belgian Grand Prix']):
    m=read(f"results/2024-{e['event']}-manifest.json")
    assert m['resolved_round']==round_no and m['resolved_event']==title
    assert m['processed_sha256']==e['input_sha256'] and m['retrieved_utc']==e['manifest_retrieved']
    assert datetime.fromisoformat(m['retrieved_utc'])>datetime.fromisoformat(hp['frozen_at'])
    c=next(v for v in e['variants'] if v['nuisance_improvement']==.05 and v['pit_loss']==24)
    d=c['decisions']; predictions=e['predictions']; metrics=c['forecast_metrics']
    assert len(e['variants'])==9 and len(predictions)==metrics['count']
    close(mean(abs(x['observed']-x['prediction']) for x in predictions),metrics['mae'])
    close(mean(abs(x['observed']-x['last_observation']) for x in predictions),metrics['last_observation_mae'])
    close(mean(x['lower']<=x['observed']<=x['upper'] for x in predictions),metrics['coverage90'])
    assert metrics['mae']>metrics['last_observation_mae']
    counts.append(len(d)); forecasts.append(len(predictions)); changes.append(sum(x['adaptive_action']!=x['frozen_action'] for x in d))
    assert len(e['refinements'])==12
    for r,x in zip(e['refinements'],d[:12]):
        assert (r['driver'],r['lap'])==(x['driver'],x['lap'])
        for a in ['adaptive_action','frozen_action']: assert r['report'][a]==x[a]
        assert abs(r['report']['policy_gain']-x['policy_gain'])<.000025
assert counts==[134,199,193] and forecasts==[542,1056,575] and changes==[0,10,1]
a=read('results/history-policy-audit.json'); assert digest('paper/history_policy_audit.py')==a['source_sha256']
assert sum(c['trials'] for c in a['cases'])==300000
for c in a['cases']: assert c['ci'][0]<=c['refined']['policy_gain']<=c['ci'][1]
a=read('results/global-change-audit.json'); assert digest('paper/global_change_audit.py')==a['source_sha256']
assert a['rollout']['gain_95_ci'][0]<=a['refined']['policy_gain']<=a['rollout']['gain_95_ci'][1]
r=read('results/recovery-study.json'); rp=read('research/recovery-protocol.json')
assert r['protocol']==rp and digest('paper/recovery_study.py')==rp['source_sha256']
assert len(r['results'])==16 and rp['trials']==20000
for x in r['results']: assert sum(b['count'] for b in x['calibration_bins'])==20000
text=(ROOT/'paper/manuscript-v2.md').read_text()
abstract=text.split('## Abstract')[1].split('**Keywords')[0].strip()
assert len(abstract.split())==200,len(abstract.split())
assert not re.search(r'__[A-Z][A-Z_]+__',text)
for heading in ['Appendix A','Appendix B','Appendix C','## References']: assert heading in text
pdf=fitz.open(ROOT/'output/pdf/value-of-information-f1-paper-v2.pdf'); assert len(pdf)==19
for i,page in enumerate(pdf):
    for b in page.get_text('blocks'): assert b[0]>=0 and b[1]>=0 and b[2]<=page.rect.width+.5 and b[3]<=page.rect.height+.5,(i,b[:4])
with zipfile.ZipFile(ROOT/'output/docx/value-of-information-f1-paper-v2.docx') as z:
    xml=z.read('word/document.xml').decode(); assert xml.count('<w:tbl>')==5
    assert not ET.fromstring(z.read('docProps/core.xml')).find('{http://purl.org/dc/elements/1.1/}creator').text
manifest=ROOT/'output/release-manifest-v2.json'
if manifest.exists(): hashes(json.loads(manifest.read_text())['files'])
print('PASS: frozen source/protocol hashes; 2,187 states; 24 simulation checks; 2,173 historical forecasts; 526 decisions; recovery and audit records; 200-word abstract; 19-page PDF bounds; five editable Word tables; release hashes when present.')
