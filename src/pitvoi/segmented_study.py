"""Full numerical replacement study, versioned separately from manuscript v1."""
from dataclasses import replace
from datetime import datetime,timezone
from itertools import product
from pathlib import Path
import hashlib,json,sys,time
import numpy as np
from .gaussian import LapScenario
from .replacement import Replacement
from .segmented import SegmentedSolver
ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/'research/segmented-study-protocol.json'
OUTPUT=ROOT/'results/segmented-study.json'
SOURCES=['src/pitvoi/segmented_study.py','src/pitvoi/segmented.py','src/pitvoi/replacement.py','src/pitvoi/nuisance.py','src/pitvoi/gaussian.py']
def hashes():return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in SOURCES}
def freeze():
 d=json.loads((ROOT/'research/final-study-protocol.json').read_text())
 d.update(name='full-grid-analytic-segments-v2',locked_at=datetime.now(timezone.utc).isoformat(),status='Post-development numerical replacement study; synthetic, not empirical confirmation',source_sha256=hashes(),grid_size=1601,refinement={'grid_size':3201},seed=20261001)
 d.pop('quadrature',None)
 d['validation_indices']=[v['index'] for v in json.loads((ROOT/'results/final-study.json').read_text())['validations']]
 d['validation_selection']='Same 24 state indices as v1, fixed before new integration results'
 with PROTOCOL.open('x') as f:json.dump(d,f,indent=2)
def run():
 if OUTPUT.exists():raise FileExistsError(OUTPUT)
 d=json.loads(PROTOCOL.read_text());assert hashes()==d['source_sha256'];rows=[];start=time.perf_counter()
 for j,(n,a,loss,noise,offset,rho) in enumerate(product(d['laps'],d['ages'],d['pit_losses'],d['noise_sds'],d['offset_sds'],d['dependence'])):
  s=LapScenario(laps=n,age=a,pit_loss=loss,noise_sd=noise);r=Replacement(high_given_old_low=(1-rho)/2,high_given_old_high=(1+rho)/2)
  m=SegmentedSolver(s,r,offset,grid_size=d['grid_size'])
  for p in d['priors']:
   m.s=replace(s,prior_high=p)
   rows.append(dict(index=len(rows),laps=n,age=a,pit_loss=loss,noise_sd=noise,offset_sd=offset,dependence=rho,prior_high=p,**m.report(),fixed_prior_cost=float(np.interp(p,m.grid,m.frozen[0]))))
  if (j+1)%25==0:print('Models',j+1,'states',len(rows),'seconds',round(time.perf_counter()-start),flush=True)
 validations=[]
 for index in d['validation_indices']:
  x=rows[index];s=LapScenario(laps=x['laps'],age=x['age'],pit_loss=x['pit_loss'],noise_sd=x['noise_sd'],prior_high=x['prior_high']);rho=x['dependence'];r=Replacement(high_given_old_low=(1-rho)/2,high_given_old_high=(1+rho)/2)
  m=SegmentedSolver(s,r,x['offset_sd'],**d['refinement'])
  validations.append(dict(index=index,refined=m.report(),rollout=m.monte_carlo(trials=d['trials'],seed=d['seed']+index)))
 result=dict(protocol=d,protocol_sha256=hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),states=rows,validations=validations,completed_at=datetime.now(timezone.utc).isoformat(),seconds=time.perf_counter()-start)
 with OUTPUT.open('x') as f:json.dump(result,f,indent=2)
 print('Complete',len(rows),flush=True)
if __name__=='__main__':{'freeze':freeze,'run':run}[sys.argv[1]]()
