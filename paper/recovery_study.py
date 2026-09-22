"""Synthetic identification stress: frozen assumptions, not empirical tyre truth."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
import numpy as np
from scipy.special import expit
ROOT=Path(__file__).resolve().parents[1]
protocol=dict(status='Synthetic model and misspecification checks, fixed before executing this script',seed=20261002,trials=20000,observations=[4,8,16,24],rates=[.04,.30],assumed_noise=1.2,scenarios=[{'name':'matched','unmodelled_drift':0.,'outlier_probability':0.},{'name':'drift_0.05','unmodelled_drift':.05,'outlier_probability':0.},{'name':'drift_0.15','unmodelled_drift':.15,'outlier_probability':0.},{'name':'traffic_contamination','unmodelled_drift':0.,'outlier_probability':.10}],outlier_seconds=6.,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
path=ROOT/'research/recovery-protocol.json'
with path.open('x') as f:json.dump(protocol,f,indent=2)
rng=np.random.default_rng(protocol['seed']);N=protocol['trials'];high=rng.random(N)<.5;theta=np.where(high,.30,.04);noise=rng.normal(0,1.2,(N,24));outlier=rng.random((N,24))<.10;rows=[]
for scenario in protocol['scenarios']:
 sum_y=np.zeros(N);sum_age=0.;logodds=np.zeros(N)
 for i in range(24):
  age=i+1;y=90+age*(theta+scenario['unmodelled_drift'])+noise[:,i]
  if scenario['outlier_probability']:y=y+6*outlier[:,i]
  if i:
   mlow=sum_y/i+(age-sum_age/i)*.04;mhigh=sum_y/i+(age-sum_age/i)*.30
   sd=1.2*np.sqrt(1+1/i);logodds+=((y-mlow)**2-(y-mhigh)**2)/(2*sd**2)
  sum_y+=y;sum_age+=age;p=expit(logodds)
  if i+1 in protocol['observations']:
   bins=[]
   for left,right in zip(np.linspace(0,.9,10),np.linspace(.1,1,10)):
    mask=(p>=left)&((p<right) if right<1 else (p<=right))
    if mask.any():bins.append(dict(count=int(mask.sum()),predicted=float(p[mask].mean()),observed=float(high[mask].mean())))
   rows.append(dict(scenario=scenario['name'],observations=i+1,accuracy=float(np.mean((p>=.5)==high)),brier=float(np.mean((p-high)**2)),confidently_wrong=float(np.mean(((p>.95)&~high)|((p<.05)&high))),calibration_bins=bins))
with (ROOT/'results/recovery-study.json').open('x') as f:json.dump(dict(protocol=protocol,results=rows,completed_at=datetime.now(timezone.utc).isoformat()),f,indent=2)
print(json.dumps([{k:v for k,v in r.items() if k!='calibration_bins'} for r in rows if r['observations']==24],indent=2))
