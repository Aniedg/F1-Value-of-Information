"""Post-test diagnostic of the largest central model gain in each new event."""
from pathlib import Path
from dataclasses import replace
import json,hashlib
import numpy as np
from scipy.special import expit,logit
from pitvoi.historical_decisions import HistorySolver
from pitvoi.gaussian import LapScenario
from pitvoi.replacement import Replacement
ROOT=Path(__file__).resolve().parents[1]
x=json.loads((ROOT/'results/historical-decisions.json').read_text());d=x['protocol'];out=[]
for j,e in enumerate(x['events']):
 v=next(v for v in e['variants'] if v['nuisance_improvement']==.05 and v['pit_loss']==24)
 state=max(v['decisions'],key=lambda s:s['policy_gain'])
 s=LapScenario(laps=state['laps'],age=state['age'],low=d['low'],high=d['high'],noise_sd=d['noise_sd'],pit_loss=24,prior_high=state['prior_high'])
 m=HistorySolver(s,Replacement(low=.06,high=.06),state['history_count'],state['history_sum_age'],1601)
 N=100000;seed=20261003+j;rng=np.random.default_rng(seed)
 old=np.where(rng.random(N)<s.prior_high,s.high,s.low)
 baseline=-state['history_sum_age']/state['history_count']*old+rng.normal(0,s.noise_sd/np.sqrt(state['history_count']),N)
 noise=rng.normal(0,s.noise_sd,(N,s.laps));costs={}
 for policy in ['adaptive','frozen_belief']:
  odds=np.full(N,logit(s.prior_high));sum_y=np.zeros(N);active=np.ones(N,dtype=bool);cost=np.zeros(N)
  for t in range(s.laps):
   p=expit(odds);pit=active&m.action(t,p,policy);n=s.laps-t
   cost[pit]+=s.pit_loss+.06*n*(n-1)/2;active[pit]=False
   age=s.age+t;cost[active]+=age*old[active]
   k=state['history_count']+t;sum_age=state['history_sum_age']+t*s.age+t*(t-1)/2
   y=baseline[active]+age*old[active]+noise[active,t]
   means=[sum_y[active]/k+(age-sum_age/k)*theta for theta in [s.low,s.high]]
   var=s.noise_sd**2*(1+1/k)
   odds[active]+=((y-means[0])**2-(y-means[1])**2)/(2*var);sum_y[active]+=y
  costs[policy]=cost
 delta=costs['frozen_belief']-costs['adaptive'];gain=float(delta.mean());se=float(delta.std(ddof=1)/np.sqrt(N))
 out.append(dict(event=e['event'],state=state,refined=m.report(),trials=N,seed=seed,gain=gain,se=se,ci=[gain-1.96*se,gain+1.96*se]))
 print(e['event'],state['driver'],state['lap'],m.report()['policy_gain'],gain,[gain-1.96*se,gain+1.96*se],flush=True)
with (ROOT/'results/history-policy-audit.json').open('x') as f:json.dump(dict(status='Post-test largest-gain numerical check, conditional synthetic rewards only',source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),cases=out),f,indent=2)
