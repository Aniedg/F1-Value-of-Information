"""Verify manuscript evidence integrity and final-PDF basic layout bounds."""
import hashlib,json,math
from pathlib import Path
import fitz
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'results/final-study.json').read_text());protocol=ROOT/'research/final-study-protocol.json'
assert hashlib.sha256(protocol.read_bytes()).hexdigest()==d['protocol_sha256']
for name,h in d['protocol']['source_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
rows=d['states'];assert len(rows)==2187
keys=['laps','age','pit_loss','noise_sd','offset_sd','dependence','prior_high']
assert len({tuple(x[k] for k in keys) for x in rows})==2187
for x in rows:
 assert math.isclose(x['policy_gain'],x['frozen_policy_cost']-x['adaptive_cost'],abs_tol=1e-10)
 assert math.isclose(x['adaptive_wait_advantage'],x['continuation_learning_benefit']-x['waiting_margin'],abs_tol=1e-10)
 assert x['adaptive_cost']>=x['joint_oracle_cost']-.01
 assert x['policy_gain']>=-.01
 if x['adaptive_action']!=x['frozen_action']:assert (x['adaptive_action'],x['frozen_action'])==('stay','pit')
assert len(d['validations'])==24
assert sum(v['rollout']['trials'] for v in d['validations'])==1200000
assert sum(x['adaptive_action']!=x['frozen_action'] for x in rows)==319
assert sum(x['policy_gain']>.05 for x in rows)==463
text=(ROOT/'paper/manuscript.md').read_text()
assert '__' not in text and 'TODO' not in text
assert len(text.split())>4500
pdf=fitz.open(ROOT/'output/pdf/value-of-information-f1-paper.pdf')
issues=[]
for i,page in enumerate(pdf):
 content=page.get_text()
 assert '\ufffd' not in content and '\u25a0' not in content,(i,'missing glyph')
 assert len(content.split())>50,(i,'empty page')
 for word in page.get_text('words'):
  x0,y0,x1,y1,*_=word
  if x0<40 or x1>page.rect.width-40 or y0<15 or y1>page.rect.height-15:issues.append((i+1,word))
assert not issues,issues[:5]
print('PASS: source/protocol hashes; 2,187 unique states; identities and oracle bounds; 24 paired validations; manuscript completeness; PDF text bounds.')
print('PDF pages:',len(pdf),'Manuscript words:',len(text.split()))
