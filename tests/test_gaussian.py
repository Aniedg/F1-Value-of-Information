import unittest
import numpy as np
from pitvoi.gaussian import LapScenario, LapSolver, update, calibration


class GaussianTests(unittest.TestCase):
    def test_likelihood_and_zero_age(self):
        s = LapScenario()
        self.assertAlmostEqual(float(update(0.5, 12*(s.low+s.high)/2, 12, s)), 0.5)
        self.assertAlmostEqual(float(update(0.3, 5, 0, s)), 0.3)
        np.testing.assert_equal(update(np.array([0, 1]), 10000, 12, s), [0, 1])

    def test_batch_equals_sequential_posterior(self):
        s = LapScenario()
        ages, y = np.array([12, 13, 14]), np.array([1.2, 2.1, 0.7])
        p = s.prior_high
        for a, value in zip(ages, y):
            p = update(p, value, a, s)
        from scipy.special import expit
        expected = expit(np.sum(((y-ages*s.low)**2-(y-ages*s.high)**2)/(2*s.noise_sd**2)))
        self.assertAlmostEqual(float(p), float(expected))

    def test_future_observations_cannot_change_prefix(self):
        s = LapScenario()
        def trajectory(y):
            p, result = s.prior_high, []
            for t, value in enumerate(y):
                p = update(p, value, s.age+t, s)
                result.append(float(p))
            return result
        self.assertEqual(trajectory([1, 2, 3])[:2], trajectory([1, 2, 100])[:2])

    def test_single_lap_has_no_information_value(self):
        r = LapSolver(LapScenario(laps=1)).report()
        self.assertAlmostEqual(r['policy_gain'], 0)

    def test_known_regime_matches_exhaustive_schedules(self):
        for p, theta in ((0, 0.04), (1, 0.3)):
            s = LapScenario(prior_high=p)
            solver = LapSolver(s)
            exact = min(sum(theta*(s.age+j) for j in range(k))+
                        (solver.pit_cost(s.laps-k) if k < s.laps else 0)
                        for k in range(s.laps+1))
            self.assertAlmostEqual(solver.report()['adaptive_cost'], exact)

    def test_numerical_convergence_and_independent_rollouts(self):
        coarse = LapSolver(LapScenario(), grid_size=801, quadrature=41)
        fine = LapSolver(LapScenario(), grid_size=3201, quadrature=81)
        r = fine.report()
        self.assertLess(abs(r['adaptive_cost']-coarse.report()['adaptive_cost']), 0.03)
        mc = fine.monte_carlo(trials=30000)
        self.assertLess(abs(mc['gain']-r['policy_gain']), 4*mc['paired_standard_error']+0.03)
        self.assertGreaterEqual(r['adaptive_cost']+0.03, r['oracle_cost'])

    def test_predictive_coverage_under_generating_model(self):
        result = calibration(LapScenario(), trials=4000)
        for row in result['by_lap']:
            self.assertLess(abs(row['predictive_90_coverage']-0.9), 0.035)


if __name__ == '__main__':
    unittest.main()
