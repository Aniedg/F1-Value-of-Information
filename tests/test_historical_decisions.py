import unittest
import numpy as np
import pandas as pd
from scipy.special import expit
from pitvoi.historical_decisions import RegimeFilter,HistorySolver,forecasts
from pitvoi.gaussian import LapScenario
from pitvoi.replacement import Replacement

class HistoricalDecisionTests(unittest.TestCase):
 def test_diffuse_baseline_posterior_equals_batch_likelihood(self):
  ages=np.array([2.,3.,7.,8.,11.]);y=np.array([94.,93.8,95.,95.4,96.])
  f=RegimeFilter(.04,.30,.6)
  for a,v in zip(ages,y):f.update(a,v)
  rss=[]
  for theta in [.04,.30]:
   residual=y-ages*theta;rss.append(sum((residual-residual.mean())**2))
  self.assertAlmostEqual(f.p,expit((rss[0]-rss[1])/(2*.6**2)),places=12)
 def test_baseline_shift_invariance(self):
  a=RegimeFilter(.04,.30,.6);b=RegimeFilter(.04,.30,.6)
  for age,y in [(1,80.),(3,80.2),(5,81.)]:a.update(age,y);b.update(age,y+1000)
  self.assertAlmostEqual(a.p,b.p,places=10)
 def test_extreme_evidence_can_reverse(self):
  f=RegimeFilter(.04,.30,.3)
  for a,y in [(0,100),(10,110)]:f.update(a,y)
  self.assertGreater(f.log_odds,30)
  f.update(20,80)
  self.assertLess(f.p,.5)
 def test_history_kernel_predictive_separation(self):
  f=RegimeFilter(.04,.30,.6)
  for a,y in [(2,90),(5,91),(6,91.3)]:f.update(a,y)
  s=LapScenario(laps=3,age=7,noise_sd=.6)
  m=HistorySolver(s,Replacement(),f.count,f.sum_age,51)
  means,sd=f.predict(7);_,h,predsd=m.observation_parameters(0)
  self.assertAlmostEqual(means[1]-means[0],h*(.30-.04))
  self.assertAlmostEqual(sd,predsd)
 def test_future_rows_do_not_change_earlier_forecasts_or_decisions(self):
  rows=[]
  for lap in range(1,13):
   rows.append(dict(Driver='AAA',LapNumber=lap,Stint=1 if lap<3 else 2,tyre_age_start=lap-1 if lap<3 else lap-3,lap_seconds=90+.1*lap,lap_end_session_seconds=100*lap,Compound='SOFT' if lap<3 else 'HARD',eligible=True))
  frame=pd.DataFrame(rows);a,b=forecasts(frame,.04,.30,.6,.05,True,14)
  changed=frame.copy();changed.loc[changed.LapNumber>8,'lap_seconds']=1000
  c,d=forecasts(changed,.04,.30,.6,.05,True,14)
  self.assertEqual([x for x in a if x['lap']<=8],[x for x in c if x['lap']<=8])
  self.assertEqual([x for x in b if x['lap']<=8],[x for x in d if x['lap']<=8])
  self.assertTrue(all(x['history_count']>=3 and len(x['observed_compounds'])>=2 for x in b))
 def test_no_compound_obligation_lookahead(self):
  frame=pd.DataFrame([dict(Driver='A',LapNumber=i,Stint=1,tyre_age_start=i-1,lap_seconds=90,lap_end_session_seconds=i*90,Compound='SOFT' if i<8 else 'HARD',eligible=True) for i in range(1,10)])
  _,states=forecasts(frame,.04,.30,.6,.05,True,12)
  self.assertTrue(all(s['lap']>=8 for s in states))
if __name__=='__main__':unittest.main()
