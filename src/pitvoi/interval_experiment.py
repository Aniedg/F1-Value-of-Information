"""Freeze interval-only revision before new race evaluation."""
import argparse
from datetime import datetime,timezone
from itertools import product
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
from pitvoi.forecast import Z90,load_laps
from pitvoi.robust import RobustConfig,replay_robust
from pitvoi.robust_experiment import sha,data_path
from pitvoi.intervals import prior_support,apply_intervals,interval_metrics

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/'research/interval-protocol.json'
FROZEN=ROOT/'results/interval-frozen.json'


def train():
    if FROZEN.exists():raise RuntimeError('Frozen record already exists')
    p=json.loads(PROTOCOL.read_text());old=json.loads((ROOT/'results/robust-frozen.json').read_text())
    config=RobustConfig(**old['selected']['config'])
    races={e:replay_robust(load_laps(data_path(e)),config) for e in p['development']}
    priors={e:prior_support([r for name,r in races.items() if name!=e],p['prior_support_size']) for e in races}
    candidates=[]
    for window,mass in product(p['window_candidates'],p['prior_mass_candidates']):
        metrics={e:interval_metrics(apply_intervals(r,priors[e],window,mass)) for e,r in races.items()}
        candidates.append(dict(window=window,prior_mass=mass,
            selection_score=float(np.mean([m['interval_score'] for m in metrics.values()])),by_race=metrics))
    selected=min(candidates,key=lambda c:c['selection_score'])
    names=['intervals.py','interval_experiment.py','robust.py','forecast.py','historical.py','robust_experiment.py']
    result=dict(protocol=p,protocol_sha256=sha(PROTOCOL),frozen_utc=datetime.now(timezone.utc).isoformat(),
                selected=selected,candidates=candidates,point_config=old['selected']['config'],
                old_q=Z90*old['interval_scale'],support=prior_support(list(races.values()),p['prior_support_size']),
                source_hashes={n:sha(ROOT/'src/pitvoi'/n) for n in names},
                data_hashes={e:sha(data_path(e)) for e in races},
                point_frozen_sha256=sha(ROOT/'results/robust-frozen.json'))
    FROZEN.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(selected=selected,old_q=result['old_q'],frozen_utc=result['frozen_utc']),indent=2))


def verify():
    f=json.loads(FROZEN.read_text())
    assert sha(PROTOCOL)==f['protocol_sha256']
    assert sha(ROOT/'results/robust-frozen.json')==f['point_frozen_sha256']
    for name,value in f['source_hashes'].items():assert sha(ROOT/'src/pitvoi'/name)==value
    for e,value in f['data_hashes'].items():assert sha(data_path(e))==value
    return f


def download():
    f=verify()
    for event in f['protocol']['heldout']:
        print('Downloading '+event,flush=True)
        subprocess.run([sys.executable,'-m','pitvoi.historical','--selection',f'research/selection-{event.lower()}.json'],cwd=ROOT,check=True)


def evaluate():
    out=ROOT/'results/interval-evaluation.json'
    if out.exists():raise RuntimeError('First evaluation already recorded')
    f=verify();races=[]
    for e in f['protocol']['heldout']:
        manifest=json.loads((ROOT/f'results/2024-{e.lower()}-manifest.json').read_text())
        assert sha(data_path(e))==manifest['processed_sha256']
        assert manifest['retrieved_utc']>f['frozen_utc']
        rows=replay_robust(load_laps(data_path(e)),RobustConfig(**f['point_config']))
        if not rows:raise RuntimeError('No eligible forecasts; report scope failure, do not silently omit '+e)
        s=f['selected'];adaptive=apply_intervals(rows,f['support'],s['window'],s['prior_mass'])
        static=apply_intervals(rows,f['support'],static=True)
        old=apply_intervals(rows,f['support'],fixed_q=f['old_q'])
        metrics={k:interval_metrics(v) for k,v in [('adaptive',adaptive),('refit_static',static),('original_intervals',old)]}
        assert len({m['mae'] for m in metrics.values()})==1
        # Detailed forecast records preserve both comparator widths for auditing.
        for a,b,c in zip(adaptive,static,old):
            a.update(static_lower=b['lower'],static_upper=b['upper'],old_lower=c['lower'],old_upper=c['upper'])
        races.append(dict(event=e,input_sha256=sha(data_path(e)),total_laps=manifest['total_laps'],
                          eligible_laps=manifest['eligible_laps'],metrics=metrics,predictions=adaptive))
    keys=['coverage90','mean_width','interval_score','mae']
    aggregate={m:{k:float(np.mean([r['metrics'][m][k] for r in races])) for k in keys}
               for m in ('adaptive','refit_static','original_intervals')}
    result=dict(experiment=f['protocol']['experiment'],evaluated_utc=datetime.now(timezone.utc).isoformat(),
                frozen_sha256=sha(FROZEN),selected=f['selected'],races=races,equal_race=aggregate,
                limitations=['Predictive uncertainty is not latent tyre-parameter uncertainty',
                  'Dry-compound eligible subsets only; not whole-race/all-weather validation',
                  'Three races, no iid-lap significance claim or coverage guarantee'])
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(aggregate,indent=2))
    for r in races:print(json.dumps(dict(event=r['event'],metrics=r['metrics'])))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['train','download','evaluate']);a=p.parse_args()
    {'train':train,'download':download,'evaluate':evaluate}[a.mode]()
