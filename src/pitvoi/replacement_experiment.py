"""Matched-prior-mean replacement uncertainty development experiment."""
from dataclasses import asdict
from datetime import datetime,timezone
import hashlib,json
from pathlib import Path
from .gaussian import LapScenario
from .replacement import Replacement,ReplacementSolver

CASES={
    'known':Replacement(low=.06,high=.06),
    'independent':Replacement(),
    'positive':Replacement(high_given_old_low=.125,high_given_old_high=.875),
    'negative':Replacement(high_given_old_low=.875,high_given_old_high=.125),
}


def main():
    root=Path(__file__).resolve().parents[2];s=LapScenario();rows=[]
    for offset in [0,3,6]:
        for name,replacement in CASES.items():
            coarse=ReplacementSolver(s,replacement,offset)
            fine=ReplacementSolver(s,replacement,offset,grid_size=3201,quadrature=81)
            row=dict(name=name,offset_sd=offset,replacement=asdict(replacement),report=fine.report(),
                     coarse_report=coarse.report(),rollout=fine.monte_carlo())
            if offset==3 or (offset==6 and name in ('positive','negative')):
                dense=ReplacementSolver(s,replacement,offset,grid_size=6401,quadrature=161)
                row['dense_report']=dense.report()
            rows.append(row)
    stress=[]
    for name in ['independent','positive','negative']:
        model=ReplacementSolver(s,CASES[name],3,grid_size=3201,quadrature=81)
        stress.append(dict(assumed=name,actual='positive',**model.monte_carlo(actual_replacement=CASES['positive'])))
    paths=['src/pitvoi/replacement.py','src/pitvoi/replacement_experiment.py','src/pitvoi/nuisance.py','src/pitvoi/gaussian.py']
    d=dict(version=9,created_at=datetime.now(timezone.utc).isoformat(),scenario=asdict(s),cases=rows,stress=stress,
           status='Illustrative synthetic development study; no historical strategy claim',
           grid_size=3201,quadrature=81,source_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths})
    (root/'results/replacement-experiment.json').write_text(json.dumps(d,indent=2)+'\n')
    print(json.dumps([dict(case=r['name'],offset=r['offset_sd'],gain=r['report']['policy_gain'],action=r['report']['adaptive_action'],mc=r['rollout']['gain'],ci=r['rollout']['gain_95_ci'],joint_oracle=r['report']['joint_oracle_cost']) for r in rows],indent=2))

if __name__=='__main__':main()
