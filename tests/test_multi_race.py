import unittest
from pitvoi.multi_race import aggregate
from pitvoi.forecast import scores


class AggregationTests(unittest.TestCase):
    def test_equal_race_not_equal_lap_weighting(self):
        races = []
        for n, error in ((1, 1), (9, 3)):
            rows = [dict(observed=error, predicted=0, variance=1, last_observation=0)]*n
            races.append(dict(predictions=rows, metrics={'bayesian_trend': scores(rows),
                         'last_observation': scores(rows, 'last_observation', 1)}))
        result = aggregate(races, {'baseline_sd': {'last_observation': 1}})
        self.assertEqual(result['equal_race']['bayesian_trend']['mae'], 2)
        self.assertAlmostEqual(result['pooled']['bayesian_trend']['mae'], 2.8)
        self.assertEqual(result['pooled']['bayesian_trend']['n'], 10)


if __name__ == '__main__':
    unittest.main()
