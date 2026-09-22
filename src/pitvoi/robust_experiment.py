"""Versioned robust development, freeze, and untouched three-race evaluation."""
from dataclasses import asdict
from datetime import datetime, timezone
from itertools import product
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
from pitvoi.forecast import ForecastConfig, Z90, load_laps, replay, scores
from pitvoi.robust import RobustConfig, replay_robust, weighted_quantile

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/'research/robust-protocol.json'
FROZEN=ROOT/'results/robust-frozen.json'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def data_path(event):
    return ROOT/f"data/processed/2024-{event.lower().replace(' ', '-')}-audited.csv"


def train():
    if FROZEN.exists():
        raise RuntimeError('Refusing to overwrite frozen model')
    p=json.loads(PROTOCOL.read_text())
    frames={e:load_laps(data_path(e)) for e in p['development']}
    candidates=[]
    for noise,level,clip,gap in product(p['noise_sd'],p['level_sd'],p['clip'],p['reset_gap']):
        c=RobustConfig(noise,level,clip,gap)
        metrics={e:scores(replay_robust(f,c)) for e,f in frames.items()}
        candidates.append(dict(config=asdict(c),mae=float(np.mean([m['mae'] for m in metrics.values()])),by_race=metrics))
    best=min(candidates,key=lambda x:x['mae'])
    c=RobustConfig(**best['config'])
    residuals,weights,baseline_errors=[],[],[]
    for frame in frames.values():
        rows=replay_robust(frame,c)
        for r in rows:
            residuals.append(abs(r['observed']-r['predicted'])/np.sqrt(r['variance']))
            baseline_errors.append(abs(r['observed']-r['last_observation']))
            weights.append(1/len(rows))
    scale=weighted_quantile(residuals,weights,.9)/Z90
    baseline_sd=weighted_quantile(baseline_errors,weights,.9)/Z90
    # Paired development ablations are exploratory, not fresh validation.
    variants={'selected':(c,True),'no_median_start':(c,False),
              'no_clipping':(RobustConfig(c.noise_sd,c.level_sd,1e6,c.reset_gap),True),
              'no_gap_reset':(RobustConfig(c.noise_sd,c.level_sd,c.clip,False),True)}
    ablations={name:{e:scores(replay_robust(f,vc,median_start=median)) for e,f in frames.items()}
               for name,(vc,median) in variants.items()}
    names=['robust.py','robust_experiment.py','forecast.py','historical.py']
    result=dict(protocol=p,protocol_sha256=sha(PROTOCOL),frozen_utc=datetime.now(timezone.utc).isoformat(),
                selected=best,interval_scale=scale,last_lap_interval_sd=baseline_sd,candidates=candidates,
                development_ablations=ablations,development_hashes={e:sha(data_path(e)) for e in frames},
                source_hashes={n:sha(ROOT/'src/pitvoi'/n) for n in names},
                original_frozen_sha256=sha(ROOT/'results/forecast-frozen.json'))
    FROZEN.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('candidates','development_ablations')},indent=2))


def verify():
    f=json.loads(FROZEN.read_text())
    assert sha(PROTOCOL)==f['protocol_sha256'], 'Protocol changed'
    for name,value in f['source_hashes'].items():
        assert sha(ROOT/'src/pitvoi'/name)==value, 'Frozen code changed'
    for event,value in f['development_hashes'].items():
        assert sha(data_path(event))==value, 'Development data changed'
    assert sha(ROOT/'results/forecast-frozen.json')==f['original_frozen_sha256']
    return f


def download():
    f=verify()
    for event in f['protocol']['heldout']:
        slug=event.lower().replace(' ','-')
        print(f'Downloading {event}',flush=True)
        subprocess.run([sys.executable,'-m','pitvoi.historical','--selection',f'research/selection-{slug}.json'],
                       cwd=ROOT,check=True)


def evaluate():
    out=ROOT/'results/robust-evaluation.json'
    if out.exists():
        raise RuntimeError('Refusing to overwrite first evaluation')
    f=verify(); c=RobustConfig(**f['selected']['config'])
    old=json.loads((ROOT/'results/forecast-frozen.json').read_text())
    races=[]
    for event in f['protocol']['heldout']:
        frame=load_laps(data_path(event)); rows=replay_robust(frame,c)
        original=replay(frame,ForecastConfig(**old['selected']['config']))
        assert [(r['driver'],r['lap']) for r in rows]==[(r['driver'],r['lap']) for r in original]
        for r in rows:
            r['variance']*=f['interval_scale']**2
        metrics={'robust':scores(rows),'original':scores(original),
                 'last_observation':scores(rows,'last_observation',f['last_lap_interval_sd'])}
        races.append(dict(event=event,input_sha256=sha(data_path(event)),metrics=metrics,predictions=rows,
                          original_predictions=original))
    keys=['mae','rmse','coverage90','mean_interval_width','bias']
    aggregate={m:{k:float(np.mean([r['metrics'][m][k] for r in races])) for k in keys}
               for m in ('robust','original','last_observation')}
    result=dict(experiment=f['protocol']['experiment'],evaluated_utc=datetime.now(timezone.utc).isoformat(),
                frozen_sha256=sha(FROZEN),config=asdict(c),interval_scale=f['interval_scale'],
                equal_race=aggregate,races=races,
                limitations=['Robust working covariance is not an exact Bayesian posterior',
                             'Empirical development-calibrated intervals, no coverage guarantee',
                             'Three held-out races; retrospective eligibility; no causal strategy claims'])
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(aggregate,indent=2))
    for r in races: print(json.dumps(dict(event=r['event'],metrics=r['metrics'])))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['train','download','evaluate'])
    args=parser.parse_args();{'train':train,'download':download,'evaluate':evaluate}[args.mode]()
