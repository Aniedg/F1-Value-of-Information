import unittest
import numpy as np
import pandas as pd
from pitvoi.forecast import ForecastConfig, PaceFilter, replay, scores


def sample_frame(values):
    return pd.DataFrame([dict(Driver='AAA', Stint=1, LapNumber=t+2,
                              tyre_age_start=t+1, lap_seconds=y, Compound='MEDIUM')
                         for t, y in enumerate(values)])


class ForecastTests(unittest.TestCase):
    def test_static_filter_matches_batch_bayesian_regression(self):
        c = ForecastConfig(noise_sd=0.6)
        f = PaceFilter(c)
        ages = np.array([1, 2, 4, 8], dtype=float)
        y = np.array([92, 92.1, 92.5, 92.8])
        for age, value in zip(ages, y):
            f.predict(age)
            f.update(value)
        design = np.column_stack([np.ones(4), ages-ages[0]])
        precision = np.diag([1/c.initial_level_variance, 1/c.initial_slope_sd**2])
        covariance = np.linalg.inv(precision+design.T@design/c.noise_sd**2)
        mean = covariance@(precision@np.array([0, c.initial_slope_mean])+design.T@y/c.noise_sd**2)
        transform = np.array([[1, ages[-1]-ages[0]], [0, 1]])
        np.testing.assert_allclose(f.mean, transform@mean, atol=1e-8)
        np.testing.assert_allclose(f.cov, transform@covariance@transform.T, atol=1e-8)

    def test_no_current_or_future_observation_leaks_into_prediction(self):
        c = ForecastConfig(0.6, 0.1, 0.01)
        original = replay(sample_frame([90, 91, 92, 93, 94, 95]), c)
        changed = replay(sample_frame([90, 91, 92, 200, 500, 800]), c)
        for key in ('predicted', 'variance', 'last_observation', 'expanding_mean', 'net_slope_before'):
            self.assertEqual(original[0][key], changed[0][key])
        prefix = replay(sample_frame([90, 91, 92, 93]), c)
        self.assertEqual(prefix[0], original[0])

    def test_stints_are_independent_and_warmup_not_scored(self):
        first = sample_frame([90, 91, 92, 93])
        second = sample_frame([100, 101, 102, 103]).assign(Stint=2, LapNumber=lambda df: df.LapNumber+10)
        c = ForecastConfig(0.6)
        combined = replay(pd.concat([first, second]), c)
        self.assertEqual(len(combined), 2)
        self.assertEqual(combined[-1], replay(second, c)[0])

    def test_process_uncertainty_grows_with_gap(self):
        c = ForecastConfig(0.6, 0.1, 0.03)
        variances = []
        for next_age in (2, 8):
            f = PaceFilter(c)
            f.predict(1)
            f.update(90)
            _, v = f.predict(next_age)
            variances.append(v)
            self.assertGreaterEqual(np.linalg.eigvalsh(f.cov).min(), 0)
        self.assertGreater(variances[1], variances[0])

    def test_invalid_parameters_and_age_order_rejected(self):
        for noise in (0, -1, float('nan')):
            with self.assertRaises(ValueError):
                ForecastConfig(noise)
        f = PaceFilter(ForecastConfig(0.6))
        f.predict(2)
        with self.assertRaises(ValueError):
            f.predict(2)

    def test_score_known_errors(self):
        result = scores([dict(observed=2, predicted=1, variance=1),
                         dict(observed=2, predicted=3, variance=1)])
        self.assertEqual(result['mae'], 1)
        self.assertEqual(result['bias'], 0)
        self.assertEqual(result['coverage90'], 1)


if __name__ == '__main__':
    unittest.main()
