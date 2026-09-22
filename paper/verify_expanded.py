"""Check the expanded release independently of the immutable v1 protocol."""
from pathlib import Path
import json,hashlib
import fitz
ROOT=Path(__file__).resolve().parents[1]
x=json.loads((ROOT/'results/segmented-audit.json').read_text())
for name,digest in x['source_hashes'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
assert [c['index'] for c in x['cases']]==[1788,1192,993]
for c in x['cases']:
    assert [r['grid_size'] for r in c['resolutions']]==[801,1601,3201]
    fine=c['resolutions'][-1]['report'];lo,hi=c['rollout']['gain_95_ci']
    assert lo<=fine['policy_gain']<=hi
    assert fine['joint_oracle_cost']<=fine['adaptive_cost']+1e-8
    assert abs(fine['frozen_policy_cost']-fine['adaptive_cost']-fine['policy_gain'])<1e-10
assert sum(c['rollout']['trials'] for c in x['cases'])==600000
text=(ROOT/'paper/manuscript-expanded.md').read_text()
assert '__AUDIT_' not in text and '__MAX_CHANGE__' not in text
for heading in ['Appendix A.','Appendix B.','Appendix C.','## References']:
    assert heading in text
pdf=fitz.open(ROOT/'output/pdf/value-of-information-f1-paper-expanded.pdf')
for i,p in enumerate(pdf):
    for block in p.get_text('blocks'):
        assert block[0]>=0 and block[1]>=0 and block[2]<=p.rect.width+.5 and block[3]<=p.rect.height+.5,(i,block[:4])
assert len(pdf)==16
print(f'PASS: source hashes, three-case convergence records, 600,000 paired trajectories, numerical identities, manuscript completeness and {len(pdf)}-page PDF text bounds.')
