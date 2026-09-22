import unittest
import numpy as np
from scipy.integrate import quad
from scipy.special import expit
from scipy.stats import norm
from pitvoi.gaussian import LapScenario,LapSolver
from pitvoi.nuisance import OffsetSolver


class NuisanceTests(unittest.TestCase):
    def test_zero_offset_recovers_original_planner(self):
        s=LapScenario();original=LapSolver(s);extended=OffsetSolver(s,0)
        np.testing.assert_allclose(original.adaptive,extended.adaptive,atol=1e-12)
        np.testing.assert_allclose(original.deployed_frozen,extended.deployed_frozen,atol=1e-12)

    def test_sequential_regime_posterior_matches_dense_marginal_likelihood(self):
        s=LapScenario(prior_high=.3);model=OffsetSolver(s,6,grid_size=101)
        y=np.array([6.1,7.3,5.4,8.2,6.9,7.1,9.2,8.4]);p=s.prior_high;past=0.
        for t,value in enumerate(y):
            p=model.posterior_update(p,value,past,t);past+=value
            a=s.age+np.arange(t+1)
            cov=s.noise_sd**2*np.eye(t+1)+36*np.ones((t+1,t+1))
            hi=y[:t+1]-a*s.high;lo=y[:t+1]-a*s.low
            logratio=-.5*(hi@np.linalg.solve(cov,hi)-lo@np.linalg.solve(cov,lo))
            expected=expit(np.log(.3/.7)+logratio)
            self.assertAlmostEqual(float(p),float(expected),places=12)

    def test_two_lap_value_against_independent_scalar_integration(self):
        s=LapScenario(laps=2,pit_loss=4);tau=3
        model=OffsetSolver(s,tau,grid_size=3201,quadrature=81)
        sd=np.sqrt(tau**2+s.noise_sd**2)
        def weighted_future(y):
            lo=norm.pdf(y,s.age*s.low,sd);hi=norm.pdf(y,s.age*s.high,sd)
            density=(1-s.prior_high)*lo+s.prior_high*hi
            if density<1e-250:return 0.
            p=s.prior_high*hi/density
            return density*min(s.pit_loss,(s.age+1)*((1-p)*s.low+p*s.high))
        future=quad(weighted_future,-50,50,epsabs=1e-9,points=[s.age*.17])[0]
        expected=min(s.pit_loss+s.fresh_degradation,s.age*.17+future)
        self.assertAlmostEqual(model.report()['adaptive_cost'],expected,delta=.003)

    def test_no_learning_when_regime_known_or_no_future_decision(self):
        for s in [LapScenario(prior_high=0),LapScenario(prior_high=1),LapScenario(laps=1)]:
            self.assertAlmostEqual(OffsetSolver(s,6).report()['policy_gain'],0,places=10)

    def test_unknown_offset_rollout_matches_planning(self):
        model=OffsetSolver(LapScenario(),3,grid_size=3201,quadrature=81)
        r=model.report();mc=model.monte_carlo(trials=20000)
        self.assertLess(abs(mc['gain']-r['policy_gain']),4*mc['paired_standard_error']+.03)
        self.assertGreaterEqual(r['adaptive_regret'],-.01)

    def test_physical_baseline_cancels_for_every_stop_schedule(self):
        s=LapScenario();b=6.7;theta=.3
        for stop in range(s.laps+1):
            old=sum(theta*(s.age+j) for j in range(stop))
            fresh=s.pit_loss+s.fresh_degradation*(s.laps-stop)*(s.laps-stop-1)/2 if stop<s.laps else 0
            full=old+stop*b+fresh+(s.laps-stop)*b
            self.assertAlmostEqual(full-(old+fresh),s.laps*b)

    def test_reject_invalid_offset(self):
        for offset in [-1,float('nan'),float('inf')]:
            with self.assertRaises(ValueError):OffsetSolver(LapScenario(),offset)
