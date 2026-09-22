"""Present v0.5 results without modifying frozen records."""
import json
import os
from pathlib import Path
import numpy as np


def main():
    root=Path(__file__).resolve().parents[2];out=root/'results'
    data=json.loads((out/'robust-evaluation.json').read_text())
    frozen=json.loads((out/'robust-frozen.json').read_text())
    data['development_ablations']=frozen['development_ablations']
    os.environ.setdefault('MPLCONFIGDIR',str(root/'.mplconfig'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,3,figsize=(15,4.6),constrained_layout=True)
    x=np.arange(3)
    for ax,key,title,ylabel in zip(axes,['mae','rmse','coverage90'],
        ['Average absolute error','Large-error sensitivity','90% interval coverage'],
        ['MAE (seconds)','RMSE (seconds)','Observed coverage (%)']):
        for shift,model,label,color in [(-.24,'robust','Robust version','#176d62'),
                (0,'original','Original model','#91a29b'),(.24,'last_observation','Last observed lap','#4b5963')]:
            ax.bar(x+shift,[r['metrics'][model][key]*(100 if key=='coverage90' else 1) for r in data['races']],.24,label=label,color=color)
        ax.set_xticks(x,[r['event'] for r in data['races']]);ax.set(title=title,ylabel=ylabel,xlabel='Held-out race (2024)')
        if key=='coverage90':ax.axhline(90,color='#777777',linestyle='--');ax.set_ylim(0,100)
        ax.legend(fontsize=8)
    fig.suptitle('Robust pace model · frozen before Miami, Emilia Romagna and Monaco · retrospective eligible laps',fontsize=12)
    fig.savefig(out/'robust-validation.png',dpi=180);fig.savefig(out/'robust-validation.svg');plt.close(fig)
    html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Pit timing · robust model test</title>
<style>body{margin:0;background:#f5f4ef;color:#182d2b;font:16px/1.6 system-ui}main{max-width:1100px;margin:40px auto;padding:0 24px}h1{font-size:38px;line-height:1.15;max-width:850px}h2{font-size:23px;margin-top:28px}p{max-width:900px}.tag{font:12px monospace;letter-spacing:2px;color:#176d62;text-transform:uppercase}a{color:#176d62}section{border-top:1px solid #cdd5cf;padding-top:20px;margin-top:32px}small{color:#58675f}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:10px 8px;border-bottom:1px solid #d2dcd5}.scroll{overflow-x:auto}select{font:inherit;padding:8px;background:white;border:1px solid #a0ada5}img{width:100%}.note{border-left:3px solid #a05c3b;padding-left:16px}.metric{font-size:25px;font-weight:650;color:#176d62}</style>
<main><div class="tag">Research prototype / experiment 05</div><h1>Can we learn pace without overreacting to unusual laps?</h1><p>The new estimator uses a median warm-start and limits individual observations’ influence. Gap resets were tested during development. Settings and interval widths were frozen before the three new races.</p><p><a href="interval-demo.html">Next: adaptive prediction intervals</a> · <a href="multi-race-demo.html">Original failure analysis</a> · <a href="robust-evaluation.json">Recorded evaluation</a> · <a href="robust-frozen.json">Frozen development record</a> · <a href="robust-validation.svg">Export figure</a></p>
<section><h2>Three untouched races</h2><div id="headline" class="metric"></div><p id="verdict" class="note"></p><div class="scroll" id="summary"></div><small>Primary summary: arithmetic mean of each race’s metric. MAE measures typical absolute error; RMSE penalises large misses more. The robust and last-lap interval widths were calibrated on development races only. Original-model intervals retain their original settings.</small><img src="robust-validation.png" alt="Per-race forecast accuracy and predictive coverage for the robust model, original model and last-lap baseline"><small>Source: FastF1 2024 Miami, Emilia Romagna and Monaco race sessions; retrospective quality-filtered observations. Within-stint forecasts after three earlier eligible observations. No independent-lap statistical significance claim.</small></section>
<section><h2>Inspect a race</h2><label>Race <select id="race"></select></label><div class="scroll" id="raceMetrics"></div><h2>Largest misses remain in the scores</h2><div class="scroll" id="misses"></div></section>
<section><h2>What changed</h2><p id="config"></p><p>Median initialization replaces an unusually slow first lap with the middle value of the first three already-observed laps. Clipped updates limit how far a single surprising lap can move the filter. A gap reset, if selected, resets trend after a gap in usable observations; a gap is not a verified race-interruption label.</p><p>This is a robust state estimator with approximate working uncertainty, not exact Bayesian inference. Empirical 90% interval calibration on earlier races does not guarantee 90% coverage on new circuits.</p><h2>Development ablation checks</h2><div class="scroll" id="ablations"></div><small>These averages use all five previously inspected development races, including Japan. They explain the redesign but are not held-out evidence. Components are removed one at a time without retuning other settings.</small></section>
<section><h2>Research limits</h2><p>Forecasting net pace does not identify tyre degradation separately from fuel, traffic and driving intent. The same retrospective quality filters are retained, so this is not a proven live/as-of evaluation. Neither version has established real pit-strategy gains. Further changes informed by these results must be evaluated on newly reserved races.</p></section></main>
<script>const data=__DATA__;const el=id=>document.getElementById(id),names={robust:'Robust version',original:'Original model',last_observation:'Last observed lap'};
function table(metrics){return '<table><tr><th>Estimator</th><th>MAE (s)</th><th>RMSE (s)</th><th>90% coverage</th><th>Mean interval width (s)</th></tr>'+Object.entries(metrics).map(([k,v])=>`<tr><td>${names[k]}</td><td>${v.mae.toFixed(3)}</td><td>${v.rmse.toFixed(3)}</td><td>${(v.coverage90*100).toFixed(1)}%</td><td>${v.mean_interval_width.toFixed(2)}</td></tr>`).join('')+'</table>';}
const total=data.races.reduce((s,r)=>s+r.metrics.robust.n,0),a=data.equal_race.robust,b=data.equal_race.last_observation,o=data.equal_race.original;el('headline').textContent=`${total.toLocaleString()} forecasts · 3 fresh races · model settings unchanged during testing`;
const pct=(base,val)=>100*(base-val)/base;const change=p=>`${Math.abs(p).toFixed(1)}% ${p>=0?'lower':'higher'}`;el('verdict').textContent=`Equal-race average absolute error is ${change(pct(o.mae,a.mae))} than the original model and ${change(pct(b.mae,a.mae))} than using the last observed lap. Mean nominal 90% interval coverage is ${(100*a.coverage90).toFixed(1)}%. Check the per-race results before drawing a general conclusion.`;el('summary').innerHTML=table(data.equal_race);
el('race').innerHTML=data.races.map(r=>`<option>${r.event}</option>`).join('');function render(){const r=data.races.find(r=>r.event===el('race').value);el('raceMetrics').innerHTML=table(r.metrics);const rows=[...r.predictions].sort((a,b)=>Math.abs(b.observed-b.predicted)-Math.abs(a.observed-a.predicted)).slice(0,5);el('misses').innerHTML='<table><tr><th>Driver / lap</th><th>Observed (s)</th><th>Predicted (s)</th><th>Absolute error (s)</th></tr>'+rows.map(x=>`<tr><td>${x.driver} / ${x.lap}</td><td>${x.observed.toFixed(3)}</td><td>${x.predicted.toFixed(3)}</td><td>${Math.abs(x.observed-x.predicted).toFixed(3)}</td></tr>`).join('')+'</table>';}
el('race').onchange=render;render();el('config').textContent=`Selected on development data: observation noise ${data.config.noise_sd} s; level-process noise ${data.config.level_sd} s per square-root lap; innovation clipping ${data.config.clip>=1000000?'disabled':data.config.clip+' predicted standard deviations'}; gap resets ${data.config.reset_gap?'enabled':'disabled'}. Prediction standard deviations are multiplied by ${data.interval_scale.toFixed(3)} based on development residuals.`;
const abNames={selected:'Selected configuration',no_median_start:'Without median initialization',no_clipping:'Without clipped updates',no_gap_reset:'Without gap resets'};el('ablations').innerHTML='<table><tr><th>Development variant</th><th>Equal-race MAE (s)</th></tr>'+Object.entries(data.development_ablations).map(([k,rs])=>`<tr><td>${abNames[k]}</td><td>${(Object.values(rs).reduce((s,m)=>s+m.mae,0)/Object.values(rs).length).toFixed(3)}</td></tr>`).join('')+'</table>';
</script></html>'''
    (out/'robust-demo.html').write_text(html.replace('__DATA__',json.dumps(data)))
    print('Rendered robust-demo.html and figures')


if __name__=='__main__':main()
