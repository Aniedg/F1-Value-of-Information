import unittest
from itertools import product
from pitvoi.model import Scenario, Solver


class ModelTests(unittest.TestCase):
    def test_bayes_update(self):
        branches = list(Solver(Scenario()).branches(0.5))
        self.assertAlmostEqual(sum(w for w, p in branches), 1)
        self.assertAlmostEqual(sum(w*p for w, p in branches), 0.5)
        self.assertAlmostEqual(branches[0][1], 0.8)

    def test_oracle_matches_exhaustive_pit_times(self):
        s = Scenario()
        solver = Solver(s)
        for p, theta in ((0.0, s.low), (1.0, s.high)):
            costs = [sum(theta*(s.age+j) for j in range(k))
                     + (solver.pit_cost(s.laps-k) if k < s.laps else 0)
                     for k in range(s.laps+1)]
            self.assertAlmostEqual(min(costs), min(solver.values(s.laps, s.age, p, False)))

    def test_no_information_no_benefit(self):
        r = Solver(Scenario(accuracy=0.5)).report()
        self.assertAlmostEqual(r['realized_policy_gain_seconds'], 0)
        self.assertAlmostEqual(r['planning_information_value_seconds'], 0)

    def test_known_regime_no_benefit(self):
        for p in (0.0, 1.0):
            r = Solver(Scenario(prior_high=p)).report()
            self.assertAlmostEqual(r['policies']['adaptive']['regret_seconds'], 0)

    def test_exact_enumeration_independent_of_bellman_expectations(self):
        s = Scenario(laps=5, pit_loss=10)
        solver = Solver(s)
        for policy in ('fixed', 'certainty_equivalent', 'frozen_belief', 'adaptive'):
            total = 0.0
            for theta, prior, high_prob in ((s.low, 1-s.prior_high, 1-s.accuracy),
                                           (s.high, s.prior_high, s.accuracy)):
                for signals in product((0, 1), repeat=s.laps):
                    weight = prior
                    for signal in signals:
                        weight *= high_prob if signal else 1-high_prob
                    p, cost = s.prior_high, 0.0
                    for t, signal in enumerate(signals):
                        if solver.action(s.laps-t, s.age+t, p, policy) == 'pit':
                            cost += solver.pit_cost(s.laps-t)
                            break
                        cost += theta * (s.age+t)
                        lh = s.accuracy if signal else 1-s.accuracy
                        ll = 1-lh
                        p = p*lh/(p*lh+(1-p)*ll)
                    total += weight*cost
            self.assertAlmostEqual(total, solver.evaluate(s.laps, s.age, s.prior_high, policy))

    def test_adaptive_dominance_and_mean_equivalence(self):
        for p, q, loss in product((0.2, 0.5, 0.8), (0.5, 0.8, 1.0), (10, 18, 25)):
            r = Solver(Scenario(prior_high=p, accuracy=q, pit_loss=loss)).report()
            a = r['policies']['adaptive']['expected_excess_seconds']
            self.assertGreaterEqual(a+1e-10, r['oracle_seconds'])
            self.assertGreaterEqual(r['realized_policy_gain_seconds'], -1e-10)
            self.assertEqual(r['policies']['certainty_equivalent'], r['policies']['frozen_belief'])


if __name__ == '__main__':
    unittest.main()
