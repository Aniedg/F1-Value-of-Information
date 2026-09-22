"""Finite-horizon Bayesian optimal stopping; all costs are excess seconds.

The unknown regime belongs to the current tyre set. The replacement set has
known pace. Observations are binary diagnostic signals, NOT real lap times.
"""
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Scenario:
    laps: int = 8
    age: int = 12
    low: float = 0.04
    high: float = 0.30
    prior_high: float = 0.5
    accuracy: float = 0.8
    pit_loss: float = 18.0
    fresh_degradation: float = 0.06

    def __post_init__(self):
        if not isinstance(self.laps, int) or not 1 <= self.laps <= 16:
            raise ValueError('laps must be an integer from 1 to 16')
        if not isinstance(self.age, int) or self.age < 0:
            raise ValueError('age must be a nonnegative integer')
        if not 0 <= self.prior_high <= 1 or not 0.5 <= self.accuracy <= 1:
            raise ValueError('invalid prior or signal accuracy')
        if not 0 <= self.low < self.high or min(self.pit_loss, self.fresh_degradation) < 0:
            raise ValueError('invalid cost parameters')


class Solver:
    def __init__(self, scenario):
        self.s = scenario

    def branches(self, p):
        """Return (predictive probability, posterior) for possible signals."""
        q = self.s.accuracy
        for high_likelihood, low_likelihood in ((q, 1-q), (1-q, q)):
            mass = p * high_likelihood + (1-p) * low_likelihood
            if mass > 0:
                yield mass, p * high_likelihood / mass

    def pit_cost(self, remaining):
        # Pit before the next lap; fresh ages are 0,...,remaining-1.
        return self.s.pit_loss + self.s.fresh_degradation * remaining * (remaining-1) / 2

    @lru_cache(maxsize=None)
    def values(self, remaining, age, p, learn):
        if remaining == 0:
            return (0.0, 0.0)
        current = age * ((1-p) * self.s.low + p * self.s.high)
        if learn:
            future = sum(mass * min(self.values(remaining-1, age+1, post, True))
                         for mass, post in self.branches(p))
        else:
            future = min(self.values(remaining-1, age+1, p, False))
        return self.pit_cost(remaining), current + future

    def action(self, remaining, age, p, policy):
        if policy not in ('fixed', 'certainty_equivalent', 'frozen_belief', 'adaptive'):
            raise ValueError('unknown policy')
        planning_p = self.s.prior_high if policy == 'fixed' else p
        pit, stay = self.values(remaining, age, planning_p, policy == 'adaptive')
        return 'pit' if pit <= stay else 'stay'

    @lru_cache(maxsize=None)
    def evaluate(self, remaining, age, p, policy):
        """Exact policy evaluation, including online updates for both baselines.

        Frozen-belief planning ignores future updates, but its actual policy
        updates and replans after each signal. This is a fair learning ablation.
        """
        if remaining == 0:
            return 0.0
        if self.action(remaining, age, p, policy) == 'pit':
            return self.pit_cost(remaining)
        current = age * ((1-p) * self.s.low + p * self.s.high)
        return current + sum(mass * self.evaluate(remaining-1, age+1, post, policy)
                             for mass, post in self.branches(p))

    def oracle(self):
        # Knows the latent regime, not future random signals.
        s = self.s
        return ((1-s.prior_high) * min(self.values(s.laps, s.age, 0.0, False))
                + s.prior_high * min(self.values(s.laps, s.age, 1.0, False)))

    def report(self):
        s = self.s
        oracle = self.oracle()
        policies = {}
        for policy in ('fixed', 'certainty_equivalent', 'frozen_belief', 'adaptive'):
            cost = self.evaluate(s.laps, s.age, s.prior_high, policy)
            policies[policy] = dict(action=self.action(s.laps, s.age, s.prior_high, policy),
                                    expected_excess_seconds=cost, regret_seconds=cost-oracle)
        frozen = self.values(s.laps, s.age, s.prior_high, False)
        adaptive = self.values(s.laps, s.age, s.prior_high, True)
        result = dict(policies=policies, oracle_seconds=oracle,
                      planning_information_value_seconds=min(frozen)-min(adaptive),
                      realized_policy_gain_seconds=policies['frozen_belief']['expected_excess_seconds']-policies['adaptive']['expected_excess_seconds'],
                      action_values=dict(pit_seconds=adaptive[0],
                                         stay_frozen_seconds=frozen[1],
                                         stay_adaptive_seconds=adaptive[1]))
        self.values.cache_clear()
        self.evaluate.cache_clear()
        return result
