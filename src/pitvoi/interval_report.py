"""Render saved predictive-interval evaluation without refitting."""
import json
import os
from pathlib import Path
import numpy as np


def main():
    root=Path(__file__).resolve().parents[2];out=root/'results'
    d=json.loads((out/'interval-evaluation.json').read_text())
    os.environ.setdefault('MPLCONFIGDIR',str(root/'.mplconfig'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,3,figsize=(15,4.6),constrained_layout=True);x=np.arange(3)
    for ax,key,title,unit in zip(axes,['coverage90','mean_width','interval_score'],
        ['Do intervals contain the observations?','How wide are they?','Width and misses together'],
        ['Observed coverage (%)','Mean interval width (seconds)','Mean 90% interval score (seconds; lower is better)']):
        for shift,name,label,color in [(-.24,'adaptive','Adaptive','#176d62'),(0,'refit_static','Recalibrated static','#91a29b'),(.24,'original_intervals','Original static','#4b5963')]:
            ax.bar(x+shift,[r['metrics'][name][key]*(100 if key=='coverage90' else 1) for r in d['races']],.24,label=label,color=color)
        ax.set_xticks(x,[r['event'] for r in d['races']]);ax.set(title=title,ylabel=unit,xlabel='Held-out race (2024)')
        if key=='coverage90':ax.axhline(90,color='#888888',linestyle='--');ax.set_ylim(0,100)
        ax.legend(fontsize=8)
    fig.suptitle('Fixed pace predictions · interval-only test · retrospective dry-compound eligible observations',fontsize=12)
    fig.savefig(out/'interval-validation.png',dpi=180);fig.savefig(out/'interval-validation.svg');plt.close(fig)
    html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Pit timing · adaptive uncertainty</title>
<style>body{margin:0;background:#f5f4ef;color:#182d2b;font:16px/1.6 system-ui}main{max-width:1100px;margin:40px auto;padding:0 24px}h1{font-size:38px;line-height:1.15;max-width:850px}h2{font-size:23px;margin-top:28px}p{max-width:900px}.tag{font:12px monospace;letter-spacing:2px;color:#176d62;text-transform:uppercase}a{color:#176d62}section{border-top:1px solid #cdd5cf;padding-top:20px;margin-top:32px}small{color:#58675f}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:10px 8px;border-bottom:1px solid #d2dcd5}.scroll{overflow-x:auto}select{font:inherit;padding:8px;background:white;border:1px solid #a0ada5}img{width:100%}.note{border-left:3px solid #a05c3b;padding-left:16px}.metric{font-size:25px;font-weight:650;color:#176d62}</style>
<main><div class="tag">Research prototype / experiment 06</div><h1>Can uncertainty adjust as a race unfolds?</h1><p>Pace predictions are identical across all three methods. Only the prediction intervals change. The adaptive method learns from earlier forecast errors for the same driver, without seeing the current or future lap.</p><p><a href="robust-demo.html">Previous point-prediction test</a> · <a href="interval-evaluation.json">Recorded evaluation</a> · <a href="interval-frozen.json">Frozen settings</a> · <a href="interval-validation.svg">Export figure</a></p>
<section><h2>Fresh-race results</h2><div id="headline" class="metric"></div><p id="verdict" class="note"></p><div class="scroll" id="summary"></div><small>Equal-race means. A 90% interval score equals interval width plus 20 times the distance of an observation outside it. Lower is better: a method must balance missed observations against unnecessarily wide intervals.</small><img src="interval-validation.png" alt="Coverage, width and interval-score comparisons across three untouched races"><small>Source: FastF1 Canada, Spain and Austria 2024 race sessions, dry-compound green-flag eligible subsets only. This is not a whole-race or all-weather evaluation. No population-level significance claim.</small></section>
<section><h2>Inspect each race</h2><label>Race <select id="race"></select></label><p id="scope"></p><div class="scroll" id="raceMetrics"></div><h2>First predictions before adaptation</h2><p>The first alphabetical scored driver is shown. Interval widths are chosen before each listed observation; the observed value contributes only to later intervals.</p><div class="scroll" id="trace"></div></section>
<section><h2>What the new method learns</h2><p id="method"></p><p>The static comparator uses the same expanded development data but does not adapt. The original comparator preserves the earlier fixed interval multiplier. This distinguishes the benefit of fresh calibration data from the benefit of online adaptation.</p><p>The method uses empirical absolute forecast errors, not an exact Bayesian likelihood or a coverage-guaranteed procedure. Recent errors from one driver do not update another driver’s intervals.</p></section>
<section><h2>Connection to the paper</h2><p>These are intervals for a future observed lap. They include noise from traffic, driving and other variation. They are not credible intervals for an unknown tyre-degradation parameter. Reliable predictive intervals are useful, but cannot be substituted directly for the belief about degradation in a value-of-information controller.</p><p>We still need to separate learnable tyre uncertainty from observation noise, validate the resulting belief updates, and test decision value under explicit counterfactual assumptions. Three fresh races and retrospective quality control do not establish live strategy benefits.</p></section><p><a href="information-demo.html">Next: what uncertainty can we learn from? →</a></p></main>
<script>const d=__DATA__,el=id=>document.getElementById(id),names={adaptive:'Adaptive intervals',refit_static:'Recalibrated static',original_intervals:'Original static'};
function table(m){return '<table><tr><th>Method</th><th>90% coverage</th><th>Mean width (s)</th><th>Interval score (s) ↓</th></tr>'+Object.entries(m).map(([k,v])=>`<tr><td>${names[k]}</td><td>${(100*v.coverage90).toFixed(1)}%</td><td>${v.mean_width.toFixed(3)}</td><td>${v.interval_score.toFixed(3)}</td></tr>`).join('')+'</table>';}
const a=d.equal_race.adaptive,s=d.equal_race.refit_static,o=d.equal_race.original_intervals;const pct=100*(s.interval_score-a.interval_score)/s.interval_score;el('headline').textContent=d.races.reduce((n,r)=>n+r.metrics.adaptive.n,0).toLocaleString()+' identical point forecasts · three interval methods';el('verdict').textContent=`Adaptive intervals cover ${(100*a.coverage90).toFixed(1)}% on average, versus ${(100*s.coverage90).toFixed(1)}% for recalibrated static and ${(100*o.coverage90).toFixed(1)}% for original static intervals. Their equal-race interval score is ${Math.abs(pct).toFixed(1)}% ${pct>=0?'lower':'higher'} than recalibrated static intervals. Per-race differences remain essential.`;el('summary').innerHTML=table(d.equal_race);
el('race').innerHTML=d.races.map(r=>`<option>${r.event}</option>`).join('');function render(){const r=d.races.find(x=>x.event===el('race').value);el('scope').textContent=`${r.event}: ${r.total_laps} ingested laps; ${r.eligible_laps} pass the historical filters; ${r.metrics.adaptive.n} forecasts remain after per-stint initialization. Mean absolute point error is ${r.metrics.adaptive.mae.toFixed(3)} s for every interval method.`;el('raceMetrics').innerHTML=table(r.metrics);const driver=r.predictions[0].driver,rows=r.predictions.filter(x=>x.driver===driver).slice(0,8);el('trace').innerHTML='<table><tr><th>Driver / lap</th><th>Past scored errors</th><th>Prediction (s)</th><th>Adaptive 90% interval (s)</th><th>Observed (s)</th></tr>'+rows.map(x=>`<tr><td>${x.driver} / ${x.lap}</td><td>${x.prior_error_count}</td><td>${x.predicted.toFixed(3)}</td><td>${x.lower.toFixed(2)} – ${x.upper.toFixed(2)}</td><td>${x.observed.toFixed(3)}</td></tr>`).join('')+'</table>';}
el('race').onchange=render;render();el('method').textContent=`The selected method combines a development-error distribution with the last ${d.selected.window} scored errors from the same driver. The development distribution has the weight of ${d.selected.prior_mass} observations. Driver histories persist across stints within a race and reset at the next race. Settings were frozen before test data was downloaded.`;
</script></html>'''
    (out/'interval-demo.html').write_text(html.replace('__DATA__',json.dumps(d)))
    print('Rendered interval-demo.html and exportable figures')


if __name__=='__main__':main()
