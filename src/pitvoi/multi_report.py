"""Presentation of recorded multi-race results; no model selection or fitting."""
import json
import os
from pathlib import Path
import numpy as np


def main():
    root = Path(__file__).resolve().parents[2]
    out = root/'results'
    data = json.loads((out/'multi-race-evaluation.json').read_text())
    os.environ.setdefault('MPLCONFIGDIR', str(root/'.mplconfig'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6), constrained_layout=True)
    x = np.arange(len(data['races']))
    for ax, key, title, ylabel in zip(axes, ['mae', 'rmse', 'coverage90'],
        ['Typical forecast error', 'Error with larger penalty for big misses', '90% predictive interval coverage'],
        ['Mean absolute error (seconds)', 'Root mean squared error (seconds)', 'Observed coverage (%)']):
        for shift, model, label, color in ((-.18,'bayesian_trend','Bayesian trend','#176d62'),(.18,'last_observation','Last observed lap','#91a29b')):
            values = [r['metrics'][model][key]*(100 if key=='coverage90' else 1) for r in data['races']]
            ax.bar(x+shift, values, .36, label=label, color=color)
        ax.set_xticks(x, [r['event'] for r in data['races']])
        ax.set(title=title, xlabel='Held-out race (2024)', ylabel=ylabel)
        if key == 'coverage90':
            ax.axhline(90, linestyle='--', color='#666666', label='Nominal 90%')
            ax.set_ylim(0,100)
        ax.legend(fontsize=8)
    fig.suptitle('Unchanged Bahrain-selected model · three additional races · retrospective eligible laps', fontsize=12)
    fig.savefig(out/'multi-race-validation.png', dpi=180)
    fig.savefig(out/'multi-race-validation.svg')
    plt.close(fig)
    html = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Pit timing · three-race test</title>
<style>body{margin:0;background:#f5f4ef;color:#182d2b;font:16px/1.6 system-ui}main{max-width:1100px;margin:40px auto;padding:0 24px}h1{font-size:38px;line-height:1.15;max-width:850px}h2{font-size:23px;margin-top:28px}p{max-width:900px}.tag{font:12px monospace;letter-spacing:2px;color:#176d62;text-transform:uppercase}a{color:#176d62}section{border-top:1px solid #cdd5cf;padding-top:20px;margin-top:32px}small{color:#58675f}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:10px 8px;border-bottom:1px solid #d2dcd5}.scroll{overflow-x:auto}select{font:inherit;padding:8px;background:white;border:1px solid #a0ada5}img{width:100%}.note{border-left:3px solid #a05c3b;padding-left:16px}.metric{font-size:24px;font-weight:650;color:#176d62}</style>
<main><div class="tag">Research prototype / experiment 04</div><h1>Does the result hold across more races?</h1><p>Australia, Japan and China 2024 were selected chronologically before downloading. Model settings, baseline settings and filters stayed unchanged from the Bahrain development experiment.</p><p><a href="robust-demo.html">Next: robust revision on three fresh races</a> · <a href="forecast-demo.html">Earlier Saudi Arabia test</a> · <a href="multi-race-evaluation.json">Recorded results</a> · <a href="multi-race-validation.svg">Export figure</a></p>
<section><h2>The new three-race test</h2><div class="metric" id="headline"></div><p id="verdict" class="note"></p><label>Summary weighting <select id="weight"><option value="equal_race">Equal weight per race (primary)</option><option value="pooled">Equal weight per forecast (secondary)</option></select></label><div class="scroll" id="summary"></div><small>MAE is average absolute error; RMSE gives larger misses more weight. Lower is better for both. The primary RMSE summary is the mean of each race’s RMSE, not the square root of a pooled error average. Coverage target is 90%.</small><img src="multi-race-validation.png" alt="Per-race error and coverage comparisons for Australia Japan and China 2024"><small>Source: FastF1 historical race timing, 2024 Grands Prix; forecasts generated using the frozen v0.3 model. Only eligible within-stint observations after three earlier eligible laps are scored.</small></section>
<section><h2>Every race stays visible</h2><div class="scroll" id="races"></div><p>Saudi Arabia’s earlier result remains separate. No race was dropped because the model performed badly, and no post-test adjustments were made.</p></section>
<section><h2>Inspect the largest misses</h2><label>Race <select id="event"></select></label><div class="scroll" id="misses"></div><p>These are the five largest absolute prediction errors for the Bayesian model in the selected race. They are retained in every reported metric. This view describes failures; it does not establish whether traffic, driver behaviour, track changes or another factor caused them.</p></section>
<section><h2>A concrete failure to investigate</h2><p>In Japan, GAS’s first eligible lap in stint 2 was 138.362 seconds, followed by 99.925 and 99.473 seconds. These observations all passed the existing filters. By lap 8, the model had learned an implausible −3.353 s/lap trend and predicted 95.496 seconds; the observed lap was 101.363 seconds.</p><p>This is evidence of initialization being distorted by an unusual observation. It does not establish the physical cause or explain every Japan error. The observation and its downstream misses remain in the recorded evaluation.</p></section><section><h2>Research status</h2><p>The model predicts net pace, not separately identified tyre wear. Eligibility uses retrospective quality flags, and green-flag dry-compound filtering excludes other race conditions. With only three new races, these are descriptive results without a population-level significance claim.</p><p>Before claiming pit-strategy benefits, we need reliable uncertainty across race conditions, a defensible tyre interpretation and a validated counterfactual simulator. Any redesign informed by these results must use new races for its next held-out test.</p><small id="provenance"></small></section></main>
<script>const data=__DATA__;const el=id=>document.getElementById(id);const names={bayesian_trend:'Bayesian pace trend',last_observation:'Last observed lap',expanding_mean:'Mean of earlier laps'};
const total=data.races.reduce((sum,r)=>sum+r.metrics.bayesian_trend.n,0),wins=data.races.filter(r=>r.metrics.bayesian_trend.mae<r.metrics.last_observation.mae).length;el('headline').textContent=`${total.toLocaleString()} forecasts · ${data.races.length} new races · lower MAE in ${wins}/${data.races.length} races`;
const a=data.equal_race.bayesian_trend,b=data.equal_race.last_observation;const mae=100*(b.mae-a.mae)/b.mae,rmse=100*(b.rmse-a.rmse)/b.rmse;el('verdict').textContent=`Giving each race equal weight, the model’s MAE is ${Math.abs(mae).toFixed(1)}% ${mae>=0?'lower':'higher'} than the last-lap baseline; mean race RMSE is ${Math.abs(rmse).toFixed(1)}% ${rmse>=0?'lower':'higher'}. Mean 90% interval coverage is ${(100*a.coverage90).toFixed(1)}%. These metrics assess different aspects of performance; they do not establish real strategy gains.`;
function summary(){el('summary').innerHTML='<table><tr><th>Predictor</th><th>MAE (s)</th><th>RMSE (s)</th><th>90% coverage</th><th>Mean interval width (s)</th></tr>'+Object.entries(data[el('weight').value]).map(([k,v])=>`<tr><td>${names[k]}</td><td>${v.mae.toFixed(3)}</td><td>${v.rmse.toFixed(3)}</td><td>${(100*v.coverage90).toFixed(1)}%</td><td>${v.mean_interval_width.toFixed(2)}</td></tr>`).join('')+'</table>';}
el('races').innerHTML='<table><tr><th>Race</th><th>Forecasts</th><th>Model MAE (s)</th><th>Last-lap MAE (s)</th><th>Model 90% coverage</th></tr>'+data.races.map(r=>`<tr><td>${r.event}</td><td>${r.metrics.bayesian_trend.n}</td><td>${r.metrics.bayesian_trend.mae.toFixed(3)}</td><td>${r.metrics.last_observation.mae.toFixed(3)}</td><td>${(100*r.metrics.bayesian_trend.coverage90).toFixed(1)}%</td></tr>`).join('')+'</table>';
el('event').innerHTML=data.races.map(r=>`<option>${r.event}</option>`).join('');function misses(){const r=data.races.find(r=>r.event===el('event').value);el('misses').innerHTML='<table><tr><th>Driver / lap</th><th>Observed (s)</th><th>Predicted (s)</th><th>Absolute error (s)</th><th>90% prediction interval (s)</th></tr>'+r.largest_errors.map(x=>`<tr><td>${x.driver} / ${x.lap}</td><td>${x.observed.toFixed(3)}</td><td>${x.predicted.toFixed(3)}</td><td>${Math.abs(x.observed-x.predicted).toFixed(3)}</td><td>${(x.predicted-1.644854*Math.sqrt(x.variance)).toFixed(2)} – ${(x.predicted+1.644854*Math.sqrt(x.variance)).toFixed(2)}</td></tr>`).join('')+'</table>';}
el('weight').onchange=summary;el('event').onchange=misses;summary();misses();el('provenance').textContent=`Selection recorded ${data.protocol.selected_utc}; evaluation recorded ${data.evaluated_utc}. Frozen-model, ingestion-code and input checksums verified. Results are preserved without overwriting the original single-race test.`;
</script></html>'''
    (out/'multi-race-demo.html').write_text(html.replace('__DATA__', json.dumps(data)))
    print('Rendered results/multi-race-demo.html and exportable figures.')


if __name__ == '__main__':
    main()
