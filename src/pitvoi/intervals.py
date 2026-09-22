"""Prequential empirical prediction intervals around unchanged point forecasts."""
import numpy as np
from pitvoi.robust import weighted_quantile


def prior_support(races, size=201):
    values,weights=[],[]
    for rows in races:
        for r in rows:
            values.append(abs(r['observed']-r['predicted'])/np.sqrt(r['variance']))
            weights.append(1/len(rows))
    return [weighted_quantile(values,weights,(i+.5)/size) for i in range(size)]


def apply_intervals(rows, support, window=20, prior_mass=15, static=False, fixed_q=None):
    history={};result=[]
    for row in sorted(rows,key=lambda r:(r['driver'],r['lap'])):
        past=history.setdefault(row['driver'],[])
        recent=past[-window:]
        if fixed_q is not None:
            q=fixed_q
        elif static or not recent:
            q=weighted_quantile(support,np.ones(len(support)),.9)
        else:
            q=weighted_quantile(list(support)+recent,
                [prior_mass/len(support)]*len(support)+[1.0]*len(recent),.9)
        half=float(q*np.sqrt(row['variance']))
        # Targets do not enter width computation until after recording forecast.
        result.append(dict(**row,lower=row['predicted']-half,upper=row['predicted']+half,
                           prior_error_count=len(past)))
        past.append(abs(row['observed']-row['predicted'])/np.sqrt(row['variance']))
    return result


def interval_metrics(rows):
    widths=np.array([r['upper']-r['lower'] for r in rows])
    misses=np.array([max(r['lower']-r['observed'],0)+max(r['observed']-r['upper'],0) for r in rows])
    return dict(n=len(rows),coverage90=float(np.mean(misses==0)),
                mean_width=float(widths.mean()),interval_score=float(np.mean(widths+20*misses)),
                mae=float(np.mean([abs(r['observed']-r['predicted']) for r in rows])))
