"""Protocol-locked synthetic study for manuscript v1; no data downloads."""
from dataclasses import replace
from datetime import datetime,timezone
from itertools import product
from pathlib import Path
import hashlib,json,sys
import numpy as np
from .gaussian import LapScenario
from .replacement import Replacement,ReplacementSolver

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/'research/final-study-protocol.json'
OUTPUT=ROOT/'results/final-study.json'
SOURCES=['src/pitvoi/final_study.py','src/pitvoi/replacement.py','src/pitvoi/nuisance.py','src/pitvoi/gaussian.py']

def hashes():return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in SOURCES}

def freeze():
    d=dict(name='manuscript-v1-synthetic',locked_at=datetime.now(timezone.utc).isoformat(),
           status='Locked after exploratory experiments 01-09; not external preregistration or independent empirical validation',
           laps=[4,8,12],ages=[8,12,16],pit_losses=[12,18,24],priors=[.2,.5,.8],
           noise_sds=[.75,1.5,3],offset_sds=[0,3,6],dependence=[-.75,0,.75],
           old_rates=[.04,.30],replacement_rates=[.02,.10],grid_size=1601,quadrature=81,
           refinement=dict(grid_size=6401,quadrature=161),trials=50000,seed=20260927,
           meaningful_gain_seconds=.05,near_margin_seconds=1.,
           validation_selection='12 evenly spaced state indices including endpoints; add six largest gains not selected; add six smallest absolute adaptive wait advantages not selected; deterministic index tiebreak',
           weighting='Equal weight per enumerated initial state, not race-frequency weighting',
           source_sha256=hashes())
    with PROTOCOL.open('x') as f:json.dump(d,f,indent=2);f.write('\n')
    print('Locked',PROTOCOL)

def run():
    if OUTPUT.exists():raise FileExistsError('Refusing to overwrite final study')
    d=json.loads(PROTOCOL.read_text())
    if hashes()!=d['source_sha256']:raise ValueError('Source changed after protocol lock')
    rows=[];model_count=0
    dims=product(d['laps'],d['ages'],d['pit_losses'],d['noise_sds'],d['offset_sds'],d['dependence'])
    for n,a,loss,noise,offset,rho in dims:
        s=LapScenario(laps=n,age=a,pit_loss=loss,noise_sd=noise)
        r=Replacement(high_given_old_low=(1-rho)/2,high_given_old_high=(1+rho)/2)
        model=ReplacementSolver(s,r,offset,grid_size=d['grid_size'],quadrature=d['quadrature'])
        for p in d['priors']:
            # Prior selects the initial belief, not the all-belief Bellman arrays.
            model.s=replace(s,prior_high=p)
            report=model.report()
            rows.append(dict(index=len(rows),laps=n,age=a,pit_loss=loss,noise_sd=noise,offset_sd=offset,
                             dependence=rho,prior_high=p,**report,
                             fixed_prior_cost=float(np.interp(p,model.grid,model.frozen[0]))))
        model_count+=1
        if model_count%75==0:print('Solved',model_count,'models;',len(rows),'states',flush=True)
    selected=[int(i) for i in np.linspace(0,len(rows)-1,12,dtype=int)]
    for key in [lambda x:(-x['policy_gain'],x['index']),lambda x:(abs(x['adaptive_wait_advantage']),x['index'])]:
        candidates=[x['index'] for x in sorted(rows,key=key) if x['index'] not in selected]
        selected.extend(candidates[:6])
    validations=[]
    for index in selected:
        x=rows[index]
        s=LapScenario(laps=x['laps'],age=x['age'],pit_loss=x['pit_loss'],noise_sd=x['noise_sd'],prior_high=x['prior_high'])
        rho=x['dependence'];r=Replacement(high_given_old_low=(1-rho)/2,high_given_old_high=(1+rho)/2)
        model=ReplacementSolver(s,r,x['offset_sd'],**d['refinement'])
        validations.append(dict(index=index,refined=model.report(),rollout=model.monte_carlo(trials=d['trials'],seed=d['seed']+index)))
    result=dict(protocol_sha256=hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),protocol=d,
                completed_at=datetime.now(timezone.utc).isoformat(),states=rows,validations=validations)
    with OUTPUT.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print('Complete:',len(rows),'states and',len(validations),'refined paired validations',flush=True)

if __name__=='__main__':
    {'freeze':freeze,'run':run}[sys.argv[1]]()
