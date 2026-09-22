from pathlib import Path
import json,re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
h=json.loads((ROOT/'results/historical-decisions.json').read_text());recovery=json.loads((ROOT/'results/recovery-study.json').read_text());audit=json.loads((ROOT/'results/history-policy-audit.json').read_text())
central=[next(v for v in e['variants'] if v['nuisance_improvement']==.05 and v['pit_loss']==24) for e in h['events']]
rows=[s for v in central for s in v['decisions']];counts=[len(v['decisions']) for v in central];changes=[sum(s['adaptive_action']!=s['frozen_action'] for s in v['decisions']) for v in central]
metrics=[v['forecast_metrics'] for v in central]
labels=['Great Britain','Hungary','Belgium']
table='| Event | Forecasts | Model MAE (s) | Last-lap MAE (s) | 90% coverage | Decision states | Initial changes |\n|---|---:|---:|---:|---:|---:|---:|\n'
for label,v,count,change in zip(labels,central,counts,changes):
 m=v['forecast_metrics'];table+=f'| {label} | {m["count"]:,} | {m["mae"]:.3f} | {m["last_observation_mae"]:.3f} | {m["coverage90"]*100:.1f}% | {count} | {change} |\n'
mae=np.mean([m['mae'] for m in metrics]);base=np.mean([m['last_observation_mae'] for m in metrics]);coverage=np.mean([m['coverage90'] for m in metrics])
forecasttext=f'The reserved events contain {sum(m["count"] for m in metrics):,} scored forecasts. Equal-event MAE is {mae:.3f} s versus {base:.3f} s for the previous eligible lap, a deterioration of {100*(mae/base-1):.1f}%. The observation model is worse on MAE in every event. Its nominal 90% coverage ranges from 78.2% to 100.0%, with equal-event coverage {coverage*100:.1f}%. The high coverage in Hungary and Belgium accompanies mean interval widths of about 4.34 and 4.41 s; it is not evidence of sharp, well-calibrated predictions. Great Britain contributes only its dry-compound eligible subset, not an all-weather strategy test.'
decisiontext=f'Across {len(rows)} central decision states, the adaptive policy differs initially from the updating frozen-belief policy in {sum(changes)} states ({sum(changes)/len(rows)*100:.2f}%). These are 0/134 in Great Britain, 10/199 in Hungary and 1/193 in Belgium; every difference is an adaptive delay. Central adaptive stop recommendations number 0, 4 and 0, respectively. The mean statewise model advantages are approximately 0.000, 0.218 and 0.060 s. These values are conditional calculations under the assumed model, not historical rewards. At pit loss 24 s, increasing the nuisance correction from 0 to 0.10 s per race lap changes Hungary\'s adaptive stop count from 1 to 20. Against the central assumptions, the joint sensitivity setting g=0.10 and L=18 changes 31 of Hungary\'s 199 recommendations. This dependence is stronger evidence of modelling sensitivity than of a robust racing advantage.'
refined=[]
for e,c in zip(h['events'],central):
 lookup={(s['driver'],s['lap']):s for s in c['decisions']}
 refined += [abs(v['report']['policy_gain']-lookup[v['driver'],v['lap']]['policy_gain']) for v in e['refinements']]
refinement=f'The first 12 central states in each event, selected by the frozen driver-and-lap ordering, are refined from 401 to 1,601 belief points. None of these 36 initial actions changes; the largest gain change is {max(refined):.8f} s. A clearly labelled post-test diagnostic additionally refines the largest central model-gain state in each event and evaluates its policy on 100,000 paired conditional trajectories. All three refined gains fall within the corresponding simulation intervals. The largest grid change in this additional check is {max(abs(c["state"]["policy_gain"]-c["refined"]["policy_gain"]) for c in audit["cases"]):.6f} s. These simulations check the conditional calculation, not the accuracy of the historical observation model.'
r24=[r for r in recovery['results'] if r['observations']==24]
recoverytext='After 24 observations, the matched-model classification accuracy is 99.995%, with Brier score 0.000063. An unmodelled drift of 0.05 reduces accuracy to 99.42%; drift of 0.15 reduces it to 63.76%, with 28.97% of trajectories confidently assigned to the wrong regime. Ten-percent positive contamination yields 97.66% accuracy and 1.32% confidently wrong assignments. Regime recovery under correct assumptions is therefore compatible with severe overconfidence under a plausible class of omitted effects. The magnitude and prevalence of the selected stresses are illustrative, not estimated from Formula One telemetry.'
section=(ROOT/'paper/replay-section.md').read_text()
for key,val in {'__REPLAY_TABLE__':table,'__REPLAY_FORECAST_TEXT__':forecasttext,'__REPLAY_DECISION_TEXT__':decisiontext,'__REPLAY_REFINEMENT_TEXT__':refinement,'__RECOVERY_TEXT__':recoverytext}.items():section=section.replace(key,val)
# Figures are scientific plots, kept as both PNG and SVG.
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(1,2,figsize=(8,3.6),constrained_layout=True);a=axes[0];pos=np.arange(3)
a.bar(pos-.18,[m['mae'] for m in metrics],width=.35,label='Observation model',color='#245b70');a.bar(pos+.18,[m['last_observation_mae'] for m in metrics],width=.35,label='Last eligible lap',color='#ad6a41');a.set_xticks(pos,labels,rotation=18);a.set_ylabel('Mean absolute error (s)');a.legend(fontsize=8)
# Plot Hungary sensitivity, explicitly labelled; all event variants remain in saved outputs.
e=h['events'][1];grid=np.zeros((3,3));lookup={(s['driver'],s['lap']):s['adaptive_action'] for s in central[1]['decisions']}
for v in e['variants']:
 i=[0,.05,.1].index(v['nuisance_improvement']);j=[18.,24.,30.].index(v['pit_loss']);grid[i,j]=sum(s['adaptive_action']!=lookup[s['driver'],s['lap']] for s in v['decisions'])
a=axes[1];a.imshow(grid,cmap='Blues',vmin=0,vmax=35);a.set_xticks(range(3),[18,24,30]);a.set_yticks(range(3),[0,.05,.10]);a.set_xlabel('Assumed pit loss (s)');a.set_ylabel('Assumed pace improvement (s/lap)');a.set_title('Hungary: changed actions / 199',fontsize=9)
for i in range(3):
 for j in range(3):a.text(j,i,str(int(grid[i,j])),ha='center',va='center',color='white' if grid[i,j]>20 else '#183647')
for ext in ['png','svg']:fig.savefig(ROOT/f'paper/figures/v2-historical-replay.{ext}',dpi=250)
plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(8,3.3),constrained_layout=True)
for name,label,color in [('matched','Matched','#176c70'),('drift_0.05','Drift +0.05','#728194'),('drift_0.15','Drift +0.15','#b25435'),('traffic_contamination','10% contamination','#9a8937')]:
 rr=[r for r in recovery['results'] if r['scenario']==name]
 for ax,key in zip(axes,['accuracy','confidently_wrong']):ax.plot([r['observations'] for r in rr],[100*r[key] for r in rr],'-o',ms=4,label=label,color=color)
axes[0].set_ylabel('Regime classification accuracy (%)');axes[1].set_ylabel('Confidently wrong (%)')
for ax in axes:ax.set_xlabel('Observations');ax.set_xticks([4,8,16,24]);ax.grid(alpha=.15)
axes[0].legend(fontsize=7)
for ext in ['png','svg']:fig.savefig(ROOT/f'paper/figures/v2-recovery.{ext}',dpi=250)
plt.close(fig)
text=(ROOT/'paper/manuscript-template.md').read_text()
text=text.replace('Bayesian stopping with uncertain baseline pace and replacement tyres','Bayesian stopping and conditional historical replay').replace('Version 1.0','Version 2.0')
abstract='''A pit stop replaces worn tyres but ends the opportunity to learn about their degradation before committing. We ask when another lap of information justifies delaying that stop. A finite-horizon Bayesian stopping model incorporates two degradation regimes, noisy observations, an unknown persistent baseline and dependent replacement performance. Waiting is optimal when the continuation benefit of learning exceeds the immediate planning disadvantage. Independent replacement uncertainty affects risk-neutral decisions only through its mean. Analytic integration across policy boundaries stabilizes a 2,187-state study: adaptive and updating certainty-equivalent policies differ initially in 319 states, with mean simulated benefit 0.377 seconds. Twenty-four refined cases agree with independent paired simulation. A frozen historical replay evaluates 2,173 forecasts and 526 late-race decision states across three unused events. The adaptive policy delays eleven initial stops, but the observation model predicts worse than a last-lap baseline in every event, and recommendations depend on nuisance assumptions. Synthetic recovery tests demonstrate severe posterior overconfidence under unmodelled trends. Thus learnable, decision-relevant uncertainty can justify waiting within the model, while the historical results do not establish operational savings. The contribution is a reproducible mechanism study, a numerical evaluation correction and a conditional empirical test that exposes the limits of translating uncertainty into strategy.'''
assert len(abstract.split())==200,len(abstract.split())
start=text.index('### Abstract');end=text.index('**Keywords:**',start);text=text[:start]+'### Abstract\n\n'+abstract+'\n\n'+text[end:]
related='''## 2. Related work and contribution

Aguad and Thraves (2024) formulate pit-stop competition as a stochastic feedback Stackelberg game. Their objective concerns strategic interaction between drivers. Our problem removes opponents to isolate information acquired before a final-stop commitment. The accessible publisher and author-preprint abstracts support this distinction; the final article's full text was not available for a complete observation-model audit. We therefore make no claim that previous pit models universally omit learning.

Cappello and Hoegh (2026) model latent tyre performance with Bayesian state-space methods, fuel covariates and pit resets. Their published evaluation spans 19 sessions. Our empirical inference is substantially simpler and is not proposed as a superior forecasting method. The question here is whether a planner should incur another lap's cost because of the decisions enabled by its observation. Forecasting accuracy and that decision value are different targets.

Fieni et al. (2025) jointly optimize energy allocation, wear and pit timing using nonlinear optimization and reinforcement learning. Their Section 4.2 explicitly specifies a fully observable environment, and Section 4.4 deterministic nominal transitions. Our uncertainty is instead a hidden degradation regime inferred from lap observations. This contrast applies to the inspected version and does not imply that learning-based race strategy as a broader field excludes partial observability. The authors' institutional publication record continues to list the work as submitted, so it is cited as a preprint.

Heilmeier et al. (2020) use neural networks to select stops and compounds inside a race simulation. Sasikumar et al. (2025) assess deep-learning pit-decision predictions using classification metrics. These establish relevant simulation and predictive precedents. Reproducing observed decisions or achieving a classification score does not by itself measure the reward of acquiring another observation. We compare two planners sharing the same current belief and actual update rule, so the controlled difference is whether hypothetical future observations enter planning.

Ross, Chaib-draa and Pineau (2007) provide the Bayes-adaptive planning foundation. Harrison and Sunar (2015) study costly learning and investment timing with a binary unknown value. Our waiting condition is an application of established information and stopping principles, not a novel general theorem. Gneiting and Raftery (2007) motivate proper probabilistic scoring; FastF1 contributors (2026) provide the historical timing interface.

The contribution is an inspectable applied characterization of learning before a tyre-replacement commitment. It distinguishes baseline ambiguity from learnable degradation, separates independent replacement variance from cross-set dependence, and shows why deployed certainty-equivalent policy values require careful numerical treatment. The new historical test is deliberately capable of returning a negative result. Its failure of forecast transfer limits the interpretation of favourable conditional policy values. This targeted literature review supports that positioning without establishing priority or claiming an exhaustive search.

'''
a=text.index('## 2.');b=text.index('## 3.',a);text=text[:a]+related+text[b:]
text=text.replace('Historical forecasts supply a separate assessment of observation-model feasibility.','Historical forecasts and a separately frozen three-event conditional decision replay assess the observation-to-decision connection.')
text=text.replace('Main computations use 1,601 equally spaced belief points and 81-point Gauss-Hermite quadrature, with linear interpolation.','Revised main computations use 1,601 equally spaced belief points with analytic integration of affine posterior segments and explicit deployed-policy action boundaries (Appendix A).')
text=text.replace('Each selected state is recomputed using 6,401 belief points and 161 quadrature nodes and evaluated with 50,000 paired trajectories, totaling 1.2 million paired trajectories.','The resulting 24 indices from the original study are fixed before the revised run. Each is recomputed with 3,201 belief points using analytic segment integration and evaluated with 50,000 fresh paired trajectories, totaling 1.2 million pairs.')
text=text.replace('The 47-test suite','The 59-test suite')
start=text.index('### 6.3 Baseline');end=text.index('### 6.4',start)
text=text[:start]+"""### 6.3 Baseline uncertainty and replacement dependence

A matched illustrative comparison on the revised grid holds horizon, age, degradation, noise and pit loss fixed at 8 laps, age 12, rates 0.04/0.30, observation SD 1.5 s and pit loss 18 s, with prior high-regime probability 0.5. For independent replacement performance with mean 0.06, increasing baseline SD from 0 to 3 and 6 s gives gains of 4.389, 1.143 and 0.000 s. The initial adaptive action changes from stay to pit at the last setting. The known replacement at this same mean is analytically equivalent. This is a sensitivity comparison, not an estimated universal threshold.

At baseline SD 3 s, positive and negative replacement dependence yield gains of 1.026 and 1.259 s. Their uncertain replacement marginals are identical at p=0.5; the joint relationship changes both cross-set learning and conditional physical payoffs. It is not purely a manipulation of observation quality. At baseline SD 6 s, negative dependence gives only 0.0093 s. The earlier development rollout for this marginal setting had an interval crossing zero widely, so it does not support a reliably meaningful advantage.

"""+text[end:]
text=text.replace('figures/final-grid.png','figures/v2-final-grid.png').replace('figures/waiting-region.png','figures/v2-waiting-region.png')
text=text.replace('Accordingly, this paper reports historical forecasting feasibility, not leakage-free historical decision replay, empirical oracle regret, or causal pit savings. The failure to achieve the desired predictive coverage and the unresolved as-of-data audit are substantive limits on deployment. They are included in the answer rather than hidden behind favorable synthetic gains.','These preceding results assess forecasting feasibility. The conditional decision replay below adds an explicit inference-to-planning connection, but neither component establishes causal pit savings or resolves retrospective information availability.')
text=text.replace('## 8. Discussion',section+'\n\n## 8. Discussion')
text=text.replace('Grid interpolation and quadrature can affect marginal decisions; the additional calculations probe but do not certify numerical error.','Belief interpolation can affect marginal decisions; analytic integration removes the earlier observation-quadrature error but does not certify all grid values.')
text=text.replace('A practical extension would need a physically interpretable observation model, posterior checks on identifiable latent quantities, event-level validation of the simulator, a documented live-information set and a counterfactual design that does not recycle factual trajectories after policy divergence. Those requirements are not achieved by enlarging the current synthetic grid. The portfolio implementation is useful as an inspectable decision experiment; its interface should retain these distinctions instead of presenting the recommendation as operational advice.','The reserved-event replay supplies a concrete external check and a negative forecasting result. Its 11 initial policy disagreements demonstrate that the mechanism can be activated by historical prefixes under assumed parameters; they do not validate the observation model. Operational extension would require identifiable tyre inference, simulator validation, a documented live-information set, pit-entry timing and a defensible counterfactual design. Increasing numerical precision cannot substitute for those requirements.')
text=text.replace('Historical forecasts provide mixed evidence for the observation component and do not validate real-race strategy improvements.','The reserved-event replay finds 11 initial disagreements among 526 states while exposing poor forecast transfer and sensitivity to nuisance assumptions. It does not validate real-race strategy improvements.')
text=text.replace('## References',(ROOT/'paper/appendix-v2.md').read_text()+'\n\n## References')
# Author-year citations and alphabetically ordered reference entries.
body,refs=text.split('## References',1)
for number,cite in {1:'Aguad and Thraves, 2024',2:'Cappello and Hoegh, 2026',3:'Fieni et al., 2025',4:'Ross et al., 2007',5:'Harrison and Sunar, 2015',6:'Gneiting and Raftery, 2007',7:'FastF1 contributors, 2026'}.items():body=body.replace(f'[{number}]',f'({cite})')
refs=re.sub(r'\[\d+\] ','',refs).strip().split('\n\n')
refs=[r.replace('FastF1 contributors. *FastF1*','FastF1 contributors (2026). *FastF1*') for r in refs]
refs.extend(['Heilmeier, A., Thomaser, A., Graf, M., and Betz, J. (2020). Virtual Strategy Engineer: Using Artificial Neural Networks for Making Race Strategy Decisions in Circuit Motorsport. *Applied Sciences*, 10(21), 7805. https://doi.org/10.3390/app10217805','Sasikumar, A., Leema, A. A., and Balakrishnan, P. (2025). Data-driven pit stop decision support for Formula 1 using deep learning models. *Frontiers in Artificial Intelligence*, 8, 1673148. https://doi.org/10.3389/frai.2025.1673148'])
text=body+'## References\n\n'+'\n\n'.join(sorted(refs))+'\n'
(ROOT/'paper/manuscript-v2-template.md').write_text(text)
(ROOT/'results/replay-summary.json').write_text(json.dumps(dict(forecasts=sum(m['count'] for m in metrics),decision_states=len(rows),initial_changes=sum(changes),equal_event_mae=mae,last_lap_equal_event_mae=base,equal_event_coverage=coverage,main_refinement_max=max(refined)),indent=2))
print('Prepared v2; abstract words',len(abstract.split()))
