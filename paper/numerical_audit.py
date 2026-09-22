"""Post-run follow-up of the three largest refinement discrepancies."""
from pathlib import Path
import json
from pitvoi.gaussian import LapScenario
from pitvoi.replacement import Replacement,ReplacementSolver
root=Path(__file__).resolve().parents[1]
d=json.loads((root/'results/final-study.json').read_text());out=[]
chosen=sorted(d['validations'],key=lambda v:abs(v['refined']['policy_gain']-d['states'][v['index']]['policy_gain']),reverse=True)[:3]
for v in chosen:
 x=d['states'][v['index']];s=LapScenario(laps=x['laps'],age=x['age'],pit_loss=x['pit_loss'],noise_sd=x['noise_sd'],prior_high=x['prior_high']);rho=x['dependence']
 r=Replacement(high_given_old_low=(1-rho)/2,high_given_old_high=(1+rho)/2)
 model=ReplacementSolver(s,r,x['offset_sd'],grid_size=12801,quadrature=321)
 entry=dict(index=x['index'],parameters={k:x[k] for k in ['laps','age','pit_loss','noise_sd','prior_high','offset_sd','dependence']},report=model.report(),previous=v['refined'],grid_size=12801,quadrature=321)
 if x['index']==chosen[0]['index']:entry['rollout']=model.monte_carlo(trials=200000,seed=20260929)
 out.append(entry);print(entry,flush=True)
(root/'results/final-study-numerical-audit.json').write_text(json.dumps(dict(status='Post-run diagnostic, not a change to the locked grid',cases=out),indent=2)+'\n')
