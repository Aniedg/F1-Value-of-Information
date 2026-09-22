"""Robust pace estimator; covariance is a working approximation, not a posterior."""
from dataclasses import dataclass
import numpy as np
from pitvoi.forecast import ForecastConfig, PaceFilter


@dataclass(frozen=True)
class RobustConfig:
    noise_sd: float = 0.6
    level_sd: float = 0.3
    clip: float = 4.0
    reset_gap: bool = True


def replay_robust(frame, config, *, median_start=True, warmup=3):
    records = []
    for (driver, stint), group in frame.groupby(['Driver', 'Stint'], sort=True):
        f = PaceFilter(ForecastConfig(config.noise_sd, config.level_sd))
        past, previous_age = [], None
        for row in group.sort_values('LapNumber').itertuples():
            age, value = float(row.tyre_age_start), float(row.lap_seconds)
            if len(past) == warmup and median_start:
                # Only the three already observed laps initialise this state.
                f.mean = np.array([float(np.median(past)), 0.0])
                f.cov = np.diag([config.noise_sd**2, 0.15**2])
                f.age = previous_age
            reset = config.reset_gap and previous_age is not None and age-previous_age > 1
            if reset:
                # A gap is observable but is NOT a verified interruption label.
                f.mean = np.array([past[-1], 0.0])
                f.cov = np.diag([config.noise_sd**2, 0.15**2])
            mean, variance = f.predict(age)
            if len(past) >= warmup:
                records.append(dict(driver=driver, stint=int(stint), lap=int(row.LapNumber),
                    observed=value, predicted=mean, variance=variance, gap_reset=bool(reset),
                    last_observation=past[-1], expanding_mean=float(np.mean(past))))
            residual = value-mean
            clipped = np.clip(residual, -config.clip*np.sqrt(variance), config.clip*np.sqrt(variance))
            # Warm-up is replaced by the robust initial state before scoring.
            f.update(value if len(past) < warmup else mean+clipped)
            past.append(value)
            previous_age = age
    return records


def weighted_quantile(values, weights, probability):
    order = np.argsort(values)
    values, weights = np.asarray(values)[order], np.asarray(weights)[order]
    return float(values[np.searchsorted(np.cumsum(weights)/weights.sum(), probability)])
