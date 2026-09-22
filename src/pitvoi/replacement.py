"""Uncertain replacement degradation with dependence on the old-tyre regime.

Only old-set observations arrive before the optional final stop. Replacement
uncertainty therefore affects risk-neutral decisions through its conditional
mean given that history. Full-information and old-regime-only oracles differ.
"""
from dataclasses import dataclass,asdict
import numpy as np
from .nuisance import OffsetSolver


@dataclass(frozen=True)
class Replacement:
    low: float = .02
    high: float = .10
    high_given_old_low: float = .5
    high_given_old_high: float = .5

    def __post_init__(self):
        if not all(np.isfinite(x) for x in asdict(self).values()):
            raise ValueError('replacement parameters must be finite')
        if not 0 <= self.low <= self.high:
            raise ValueError('invalid replacement degradation')
        if not all(0 <= q <= 1 for q in (self.high_given_old_low,self.high_given_old_high)):
            raise ValueError('invalid conditional probability')

    def high_probability(self,p):
        return (1-np.asarray(p))*self.high_given_old_low+np.asarray(p)*self.high_given_old_high

    def mean(self,p):
        return self.low+(self.high-self.low)*self.high_probability(p)


class ReplacementSolver(OffsetSolver):
    def __init__(self,scenario,replacement,offset_sd=3.,grid_size=1601,quadrature=41):
        self.replacement=replacement
        super().__init__(scenario,offset_sd,grid_size,quadrature)

    def pit_cost(self,remaining,p=None):
        # During the inherited Bellman recursion, evaluate on the whole grid.
        belief=self.grid if p is None else np.asarray(p)
        return self.s.pit_loss+self.replacement.mean(belief)*remaining*(remaining-1)/2

    def action(self,t,p,policy):
        if policy not in ('adaptive','frozen_belief'):
            raise ValueError('unknown policy')
        values=self.stay_adaptive if policy=='adaptive' else self.stay_frozen
        return self.pit_cost(self.s.laps-t,p)<=np.interp(p,self.grid,values[t])

    def schedule_optimum(self,old,fresh):
        s=self.s
        return np.min([old*(k*s.age+k*(k-1)/2)+
                       (s.pit_loss+fresh*(s.laps-k)*(s.laps-k-1)/2 if k<s.laps else 0)
                       for k in range(s.laps+1)],axis=0)

    def report(self):
        s=self.s;r=self.replacement;p=s.prior_high
        at=lambda x:float(np.interp(p,self.grid,x[0]))
        limited=float((1-p)*self.frozen[0,0]+p*self.frozen[0,-1])
        joint=0.
        for old,prob,q in [(s.low,1-p,r.high_given_old_low),(s.high,p,r.high_given_old_high)]:
            joint+=prob*((1-q)*self.schedule_optimum(old,r.low)+q*self.schedule_optimum(old,r.high))
        pit=float(self.pit_cost(s.laps,p));adaptive=at(self.adaptive);frozen=at(self.deployed_frozen)
        stay=at(self.stay_adaptive);margin=at(self.stay_frozen)-pit
        return dict(adaptive_cost=adaptive,frozen_policy_cost=frozen,policy_gain=frozen-adaptive,
                    old_regime_oracle_cost=limited,joint_oracle_cost=float(joint),
                    adaptive_regret_old_oracle=adaptive-limited,adaptive_regret_joint_oracle=adaptive-float(joint),
                    prior_replacement_mean=float(r.mean(p)),pit_cost=pit,
                    planning_information_value=at(self.frozen)-adaptive,
                    waiting_margin=margin,continuation_learning_benefit=at(self.stay_frozen)-stay,
                    adaptive_wait_advantage=pit-stay,
                    adaptive_action='pit' if self.action(0,p,'adaptive') else 'stay',
                    frozen_action='pit' if self.action(0,p,'frozen_belief') else 'stay')

    def monte_carlo(self,trials=30000,seed=20260926,actual_replacement=None):
        if trials<2:raise ValueError('at least two trials required')
        s=self.s;r=self.replacement if actual_replacement is None else actual_replacement
        rng=np.random.default_rng(seed)
        old_high=rng.random(trials)<s.prior_high
        old=np.where(old_high,s.high,s.low)
        fresh=np.where(rng.random(trials)<r.high_probability(old_high.astype(float)),r.high,r.low)
        offset=rng.normal(0,self.offset_sd,trials)
        noise=rng.normal(0,s.noise_sd,(trials,s.laps))
        costs={};stops={}
        for policy in ('frozen_belief','adaptive'):
            p=np.full(trials,s.prior_high);past=np.zeros(trials);active=np.ones(trials,dtype=bool)
            cost=np.zeros(trials);stop=np.full(trials,s.laps,dtype=int)
            for t in range(s.laps):
                pit=active & self.action(t,p,policy);n=s.laps-t
                # Score the actual latent replacement, never its posterior mean.
                cost[pit]+=s.pit_loss+fresh[pit]*n*(n-1)/2
                stop[pit]=t;active[pit]=False
                cost[active]+=(s.age+t)*old[active]
                y=offset[active]+(s.age+t)*old[active]+noise[active,t]
                p[active]=self.posterior_update(p[active],y,past[active],t);past[active]+=y
            costs[policy]=cost;stops[policy]=stop
        delta=costs['frozen_belief']-costs['adaptive'];gain=float(delta.mean())
        se=float(delta.std(ddof=1)/np.sqrt(trials));oracle=self.schedule_optimum(old,fresh)
        return dict(trials=trials,seed=seed,gain=gain,paired_standard_error=se,gain_95_ci=[gain-1.96*se,gain+1.96*se],
                    adaptive_cost=float(costs['adaptive'].mean()),frozen_cost=float(costs['frozen_belief'].mean()),
                    adaptive_regret_joint_oracle=float((costs['adaptive']-oracle).mean()),
                    actual_replacement=asdict(r),assumed_replacement=asdict(self.replacement),
                    stop_time_disagreement=float(np.mean(stops['adaptive']!=stops['frozen_belief'])),
                    stop_counts={name:np.bincount(stop,minlength=s.laps+1).tolist() for name,stop in stops.items()})
