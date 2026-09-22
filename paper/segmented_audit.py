"""Post-development method check, deliberately targeting v1 discrepancies."""
import json, time, hashlib, platform
from pathlib import Path
from pitvoi.gaussian import LapScenario
from pitvoi.replacement import Replacement
from pitvoi.segmented import SegmentedSolver
ROOT=Path(__file__).resolve().parents[1]
old=json.loads((ROOT/'results/final-study-numerical-audit.json').read_text())
result={'status':'Post-development numerical diagnostic; not an independent confirmatory study',
        'method':'Analytic Gaussian integration of piecewise-affine posterior values; split deployed-policy action boundaries',
        'python':platform.python_version(), 'source_hashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['src/pitvoi/segmented.py','paper/segmented_audit.py']}, 'cases':[]}
for c in old['cases']:
    p=c['parameters'];rho=p['dependence']
    s=LapScenario(**{k:p[k] for k in ['laps','age','pit_loss','noise_sd','prior_high']})
    r=Replacement(high_given_old_low=(1-rho)/2,high_given_old_high=(1+rho)/2)
    row={'index':c['index'],'parameters':p,'v1_high_resolution':c['report'],'resolutions':[]}
    for size in [801,1601,3201]:
        start=time.perf_counter();m=SegmentedSolver(s,r,p['offset_sd'],grid_size=size)
        row['resolutions'].append({'grid_size':size,'seconds':time.perf_counter()-start,'report':m.report()})
        print(c['index'],size,m.report()['policy_gain'],flush=True)
    row['rollout']=m.monte_carlo(trials=200000,seed=20260930+c['index'])
    result['cases'].append(row)
(ROOT/'results/segmented-audit.json').write_text(json.dumps(result,indent=2)+'\n')
