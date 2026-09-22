"""Controlled synthetic decomposition; no historical fitting or strategy claims."""
from dataclasses import asdict
import json
from pathlib import Path
import numpy as np
from scipy.special import expit
from .gaussian import LapScenario, LapSolver


def regime_posterior(observations, ages, low, high, noise_sd, offset_sd=0):
    """Marginalize one persistent Gaussian pace offset, shared by all laps.

    Equal regime prior. Sherman–Morrison inverse of sigma² I + tau² 11'.
    Last axis indexes observations. Offset is independent of the regime.
    """
    y=np.asarray(observations); a=np.asarray(ages)
    if y.shape[-1] != len(a) or noise_sd <= 0 or offset_sd < 0:
        raise ValueError('invalid observation model')
    centered=y-a*(low+high)/2
    variance=noise_sd**2
    cross=(centered*a).sum(axis=-1)/variance
    cross-=offset_sd**2*a.sum()*centered.sum(axis=-1)/(variance*(variance+len(a)*offset_sd**2))
    return expit((high-low)*cross)


def recovery(s, offset_sd, trials=20000, seed=20260924):
    rng=np.random.default_rng(seed)
    truth=rng.random(trials)<.5
    theta=np.where(truth,s.high,s.low)
    offset=rng.normal(0,offset_sd,trials)
    ages=s.age+np.arange(s.laps)
    y=theta[:,None]*ages+offset[:,None]+rng.normal(0,s.noise_sd,(trials,s.laps))
    rows=[]
    for n in range(1,s.laps+1):
        p=regime_posterior(y[:,:n],ages[:n],s.low,s.high,s.noise_sd,offset_sd)
        naive=regime_posterior(y[:,:n],ages[:n],s.low,s.high,s.noise_sd)
        rows.append(dict(observations=n,brier=float(np.mean((p-truth)**2)),
                         posterior_theta_variance=float(np.mean(p*(1-p)*(s.high-s.low)**2)),
                         accuracy=float(np.mean((p>=.5)==truth)),
                         ignored_offset_brier=float(np.mean((naive-truth)**2))))
    return dict(offset_sd=offset_sd,trials=trials,seed=seed,by_lap=rows)


def main():
    root=Path(__file__).resolve().parents[2]
    variance=(12*.13)**2+1.5**2
    cases=[]
    for spread in [.02,.08,.13]:
        s=LapScenario(low=.17-spread,high=.17+spread,noise_sd=float(np.sqrt(variance-(12*spread)**2)))
        solver=LapSolver(s)
        refined=LapSolver(s,grid_size=3201,quadrature=81)
        sweep=[]
        for loss in [8,12,18,24,32,40]:
            scenario=LapScenario(**{**asdict(s),'pit_loss':loss})
            sweep.append(dict(pit_loss=loss,**LapSolver(scenario).report()))
        cases.append(dict(scenario=asdict(s),learnable_variance=(12*spread)**2,
                          noise_variance=s.noise_sd**2,total_variance=variance,
                          report=solver.report(),refined_report=refined.report(),
                          rollout=solver.monte_carlo(trials=30000),sweep=sweep,
                          recovery=[recovery(s,sd) for sd in [0,6]]))
    d=dict(version=7,label='Synthetic mechanism study; illustrative parameters',cases=cases,
           design='Same initial predictive mean and variance, different variance decomposition. Full predictive distributions differ.',
           caveat='Decision solver assumes known baseline. Offset recovery is a separate diagnostic, not a nuisance-aware policy evaluation.')
    (root/'results/information-experiment.json').write_text(json.dumps(d,indent=2)+'\n')
    print(json.dumps([{ 'spread':(c['scenario']['high']-c['scenario']['low'])/2,'gain':c['report']['policy_gain'],'refinement':c['refined_report']['policy_gain']-c['report']['policy_gain'],'recovery':[r['by_lap'][-1] for r in c['recovery']]} for c in cases],indent=2))

if __name__=='__main__':main()
