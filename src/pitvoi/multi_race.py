"""Evaluate the unchanged v0.3 model on preselected additional races."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy as np
from pitvoi.forecast import ForecastConfig, load_laps, replay, scores

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def aggregate(races, frozen):
    models = ['bayesian_trend', *frozen['baseline_sd']]
    metrics = ['mae', 'rmse', 'nll', 'coverage90', 'mean_interval_width', 'bias']
    equal_race = {model: {key: float(np.mean([r['metrics'][model][key] for r in races]))
                          for key in metrics} for model in models}
    rows = [row for r in races for row in r['predictions']]
    pooled = {'bayesian_trend': scores(rows)}
    for name, sd in frozen['baseline_sd'].items():
        pooled[name] = scores(rows, name, sd)
    return dict(equal_race=equal_race, pooled=pooled)


def main():
    output = ROOT/'results/multi-race-evaluation.json'
    if output.exists():
        raise RuntimeError('First multi-race result already exists; refusing overwrite')
    protocol_path = ROOT/'research/multi-race-protocol.json'
    protocol = json.loads(protocol_path.read_text())
    frozen_path = ROOT/'results/forecast-frozen.json'
    frozen = json.loads(frozen_path.read_text())
    if digest(frozen_path) != protocol['frozen_sha256']:
        raise RuntimeError('Frozen settings changed')
    if digest(ROOT/'src/pitvoi/historical.py') != protocol['historical_source_sha256']:
        raise RuntimeError('Ingestion code changed after selection')
    if digest(ROOT/'research/forecast-protocol.json') != frozen['protocol_sha256']:
        raise RuntimeError('Original model protocol changed')
    for name, expected in frozen['source_sha256'].items():
        if digest(ROOT/'src/pitvoi'/name) != expected:
            raise RuntimeError(f'Frozen code changed: {name}')
    if digest(ROOT/'data/processed/2024-bahrain-audited.csv') != frozen['development_sha256']:
        raise RuntimeError('Development input changed')
    races = []
    for event in protocol['events']:
        event_id = f"{protocol['year']}-{event.lower().replace(' ', '-')}"
        path = ROOT/f'data/processed/{event_id}-audited.csv'
        manifest = json.loads((ROOT/f'results/{event_id}-manifest.json').read_text())
        if digest(path) != manifest['processed_sha256']:
            raise RuntimeError('Processed data differ from provenance')
        rows = replay(load_laps(path), ForecastConfig(**frozen['selected']['config']),
                      frozen['protocol']['warmup_observations'])
        metrics = {'bayesian_trend': scores(rows)}
        for name, sd in frozen['baseline_sd'].items():
            metrics[name] = scores(rows, name, sd)
        extreme = sorted(rows, key=lambda r: abs(r['observed']-r['predicted']), reverse=True)[:5]
        races.append(dict(event=event, event_id=event_id, input_sha256=digest(path),
                          manifest_sha256=digest(ROOT/f'results/{event_id}-manifest.json'),
                          total_laps=manifest['total_laps'], eligible_laps=manifest['eligible_laps'],
                          scored_drivers=len({r['driver'] for r in rows}), metrics=metrics,
                          largest_errors=extreme, predictions=rows))
    result = dict(experiment=protocol['experiment'], evaluated_utc=datetime.now(timezone.utc).isoformat(),
                  protocol=protocol, protocol_sha256=digest(protocol_path),
                  evaluator_sha256=digest(Path(__file__)), selected_config=frozen['selected']['config'],
                  baseline_sd=frozen['baseline_sd'], races=races, **aggregate(races, frozen),
                  limitations=['Three newly evaluated races; descriptive, not population-level confidence',
                               'Saudi Arabia first-test result is separate from this new batch',
                               'Retrospective dry-compound, green-flag eligibility; not all race conditions',
                               'Within-stint prediction only, after three eligible observations',
                               'No physically identified degradation or counterfactual pit gains'])
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'races'}, indent=2))
    for r in races:
        print(json.dumps(dict(event=r['event'], metrics=r['metrics'])))


if __name__ == '__main__':
    main()
