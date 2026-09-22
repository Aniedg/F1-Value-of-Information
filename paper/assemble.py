"""Assemble manuscript text and scientific figures from recorded outputs."""
import json,os
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.mplconfig'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    d=json.loads((ROOT/'results/final-study.json').read_text());rows=d['states'];n=len(rows)
    gains=np.array([x['policy_gain'] for x in rows]);flip=np.array([x['adaptive_action']!=x['frozen_action'] for x in rows])
    near=np.array([abs(x['waiting_margin'])<=1 for x in rows]);material=gains>.05
    means={k:float(np.mean([x[k] for x in rows])) for k in ['fixed_prior_cost','frozen_policy_cost','adaptive_cost','joint_oracle_cost']}
    validations=d['validations'];diff=np.array([abs(v['refined']['policy_gain']-rows[v['index']]['policy_gain']) for v in validations])
    changed=sum(v['refined']['adaptive_action']!=rows[v['index']]['adaptive_action'] for v in validations)
    check95=sum(v['rollout']['gain_95_ci'][0]<=v['refined']['policy_gain']<=v['rollout']['gain_95_ci'][1] for v in validations)
    selected_nonzero=sum(v['rollout']['paired_standard_error']>0 for v in validations)
    audit=json.loads((ROOT/'results/final-study-numerical-audit.json').read_text());worst=audit['cases'][0]
    mc=worst['rollout']
    overall=(f'The adaptive and updating frozen-belief policies select different initial actions in {flip.sum():,} of {n:,} states ({100*flip.mean():.2f}%). '
             f'Every recorded disagreement is an adaptive delay of a stop chosen by the frozen planner. '
             f'The mean numerical gain is {gains.mean():.3f} s, the median is {np.median(gains):.3f} s, and the maximum is {gains.max():.3f} s. '
             f'{material.sum():,} states ({100*material.mean():.2f}%) exceed the declared 0.05 s reporting threshold. '
             'These comparisons include zero-gain states; the largest gain is an extreme of the chosen grid, not a representative effect size.')
    table='| Policy | Mean cost (s) | Mean full-oracle regret (s) |\n|---|---:|---:|\n'
    for key,label in [('fixed_prior_cost','Fixed prior'),('frozen_policy_cost','Updating frozen belief'),('adaptive_cost','Adaptive'),('joint_oracle_cost','Full-information oracle')]:
        table+=f'| {label} | {means[key]:.3f} | {means[key]-means["joint_oracle_cost"]:.3f} |\n'
    boundary=(f'The prespecified near-boundary subset contains {near.sum():,} states. Its mean gain is {gains[near].mean():.3f} s, '
              f'compared with {gains[~near].mean():.3f} s across the {sum(~near):,} other states. '
              f'Initial actions differ in {sum(flip&near)}/{sum(near)} near states ({100*flip[near].mean():.2f}%) '
              f'and {sum(flip&~near)}/{sum(~near)} other states ({100*flip[~near].mean():.2f}%). '
              f'The near subset accounts for {100*gains[near].sum()/gains.sum():.2f}% of total gain while comprising {100*near.mean():.2f}% of states. '
              'Thus this grid supports relative concentration near the declared boundary, while substantial benefits and disagreements also occur outside it.')
    validation=(f'Across the 24 selected states, main-to-refined gain changes average {diff.mean():.4f} s and reach {diff.max():.4f} s. '
                f'No selected initial action changes under that refinement. {check95} of 24 numerical gains lie inside the corresponding nominal 95% paired intervals, '
                f'with {24-selected_nonzero} zero-difference rollouts yielding degenerate intervals. These counts are descriptive and the selected cases are not independent population samples. '
                f'A post-run check of the three largest refinement differences uses 12,801 belief points and 321 quadrature nodes. '
                f'For the largest-discrepancy state (index {worst["index"]}), the refined gain changes from {worst["previous"]["policy_gain"]:.4f} to {worst["report"]["policy_gain"]:.4f} s; '
                f'a new 200,000-pair evaluation gives {mc["gain"]:.4f} s (95% interval [{mc["gain_95_ci"][0]:.4f},{mc["gain_95_ci"][1]:.4f}]). '
                'The highest-resolution quadrature estimate still falls outside this fresh sampling interval, so the small-gain comparator evaluation is not fully converged. We retain the rollout as the direct evaluation of that policy and do not hide the residual discrepancy. This diagnostic is reported separately and does not replace the locked-grid results. Small gains and threshold counts remain sensitive to numerical approximation; no all-grid error certificate is claimed.')
    text=(ROOT/'paper/manuscript-template.md').read_text()
    values={'__DISAGREE__':str(flip.sum()),'__DISAGREE_PCT__':f'{100*flip.mean():.1f}','__MATERIAL__':str(material.sum()),'__OVERALL_PARAGRAPH__':overall,'__SUMMARY_TABLE__':table,'__BOUNDARY_PARAGRAPH__':boundary,'__VALIDATION_PARAGRAPH__':validation}
    for key,value in values.items():text=text.replace(key,value)
    if '__' in text:raise ValueError('unresolved manuscript fields')
    (ROOT/'paper/manuscript.md').write_text(text)
    (ROOT/'results/manuscript-summary.json').write_text(json.dumps(dict(states=n,mean_gain=float(gains.mean()),disagreements=int(flip.sum()),material_gains=int(material.sum()),mean_costs=means,validation_max_difference=float(diff.max()),validation_inside_95=check95),indent=2)+'\n')
    out=ROOT/'paper/figures';out.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(7,3),constrained_layout=True)
    taus=[0,3,6]
    mean_gain=[np.mean([x['policy_gain'] for x in rows if x['offset_sd']==t]) for t in taus]
    disagreement=[100*np.mean([x['adaptive_action']!=x['frozen_action'] for x in rows if x['offset_sd']==t]) for t in taus]
    axes[0].bar(range(3),mean_gain,color='#256d68',width=.6);axes[0].set(ylabel='Mean policy gain (s)',title='Benefit of anticipating learning')
    axes[1].bar(range(3),disagreement,color='#657c8e',width=.6);axes[1].set(ylabel='Initial action disagreement (%)',title='How often does the first choice change?')
    for ax,values_ in zip(axes,[mean_gain,disagreement]):
        ax.set_xticks(range(3),taus);ax.set_xlabel('Baseline uncertainty SD (s)')
        ax.set_ylim(0,max(values_)*1.2)
        for i,value in enumerate(values_):ax.text(i,value+max(values_)*.03,f'{value:.3f}' if ax==axes[0] else f'{value:.1f}%',ha='center',fontsize=8)
    fig.savefig(out/'final-grid.png',dpi=300);fig.savefig(out/'final-grid.svg');plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,3.6),constrained_layout=True)
    for tau,color in [(0,'#256d68'),(3,'#bd7946'),(6,'#66798d')]:
        subset=[x for x in rows if x['waiting_margin']>=0 and x['offset_sd']==tau]
        ax.scatter([x['waiting_margin'] for x in subset],[x['continuation_learning_benefit'] for x in subset],s=11,alpha=.5,color=color,label=f'Baseline SD {tau} s')
    upper=max(x['waiting_margin'] for x in rows)*1.04
    ymax=max(x['continuation_learning_benefit'] for x in rows if x['waiting_margin']>=0)*1.1
    ax.plot([0,upper],[0,upper],'--',color='#303030',lw=1,label='B = M');ax.set(xlim=(-.25,upper),ylim=(-.1,ymax),xlabel='Frozen-planning disadvantage of waiting M (s)',ylabel='Continuation learning benefit B (s)')
    ax.legend(fontsize=8,loc='upper right');fig.savefig(out/'waiting-region.png',dpi=300);fig.savefig(out/'waiting-region.svg');plt.close(fig)
    print('Assembled manuscript:',len(text.split()),'words; outputs',out)
    print(overall);print(boundary);print(validation)

if __name__=='__main__':main()
