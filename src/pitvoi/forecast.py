"""Sequential Gaussian local trend on observed pace, not identified tyre wear.

State is current latent pace and net slope. Drift combines tyre, fuel, track,
traffic and driving effects. Conditional tyre interpretation needs assumptions.
"""
from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd

Z90 = 1.6448536269514722


@dataclass(frozen=True)
class ForecastConfig:
    noise_sd: float
    level_process_sd: float = 0.0
    slope_process_sd: float = 0.0
    initial_slope_mean: float = 0.0
    initial_slope_sd: float = 0.15
    initial_level_variance: float = 1e6

    def __post_init__(self):
        if not all(np.isfinite(v) for v in asdict(self).values()):
            raise ValueError('parameters must be finite')
        if self.noise_sd <= 0 or self.initial_slope_sd <= 0 or self.initial_level_variance <= 0:
            raise ValueError('noise and prior variances must be positive')
        if min(self.level_process_sd, self.slope_process_sd) < 0:
            raise ValueError('process standard deviations must be nonnegative')


class PaceFilter:
    def __init__(self, config):
        self.config = config
        self.mean = np.array([0.0, config.initial_slope_mean])
        self.cov = np.diag([config.initial_level_variance, config.initial_slope_sd**2])
        self.age = None

    def predict(self, age):
        if self.age is not None:
            delta = age-self.age
            if delta <= 0:
                raise ValueError('observations must have strictly increasing tyre ages')
            f = np.array([[1.0, delta], [0.0, 1.0]])
            q = self.config.slope_process_sd**2
            process = np.array([[self.config.level_process_sd**2*delta+q*delta**3/3,
                                 q*delta**2/2], [q*delta**2/2, q*delta]])
            self.mean = f@self.mean
            self.cov = f@self.cov@f.T+process
        self.age = age
        return float(self.mean[0]), float(self.cov[0, 0]+self.config.noise_sd**2)

    def update(self, observation):
        if self.age is None or not np.isfinite(observation):
            raise ValueError('predict at an age first and supply finite observation')
        variance = self.cov[0, 0]+self.config.noise_sd**2
        k = self.cov[:, 0]/variance
        self.mean = self.mean+k*(observation-self.mean[0])
        # Joseph covariance update protects positive semidefiniteness.
        a = np.eye(2)-np.outer(k, [1.0, 0.0])
        self.cov = a@self.cov@a.T+np.outer(k, k)*self.config.noise_sd**2


def load_laps(path):
    frame = pd.read_csv(path)
    frame = frame[frame['eligible'].astype(str).str.lower().eq('true')].copy()
    required = ['Driver', 'Stint', 'LapNumber', 'tyre_age_start', 'lap_seconds']
    if frame[required].isna().any().any():
        raise ValueError('eligible frame has missing required fields')
    if frame.duplicated(['Driver', 'LapNumber']).any():
        raise ValueError('duplicate driver/lap records')
    return frame.sort_values(['Driver', 'Stint', 'LapNumber'])


def replay(frame, config, warmup=3):
    records = []
    for (driver, stint), group in frame.groupby(['Driver', 'Stint'], sort=True):
        filt = PaceFilter(config)
        past = []
        for row in group.sort_values('LapNumber').itertuples():
            mean, variance = filt.predict(float(row.tyre_age_start))
            # Forecasts and comparator forecasts are fixed BEFORE this update.
            if len(past) >= warmup:
                records.append(dict(driver=driver, stint=int(stint), lap=int(row.LapNumber),
                    age=float(row.tyre_age_start), compound=row.Compound,
                    history_count=len(past), observed=float(row.lap_seconds),
                    predicted=mean, variance=variance,
                    last_observation=past[-1], expanding_mean=float(np.mean(past)),
                    net_slope_before=float(filt.mean[1]),
                    net_slope_sd_before=float(np.sqrt(filt.cov[1, 1]))))
            filt.update(float(row.lap_seconds))
            past.append(float(row.lap_seconds))
    return records


def scores(records, predictor='predicted', baseline_sd=None):
    if not records:
        raise ValueError('no scored observations')
    error = np.array([r['observed']-r[predictor] for r in records])
    variance = (np.array([r['variance'] for r in records]) if baseline_sd is None
                else np.full(len(records), baseline_sd**2))
    return dict(n=len(records), mae=float(np.abs(error).mean()),
                rmse=float(np.sqrt(np.mean(error**2))), bias=float(error.mean()),
                nll=float(np.mean(0.5*(np.log(2*np.pi*variance)+error**2/variance))),
                coverage90=float(np.mean(np.abs(error) <= Z90*np.sqrt(variance))),
                mean_interval_width=float(np.mean(2*Z90*np.sqrt(variance))))
