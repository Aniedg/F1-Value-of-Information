"""Preserve the v1 manuscript; add explicitly post-run numerical and empirical detail."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
x=json.loads((ROOT/'results/segmented-audit.json').read_text())
paragraphs=[]
for c in x['cases']:
    p=c['parameters'];r=c['resolutions'][-1]['report'];mc=c['rollout'];lo,hi=mc['gain_95_ci']
    vals=', '.join(f"{v['report']['policy_gain']:.6f}" for v in c['resolutions'])
    paragraphs.append(f"**State {c['index']}.** With {p['laps']} laps remaining, tyre age {p['age']}, pit loss {p['pit_loss']} s, observation noise {p['noise_sd']} s, prior high-regime probability {p['prior_high']}, baseline SD {p['offset_sd']} s and dependence parameter {p['dependence']}, the estimated policy gains are {vals} s at the three successive grid resolutions. The fresh paired simulation estimates {mc['gain']:.6f} s (95% interval [{lo:.6f}, {hi:.6f}] s). The earlier 12,801-point/321-node estimate was {c['v1_high_resolution']['policy_gain']:.6f} s.")
fig,ax=plt.subplots(figsize=(7.1,3.5))
for i,c in enumerate(x['cases']):
    gain=c['rollout']['gain'];lo,hi=c['rollout']['gain_95_ci']
    ax.errorbar(gain,i,xerr=[[gain-lo],[hi-gain]],fmt='o',color='#176c70',capsize=5,label='Paired simulation (95% interval)' if i==0 else None)
    ax.scatter(c['resolutions'][-1]['report']['policy_gain'],i+.13,marker='D',s=40,color='#21374b',label='Analytic segment integration' if i==0 else None)
    ax.scatter(c['v1_high_resolution']['policy_gain'],i-.13,marker='x',s=55,color='#bc6334',label='Earlier high-resolution quadrature' if i==0 else None)
ax.set_yticks(range(3),[f"State {c['index']}" for c in x['cases']]);ax.set_xlabel('Simulated expected policy gain (seconds)');ax.set_ylim(-.5,2.85);ax.grid(axis='x',alpha=.2);ax.spines[['top','right']].set_visible(False);ax.legend(loc='upper right',fontsize=8,frameon=False);fig.tight_layout()
for ext in ['png','svg']:fig.savefig(ROOT/f'paper/figures/segmented-audit.{ext}',dpi=220)
plt.close(fig)
change=max(abs(c['resolutions'][2]['report']['policy_gain']-c['resolutions'][1]['report']['policy_gain']) for c in x['cases'])
appendix=(ROOT/'paper/extended-appendix.md').read_text().replace('__AUDIT_RESULTS__','\n\n'.join(paragraphs)).replace('__MAX_CHANGE__',f'{change:.8f}')
base=(ROOT/'paper/manuscript.md').read_text().replace('Version 1.0','Version 1.1 - expanded research draft')
base=base.replace('The study provides a reproducible model-based answer and explicitly limits its empirical interpretation.','A post-study analytic integration method stabilizes three numerically sensitive cases. The study provides a reproducible model-based answer and explicitly limits its empirical interpretation.')
base=base.replace('## References',appendix+'\n\n## References')
# Explicitly link the unresolved v1 numerical caveat to the new, limited follow-up.
needle='## 7.'
pos=base.find(needle)
if pos!=-1:
    base=base[:pos]+'**Post-study update.** Appendix A investigates the numerical discrepancy with an independent integration method and new simulations. Its selected-case checks do not replace the original aggregate estimates above.\n\n'+base[pos:]
(ROOT/'paper/manuscript-expanded.md').write_text(base)
p=(ROOT/'paper/build_pdf.py').read_text().replace("paper/manuscript.md","paper/manuscript-expanded.md").replace("paper/manuscript.html","paper/manuscript-expanded.html").replace('Version 1.0','Version 1.1').replace("'value-of-information-f1-paper.pdf'","'value-of-information-f1-paper-expanded.pdf'")
p=p.replace('fontSize=10.0,leading=13.6','fontSize=9.9,leading=13.4')
(ROOT/'paper/build_pdf_extended.py').write_text(p)
print('Words:',len(base.split()))
