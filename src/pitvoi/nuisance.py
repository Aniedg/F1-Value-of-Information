"""Bayesian stopping with an unknown baseline shared by both tyre sets.

Observation y_t = b + age_t * theta + epsilon_t, b ~ N(0, offset_sd²).
The baseline persists for every remaining lap, including after a stop, so its
trajectory cost n*b cancels between policies. Conditional on each regime, b has
an exact Gaussian posterior. Its variance and the difference between the two
conditional means depend only on observation count, not observed values.
Consequently the regime probability alone determines the transition kernel for
the cost-relevant belief. This reduction relies on the common, static baseline.
"""
from dataclasses import replace
import numpy as np
from .gaussian import LapSolver, update


class OffsetSolver(LapSolver):
    def __init__(self, scenario, offset_sd=6., grid_size=1601, quadrature=41):
        if not np.isfinite(offset_sd) or offset_sd < 0:
            raise ValueError('offset_sd must be finite and nonnegative')
        self.offset_sd=float(offset_sd)
        super().__init__(scenario,grid_size,quadrature)

    def observation_parameters(self,t):
        """Return k, effective age, and conditional predictive noise SD.

        Given earlier sum S_y, use z=y-k*S_y. Its regime-conditional means
        are effective_age * theta and variance is noise²+Var(b|theta,history).
        """
        if not 0 <= t < self.s.laps:
            raise ValueError('observation index outside horizon')
        sigma2=self.s.noise_sd**2;tau2=self.offset_sd**2
        k=tau2/(sigma2+t*tau2)
        variance=sigma2*k
        sum_age=t*self.s.age+t*(t-1)/2
        return k,self.s.age+t-k*sum_age,float(np.sqrt(sigma2+variance))

    def integrate(self,future,age):
        t=age-self.s.age
        _,effective_age,sd=self.observation_parameters(t)
        observation_model=replace(self.s,noise_sd=sd)
        total=np.zeros_like(self.grid)
        for theta,prob in ((self.s.low,1-self.grid),(self.s.high,self.grid)):
            residual=effective_age*theta+sd*self.nodes
            posterior=update(self.grid[:,None],residual[None,:],effective_age,observation_model)
            total+=prob*(np.interp(posterior,self.grid,future)@self.weights)
        return total

    def posterior_update(self,p,y,past_sum,t):
        k,age,sd=self.observation_parameters(t)
        return update(p,np.asarray(y)-k*np.asarray(past_sum),age,replace(self.s,noise_sd=sd))

    def monte_carlo(self,trials=30000,seed=20260925,actual_offset_sd=None):
        """Paired physical trajectories; inference always uses assumed offset SD.

        Latent b and lap noise are shared between policies. Conditional excess
        degradation costs omit the common full-horizon baseline n*b. The oracle
        knows theta, has the same actions, and does not know future noise.
        """
        if trials < 2:
            raise ValueError('at least two trials required')
        actual=self.offset_sd if actual_offset_sd is None else actual_offset_sd
        if not np.isfinite(actual) or actual < 0:
            raise ValueError('invalid actual offset SD')
        s=self.s;rng=np.random.default_rng(seed)
        theta=np.where(rng.random(trials)<s.prior_high,s.high,s.low)
        offset=rng.normal(0,actual,trials)
        noise=rng.normal(0,s.noise_sd,(trials,s.laps))
        costs={};stops={}
        for policy in ('frozen_belief','adaptive'):
            p=np.full(trials,s.prior_high);past_sum=np.zeros(trials)
            cost=np.zeros(trials);active=np.ones(trials,dtype=bool)
            # laps means no stop; otherwise index is laps completed before stop.
            stop=np.full(trials,s.laps,dtype=int)
            for t in range(s.laps):
                pit=active & self.action(t,p,policy)
                cost[pit]+=self.pit_cost(s.laps-t);stop[pit]=t;active[pit]=False
                cost[active]+=(s.age+t)*theta[active]
                y=offset[active]+(s.age+t)*theta[active]+noise[active,t]
                p[active]=self.posterior_update(p[active],y,past_sum[active],t)
                past_sum[active]+=y
            costs[policy]=cost;stops[policy]=stop
        delta=costs['frozen_belief']-costs['adaptive']
        se=float(delta.std(ddof=1)/np.sqrt(trials));gain=float(delta.mean())
        schedules=np.array([theta*sum(s.age+j for j in range(k))+
                           (self.pit_cost(s.laps-k) if k<s.laps else 0)
                           for k in range(s.laps+1)])
        oracle=schedules.min(axis=0)
        return dict(trials=trials,seed=seed,actual_offset_sd=actual,assumed_offset_sd=self.offset_sd,
                    gain=gain,paired_standard_error=se,gain_95_ci=[gain-1.96*se,gain+1.96*se],
                    adaptive_cost=float(costs['adaptive'].mean()),
                    frozen_cost=float(costs['frozen_belief'].mean()),
                    adaptive_regret=float((costs['adaptive']-oracle).mean()),
                    frozen_regret=float((costs['frozen_belief']-oracle).mean()),
                    stop_time_disagreement=float(np.mean(stops['adaptive']!=stops['frozen_belief'])),
                    stop_counts={name:np.bincount(stop,minlength=s.laps+1).tolist() for name,stop in stops.items()})
