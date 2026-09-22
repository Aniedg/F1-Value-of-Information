import unittest
import numpy as np
from scipy.integrate import quad
from scipy.special import expit
from scipy.stats import norm
from pitvoi.gaussian import LapScenario
from pitvoi.nuisance import OffsetSolver
from pitvoi.replacement import Replacement,ReplacementSolver


class ReplacementTests(unittest.TestCase):
    def test_independent_mean_preserving_uncertainty_leaves_all_values_unchanged(self):
        s=LapScenario(prior_high=.3)
        baseline=OffsetSolver(s,3)
        for r in [Replacement(),Replacement(low=.06,high=.06)]:
            model=ReplacementSolver(s,r,3)
            np.testing.assert_allclose(model.adaptive,baseline.adaptive,atol=1e-12)
            np.testing.assert_allclose(model.deployed_frozen,baseline.deployed_frozen,atol=1e-12)

    def test_joint_bayes_update_changes_replacement_mean(self):
        s=LapScenario();r=Replacement(high_given_old_low=.125,high_given_old_high=.875)
        model=ReplacementSolver(s,r,3)
        y=4.;sd=np.sqrt(9+s.noise_sd**2)
        weights=np.array([.5*(1-.125),.5*.125,.5*(1-.875),.5*.875])
        likelihood=np.array([norm.pdf(y,s.age*s.low,sd)]*2+[norm.pdf(y,s.age*s.high,sd)]*2)
        posterior=weights*likelihood;posterior/=posterior.sum()
        expected=posterior@np.array([r.low,r.high,r.low,r.high])
        p=model.posterior_update(.5,y,0,0)
        self.assertAlmostEqual(float(r.mean(p)),float(expected),places=12)

    def test_known_old_regime_uses_conditional_replacement_mean(self):
        r=Replacement(high_given_old_low=.125,high_given_old_high=.875)
        for p,old in [(0,.04),(1,.3)]:
            s=LapScenario(prior_high=p);model=ReplacementSolver(s,r,3)
            expected=min(old*sum(s.age+j for j in range(k))+
                         (s.pit_loss+float(r.mean(p))*sum(range(s.laps-k)) if k<s.laps else 0)
                         for k in range(s.laps+1))
            self.assertAlmostEqual(model.report()['adaptive_cost'],expected)
            self.assertAlmostEqual(model.report()['policy_gain'],0)
            self.assertLessEqual(model.report()['joint_oracle_cost'],expected+1e-10)

    def test_three_lap_correlated_value_with_independent_nested_integral(self):
        s=LapScenario(laps=3,age=12,pit_loss=4);r=Replacement(high_given_old_low=.125,high_given_old_high=.875)
        model=ReplacementSolver(s,r,0,grid_size=3201,quadrature=81)
        # Direct observation density and Bayes recursion, no solver transition calls.
        def value(n,age,p):
            pit=s.pit_loss+float(r.mean(p))*n*(n-1)/2
            current=age*((1-p)*s.low+p*s.high)
            if n==1:return min(pit,current)
            def integrand(y):
                lo=norm.pdf(y,age*s.low,s.noise_sd);hi=norm.pdf(y,age*s.high,s.noise_sd)
                density=(1-p)*lo+p*hi
                if density<1e-200:return 0.
                return density*value(n-1,age+1,p*hi/density)
            continuation=quad(integrand,age*s.low-9*s.noise_sd,age*s.high+9*s.noise_sd,epsabs=2e-4,limit=100)[0]
            return min(pit,current+continuation)
        self.assertAlmostEqual(model.report()['adaptive_cost'],value(3,12,.5),delta=.005)

    def test_correlated_physical_rollout_agrees_with_planned_cost(self):
        r=Replacement(high_given_old_low=.125,high_given_old_high=.875)
        model=ReplacementSolver(LapScenario(),r,3,grid_size=3201,quadrature=81)
        result=model.report();mc=model.monte_carlo(trials=20000)
        self.assertLess(abs(mc['gain']-result['policy_gain']),4*mc['paired_standard_error']+.03)
        self.assertGreaterEqual(result['adaptive_regret_joint_oracle'],-.01)

    def test_invalid_replacement(self):
        for args in [dict(low=-.1),dict(high=.01),dict(high_given_old_low=1.1),dict(high=float('nan'))]:
            with self.assertRaises(ValueError):Replacement(**args)
