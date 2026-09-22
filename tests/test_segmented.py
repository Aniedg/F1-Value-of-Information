import unittest
import numpy as np
from scipy.integrate import quad
from scipy.special import expit
from scipy.stats import norm
from pitvoi.segmented import Segments, SegmentedSolver, policy_segments
from pitvoi.gaussian import LapScenario
from pitvoi.replacement import Replacement


class SegmentedTests(unittest.TestCase):
    def test_martingale_affine_and_endpoints(self):
        grid = np.linspace(0, 1, 37)
        f = Segments.continuous(grid, 3+7*grid)
        for separation in (0, .01, 1, 9):
            np.testing.assert_allclose(f.expectation(grid, separation), 3+7*grid, atol=1e-11)

    def test_jump_against_independent_adaptive_quadrature(self):
        f = Segments(np.array([0., .31, 1.]), np.array([2., 9.]), np.array([3., -2.]), (2., 7.))
        p = .43; d = 1.7
        def integral(high):
            mu = (1 if high else -1)*d*d/2
            threshold = (np.log(.31/.69)-np.log(p/(1-p))-mu)/d
            fn = lambda z: float(f.at(expit(np.log(p/(1-p))+mu+d*z)))*norm.pdf(z)
            return quad(fn, -12, threshold, epsabs=1e-11)[0]+quad(fn, threshold, 12, epsabs=1e-11)[0]
        expected = (1-p)*integral(False)+p*integral(True)
        self.assertAlmostEqual(float(f.expectation(np.array([p]), d)[0]), expected, places=10)

    def test_policy_jump_is_preserved(self):
        g = np.array([0., .5, 1.])
        f = policy_segments(g, np.full(3, 4.), 2+5*g, 1+g)
        self.assertAlmostEqual(float(f.at(.4-1e-7)), 1.4-1e-7)
        self.assertAlmostEqual(float(f.at(.4+1e-7)), 4.)
        self.assertIn(.4, f.edges)

    def test_one_lap_no_learning_value(self):
        model = SegmentedSolver(LapScenario(laps=1), Replacement(), grid_size=101)
        self.assertAlmostEqual(model.report()['policy_gain'], 0.)

    def test_independent_replacement_mean_invariance(self):
        s = LapScenario(laps=4)
        a = SegmentedSolver(s, Replacement(), grid_size=101)
        b = SegmentedSolver(s, Replacement(low=.06, high=.06), grid_size=101)
        np.testing.assert_allclose(a.adaptive, b.adaptive, atol=1e-10)
        np.testing.assert_allclose(a.deployed_frozen, b.deployed_frozen, atol=1e-10)

    def test_policy_value_bounds(self):
        model = SegmentedSolver(LapScenario(), Replacement(), offset_sd=0, grid_size=401)
        r = model.report()
        self.assertLessEqual(r['joint_oracle_cost'], r['adaptive_cost']+1e-8)
        self.assertLessEqual(r['adaptive_cost'], r['frozen_policy_cost']+1e-8)
        self.assertLessEqual(r['frozen_policy_cost'], model.frozen[0,200]+1e-8)

if __name__ == '__main__': unittest.main()
