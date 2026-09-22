## Appendix A. Decision-boundary-aware numerical evaluation

### A.1 Why a deployed policy can be harder to evaluate than an optimal value

The distinction between a planning objective and the cost of executing its policy is numerically consequential. The adaptive optimal value is the minimum of its immediate-stop cost and its expected continuation cost. At its action boundary these two quantities agree. By contrast, the updating frozen-belief policy chooses an action by comparing the stop cost with a continuation calculation that holds its belief fixed. Once deployed, it updates that belief after every observation. Its actual continuation cost can therefore differ from the continuation cost used to select the action. At the frozen planner's switching boundary, the two *planning* costs agree, but the two *realized-policy* costs need not agree.

Consequently, the deployed frozen-policy value may be discontinuous as a function of belief. Interpolating nodal values across that discontinuity smooths a genuine jump, and applying a finite Gaussian quadrature rule can place too many or too few nodes on either side. Increasing the node count need not produce monotone convergence. This mechanism is consistent with the earlier diagnostic: in state 1788, the adaptive value was comparatively stable, while the deployed comparator value changed substantially. The observation does not invalidate the underlying Bayesian recursion. It identifies a numerical representation that is poorly suited to one of the quantities being evaluated.

A follow-up implementation retains distinct affine representations on the two sides of every action boundary and integrates them analytically under the binary Gaussian observation kernel. It is a separate method added after the original protocol and its discrepancy audit; it does not retroactively change the frozen sources or reclassify the original study as a prospectively specified evaluation of this method.

### A.2 Exact integration of an affine segment

Let p denote the current high-regime probability and q the posterior after the next observation. Let d be the standardized separation between the two regime-conditional observation means. In the nuisance-offset model, d is the effective age times the difference in degradation rates, divided by the conditional predictive standard deviation. For an interior prior, the log odds of q are normally distributed: their mean is the log odds of p minus d squared divided by two in the low regime, or plus that quantity in the high regime; their standard deviation is d.

For an interval I in posterior-belief space, let P_L(I) and P_H(I) be its probabilities under the two regimes. They are differences of ordinary Gaussian distribution functions evaluated at the interval's log-odds endpoints. Bayes' rule gives the posterior-martingale identity E[q times the indicator of I] = p P_H(I). Therefore, for an affine segment f(q) = a + bq on I,

$$E[f(q)\mathbf{1}_{q\in I}]=a[(1-p)P_L(I)+pP_H(I)]+bpP_H(I).$$

Summing this expression over all segments integrates the represented function without observation quadrature. Known-regime priors are handled directly; if the standardized separation is zero, q equals p and no integration is necessary. Exactness refers to the expectation of the represented piecewise-affine function, up to floating-point arithmetic. The continuous belief functions are still approximated on a finite grid, so this is not an exact solution of the original continuous-state problem.

For the deployed comparator, each belief-grid interval is split at any crossing of the affine pit cost and the interpolated frozen-planning stay cost. The appropriate pit or realized-stay affine branch is retained within each resulting interval. Separate branches preserve their jump instead of drawing a line through it. The adaptive recursion retains continuous interpolation of its optimal value. This method requires a quadratic number of grid-to-segment evaluations per time step; chunking limits working memory. The tradeoff is appropriate for an offline validation method, and no real-time performance guarantee is claimed.

### A.3 Follow-up design and results

The follow-up deliberately selects the three cases with the largest discrepancies in the previous refinement audit. This is a diagnostic sample, not an unbiased sample of the 2,187 states. Each case is recomputed at 801, 1,601 and 3,201 belief points using analytic segment integration. The finest-grid policy is evaluated on 200,000 new paired trajectories per case, using seeds recorded with the output. The trajectories score the actual latent replacement performance and compare policies exposed to the same latent regimes, baseline and observation noise. The combined follow-up contains 600,000 paired trajectories.

__AUDIT_RESULTS__

![Figure 3. Diagnostic convergence and independent paired simulation. Points compare the earlier 12,801-point/321-node calculation with analytic segment integration at 3,201 belief points. Error bars are 95% Monte Carlo intervals for the latter policies, not confidence intervals for real-race savings.](figures/segmented-audit.png)

All three finest-grid estimates lie inside their respective fresh simulation intervals. This is an encouraging consistency check, not a coverage study: three selected cases cannot establish a general error rate. The largest change between 1,601 and 3,201 points is __MAX_CHANGE__ s. The result substantially reduces the numerical discrepancy in the inspected cases. It does not certify the previously reported all-grid mean, threshold counts, or every state near a decision boundary, because the complete 2,187-state experiment has not been rerun with this method.

Six additional tests check integration of affine functions against the posterior martingale, zero-information and known-regime limits, a discontinuous function against independent adaptive scalar quadrature, preservation of a policy jump, the one-lap zero-learning-value limit, replacement mean invariance and policy-value bounds. The combined suite contains 53 tests. Tests establish specified numerical properties; they cannot validate the assumptions of a race model.

## Appendix B. Interpreting lap-time evidence

### B.1 Predictive accuracy is not parameter identification

Observed lap time contains more than tyre degradation. Fuel consumption, track evolution, traffic, driver management and transient events can produce trends with the same sign or a similar time scale. A filter can predict their sum well while attributing that change to the wrong physical mechanism. The inference needed for a stop decision is harder than short-term net-pace prediction: it must support a counterfactual comparison between continuing on the old set and switching to a replacement set.

For example, a sequence of slower laps could be explained by degradation or by traffic. Both explanations may imply a similar immediate prediction. They need not imply a similar gain from a tyre change. If the estimator treats all of the slowdown as degradation, the stop-value calculation may be overconfident even when its next-lap error appears acceptable. This is why the historical forecasting results are kept separate from the synthetic policy-gain results.

The shared-baseline model isolates one part of this ambiguity in a tractable setting. A persistent offset reduces the early information about degradation while cancelling from relative full-horizon costs. It does not model time-varying traffic, compound warm-up, changing fuel sensitivity or driver adaptation. Real historical inference must either model those mechanisms, condition on a defensible restricted operating regime, or report sensitivity to their omission. A nominally narrow degradation posterior is not convincing unless parameter recovery and model checks demonstrate that it represents the intended quantity.

### B.2 Information availability at a decision time

A replay should distinguish the lap on which a quantity refers to the car from the time at which that quantity became available to the decision system. Retrospectively corrected timing data can be valid historical measurements without reproducing a live information set. Quality flags, corrected sectors and event annotations therefore require an availability audit before being used as decision-time filters.

At each replay decision, the input record should contain the decision timestamp, only completed observations available by that time, the current tyre age and compound, the model version and its training cutoff, any eligibility exclusions, and the resulting predictive distribution. Data from later laps must not be used to decide whether the current state is eligible, to estimate the current latent state, or to choose a model. If availability cannot be established, the exercise should be described as a retrospective timing-data replay with that limitation, rather than a live-ready backtest.

The original studies use chronological development and test stages, with forecasts scored before update. That ordering is necessary but does not resolve retrospective data availability. Furthermore, the events already used to diagnose failures and choose revisions are now development history. A new empirical claim needs a new locked evaluation set or an explicitly exploratory label.

### B.3 Policy evaluation and unavailable counterfactuals

A historical race supplies the outcome of the strategy that was taken. It does not also supply the same car's outcome had it stopped one lap earlier or later under identical conditions. Comparing a proposed stop lap with the team's actual stop lap is therefore a comparison of choices, not an estimate of time saved. Agreement is not proof of optimality, and disagreement is not proof of improvement.

Historical replay can nevertheless test whether the system uses information consistently, whether its forecasts remain calibrated at relevant decision states, whether its action changes are explainable, and whether conclusions survive plausible modelling alternatives. Model-based counterfactual rollouts can then evaluate policies conditional on an explicit simulator. Those rewards must remain labelled simulated. Causal real-race savings require additional identification assumptions or a suitable experimental design that is absent here.

## Appendix C. A falsifiable route to empirical decision validation

The next empirical study should test a narrower claim than operational race optimization: whether a degradation inference model calibrated on prior events produces useful and stable *conditional* stop decisions on untouched events. This appendix specifies a design direction, not a completed experiment or an externally registered protocol. Event selection, operating-regime rules and numerical thresholds must be finalized and hashed before opening the new evaluation outcomes.

First, an observation model should be fitted using development data only. Its physical components must distinguish baseline pace from the tyre-age effect and explicitly state which fuel and track assumptions are externally supplied or estimated. Synthetic parameter-recovery experiments should vary traffic contamination and baseline drift, rather than generating data only from the fitted model. Failed recovery should restrict the scope of subsequent strategy claims, even if net-lap forecasts remain accurate.

Second, the comparison should preserve a common information set. The adaptive policy and updating certainty-equivalent policy must receive the same observations and the same posterior at each actual decision. Their difference should be whether they anticipate future information. A fixed-prior schedule is an additional baseline that measures the broader value of updating. An oracle is a lower-bound reference with explicitly stated privileged information, not an implementable competitor. If linearity again makes two proposed baselines identical, they should be reported as identical instead of presented as independent victories.

Third, evaluation should operate at three levels. Forecast evaluation measures point error, proper probabilistic scores, calibration and sharpness. Decision evaluation reports stop/stay disagreement, predicted advantage and sensitivity to observation assumptions. Conditional simulation evaluation reports paired policy costs, uncertainty intervals, regret against the declared oracle and the frequency of harmful outcomes. Average lap error alone does not establish strategy utility; a decision method can be most sensitive to a small subset of laps near an action boundary.

Fourth, uncertainty estimates should respect the dependence in the data. Repeated laps from one driver or one event are not independent replications of a modelling assumption. Event-level summaries and an explicitly chosen clustering or resampling scheme should accompany pooled results. If only a few events are available, the limitation should be reported instead of using thousands of correlated laps to suggest a large independent sample. Numerical error, Monte Carlo error and between-event generalization are separate uncertainty sources and should not be combined into a single unexplained error bar.

Finally, negative results should constrain the claim. Failure to improve simulated reward narrows the circumstances in which learning is useful. Poor calibration blocks an operational claim. Decisions sensitive to plausible nuisance assumptions require further investigation. The aim is to identify when waiting is defensible, including when it is not.
