"""Freeze on development data before downloading/scoring the held-out race."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
from itertools import product
import json
from pathlib import Path
import numpy as np
from pitvoi.forecast import ForecastConfig, load_laps, replay, scores

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT/'research/forecast-protocol.json'
FROZEN = ROOT/'results/forecast-frozen.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def train():
    if FROZEN.exists():
        raise RuntimeError('Frozen experiment already exists; create a new version instead of overwriting it')
    protocol = json.loads(PROTOCOL.read_text())
    path = ROOT/f"data/processed/{protocol['development_event']}-audited.csv"
    frame = load_laps(path)
    candidates = []
    for noise, level, slope in product(protocol['noise_sd_candidates'],
                                       protocol['level_process_sd_candidates'],
                                       protocol['slope_process_sd_candidates']):
        config = ForecastConfig(noise, level, slope, protocol['initial_slope_mean'],
                                protocol['initial_slope_sd'], protocol['initial_level_variance'])
        records = replay(frame, config, protocol['warmup_observations'])
        candidates.append(dict(config=asdict(config), development_scores=scores(records)))
    best = min(candidates, key=lambda c: c['development_scores']['nll'])
    records = replay(frame, ForecastConfig(**best['config']), protocol['warmup_observations'])
    baseline_sd = {name: float(np.sqrt(np.mean([(r['observed']-r[name])**2 for r in records])))
                   for name in protocol['baselines']}
    sources = ['forecast.py', 'forecast_experiment.py']
    result = dict(experiment=protocol['experiment'], frozen_utc=datetime.now(timezone.utc).isoformat(),
                  protocol=protocol, protocol_sha256=digest(PROTOCOL),
                  development_sha256=digest(path),
                  source_sha256={name:digest(ROOT/'src/pitvoi'/name) for name in sources},
                  selected=best, baseline_sd=baseline_sd, candidates=candidates)
    FROZEN.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'candidates'}, indent=2))


def evaluate():
    frozen = json.loads(FROZEN.read_text())
    if digest(PROTOCOL) != frozen['protocol_sha256']:
        raise RuntimeError('Protocol changed after freezing')
    for name, expected in frozen['source_sha256'].items():
        if digest(ROOT/'src/pitvoi'/name) != expected:
            raise RuntimeError(f'{name} changed after freezing')
    p = frozen['protocol']
    dev = ROOT/f"data/processed/{p['development_event']}-audited.csv"
    if digest(dev) != frozen['development_sha256']:
        raise RuntimeError('Development data changed after freezing')
    test = ROOT/f"data/processed/{p['heldout_event']}-audited.csv"
    frame = load_laps(test)
    rows = replay(frame, ForecastConfig(**frozen['selected']['config']), p['warmup_observations'])
    metrics = {'bayesian_trend': scores(rows)}
    for name, sd in frozen['baseline_sd'].items():
        metrics[name] = scores(rows, name, sd)
    drivers = []
    for driver in sorted({r['driver'] for r in rows}):
        subset = [r for r in rows if r['driver'] == driver]
        drivers.append(dict(driver=driver, bayesian_trend=scores(subset),
                            last_observation=scores(subset, 'last_observation', frozen['baseline_sd']['last_observation'])))
    # No iid-lap confidence intervals: laps and drivers share a race environment.
    result = dict(experiment=p['experiment'], evaluated_utc=datetime.now(timezone.utc).isoformat(),
                  frozen_sha256=digest(FROZEN), heldout_sha256=digest(test),
                  development_event=p['development_event'], heldout_event=p['heldout_event'],
                  selected_config=frozen['selected']['config'], metrics=metrics,
                  drivers=drivers, predictions=rows,
                  nuisance_assumptions=p['nuisance_pace_improvement_assumptions_seconds_per_lap'],
                  limitations=['One held-out event; no between-race uncertainty estimate',
                               'Net pace trend is not identified tyre degradation',
                               'Retrospective eligibility; quality flags may use later information',
                               'Forecasts conditional on continuing the same stint and passing quality filters',
                               'No causal pit-strategy improvement established'])
    output = ROOT/'results/forecast-evaluation.json'
    if output.exists():
        raise RuntimeError('Held-out evaluation already recorded; do not overwrite the first test')
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('drivers', 'predictions')}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['train', 'evaluate'])
    args = parser.parse_args()
    train() if args.mode == 'train' else evaluate()
