"""Post-run check of the largest change between the two full-grid methods."""
from pathlib import Path
import json,hashlib
from pitvoi.gaussian import LapScenario
from pitvoi.replacement import Replacement
from pitvoi.segmented import SegmentedSolver
ROOT=Path(__file__).resolve().parents[1]
a=json.loads((ROOT/'results/final-study.json').read_text())['states'];b=json.loads((ROOT/'results/segmented-study.json').read_text())['states']
idx=max(range(len(a)),key=lambda i:abs(a[i]['policy_gain']-b[i]['policy_gain']));x=b[idx]
s=LapScenario(laps=x['laps'],age=x['age'],pit_loss=x['pit_loss'],noise_sd=x['noise_sd'],prior_high=x['prior_high']);rho=x['dependence'];r=Replacement(high_given_old_low=(1-rho)/2,high_given_old_high=(1+rho)/2)
m=SegmentedSolver(s,r,x['offset_sd'],3201)
out=dict(status='Post-run diagnostic chosen for largest full-grid version difference',index=idx,old=a[idx],new=x,refined=m.report(),rollout=m.monte_carlo(trials=200000,seed=20261004),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
with (ROOT/'results/global-change-audit.json').open('x') as f:json.dump(out,f,indent=2)
print(idx,x['policy_gain'],m.report()['policy_gain'],out['rollout']['gain_95_ci'])
