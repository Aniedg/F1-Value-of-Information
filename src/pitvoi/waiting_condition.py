"""Audit the waiting condition using the existing numerical Bellman solver."""
import json
from pathlib import Path
import numpy as np
from .gaussian import LapScenario, LapSolver


def decompose(solver,t=0,p=None):
    s=solver.s;p=s.prior_high if p is None else p
    at=lambda x:float(np.interp(p,solver.grid,x))
    age=s.age+t
    future_frozen=at(solver.frozen[t+1])
    expected_frozen=at(solver.integrate(solver.frozen[t+1],age))
    expected_adaptive=at(solver.integrate(solver.adaptive[t+1],age))
    margin=at(solver.stay_frozen[t])-solver.pit_cost(s.laps-t)
    benefit=future_frozen-expected_adaptive
    return dict(margin=margin,learning_benefit=benefit,
                next_observation_benefit=future_frozen-expected_frozen,
                later_learning_benefit=expected_frozen-expected_adaptive,
                adaptive_wait_advantage=benefit-margin,
                frozen_pits=bool(solver.action(t,p,'frozen_belief')),
                adaptive_pits=bool(solver.action(t,p,'adaptive')))


def main():
    rows=[]
    for noise in [.5,1.5,4.]:
        for loss in [8,12,18,24,32,40]:
            solver=LapSolver(LapScenario(noise_sd=noise,pit_loss=loss))
            rows.append(dict(noise_sd=noise,pit_loss=loss,**decompose(solver)))
    root=Path(__file__).resolve().parents[2]
    (root/'results/waiting-condition.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps([r for r in rows if r['noise_sd']==1.5 and r['pit_loss']==18],indent=2))

if __name__=='__main__':main()
