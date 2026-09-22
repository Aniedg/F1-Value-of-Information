"""Run with PYTHONPATH=src python3 -m pitvoi.experiment."""
from dataclasses import asdict
from itertools import product
from pathlib import Path
import json
import platform
from pitvoi.model import Scenario, Solver


def main():
    root = Path(__file__).resolve().parents[2]
    out = root / 'results'
    out.mkdir(exist_ok=True)
    rows = []
    for p, accuracy, pit_loss in product((0.1, 0.25, 0.5, 0.75, 0.9),
                                        (0.5, 0.65, 0.8, 0.95, 1.0), (10, 14, 18, 22, 26)):
        s = Scenario(prior_high=p, accuracy=accuracy, pit_loss=pit_loss)
        rows.append(dict(scenario=asdict(s), **Solver(s).report()))
    disagreements = [r for r in rows if r['policies']['adaptive']['action'] != r['policies']['frozen_belief']['action']]
    # This is deliberately an illustrative, selected example, not a test set.
    example = max([r for r in disagreements if r['scenario']['accuracy'] == 0.8] or rows, key=lambda r: r['realized_policy_gain_seconds'])
    result = dict(experiment='synthetic-v0.1', python=platform.python_version(),
                  evaluation='exact enumeration; no Monte Carlo randomness',
                  selection='largest adaptive gain among initial-action disagreements with 80% signal accuracy',
                  scenarios=len(rows), initial_action_disagreements=len(disagreements),
                  example=example, grid=rows)
    (out/'experiment.json').write_text(json.dumps(result, indent=2)+'\n')
    # A self-contained portfolio demo; all displayed numbers come from the run.
    template = '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pit timing · information experiment</title>
<style>body{font:16px/1.6 system-ui;color:#172525;background:#f5f4ef;margin:0}main{max-width:1050px;margin:48px auto;padding:0 24px}h1{font-size:38px;line-height:1.15;max-width:750px}h2{margin-top:36px}small,.muted{color:#586363}.tag{font:12px monospace;letter-spacing:2px;text-transform:uppercase;color:#176d62}section{border-top:1px solid #cdd3cb;margin-top:30px;padding-top:20px}.controls{display:flex;gap:24px;flex-wrap:wrap}label{display:grid;gap:8px}select{font:inherit;padding:8px;background:white;border:1px solid #9aa8a0}table{width:100%;border-collapse:collapse}td,th{text-align:left;border-bottom:1px solid #d8ded7;padding:12px 8px}.number{font-size:36px;color:#176d62;font-weight:600}p{max-width:850px}svg{max-width:100%;height:auto}button{padding:10px 16px;cursor:pointer;background:#176d62;color:white;border:0;font:inherit}</style>
<main><div class="tag">Research prototype / synthetic experiment 01</div>
<h1>When is another lap of information worth the wait?</h1><p><a href="lap-demo.html">Next: learning from noisy lap times and the historical data pilot</a></p>
<p>A minimal Bayesian pit-timing experiment. A car has eight laps left on a tyre set with an unknown low or high degradation rate. Staying out provides a noisy signal; pitting commits to a replacement set with known performance.</p>
<p><strong>This is a mechanism demonstration, not evidence of real F1 time savings.</strong> Parameters are illustrative. No historical race data is used.</p>
<section><h2>Explore the decision</h2><div class="controls">
<label>Probability of high degradation<select id="prior"></select></label>
<label>Signal accuracy<select id="accuracy"></select></label>
<label>Pit loss (seconds)<select id="loss"></select></label></div>
<p><button id="example">Show selected disagreement example</button></p>
<div class="number" id="gain"></div><div>Expected excess time saved by anticipating learning, versus updating without anticipating it.</div>
<div id="table"></div><h2>Expected regret versus a regime-knowing oracle</h2><div id="chart"></div>
<small>Source: exact synthetic-v0.1 experiment; eight remaining laps. Regret is expected excess time minus oracle expected excess time. No historical time range applies.</small>
<p id="values"></p></section>
<section><h2>What this experiment actually tests</h2><p>Both the adaptive and frozen-belief policies update after every observed signal. Only the adaptive policy anticipates those future updates when choosing its current action. The frozen-belief policy and posterior-mean policy coincide here because fixed-schedule costs are linear in degradation.</p>
<p>Only one optional stop remains. After pitting, there are no further decisions, so new-tyre observations have no decision value in this toy problem. Actual lap-time observations, multiple stops, uncertain replacement tyres, traffic and race rules remain future work.</p>
<p id="scope"></p><p>The example button selects the largest gain among initial-action disagreements with 80% signal accuracy. It is an illustrative case, not an out-of-sample estimate.</p></section></main>
<script>const data=__DATA__;
const byId=id=>document.getElementById(id);
for(const [id,key] of [['prior','prior_high'],['accuracy','accuracy'],['loss','pit_loss']]){byId(id).innerHTML=[...new Set(data.grid.map(r=>r.scenario[key]))].map(v=>`<option value="${v}">${v}</option>`).join('');byId(id).onchange=render;}
const names={fixed:'Fixed prior',certainty_equivalent:'Posterior mean',frozen_belief:'Frozen-belief planning',adaptive:'Anticipates learning'};
function render(){const r=data.grid.find(r=>r.scenario.prior_high===+byId('prior').value&&r.scenario.accuracy===+byId('accuracy').value&&r.scenario.pit_loss===+byId('loss').value);byId('gain').textContent=r.realized_policy_gain_seconds.toFixed(3)+' s';
byId('table').innerHTML='<table><thead><tr><th>Policy</th><th>Initial decision</th><th>Expected excess time (s)</th></tr></thead><tbody>'+Object.entries(r.policies).map(([k,v])=>`<tr><td>${names[k]}</td><td>${v.action.toUpperCase()}</td><td>${v.expected_excess_seconds.toFixed(3)}</td></tr>`).join('')+'</tbody></table>';
const max=Math.max(1,...Object.values(r.policies).map(v=>v.regret_seconds));
byId('chart').innerHTML='<svg role="img" aria-label="Horizontal bar chart of expected regret in seconds by policy" viewBox="0 0 900 250"><text x="0" y="18" fill="#586363">Policy</text>'+Object.entries(r.policies).map(([k,v],i)=>`<text x="0" y="${55+i*40}" fill="#172525">${names[k]}</text><rect x="225" y="${37+i*40}" width="${Math.max(0,v.regret_seconds)/max*550}" height="24" fill="${k==='adaptive'?'#176d62':'#929e98'}"/><text x="${235+Math.max(0,v.regret_seconds)/max*550}" y="${55+i*40}" fill="#172525">${v.regret_seconds.toFixed(3)}</text>`).join('')+`<line x1="225" y1="204" x2="775" y2="204" stroke="#929e98"/><text x="225" y="225">0</text><text x="750" y="225">${max.toFixed(2)}</text><text x="360" y="248">Expected regret (seconds; lower is better)</text></svg>`;
byId('values').textContent=`At this state: pit now ${r.action_values.pit_seconds.toFixed(3)} s; stay with frozen-belief planning ${r.action_values.stay_frozen_seconds.toFixed(3)} s; stay anticipating learning ${r.action_values.stay_adaptive_seconds.toFixed(3)} s. These action values include future excess time, not just the next lap.`;}
function example(){byId('prior').value=data.example.scenario.prior_high;byId('accuracy').value=data.example.scenario.accuracy;byId('loss').value=data.example.scenario.pit_loss;render();}byId('example').onclick=example;
byId('scope').textContent=`The grid contains ${data.scenarios} scenarios; ${data.initial_action_disagreements} have different initial actions. Current tyre age: 12 laps. Low/high degradation: 0.04/0.30 seconds per lap of tyre age. Replacement degradation: 0.06. No common base lap time is included.`;example();</script></html>'''
    (out/'demo.html').write_text(template.replace('__DATA__', json.dumps(result)))
    print(json.dumps({k:v for k,v in result.items() if k != 'grid'}, indent=2))


if __name__ == '__main__':
    main()
