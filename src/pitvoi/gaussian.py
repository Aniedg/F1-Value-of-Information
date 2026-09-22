"""Continuous lap observations; numerical belief-state dynamic programming.

Two latent regimes remain. Lap residual y = age * theta + N(0, sigma**2).
Base pace and other corrections must be specified without future information.
"""
from dataclasses import dataclass
import numpy as np
from numpy.polynomial.hermite import hermgauss
from scipy.special import expit, ndtr


@dataclass(frozen=True)
class LapScenario:
    laps: int = 8
    age: int = 12
    low: float = 0.04
    high: float = 0.30
    prior_high: float = 0.5
    noise_sd: float = 1.5
    pit_loss: float = 18.0
    fresh_degradation: float = 0.06

    def __post_init__(self):
        if not isinstance(self.laps, int) or not 1 <= self.laps <= 100:
            raise ValueError('laps must be an integer from 1 to 100')
        if not isinstance(self.age, int) or self.age < 0:
            raise ValueError('invalid tyre age')
        if not all(np.isfinite(v) for v in (self.low, self.high, self.prior_high,
                   self.noise_sd, self.pit_loss, self.fresh_degradation)):
            raise ValueError('all parameters must be finite')
        if not 0 <= self.low < self.high or not 0 <= self.prior_high <= 1:
            raise ValueError('invalid regimes or prior')
        if self.noise_sd <= 0 or min(self.pit_loss, self.fresh_degradation) < 0:
            raise ValueError('invalid noise or costs')


def update(p, residual, age, s):
    """Stable Gaussian likelihood update, preserving known-regime endpoints."""
    p = np.asarray(p, dtype=float)
    clipped = np.clip(p, 1e-300, 1-1e-15)
    log_odds = np.log(clipped) - np.log1p(-clipped)
    log_ratio = ((np.asarray(residual)-age*s.low)**2
                 - (np.asarray(residual)-age*s.high)**2) / (2*s.noise_sd**2)
    post = expit(log_odds + log_ratio)
    return np.where(p == 0, 0, np.where(p == 1, 1, post))


def predictive_quantile(p, age, s, probability):
    """Mixture-normal quantile; computed before observing the next lap."""
    lo = np.full_like(np.asarray(p, dtype=float), age*s.low-10*s.noise_sd)
    hi = np.full_like(lo, age*s.high+10*s.noise_sd)
    for _ in range(50):
        mid = (lo+hi)/2
        cdf = (1-p)*ndtr((mid-age*s.low)/s.noise_sd)+p*ndtr((mid-age*s.high)/s.noise_sd)
        lo, hi = np.where(cdf < probability, mid, lo), np.where(cdf >= probability, mid, hi)
    return (lo+hi)/2


class LapSolver:
    def __init__(self, s, grid_size=1601, quadrature=41):
        if grid_size < 3 or quadrature < 3:
            raise ValueError('numerical resolution too small')
        self.s = s
        self.grid = np.linspace(0, 1, grid_size)
        nodes, weights = hermgauss(quadrature)
        self.nodes, self.weights = np.sqrt(2)*nodes, weights/np.sqrt(np.pi)
        shape = (s.laps+1, grid_size)
        self.adaptive, self.frozen, self.deployed_frozen = (np.zeros(shape) for _ in range(3))
        self.stay_adaptive, self.stay_frozen = np.zeros(shape), np.zeros(shape)
        for t in range(s.laps-1, -1, -1):
            age = s.age+t
            current = age*((1-self.grid)*s.low+self.grid*s.high)
            pit = self.pit_cost(s.laps-t)
            self.stay_adaptive[t] = current+self.integrate(self.adaptive[t+1], age)
            self.stay_frozen[t] = current+self.frozen[t+1]
            self.adaptive[t] = np.minimum(pit, self.stay_adaptive[t])
            self.frozen[t] = np.minimum(pit, self.stay_frozen[t])
            self.deployed_frozen[t] = np.where(
                pit <= self.stay_frozen[t], pit,
                current+self.integrate(self.deployed_frozen[t+1], age))

    def pit_cost(self, remaining):
        return self.s.pit_loss+self.s.fresh_degradation*remaining*(remaining-1)/2

    def integrate(self, future, age):
        total = np.zeros_like(self.grid)
        for theta, prob in ((self.s.low, 1-self.grid), (self.s.high, self.grid)):
            residuals = age*theta+self.s.noise_sd*self.nodes
            post = update(self.grid[:, None], residuals[None, :], age, self.s)
            total += prob*(np.interp(post, self.grid, future) @ self.weights)
        return total

    def action(self, t, p, policy):
        if policy not in ('adaptive', 'frozen_belief'):
            raise ValueError('unknown policy')
        values = self.stay_adaptive if policy == 'adaptive' else self.stay_frozen
        return self.pit_cost(self.s.laps-t) <= np.interp(p, self.grid, values[t])

    def report(self):
        s, p = self.s, self.s.prior_high
        at = lambda a: float(np.interp(p, self.grid, a[0]))
        oracle = float((1-p)*self.frozen[0, 0]+p*self.frozen[0, -1])
        adaptive, frozen = at(self.adaptive), at(self.deployed_frozen)
        return dict(adaptive_cost=adaptive, frozen_policy_cost=frozen,
                    oracle_cost=oracle, policy_gain=frozen-adaptive,
                    adaptive_regret=adaptive-oracle,
                    planning_information_value=at(self.frozen)-adaptive,
                    pit_cost=self.pit_cost(s.laps), stay_adaptive=at(self.stay_adaptive),
                    stay_frozen=at(self.stay_frozen),
                    adaptive_action='pit' if self.action(0, p, 'adaptive') else 'stay',
                    frozen_action='pit' if self.action(0, p, 'frozen_belief') else 'stay')

    def monte_carlo(self, trials=20000, seed=20260922, actual_noise_sd=None):
        """Independent paired rollout, updating with each actual continuous lap.

        Scores conditional excess pace. Common action-independent lap noise and
        known baseline/fuel/track offsets cancel in the paired comparison.
        actual_noise_sd permits a predeclared misspecification stress test.
        """
        s = self.s
        rng = np.random.default_rng(seed)
        theta = np.where(rng.random(trials) < s.prior_high, s.high, s.low)
        noise = rng.normal(0, actual_noise_sd or s.noise_sd, (trials, s.laps))
        costs = {}
        for policy in ('frozen_belief', 'adaptive'):
            p = np.full(trials, s.prior_high)
            cost, active = np.zeros(trials), np.ones(trials, dtype=bool)
            for t in range(s.laps):
                pit = active & self.action(t, p, policy)
                cost[pit] += self.pit_cost(s.laps-t)
                active[pit] = False
                cost[active] += (s.age+t)*theta[active]
                p[active] = update(p[active], (s.age+t)*theta[active]+noise[active, t], s.age+t, s)
            costs[policy] = cost
        delta = costs['frozen_belief']-costs['adaptive']
        se = float(delta.std(ddof=1)/np.sqrt(trials))
        mean = float(delta.mean())
        return dict(trials=trials, seed=seed, gain=mean, paired_standard_error=se,
                    gain_95_ci=[mean-1.96*se, mean+1.96*se],
                    adaptive_cost=float(costs['adaptive'].mean()),
                    frozen_cost=float(costs['frozen_belief'].mean()),
                    actual_noise_sd=actual_noise_sd or s.noise_sd)


def calibration(s, trials=10000, seed=20260923, actual_noise_sd=None):
    """Prior-predictive synthetic validation; score BEFORE each update."""
    rng = np.random.default_rng(seed)
    high = rng.random(trials) < s.prior_high
    theta = np.where(high, s.high, s.low)
    p = np.full(trials, s.prior_high)
    rows = []
    for t in range(s.laps):
        age = s.age+t
        lo, hi = predictive_quantile(p, age, s, 0.05), predictive_quantile(p, age, s, 0.95)
        residual = age*theta+rng.normal(0, actual_noise_sd or s.noise_sd, trials)
        covered = (residual >= lo) & (residual <= hi)
        p = update(p, residual, age, s)
        rows.append(dict(observations=t+1, predictive_90_coverage=float(covered.mean()),
                         coverage_standard_error=float(np.sqrt(covered.mean()*(1-covered.mean())/trials)),
                         posterior_brier=float(np.mean((p-high)**2))))
    bins = []
    for left, right in zip(np.linspace(0, 0.9, 10), np.linspace(0.1, 1, 10)):
        mask = (p >= left) & ((p < right) if right < 1 else (p <= right))
        if mask.any():
            bins.append(dict(count=int(mask.sum()), predicted=float(p[mask].mean()), observed=float(high[mask].mean())))
    return dict(trials=trials, seed=seed, actual_noise_sd=actual_noise_sd or s.noise_sd,
                by_lap=rows, final_reliability_bins=bins)
