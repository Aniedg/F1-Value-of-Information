"""Render recorded results without refitting or changing the frozen experiment."""
import json
import os
from pathlib import Path
import numpy as np
from scipy.stats import norm


def main():
    root = Path(__file__).resolve().parents[2]
    out = root/'results'
    data = json.loads((out/'forecast-evaluation.json').read_text())
    frozen = json.loads((out/'forecast-frozen.json').read_text())
    manifest = json.loads((out/'2024-saudi-arabia-manifest.json').read_text())
    rows = data['predictions']
    calibration = []
    for nominal in (0.5, 0.8, 0.9, 0.95, 0.99):
        z = norm.ppf((1+nominal)/2)
        coverage = np.mean([abs(r['observed']-r['predicted']) <= z*np.sqrt(r['variance']) for r in rows])
        calibration.append(dict(nominal=nominal, observed=float(coverage)))
    data['calibration'] = calibration
    data['manifest'] = {k:v for k,v in manifest.items() if k not in ('stints', 'display_laps')}
    data['frozen_utc'] = frozen['frozen_utc']
    data['development_scores'] = frozen['selected']['development_scores']
    # Derived display data only; do not overwrite the first evaluation file.
    (out/'forecast-display.json').write_text(json.dumps(data, indent=2)+'\n')
    os.environ.setdefault('MPLCONFIGDIR', str(root/'.mplconfig'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.6), constrained_layout=True)
    names = ['bayesian_trend', 'last_observation', 'expanding_mean']
    labels = ['Bayesian trend', 'Last observation', 'Expanding mean']
    x = np.arange(3)
    ax[0].bar(x-.18, [data['metrics'][n]['mae'] for n in names], .36, label='Mean absolute error', color='#176d62')
    ax[0].bar(x+.18, [data['metrics'][n]['rmse'] for n in names], .36, label='Root mean squared error', color='#889b96')
    ax[0].set_xticks(x, labels)
    ax[0].set(ylabel='Forecast error (seconds; lower is better)', xlabel='Predictor', title='Held-out lap prediction errors')
    ax[0].legend()
    ax[1].plot([50, 99], [50, 99], '--', color='#888888', label='Ideal calibration')
    ax[1].plot([100*r['nominal'] for r in calibration], [100*r['observed'] for r in calibration], 'o-', color='#176d62', label='Bayesian trend')
    ax[1].set(xlabel='Nominal predictive coverage (%)', ylabel='Observed predictive coverage (%)',
              title='Do uncertainty intervals transfer?', xlim=(45, 102), ylim=(40, 102))
    ax[1].legend()
    fig.suptitle(f"Saudi Arabia 2024 · {len(rows)} eligible forecasts · settings selected on Bahrain only", fontsize=12)
    fig.savefig(out/'forecast-validation.png', dpi=180)
    fig.savefig(out/'forecast-validation.svg')
    plt.close(fig)
    html = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Pit timing · first held-out race</title>
<style>body{margin:0;background:#f5f4ef;color:#182d2b;font:16px/1.6 system-ui}main{max-width:1100px;margin:40px auto;padding:0 24px}h1{font-size:38px;line-height:1.15;max-width:850px}h2{font-size:23px;margin-top:30px}p{max-width:900px}.tag{font:12px monospace;letter-spacing:2px;color:#176d62;text-transform:uppercase}a{color:#176d62}section{border-top:1px solid #cdd5cf;padding-top:20px;margin-top:32px}.lead{font-size:20px}.note{border-left:3px solid #a05c3b;padding-left:16px}small{color:#58675f}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:10px 8px;border-bottom:1px solid #d2dcd5}.scroll{overflow-x:auto}select{font:inherit;background:white;padding:8px;border:1px solid #a0ada5}label{display:inline-block;margin:12px 20px 12px 0}img,svg{width:100%;height:auto}.metric{font-size:28px;font-weight:600;color:#176d62}.legend span{margin-right:18px}.observed{color:#283c45}.prediction{color:#176d62}.interval{color:#627f73}</style>
<main><div class="tag">Research prototype / experiment 03</div><h1>Can the model predict a race it has not seen?</h1>
<p class="lead">Develop on Bahrain. Freeze the settings. Test on Saudi Arabia.</p><p id="verdict" class="note"></p>
<p><a href="multi-race-demo.html">Next: three-race replication and failure analysis</a> · <a href="lap-demo.html">Previous: synthetic learning experiment</a> · <a href="forecast-evaluation.json">Original evaluation</a> · <a href="forecast-frozen.json">Frozen settings</a> · <a href="forecast-validation.svg">Export figure</a></p>
<section><h2>The held-out result</h2><p id="scope"></p><div class="scroll" id="metrics"></div><small>All models forecast the same eligible observations after three earlier eligible laps in each stint. Baseline prediction widths were learned on Bahrain. No settings were changed after test results were opened. Coverage target: 90%.</small><img src="forecast-validation.png" alt="Held-out prediction errors and observed versus nominal interval coverage"><p id="comparison"></p><p>Calibration varies across interval sizes: the nominal 50% interval covers 67.3%, while the nominal 99% interval covers only 95.1%. A near-target 90% result alone does not establish calibrated uncertainty.</p></section>
<section><h2>Inspect the predictions</h2><label>Driver <select id="driver"></select></label><div class="legend"><span class="observed">● Observed lap</span><span class="prediction">— Predicted lap</span><span class="interval">Shaded: 90% prediction interval</span></div><div id="chart"></div><small>Source: FastF1 Saudi Arabian GP 2024; retrospective rolling forecasts. Predictions use only previous eligible observations within the same stint. Lines and bands break between stints and gaps. Forecasts do not establish what would happen under another pit strategy.</small><p id="driverSummary"></p></section>
<section><h2>Why “pace trend” does not yet mean “tyre wear”</h2><p>Fuel burn and improving track conditions can make laps faster while tyre wear makes them slower. Timing data alone cannot cleanly separate those effects. The filter estimates their combined net trend, with additional random pace variation.</p><label>Assumed fuel/track improvement (seconds per lap) <select id="nuisance"></select></label><div class="metric" id="slope"></div><p id="slopeDetail"></p><p>Changing this assumption shifts the conditional tyre interpretation without changing the lap prediction. These are sensitivity scenarios, not measured fuel corrections. Negative values should not be silently clipped into a positive degradation story.</p></section>
<section><h2>What this establishes—and what remains</h2><p>We now have a reproducible test on a separate race, simple comparison models and a record of every forecast. The model learns from earlier laps of the test race, as an online estimator should, while its settings stay frozen.</p><p>This is only one held-out race. Retrospective quality flags may have used later information; traffic, driving intent and warm-up are not explicitly separated. The forecasts are conditional on a continuing stint and an eligible observation. We cannot yet claim calibrated tyre uncertainty or real pit-strategy gains.</p><small id="provenance"></small></section></main>
<script>const data=__DATA__;const el=id=>document.getElementById(id);const labels={bayesian_trend:'Bayesian pace trend',last_observation:'Last observed lap',expanding_mean:'Mean of earlier laps'};
const m=data.metrics.bayesian_trend,b=data.metrics.last_observation;el('verdict').textContent=m.coverage90<.85?`The first test exposes a limitation: the model's nominal 90% intervals cover only ${(100*m.coverage90).toFixed(1)}% of observations. Prediction accuracy and uncertainty need to be assessed separately.`:`First held-out result: mean absolute prediction error is ${m.mae.toFixed(3)} seconds and nominal 90% intervals cover ${(100*m.coverage90).toFixed(1)}% of observations. One race is a feasibility test, not broad validation.`;
el('scope').textContent=`${m.n} scored forecasts across ${data.drivers.length} drivers, from ${data.manifest.eligible_laps} eligible laps out of ${data.manifest.total_laps}. The first three eligible laps per stint initialise the models and are not scored.`;
el('metrics').innerHTML='<table><thead><tr><th>Predictor</th><th>MAE (s) ↓</th><th>RMSE (s) ↓</th><th>90% coverage</th><th>Mean interval width (s)</th></tr></thead><tbody>'+Object.entries(data.metrics).map(([name,v])=>`<tr><td>${labels[name]}</td><td>${v.mae.toFixed(3)}</td><td>${v.rmse.toFixed(3)}</td><td>${(100*v.coverage90).toFixed(1)}%</td><td>${v.mean_interval_width.toFixed(2)}</td></tr>`).join('')+'</tbody></table>';
const improvement=100*(b.mae-m.mae)/b.mae;el('comparison').textContent=`Against the last-observed-lap baseline, mean absolute error is ${Math.abs(improvement).toFixed(1)}% ${improvement>=0?'lower':'higher'}. Root mean squared error, which penalises large misses more, is ${m.rmse.toFixed(3)} s versus ${b.rmse.toFixed(3)} s. These are descriptive results for this event; no independent-lap significance claim is made.`;
el('driver').innerHTML=data.drivers.map(d=>`<option>${d.driver}</option>`).join('');el('nuisance').innerHTML=data.nuisance_assumptions.map(v=>`<option value="${v}">${v.toFixed(2)}</option>`).join('');el('nuisance').value='0.04';
function render(){const driver=el('driver').value,rows=data.predictions.filter(r=>r.driver===driver),d=data.drivers.find(d=>d.driver===driver);const xmin=Math.min(...rows.map(r=>r.lap)),xmax=Math.max(...rows.map(r=>r.lap));const ymin=Math.floor(Math.min(...rows.map(r=>Math.min(r.observed,r.predicted-1.644854*Math.sqrt(r.variance)))))-.5,ymax=Math.ceil(Math.max(...rows.map(r=>Math.max(r.observed,r.predicted+1.644854*Math.sqrt(r.variance)))))+.5;const x=v=>65+(v-xmin)/(xmax-xmin||1)*840,y=v=>285-(v-ymin)/(ymax-ymin)*220;const segments=[];for(const r of rows){const last=segments.at(-1);if(!last||last.at(-1).stint!==r.stint||last.at(-1).lap+1!==r.lap)segments.push([r]);else last.push(r);}const ticks=[0,.25,.5,.75,1];el('chart').innerHTML=`<svg viewBox="0 0 950 345" role="img" aria-label="${driver} held-out lap forecasts and 90 percent predictive intervals">${ticks.map(f=>{const v=ymin+(ymax-ymin)*f;return `<line x1="65" x2="905" y1="${y(v)}" y2="${y(v)}" stroke="#d4ddd6"/><text x="12" y="${y(v)+5}">${v.toFixed(1)}</text>`}).join('')}${segments.map(group=>{const top=group.map(r=>`${x(r.lap)},${y(r.predicted+1.644854*Math.sqrt(r.variance))}`),bot=[...group].reverse().map(r=>`${x(r.lap)},${y(r.predicted-1.644854*Math.sqrt(r.variance))}`);return `<polygon points="${[...top,...bot].join(' ')}" fill="#176d62" opacity=".14"/><polyline points="${group.map(r=>`${x(r.lap)},${y(r.predicted)}`).join(' ')}" fill="none" stroke="#176d62" stroke-width="2"/>`}).join('')}${rows.map(r=>`<circle cx="${x(r.lap)}" cy="${y(r.observed)}" r="3.5" fill="#283c45"><title>Lap ${r.lap}: observed ${r.observed.toFixed(3)} s; forecast ${r.predicted.toFixed(3)} s</title></circle>`).join('')}${ticks.map(f=>{const v=xmin+(xmax-xmin)*f;return `<text x="${x(v)-8}" y="307">${v.toFixed(0)}</text>`}).join('')}<text x="10" y="25">Lap time (seconds)</text><text x="370" y="336">Race lap (number)</text></svg>`;el('driverSummary').textContent=`${driver}: ${d.bayesian_trend.n} forecasts; mean absolute error ${d.bayesian_trend.mae.toFixed(3)} s; nominal 90% interval coverage ${(100*d.bayesian_trend.coverage90).toFixed(1)}%. Driver selection changes the view, not the overall evaluation.`;
const r=rows.at(-1),c=+el('nuisance').value,lo=r.net_slope_before-1.644854*r.net_slope_sd_before+c,hi=r.net_slope_before+1.644854*r.net_slope_sd_before+c;el('slope').textContent=(r.net_slope_before+c).toFixed(3)+' s/lap conditional tyre slope';el('slopeDetail').textContent=`For ${driver}, before lap ${r.lap}: estimated net trend ${r.net_slope_before.toFixed(3)} s/lap + assumed improvement ${c.toFixed(2)} s/lap. Conditional 90% latent-slope interval: ${lo.toFixed(3)} to ${hi.toFixed(3)} s/lap. This is not a next-lap prediction interval and excludes uncertainty in the assumed correction.`;}
el('driver').onchange=render;el('nuisance').onchange=render;render();el('provenance').textContent=`Frozen at ${data.frozen_utc}; evaluated at ${data.evaluated_utc}. FastF1 ${data.manifest.fastf1_version}. Model, protocol and data checksums are recorded in the frozen settings and original evaluation.`;
</script></html>'''
    (out/'forecast-demo.html').write_text(html.replace('__DATA__', json.dumps(data)))
    print(json.dumps(dict(metrics=data['metrics'], calibration=calibration), indent=2))


if __name__ == '__main__':
    main()
