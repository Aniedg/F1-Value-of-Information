"""Decision-boundary-aware integration; a separate post-v1 numerical method.

Exactly integrates a piecewise-affine function of posterior belief under the
binary Gaussian observation kernel. Belief interpolation remains approximate.
Unlike nodal interpolation of a deployed policy value, separate interval
coefficients retain jumps at pit/stay boundaries.
"""
from dataclasses import dataclass
import numpy as np
from scipy.special import ndtr, logit
from .replacement import ReplacementSolver


@dataclass
class Segments:
    edges: np.ndarray
    intercept: np.ndarray
    slope: np.ndarray
    endpoints: tuple

    @classmethod
    def continuous(cls, grid, values):
        slope = np.diff(values)/np.diff(grid)
        return cls(grid.copy(), values[:-1]-slope*grid[:-1], slope,
                   (float(values[0]), float(values[-1])))

    def at(self, p):
        p = np.asarray(p)
        idx = np.clip(np.searchsorted(self.edges, p, side='right')-1,
                      0, len(self.slope)-1)
        value = self.intercept[idx]+self.slope[idx]*p
        return np.where(p == 0, self.endpoints[0],
                        np.where(p == 1, self.endpoints[1], value))

    def expectation(self, prior, separation, chunk=96):
        """separation = (mu_high-mu_low)/predictive_sd, nonnegative.

        E[q 1_A(q)] = p P_high(A); logit(q)|theta is Gaussian with
        mean logit(p) +/- separation**2/2 and SD separation.
        """
        prior = np.asarray(prior, dtype=float)
        if separation < 0 or not np.isfinite(separation):
            raise ValueError('invalid standardized separation')
        if separation == 0:
            return self.at(prior)
        flat = prior.ravel(); out = np.empty_like(flat)
        edges = logit(self.edges)
        for start in range(0, len(flat), chunk):
            p = flat[start:start+chunk]
            interior = (p > 0) & (p < 1)
            result = self.at(p)
            if interior.any():
                q = p[interior]
                z = (edges[None, :]-logit(q)[:, None])/separation
                low_cdf = ndtr(z+separation/2)
                high_cdf = ndtr(z-separation/2)
                pl = np.diff(low_cdf, axis=1)
                ph = np.diff(high_cdf, axis=1)
                mass = (1-q[:, None])*pl+q[:, None]*ph
                result[interior] = (mass*self.intercept+q[:, None]*ph*self.slope).sum(axis=1)
            out[start:start+chunk] = result
        return out.reshape(prior.shape)


def policy_segments(grid, pit, planning_stay, realized_stay):
    """Retain the jump where frozen planning switches actions.

    Each cell is split at its linear pit-minus-planning-stay root. The
    realized stay value is interpolated separately from the action selector.
    """
    margin = planning_stay-pit
    edges = list(grid)
    for i in np.flatnonzero(margin[:-1]*margin[1:] < 0):
        edges.append(grid[i]-margin[i]*(grid[i+1]-grid[i])/(margin[i+1]-margin[i]))
    edges = np.unique(edges)
    mid = (edges[:-1]+edges[1:])/2
    idx = np.clip(np.searchsorted(grid, mid)-1, 0, len(grid)-2)
    pit_slope = np.diff(pit)/np.diff(grid)
    stay_slope = np.diff(realized_stay)/np.diff(grid)
    is_pit = np.interp(mid, grid, margin) >= 0
    slope = np.where(is_pit, pit_slope[idx], stay_slope[idx])
    intercept = np.where(is_pit, pit[idx]-pit_slope[idx]*grid[idx],
                         realized_stay[idx]-stay_slope[idx]*grid[idx])
    endpoint = tuple(float(pit[i] if margin[i] >= 0 else realized_stay[i]) for i in (0, -1))
    return Segments(edges, intercept, slope, endpoint)


class SegmentedSolver(ReplacementSolver):
    """Same model and action rules as v1, replacing its integration scheme."""
    def __init__(self, scenario, replacement, offset_sd=3., grid_size=1601):
        if grid_size < 3 or not np.isfinite(offset_sd) or offset_sd < 0:
            raise ValueError('invalid numerical grid or offset SD')
        self.s = scenario; self.replacement = replacement; self.offset_sd = float(offset_sd)
        self.grid = np.linspace(0, 1, grid_size)
        shape = (scenario.laps+1, grid_size)
        self.adaptive, self.frozen, self.deployed_frozen = (np.zeros(shape) for _ in range(3))
        self.stay_adaptive, self.stay_frozen = np.zeros(shape), np.zeros(shape)
        self.deployed_segments = [None]*(scenario.laps+1)
        self.deployed_segments[-1] = Segments.continuous(self.grid, self.adaptive[-1])
        for t in range(scenario.laps-1, -1, -1):
            age = scenario.age+t
            current = age*((1-self.grid)*scenario.low+self.grid*scenario.high)
            pit = self.pit_cost(scenario.laps-t)
            _, effective_age, sd = self.observation_parameters(t)
            separation = effective_age*(scenario.high-scenario.low)/sd
            self.stay_adaptive[t] = current+Segments.continuous(self.grid, self.adaptive[t+1]).expectation(self.grid, separation)
            self.stay_frozen[t] = current+self.frozen[t+1]
            self.adaptive[t] = np.minimum(pit, self.stay_adaptive[t])
            self.frozen[t] = np.minimum(pit, self.stay_frozen[t])
            realized_stay = current+self.deployed_segments[t+1].expectation(self.grid, separation)
            self.deployed_segments[t] = policy_segments(self.grid, pit, self.stay_frozen[t], realized_stay)
            self.deployed_frozen[t] = self.deployed_segments[t].at(self.grid)

    def report(self):
        result = super().report()
        result['frozen_policy_cost'] = float(self.deployed_segments[0].at(self.s.prior_high))
        result['policy_gain'] = result['frozen_policy_cost']-result['adaptive_cost']
        return result
