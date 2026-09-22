"""Development study of common-baseline nuisance uncertainty; not final test."""
from dataclasses import asdict
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from .gaussian import LapScenario
from .nuisance import OffsetSolver
from .waiting_condition import decompose


def main():
    root=Path(__file__).resolve().parents[2];s=LapScenario();rows=[]
    for offset in [0,1.5,3,6]:
        solver=OffsetSolver(s,offset)
        refined=OffsetSolver(s,offset,grid_size=3201,quadrature=81)
        fine=OffsetSolver(s,offset,grid_size=6401,quadrature=161)
        row=dict(offset_sd=offset,report=solver.report(),refined_report=refined.report(),fine_report=fine.report(),
                 decomposition=decompose(fine),rollout=fine.monte_carlo(),
                 observation_parameters=[dict(observed_laps=t,effective_age=solver.observation_parameters(t)[1],
                                         conditional_noise_sd=solver.observation_parameters(t)[2]) for t in range(s.laps)])
        row['sweep']=[]
        for loss in [8,12,18,24,32,40]:
            model=OffsetSolver(LapScenario(pit_loss=loss),offset)
            row['sweep'].append(dict(pit_loss=loss,**model.report(),**decompose(model)))
        rows.append(row)
    stress=[]
    for assumed in [0,1.5,6]:
        model=OffsetSolver(s,assumed,grid_size=3201,quadrature=81)
        stress.append(model.monte_carlo(actual_offset_sd=6))
    paths=['src/pitvoi/nuisance.py','src/pitvoi/nuisance_experiment.py','src/pitvoi/gaussian.py','src/pitvoi/waiting_condition.py']
    result=dict(version=8,created_at=datetime.now(timezone.utc).isoformat(),scenario=asdict(s),
                status='Synthetic development study; illustrative common static baseline; no historical strategy claim',
                grid_size=1601,quadrature=41,refined_grid_size=3201,refined_quadrature=81,fine_grid_size=6401,fine_quadrature=161,
                cases=rows,misspecification_actual_offset_sd=6,stress=stress,
                source_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths})
    (root/'results/nuisance-experiment.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps([dict(offset=r['offset_sd'],gain=r['report']['policy_gain'],refined_gain=r['refined_report']['policy_gain'],rollout=r['rollout']['gain_95_ci'],action=r['report']['adaptive_action']) for r in rows],indent=2))
    print('Stress:',json.dumps(stress,indent=2))

if __name__=='__main__':main()
