"""Prospectively frozen conditional historical replay, not causal policy evaluation.

Observation: lap_seconds + g*race_lap = intercept + age*theta + noise.
The common intercept has a diffuse prior. One first observation initializes its
conditional distribution but supplies no slope evidence. Conditional Gaussian
updates and the binary regime posterior are then exact under this model.
"""
from pathlib import Path
from dataclasses import replace
from functools import lru_cache
from datetime import datetime,timezone
import json,hashlib,sys
import numpy as np
import pandas as pd
from scipy.special import expit,logsumexp,ndtr
from scipy.optimize import brentq
from .gaussian import LapScenario
from .replacement import Replacement
from .segmented import SegmentedSolver
ROOT=Path(__file__).resolve().parents[2]
FROZEN=ROOT/'research/historical-decisions-frozen.json'
OUTPUT=ROOT/'results/historical-decisions.json'
SOURCES=['src/pitvoi/historical_decisions.py','src/pitvoi/segmented.py','src/pitvoi/replacement.py','src/pitvoi/nuisance.py','src/pitvoi/gaussian.py','src/pitvoi/historical.py']
EVENTS={'great-britain':52,'hungary':70,'belgium':44}
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

class RegimeFilter:
 def __init__(self,low,high,noise,p=.5):
  self.rates=np.array([low,high]);self.noise=noise;self.log_odds=float(np.log(p/(1-p)))
  self.count=0;self.sum_age=0.;self.sum_y=0.
 @property
 def p(self):return float(expit(self.log_odds))
 def predict(self,age):
  if self.count==0:raise ValueError('first observation must initialize baseline')
  means=self.sum_y/self.count+(age-self.sum_age/self.count)*self.rates
  sd=self.noise*np.sqrt(1+1/self.count)
  return means,float(sd)
 def update(self,age,y):
  if self.count:
   means,sd=self.predict(age)
   ll=-(y-means)**2/(2*sd**2)
   self.log_odds+=float(ll[1]-ll[0])
  self.count+=1;self.sum_age+=float(age);self.sum_y+=float(y)
 def quantiles(self,age):
  means,sd=self.predict(age)
  def cdf(y):return (1-self.p)*ndtr((y-means[0])/sd)+self.p*ndtr((y-means[1])/sd)
  return [brentq(lambda y:cdf(y)-q,means.min()-12*sd,means.max()+12*sd) for q in [.05,.95]]

class HistorySolver(SegmentedSolver):
 def __init__(self,s,replacement,count,sum_age,grid_size=401):
  if count<1:raise ValueError('observed history required')
  self.history_count=count;self.history_sum_age=sum_age
  super().__init__(s,replacement,offset_sd=0,grid_size=grid_size)
 def observation_parameters(self,t):
  count=self.history_count+t
  previous=self.history_sum_age+t*self.s.age+t*(t-1)/2
  age=self.s.age+t
  return 1/count,age-previous/count,self.s.noise_sd*np.sqrt(1+1/count)


def forecasts(frame,low,high,noise,g,decisions=False,race_laps=0):
 """Only prior completed rows enter each forecast; decisions follow update.

 Decision states are end-of-lap states, so forecast y_t is scored before
 update, and the decision after lap t legitimately includes that observation.
 """
 output=[];states=[]
 for driver,group in frame.groupby('Driver',sort=True):
  filters={};compounds=set();last={}
  for row in group.sort_values('lap_end_session_seconds').itertuples():
   if row.Compound in ['SOFT','MEDIUM','HARD']:compounds.add(row.Compound)
   if not row.eligible:continue
   stint=int(row.Stint);age=float(row.tyre_age_start);lap=int(row.LapNumber)
   if stint not in filters:filters[stint]=RegimeFilter(low,high,noise)
   f=filters[stint];y=float(row.lap_seconds)+g*lap
   if f.count>=3:
    means,sd=f.predict(age);weights=np.array([1-f.p,f.p]);mean=float(weights@means)
    ll=-.5*((y-means)/sd)**2-np.log(sd*np.sqrt(2*np.pi))
    nll=float(-logsumexp(np.log(np.maximum(weights,1e-300))+ll))
    lo,hi=f.quantiles(age)
    output.append(dict(driver=driver,stint=stint,lap=lap,age=age,observed=float(row.lap_seconds),prediction=mean-g*lap,lower=lo-g*lap,upper=hi-g*lap,nll=nll,prior_high=f.p,last_observation=last[stint]))
   f.update(age,y);last[stint]=float(row.lap_seconds)
   # Only previously observed dry compounds establish the restricted legal scope.
   n=race_laps-lap
   if decisions and 1<=n<=12 and f.count>=3 and len(compounds)>=2:
    states.append(dict(driver=driver,stint=stint,lap=lap,time=float(row.lap_end_session_seconds),laps=n,age=int(age+1),prior_high=f.p,history_count=f.count,history_sum_age=f.sum_age,observed_compounds=sorted(compounds)))
 return output,states


def metrics(rows):
 if not rows:return {'count':0}
 y=np.array([r['observed'] for r in rows]);p=np.array([r['prediction'] for r in rows]);lo=np.array([r['lower'] for r in rows]);hi=np.array([r['upper'] for r in rows])
 return dict(count=len(rows),mae=float(np.mean(abs(y-p))),rmse=float(np.sqrt(np.mean((y-p)**2))),nll=float(np.mean([r['nll'] for r in rows])),coverage90=float(np.mean((y>=lo)&(y<=hi))),width=float(np.mean(hi-lo)),interval_score=float(np.mean(hi-lo+20*np.maximum(lo-y,0)+20*np.maximum(y-hi,0))),last_observation_mae=float(np.mean(abs(y-np.array([r['last_observation'] for r in rows])))))


def freeze():
 if FROZEN.exists():raise FileExistsError(FROZEN)
 for name in EVENTS:
  if (ROOT/f'data/processed/2024-{name}-audited.csv').exists():raise ValueError('test data already present')
 paths=sorted((ROOT/'data/processed').glob('*-audited.csv'))
 assert len(paths)==11
 # Fixed illustrative rate support isolates the inference/decision bridge.
 # Fit only observation noise; fuel/track improvement is an assumption.
 low,high,g=.04,.30,.05
 candidates=[]
 for noise in [.3,.6,1.2,2.4]:
  by_event=[]
  for path in paths:
   rows,_=forecasts(pd.read_csv(path),low,high,noise,g)
   by_event.append(dict(event=path.stem,**metrics(rows)))
  candidates.append(dict(noise_sd=noise,equal_event_nll=float(np.mean([x['nll'] for x in by_event])),events=by_event))
 selected=min(candidates,key=lambda x:x['equal_event_nll'])
 d=dict(name='conditional-historical-decision-replay-v1',frozen_at=datetime.now(timezone.utc).isoformat(),status='New events reserved before ingestion; retrospective feed, conditional model, no causal reward',events=EVENTS,low=low,high=high,prior_high=.5,noise_sd=selected['noise_sd'],nuisance_improvement=.05,nuisance_sensitivity=[0,.05,.10],pit_loss=24.,pit_loss_sensitivity=[18.,24.,30.],fresh_degradation=.06,grid_size=401,refinement_grid_size=1601,refinement_selection='first 12 central states in each event ordered by driver and lap',warmup=3,candidates=candidates,development_sha256={str(p.relative_to(ROOT)):digest(p) for p in paths},source_sha256={p:digest(ROOT/p) for p in SOURCES},limitations=['Fixed two-point tyre support is assumed, not physically identified','Fuel and track improvement is a declared sensitivity, not telemetry-estimated','Retrospective quality flags are not guaranteed available live','End-of-lap decision abstraction omits physical pit-entry commitment timing','Fresh same-baseline equivalent replacement, no measured compound offset, inventory or warm-up','Late-race optional-stop scope after two observed dry compounds; no wet-weather strategy','No counterfactual actual race reward or pit-lap imitation score'])
 with FROZEN.open('x') as f:json.dump(d,f,indent=2)
 for name in EVENTS:
  selection=dict(year=2024,event=name.replace('-',' ').title(),session='R',purpose='Held-out conditional replay after eleven development events',selected_before_download=True)
  with (ROOT/f'research/selection-replay-{name}.json').open('x') as f:json.dump(selection,f,indent=2)
 print('Frozen noise',d['noise_sd'],'on 11 development events',flush=True)


def evaluate():
 if OUTPUT.exists():raise FileExistsError(OUTPUT)
 d=json.loads(FROZEN.read_text())
 assert all(digest(ROOT/p)==h for p,h in d['source_sha256'].items())
 assert all(digest(ROOT/p)==h for p,h in d['development_sha256'].items())
 @lru_cache(maxsize=256)
 def solver(n,age,count,sumage,loss,size):
  s=LapScenario(laps=n,age=age,low=d['low'],high=d['high'],noise_sd=d['noise_sd'],pit_loss=loss)
  return HistorySolver(s,Replacement(low=d['fresh_degradation'],high=d['fresh_degradation']),count,sumage,size)
 results=[]
 for name,total in d['events'].items():
  path=ROOT/f'data/processed/2024-{name}-audited.csv';frame=pd.read_csv(path)
  manifest=json.loads((ROOT/f'results/2024-{name}-manifest.json').read_text())
  assert manifest['processed_sha256']==digest(path)
  assert manifest['retrieved_utc']>d['frozen_at']
  result=dict(event=name,planned_laps=total,input_sha256=digest(path),manifest_retrieved=manifest['retrieved_utc'],variants=[],refinements=[])
  for g in d['nuisance_sensitivity']:
   preds,states=forecasts(frame,d['low'],d['high'],d['noise_sd'],g,True,total)
   for loss in d['pit_loss_sensitivity']:
    decisions=[]
    for st in states:
     m=solver(st['laps'],st['age'],st['history_count'],st['history_sum_age'],loss,d['grid_size'])
     m.s=replace(m.s,prior_high=st['prior_high'])
     decisions.append(dict(**st,**m.report()))
    v=dict(nuisance_improvement=g,pit_loss=loss,forecast_metrics=metrics(preds),decisions=decisions)
    if g==d['nuisance_improvement'] and loss==d['pit_loss']:
     result['predictions']=preds
     for st in states[:12]:
      m=solver(st['laps'],st['age'],st['history_count'],st['history_sum_age'],loss,d['refinement_grid_size']);m.s=replace(m.s,prior_high=st['prior_high'])
      result['refinements'].append(dict(driver=st['driver'],lap=st['lap'],report=m.report()))
    result['variants'].append(v)
   print(name,'nuisance',g,'forecast targets',len(preds),'decision states',len(states),flush=True)
  results.append(result)
 with OUTPUT.open('x') as f:json.dump(dict(protocol_sha256=digest(FROZEN),protocol=d,completed_at=datetime.now(timezone.utc).isoformat(),events=results),f,indent=2)
 print('Complete historical replay',flush=True)

if __name__=='__main__':{'freeze':freeze,'evaluate':evaluate}[sys.argv[1]]()
