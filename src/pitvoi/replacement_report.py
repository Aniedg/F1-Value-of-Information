"""Display the saved replacement-uncertainty study, including null results."""
import json,os
from pathlib import Path
import numpy as np


def main():
    root=Path(__file__).resolve().parents[2];out=root/'results'
    d=json.loads((out/'replacement-experiment.json').read_text())
    os.environ.setdefault('MPLCONFIGDIR',str(root/'.mplconfig'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,3,figsize=(14,4.7),constrained_layout=True)
    labels=['Known','Independent','Move\ntogether','Move\noppositely']
    for ax,tau in zip(axes,[0,3,6]):
        rows=[c for c in d['cases'] if c['offset_sd']==tau];x=np.arange(4)
        ax.plot(x-.07,[r['report']['policy_gain'] for r in rows],'o',color='#176d62',label='Numerical expectation')
        ax.errorbar(x+.07,[r['rollout']['gain'] for r in rows],yerr=[1.96*r['rollout']['paired_standard_error'] for r in rows],fmt='s',color='#b7683c',capsize=3,label='Paired rollout + 95% interval')
        ax.axhline(0,color='#888',ls='--',lw=.8);ax.set_xticks(x,labels);ax.set_title(f'Baseline SD = {tau} s')
        ax.set_ylabel('Frozen-policy cost − adaptive cost (s)');ax.legend(fontsize=8)
    fig.suptitle('Same prior replacement mean · uncertain cases share the same marginal distribution\nSynthetic development results; each panel uses its own vertical scale',fontsize=12)
    fig.savefig(out/'replacement-validation.png',dpi=180);fig.savefig(out/'replacement-validation.svg');plt.close(fig)
    html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Pit timing · uncertain replacement tyres</title>
<style>body{margin:0;background:#f5f4ef;color:#182d2b;font:16px/1.6 system-ui}main{max-width:1120px;margin:40px auto;padding:0 24px}h1{font-size:40px;line-height:1.16;max-width:900px}h2{font-size:24px;margin-top:30px}a{color:#176d62}.tag{font:12px monospace;letter-spacing:2px;color:#176d62}section{border-top:1px solid #ccd4cd;margin-top:30px;padding-top:12px}.cards{display:flex;gap:16px;flex-wrap:wrap}.card{flex:1;min-width:190px;background:white;padding:20px;border-radius:12px}.number{font-size:32px;font-weight:650}select{font:inherit;padding:9px;margin:8px}table{border-collapse:collapse;width:100%;font-size:14px}td,th{text-align:left;padding:10px;border-bottom:1px solid #ddd}.scroll{overflow:auto}.note{background:#e5eae4;padding:18px;border-radius:8px}img{width:100%;height:auto}</style>
<main><a href="nuisance-demo.html">← Unknown baseline experiment</a><p class="tag">EXPERIMENT 09 · REPLACEMENT TYRE UNCERTAINTY</p><h1>What can the current tyres tell us about the next set?</h1>
<p>Uncertainty alone does not necessarily change the pit strategy. What matters here is whether current observations change our expectations of the replacement tyres.</p>
<p class="note">Independent uncertainty gives exactly the same policies and expected costs as known replacement performance at the same mean. This is a structural result for linear costs, expected-time optimisation and one final stop—not a claim about risk-sensitive or full-race strategy.</p>
<img src="replacement-validation.png" alt="Known and independent replacement cases have identical numerical gains. Positive and negative dependence give different gains, while high baseline uncertainty leaves little or no gain.">
<p><a href="replacement-validation.svg">Export figure</a> · <a href="replacement-experiment.json">Download all results and source hashes</a></p>
<section><h2>Inspect the relationship</h2><label for="offset">Baseline SD:</label><select id="offset"><option value="0">0 s</option><option value="3" selected>3 s</option><option value="6">6 s</option></select>
<label for="relationship">Replacement performance:</label><select id="relationship"><option value="known">Known degradation</option><option value="independent" selected>Independent of old tyres</option><option value="positive">Tends to move together</option><option value="negative">Tends to move oppositely</option></select><div id="summary"></div>
<h2>What do observations update?</h2><div id="belief"></div><p>Rates are seconds per lap of tyre age. All cases have prior expected replacement degradation 0.060. The three uncertain cases each put 50% on 0.020 and 50% on 0.100 before observing anything; only their dependence on the old set changes.</p>
<div id="precision"></div></section>
<section><h2>What if we assume the wrong relationship?</h2><p>Actual tyres tend to move together, and actual baseline SD is 3 s. Each row gives both policies the same assumed relationship, then evaluates them on identical physical trajectories.</p><div class="scroll" id="stress"></div><p>Each row compares adaptive versus updating frozen-belief under that row’s assumption. It is not a direct estimate of the cost of misspecification relative to the correctly specified adaptive policy.</p></section>
<section><h2>Scope of the conclusion</h2><p>There is one optional last stop, with no later decisions about the replacement set. The shared baseline remains constant. We minimise expected time and evaluate actual sampled replacement degradation in the simulations. The assumed relationships are illustrative and have not been estimated from race data.</p><p>We report separate oracles knowing the old regime and knowing both tyre regimes. Their costs happen to coincide for these selected states; that equivalence is not assumed generally. Forecast quality, posterior calibration and historical policy benefit remain separate questions.</p><p class="note">At baseline SD 6 s, opposite movement gives only about 0.01 s of predicted gain and its simulation interval crosses zero. The nominal “stay” recommendation there is a marginal model result, not evidence of a practically reliable advantage.</p><p>47 tests pass. Historical decision replay and the final frozen study remain outstanding. No real-race time saving or novelty claim is established.</p></section></main>
<script>const d=__DATA__,el=id=>document.getElementById(id),f=x=>x.toFixed(3),names={known:'Known',independent:'Independent',positive:'Move together',negative:'Move oppositely'};
function render(){let c=d.cases.find(x=>x.offset_sd===+el('offset').value&&x.name===el('relationship').value),r=c.report,m=c.rollout,s=c.replacement;el('summary').innerHTML=`<div class="cards"><div class="card">Expected policy gain<div class="number">${f(r.policy_gain)} s</div>Numerical expectation</div><div class="card">Adaptive first action<div class="number">${r.adaptive_action}</div>Frozen-belief planner: ${r.frozen_action}</div><div class="card">Paired simulation<div class="number">${f(m.gain)} s</div>95% interval: ${m.gain_95_ci.map(f).join(' to ')} s</div></div><p>Expected adaptive cost ${f(r.adaptive_cost)} s; frozen-policy cost ${f(r.frozen_policy_cost)} s. Both-regime oracle ${f(r.joint_oracle_cost)} s; old-regime-only oracle ${f(r.old_regime_oracle_cost)} s.</p>`;
let low=s.low+(s.high-s.low)*s.high_given_old_low,high=s.low+(s.high-s.low)*s.high_given_old_high;
el('belief').innerHTML=`<div class="scroll"><table><tr><th>Belief about old tyres</th><th>Expected replacement degradation</th></tr><tr><td>Old regime known to be low degradation</td><td>${f(low)}</td></tr><tr><td>Equal old-regime probabilities (initial belief)</td><td>${f((low+high)/2)}</td></tr><tr><td>Old regime known to be high degradation</td><td>${f(high)}</td></tr></table></div>`;
el('precision').innerHTML=`<p>Resolution check, expected gains: ${[c.coarse_report,c.report,...(c.dense_report?[c.dense_report]:[])].map(x=>f(x.policy_gain)).join(' → ')} s. Base: 1,601/41; main: 3,201/81${c.dense_report?'; additional: 6,401/161':''} belief points/quadrature nodes. Differences are diagnostics, not certified error bounds. Each rollout uses 30,000 paired trajectories and the main-resolution policies.</p>`;}
el('stress').innerHTML='<table><tr><th>Assumed relationship</th><th>Adaptive cost (s)</th><th>Gain (s)</th><th>95% paired interval (s)</th></tr>'+d.stress.map(x=>`<tr><td>${names[x.assumed]}</td><td>${f(x.adaptive_cost)}</td><td>${f(x.gain)}</td><td>${x.gain_95_ci.map(f).join(' to ')}</td></tr>`).join('')+'</table>';el('offset').onchange=render;el('relationship').onchange=render;render();</script></html>'''
    (out/'replacement-demo.html').write_text(html.replace('__DATA__',json.dumps(d)))

if __name__=='__main__':main()
