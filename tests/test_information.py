import unittest
import numpy as np
from scipy.special import expit
from pitvoi.information_experiment import regime_posterior
from pitvoi.gaussian import LapScenario, update

class InformationTests(unittest.TestCase):
    def test_known_baseline_matches_sequential_update(self):
        s=LapScenario(); y=np.array([1.,3.,2.]);ages=np.array([12,13,14]);p=.5
        for value,age in zip(y,ages):p=update(p,value,age,s)
        self.assertAlmostEqual(float(p),float(regime_posterior(y,ages,s.low,s.high,s.noise_sd)))

    def test_marginal_likelihood_matches_dense_covariance(self):
        y=np.array([5.,4.,7.]);a=np.array([12,13,14]);lo=.04;hi=.3
        covariance=2.25*np.eye(3)+36*np.ones((3,3))
        inverse=np.linalg.inv(covariance)
        odds=-.5*((y-a*hi)@inverse@(y-a*hi)-(y-a*lo)@inverse@(y-a*lo))
        self.assertAlmostEqual(float(expit(odds)),float(regime_posterior(y,a,lo,hi,1.5,6)))

    def test_unidentified_constant_age_with_diffuse_offset(self):
        p=regime_posterior(np.full(8,9.),np.full(8,12),.04,.3,1.5,1e6)
        self.assertAlmostEqual(float(p),.5,places=8)
