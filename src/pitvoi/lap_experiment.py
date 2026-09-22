"""Reproduce continuous-observation experiments and a self-contained demo."""
from dataclasses import asdict
import json
import os
from pathlib import Path
import platform
import numpy as np
from pitvoi.gaussian import LapScenario, LapSolver, calibration, predictive_quantile, update


def observed_trace(s, seed=42):
    rng = np.random.default_rng(seed)
    p, trace = s.prior_high, []
    theta = s.low  # Fixed illustrative trace, not used to estimate policy gain.
    for t in range(s.laps):
        age = s.age+t
        baseline, fuel, track = 90.0, 2-0.04*t, -0.015*t
        correction = baseline+fuel+track
        lo, hi = predictive_quantile(p, age, s, 0.05), predictive_quantile(p, age, s, 0.95)
        observed = correction+age*theta+rng.normal(0, s.noise_sd)
        post = float(update(p, observed-correction, age, s))
        trace.append(dict(lap=t+1, age=age, observed_seconds=observed,
                          known_correction_seconds=correction,
                          predicted_seconds=correction+age*((1-p)*s.low+p*s.high),
                          prediction_low=correction+float(lo), prediction_high=correction+float(hi),
                          prior_high=p, posterior_high=post))
        p = post
    return dict(seed=seed, true_degradation=theta, rows=trace,
                interpretation='Fixed low-regime observation-only trace; not a policy rollout. Corrections are known synthetic inputs.')


def main():
    root = Path(__file__).resolve().parents[2]
    out = root/'results'
    out.mkdir(exist_ok=True)
    runs = []
    for sigma in (0.5, 1.0, 1.5, 2.5, 4.0):
        s = LapScenario(noise_sd=sigma)
        solver = LapSolver(s, grid_size=1601, quadrature=41)
        fine = LapSolver(s, grid_size=3201, quadrature=81)
        report, finer = solver.report(), fine.report()
        runs.append(dict(scenario=asdict(s), report=report,
                         numerical_check=dict(grid_size=3201, quadrature=81,
                           adaptive_cost_change=abs(report['adaptive_cost']-finer['adaptive_cost']),
                           frozen_policy_cost_change=abs(report['frozen_policy_cost']-finer['frozen_policy_cost'])),
                         rollout=solver.monte_carlo(), calibration=calibration(s), trace=observed_trace(s)))
    s = LapScenario()
    stress = dict(assumed_noise_sd=s.noise_sd, actual_noise_sd=3.0,
                  calibration=calibration(s, actual_noise_sd=3.0),
                  rollout=LapSolver(s).monte_carlo(actual_noise_sd=3.0))
    result = dict(experiment='continuous-laps-v0.2', python=platform.python_version(),
                  numpy=np.__version__, grid_size=1601, quadrature=41,
                  regimes='two fixed latent degradation rates; continuous noisy observations',
                  runs=runs, stress=stress)
    (out/'lap-experiment.json').write_text(json.dumps(result, indent=2)+'\n')
    os.environ.setdefault('MPLCONFIGDIR', str(root/'.mplconfig'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), constrained_layout=True)
    xs = [r['scenario']['noise_sd'] for r in runs]
    axes[0].plot(xs, [r['report']['policy_gain'] for r in runs], 'o-', color='#176d62', label='Numerical planning')
    axes[0].errorbar(xs, [r['rollout']['gain'] for r in runs],
                    yerr=[1.96*r['rollout']['paired_standard_error'] for r in runs],
                    fmt='x', color='#263b45', label='Paired rollout, 95% CI')
    axes[0].set(xlabel='Observation noise SD (seconds)', ylabel='Expected time saved (seconds)', title='Anticipating learning vs frozen planning')
    axes[0].legend(fontsize=8)
    for rows, label, color in ((runs[2]['calibration']['by_lap'], 'Correct noise model', '#176d62'),
                               (stress['calibration']['by_lap'], 'Actual noise doubled', '#a25136')):
        axes[1].plot([r['observations'] for r in rows], [r['predictive_90_coverage'] for r in rows], 'o-', label=label, color=color)
    axes[1].axhline(0.9, color='#888888', linestyle='--', label='Nominal 90%')
    axes[1].set(xlabel='Predicted observation number (lap)', ylabel='Predictive interval coverage (fraction)',
                ylim=(0.4, 1), title='Does the model know its uncertainty?')
    axes[1].legend(fontsize=8)
    rows = runs[2]['trace']['rows']
    t = [r['lap'] for r in rows]
    axes[2].fill_between(t, [r['prediction_low'] for r in rows], [r['prediction_high'] for r in rows], color='#176d62', alpha=.15, label='90% predictive interval')
    axes[2].plot(t, [r['observed_seconds'] for r in rows], 'o-', color='#263b45', label='Observed synthetic lap')
    axes[2].set(xlabel='Observation number (lap)', ylabel='Lap time (seconds)', title='Predict first, then observe and update')
    axes[2].legend(fontsize=8)
    fig.suptitle('Synthetic lap-time experiment · known pace corrections · two latent degradation regimes', fontsize=12)
    fig.savefig(out/'lap-experiment.png', dpi=180)
    fig.savefig(out/'lap-experiment.svg')
    plt.close(fig)
    build_demo(root, result)
    print(json.dumps(dict(runs=[dict(noise=r['scenario']['noise_sd'], gain=r['report']['policy_gain'],
                            ci=r['rollout']['gain_95_ci'], convergence=r['numerical_check']) for r in runs],
                         correct_coverage=[r['predictive_90_coverage'] for r in runs[2]['calibration']['by_lap']],
                         misspecified_coverage=[r['predictive_90_coverage'] for r in stress['calibration']['by_lap']]), indent=2))


def build_demo(root, result):
    historical_path = root/'results/historical-pilot.json'
    historical = json.loads(historical_path.read_text()) if historical_path.exists() else None
    template = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Pit timing · learning from lap times</title>
<style>body{margin:0;background:#f5f4ef;color:#182d2b;font:16px/1.6 system-ui}main{max-width:1080px;margin:40px auto;padding:0 24px}h1{font-size:38px;line-height:1.15;max-width:850px}h2{font-size:23px;margin-top:32px}p{max-width:880px}.tag{font:12px monospace;letter-spacing:2px;color:#176d62;text-transform:uppercase}a{color:#176d62}section{border-top:1px solid #ced6d0;margin-top:32px;padding-top:20px}label{display:block;margin:16px 0}select{font:inherit;padding:8px;border:1px solid #9ba9a2;background:white}.metric{font-size:34px;font-weight:650;color:#176d62}small{color:#57655f}table{width:100%;border-collapse:collapse}td,th{padding:10px 8px;text-align:left;border-bottom:1px solid #d5ddd7}.scroll{overflow-x:auto}img{width:100%}input{width:280px;max-width:100%}.note{border-left:3px solid #176d62;padding-left:16px}svg{width:100%;height:auto}</style>
<main><div class="tag">Research prototype / experiment 02</div><h1>Learning tyre behaviour from noisy lap times</h1>
<p>The controller now sees a measured lap time and updates its belief using a Gaussian observation model. It asks whether the next observation could change a later pit decision.</p>
<p class="note"><strong>Synthetic policy results.</strong> The two degradation regimes and known pace corrections remain simplifying assumptions. Historical data below is a feasibility pilot, not validation of these time savings.</p>
<p><a href="forecast-demo.html">Next: the first held-out race test</a> · <a href="demo.html">Experiment 01: binary signals</a> · <a href="lap-experiment.json">Download experiment results</a> · <a href="lap-experiment.svg">Export figure</a></p>
<section><h2>How much does observation quality matter?</h2><label>Lap-time noise standard deviation (seconds) <select id="noise"></select></label><div id="gain" class="metric"></div><p id="decision"></p><p id="check"></p>
<small>Gain compares two policies that both update after observed laps. Only one anticipates future learning. Rollouts use 20,000 paired synthetic trajectories; intervals describe Monte Carlo uncertainty under the assumed model.</small>
<h2>Watch the belief update</h2><p>Illustrative eight-lap observation sequence with true low degradation. This trace keeps observing regardless of pit decisions. Baseline, fuel and track corrections are synthetic and known exactly.</p>
<label>Observations revealed: <strong id="stepLabel"></strong><br><input id="step" type="range" min="1" max="8" value="1"></label>
<div id="belief" class="metric"></div><div class="scroll" id="trace"></div>
<small>Prediction intervals are computed before observing each lap. Future observations never enter earlier updates.</small></section>
<section><h2>Calibration and independent checks</h2><img src="lap-experiment.png" alt="Three charts compare learning benefit by noise, prediction interval coverage under correct and doubled noise, and one synthetic lap sequence"><p id="calibration"></p><small>Source: continuous-laps-v0.2 synthetic experiment. Coverage uses 10,000 independent sequences. The doubled-noise case deliberately violates the model. All results are conditional on the stated assumptions.</small></section>
<div id="historical"></div>
<section><h2>The next research hurdle</h2><p>In real data, fuel burn, track evolution, warm-up, traffic and tyre degradation all affect lap time. Within a stint, tyre age and race lap advance together, so a fitted slope alone cannot separate their effects. Next we need a defensible observation model with explicit assumptions and held-out predictive checks before attaching strategy claims to real races.</p></section></main>
<script>const data=__DATA__, historical=__HISTORICAL__;
const el=id=>document.getElementById(id);el('noise').innerHTML=data.runs.map(r=>`<option value="${r.scenario.noise_sd}">${r.scenario.noise_sd.toFixed(1)}</option>`).join('');el('noise').value='1.5';
function render(){const r=data.runs.find(r=>r.scenario.noise_sd===+el('noise').value), n=+el('step').value;el('gain').textContent=r.report.policy_gain.toFixed(3)+' seconds expected gain';el('decision').textContent=`Initial decision: frozen-belief planning ${r.report.frozen_action.toUpperCase()}; anticipating learning ${r.report.adaptive_action.toUpperCase()}. Pit now costs ${r.report.pit_cost.toFixed(3)} excess seconds.`;el('check').textContent=`Independent rollout gain: ${r.rollout.gain.toFixed(3)} s (95% interval ${r.rollout.gain_95_ci.map(v=>v.toFixed(3)).join(' to ')} s). Refining the numerical solver changes adaptive cost by ${r.numerical_check.adaptive_cost_change.toFixed(4)} s.`;el('stepLabel').textContent=n;el('belief').textContent=(100*r.trace.rows[n-1].posterior_high).toFixed(1)+'% probability of high degradation';el('trace').innerHTML='<table><tr><th>Lap</th><th>Observed (s)</th><th>Pre-lap 90% interval (s)</th><th>Updated P(high)</th></tr>'+r.trace.rows.slice(0,n).map(x=>`<tr><td>${x.lap}</td><td>${x.observed_seconds.toFixed(2)}</td><td>${x.prediction_low.toFixed(2)} – ${x.prediction_high.toFixed(2)}</td><td>${(100*x.posterior_high).toFixed(1)}%</td></tr>`).join('')+'</table>';}
el('noise').onchange=render;el('step').oninput=render;render();const coverage=rows=>rows.map(r=>100*r.predictive_90_coverage);const correct=coverage(data.runs[2].calibration.by_lap), wrong=coverage(data.stress.calibration.by_lap);el('calibration').textContent=`With the correct noise model, nominal 90% intervals cover ${Math.min(...correct).toFixed(1)}–${Math.max(...correct).toFixed(1)}% across the eight prediction steps. When actual noise doubles, coverage drops to ${Math.min(...wrong).toFixed(1)}–${Math.max(...wrong).toFixed(1)}%. These are synthetic calibration checks, not real-race validation.`;
if(historical){const h=historical, rows=h.display_laps;const xmin=Math.min(...rows.map(r=>r.lap)),xmax=Math.max(...rows.map(r=>r.lap)), ymin=Math.floor(Math.min(...rows.map(r=>r.seconds)))-1,ymax=Math.ceil(Math.max(...rows.map(r=>r.seconds)))+1;const x=v=>70+(v-xmin)/(xmax-xmin||1)*800,y=v=>260-(v-ymin)/(ymax-ymin)*200;const ticks=[0,.25,.5,.75,1];el('historical').innerHTML=`<section><div class="tag">Historical ingestion pilot</div><h2>2024 Bahrain Grand Prix</h2><p><strong>${h.eligible_laps} of ${h.total_laps} laps pass the initial filters</strong>, across ${h.eligible_stints} stints. All ${h.drivers} drivers were ingested. This event was selected before download; it is development data, not a held-out test.</p><h2>${h.display_driver}: eligible observed lap times</h2><p>The displayed driver is the first alphabetically. Raw pace is shown without claiming it measures tyre degradation.</p><svg viewBox="0 0 920 325" role="img" aria-label="Historical eligible lap times in seconds by race lap">${ticks.map(f=>{const v=ymin+(ymax-ymin)*f;return `<line x1="70" x2="870" y1="${y(v)}" y2="${y(v)}" stroke="#d5ddd7"/><text x="22" y="${y(v)+5}">${v.toFixed(1)}</text>`}).join('')}${ticks.map(f=>{const v=xmin+(xmax-xmin)*f;return `<text x="${x(v)-8}" y="282">${v.toFixed(0)}</text>`}).join('')}${rows.map(r=>`<circle cx="${x(r.lap)}" cy="${y(r.seconds)}" r="4" fill="#176d62"><title>Lap ${r.lap}, ${r.seconds.toFixed(3)} s, ${r.compound}</title></circle>`).join('')}<text x="365" y="315">Race lap (number)</text><text x="15" y="25">Lap time (seconds)</text></svg><small>Source: FastF1 ${h.fastf1_version}, 2024 Bahrain race. No pit laps, non-green laps, non-dry compounds, first laps, generated or inaccurate timings. Retrospective quality flags may not have been available live. Traffic remains unfiltered.</small><p><a href="historical-pilot.json">Provenance, exclusion counts and stint inventory</a></p></section>`;}
</script></html>'''
    (root/'results/lap-demo.html').write_text(template.replace('__DATA__', json.dumps(result)).replace('__HISTORICAL__', json.dumps(historical)))


if __name__ == '__main__':
    main()
