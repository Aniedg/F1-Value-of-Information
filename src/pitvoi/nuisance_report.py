"""Render the saved shared-baseline decision study without refitting."""
import json
import os
from pathlib import Path
import numpy as np


def main():
    root=Path(__file__).resolve().parents[2];out=root/'results'
    d=json.loads((out/'nuisance-experiment.json').read_text())
    os.environ.setdefault('MPLCONFIGDIR',str(root/'.mplconfig'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(12,4.8),constrained_layout=True)
    cases=d['cases'];x=np.array([c['offset_sd'] for c in cases])
    axes[0].plot(x,[c['fine_report']['policy_gain'] for c in cases],color='#176d62',marker='o',label='Numerical expected gain')
    axes[0].errorbar(x+.07,[c['rollout']['gain'] for c in cases],yerr=[1.96*c['rollout']['paired_standard_error'] for c in cases],fmt='s',color='#b7683c',capsize=4,label='Paired rollout + 95% interval')
    axes[0].set_xticks(x,[str(c['offset_sd']) for c in cases]);axes[0].set(xlabel='Assumed = actual baseline SD (s)',ylabel='Frozen-policy cost − adaptive cost (s)',title='Correctly modelling the unknown baseline')
    axes[0].legend(fontsize=8)
    stress=d['stress'];x=np.array([c['assumed_offset_sd'] for c in stress])
    axes[1].errorbar(x,[c['gain'] for c in stress],yerr=[1.96*c['paired_standard_error'] for c in stress],fmt='o',color='#b7683c',capsize=5)
    axes[1].set_xticks(x,[str(c['assumed_offset_sd']) for c in stress]);axes[1].set(xlabel='Assumed baseline SD (s); actual SD = 6 s',ylabel='Paired rollout gain (s), with 95% interval',title='Ignoring baseline uncertainty can hurt')
    for ax in axes:ax.axhline(0,color='#777777',linestyle='--',linewidth=.8)
    fig.suptitle('Synthetic shared-baseline model · 8 laps remaining · pit loss 18 s',fontsize=12)
    fig.savefig(out/'nuisance-validation.png',dpi=180);fig.savefig(out/'nuisance-validation.svg');plt.close(fig)
    html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Pit timing · uncertain baseline</title>
<style>body{margin:0;background:#f5f4ef;color:#182d2b;font:16px/1.6 system-ui}main{max-width:1100px;margin:40px auto;padding:0 24px}h1{font-size:40px;line-height:1.16;max-width:900px}h2{font-size:24px;margin-top:30px}a{color:#176d62}.tag{font:12px monospace;letter-spacing:2px;color:#176d62}section{border-top:1px solid #ccd4cd;margin-top:30px;padding-top:12px}.cards{display:flex;gap:16px;flex-wrap:wrap}.card{flex:1;min-width:200px;background:white;padding:20px;border-radius:12px}.number{font-size:32px;font-weight:650}select{font:inherit;padding:9px}table{border-collapse:collapse;width:100%;font-size:14px}td,th{text-align:left;padding:10px;border-bottom:1px solid #ddd}.scroll{overflow:auto}.note{background:#e5eae4;padding:18px;border-radius:8px}img{width:100%;height:auto}</style>
<main><a href="information-demo.html">← Uncertainty versus learning</a><p class="tag">EXPERIMENT 08 · SYNTHETIC DECISION STUDY</p><h1>When baseline pace is uncertain, waiting can lose its value.</h1>
<p>A slow lap may indicate worn tyres, or a car that is simply slower than expected. The planner now accounts for both possibilities. All policies receive the same observations and use the same assumed model.</p>
<img src="nuisance-validation.png" alt="Expected gains decrease as shared baseline uncertainty increases. Ignoring a true 6-second baseline standard deviation gives a small negative simulated gain.">
<p><a href="nuisance-validation.svg">Export figure</a> · <a href="nuisance-experiment.json">Download results and source hashes</a></p>
<section><h2>Inspect a baseline assumption</h2><label for="offset">Baseline uncertainty (standard deviation): </label><select id="offset"><option value="0">0 s — known baseline</option><option value="1">1.5 s</option><option value="2">3 s</option><option value="3" selected>6 s</option></select><div id="summary"></div>
<h2>Does learning outweigh the cost of delay?</h2><div id="condition"></div><p>The margin is the frozen planner’s predicted disadvantage of staying. Learning changes “pit” to “stay” only when the continuation benefit exceeds that margin. This benefit differs from the gain against the deployed policy.</p>
<h2>What if the pit loss changes?</h2><div class="scroll" id="sweep"></div><p>All 24 development-grid cases are retained. This table uses the base numerical resolution; the main result above uses the finest resolution.</p></section>
<section><h2>What if the model gets baseline uncertainty wrong?</h2><p>Here the actual baseline SD is always 6 s. Both policies use the listed assumed SD. Positive gain favors the adaptive policy; negative gain means waiting made it worse.</p><div class="scroll" id="stress"></div><p>30,000 paired trajectories per case, with shared random draws across assumptions. Intervals describe simulation sampling uncertainty, not model validity or generalization to races. The stress policies use the intermediate numerical resolution.</p></section>
<section><h2>Why this model can be solved</h2><p>The unknown baseline is constant and shared by both tyre sets. Over the fixed remaining race, its time cost is identical for every strategy and cancels in comparisons. It still obscures the observations used to learn degradation. We integrate it out with a conditional Gaussian update; this preserves a one-dimensional decision belief.</p><p class="note">This does not cover tyre-specific offsets, changing track pace, uncertain replacement degradation, traffic, fuel-model error, or another decision after the stop. The 6 s uncertainty is illustrative, not fitted to historical data. Zero gain here means both policies pit immediately at this state; it does not mean information is worthless everywhere.</p>
<p>The paper now has a tested unknown-baseline extension. Historical decision replay and final frozen evaluation remain outstanding. No real-race time saving or novelty claim is established.</p></section><p><a href="replacement-demo.html">Next: learning about replacement tyres →</a></p></main>
<script>const d=__DATA__,el=id=>document.getElementById(id),f=x=>x.toFixed(3);
function render(){let c=d.cases[+el('offset').value],r=c.fine_report,m=c.rollout,b=c.decomposition;el('summary').innerHTML=`<div class="cards"><div class="card">Expected policy gain<div class="number">${f(r.policy_gain)} s</div>With correctly specified uncertainty</div><div class="card">Adaptive first action<div class="number">${r.adaptive_action}</div>Frozen-belief planner: ${r.frozen_action}</div><div class="card">Paired simulation<div class="number">${f(m.gain)} s</div>95% interval: ${m.gain_95_ci.map(f).join(' to ')} s</div></div><p>Expected costs: adaptive ${f(r.adaptive_cost)} s; updating frozen-belief policy ${f(r.frozen_policy_cost)} s; known-regime oracle ${f(r.oracle_cost)} s. Costs omit the common baseline.</p><p>Refinement gains: ${[c.report,c.refined_report,c.fine_report].map(v=>f(v.policy_gain)).join(' → ')} s (1,601/41 → 3,201/81 → 6,401/161 belief points/quadrature nodes). Resolution differences are diagnostics, not certified error bounds.</p>`;
el('condition').innerHTML=`<p class="note">Waiting margin: <strong>${f(b.margin)} s</strong> · continuation learning benefit: <strong>${f(b.learning_benefit)} s</strong> · net advantage of staying versus pitting now: <strong>${f(b.adaptive_wait_advantage)} s</strong>.</p>`;
el('sweep').innerHTML='<table><tr><th>Pit loss (s)</th><th>Adaptive</th><th>Frozen-belief</th><th>Expected gain (s)</th></tr>'+c.sweep.map(x=>`<tr><td>${x.pit_loss}</td><td>${x.adaptive_action}</td><td>${x.frozen_action}</td><td>${f(x.policy_gain)}</td></tr>`).join('')+'</table>';}
el('stress').innerHTML='<table><tr><th>Assumed baseline SD (s)</th><th>Simulation gain (s)</th><th>95% paired interval (s)</th></tr>'+d.stress.map(x=>`<tr><td>${x.assumed_offset_sd}</td><td>${f(x.gain)}</td><td>${x.gain_95_ci.map(f).join(' to ')}</td></tr>`).join('')+'</table>';el('offset').onchange=render;render();</script></html>'''
    (out/'nuisance-demo.html').write_text(html.replace('__DATA__',json.dumps(d)))

if __name__=='__main__':main()
