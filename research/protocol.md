# Research protocol — working draft, 22 September 2026

## Central question

Under what conditions does anticipating future tyre-performance observations change optimal pit timing and reduce expected remaining race time?

Working title: **The Value of Information in Formula One Pit Strategy**. Use “Bayes-adaptive” in the eventual subtitle only if the implemented controller and evaluation justify it.

## Experiment 01: isolate the mechanism

State: remaining laps n, current tyre age a, posterior probability p of high degradation. The set's fixed latent degradation theta is either 0.04 or 0.30 seconds per lap of tyre age. These illustrative values are not fitted to F1 data. A common base lap time is omitted because it cancels across strategies.

On staying out, expected excess lap time is a E[theta], tyre age increases by one, and a binary signal arrives. P(high signal | high regime)=q and P(high signal | low regime)=1-q. Signals are conditionally independent given the regime. This is an abstract noisy diagnostic, not a model of measured lap times. Costs are scored by the evaluator; the agent observes only the signal. Giving the agent the noiseless regime-dependent lap cost would reveal theta immediately and invalidate this experiment.

After a high signal, p' = pq / [pq+(1-p)(1-q)]. Low-signal updates follow the same Bayes rule. Zero-probability branches are omitted.

Pitting before the next lap costs L and commits to a known replacement set whose excess lap times are d times ages 0 through n-1. Therefore P(n)=L+d n(n-1)/2. No more stops or other decisions follow. Replacement-tyre observations have no decision value under this assumption; they are not assumed uninformative in real races. Zero stops within the remaining horizon are permitted. We assume any earlier mandatory-compound obligation is already satisfied; the model is not a complete regulation-constrained race.

For an adaptive cost-minimising controller:

    V(n,a,p) = min{P(n), a E[theta|p] + E_y[V(n-1,a+1,p_y)]}
    V(0,a,p) = 0

The frozen-belief planner replaces p_y by p in its lookahead. Crucially, when deployed it still updates from each real signal and replans. Thus its evaluated performance is not generally the same as its frozen planning value. The fixed-prior policy also receives signals but ignores them in action selection. Ties select pit.

For linear fixed-schedule costs, E[C(theta)] = C(E[theta]); consequently posterior-mean and frozen-belief planners coincide. We retain both labels to make this degeneracy explicit, not count them as independent methods.

## Metrics and interpretation

- Oracle regret: policy expected cost minus the expected cost of a policy that knows the current set's latent regime. The oracle does not know future random signals and has the same pit options.
- Realized policy gain: exactly evaluated frozen-belief policy cost minus adaptive policy cost. “Realized” distinguishes deployed-policy evaluation from internal planning values; it does not mean historical observations.
- Planning information value: optimal frozen planning cost minus adaptive planning cost. Lower cost is better, so this sign convention gives nonnegative information value.
- Initial action disagreement: policies choose different first actions at the same state and prior.

The selected demo example is the largest gain among grid disagreements at 80% diagnostic accuracy. It is selected for explanation, not an unbiased effect-size estimate. The grid includes uninformative and perfect signals as controls. All possible signal histories are integrated exactly. There is no sampling confidence interval to estimate for this finite model.

Tests establish Bayesian probability conservation, agreement with exhaustive oracle schedules, agreement with independent trajectory enumeration, no learning benefit for uninformative signals or known parameters, and adaptive-policy dominance over the comparator under the correctly specified toy model.

## Questions, not predetermined conclusions

1. Does planning for future learning beat online estimation with frozen-belief planning in realistic, held-out settings?
2. Does the benefit concentrate near action boundaries?
3. How do observation noise, uncertainty, remaining decision opportunities and model error interact?
4. Does any advantage survive uncertainty about replacement tyres and correlated compound performance?

Do not assume information value is monotonic in posterior variance. Do not assume uncertainty-aware planning strictly beats posterior-mean planning. Under correct-model exact optimisation, adaptive dominance in expectation is built into the decision problem; demonstrating it in the toy model is a correctness check, not a publishable discovery.

## Next milestones and completion gates

1. **Literature review.** Read full texts on Bayesian degradation, stochastic/dynamic pit optimisation, and Bayesian optimal stopping. Record whether each planner integrates future posterior updates. Establish what contribution remains before claiming novelty.
2. **Observation model.** Replace abstract signals with noisy lap observations; include fuel, traffic and track evolution as confounders. Distinguish posterior intervals for latent degradation from posterior predictive intervals for lap times. Check identifiability and calibration on synthetic truth before fitting data.
3. **Historical feasibility pilot.** Ingest a small set of dry-race stints with FastF1. Record source, version, filtering decisions, observation availability times and permitted reuse. Do not choose only races showing favorable results.
4. **Validation split.** Fit priors and nuisance corrections on training races only; tune on validation races and freeze before evaluating whole held-out races. A historical replay may reveal only information available at each decision time. Do not use smoothed future-aware state estimates as online inputs.
5. **Counterfactual evaluation.** Historical data cannot directly identify outcomes of unchosen strategies. Validate a simulator on held-out observed trajectories and label alternate-policy gains as model-based. Compare policies on shared latent trajectories/noise streams. Report sensitivity to misspecification and intervals clustered by race where appropriate.
6. **Paper and portfolio.** Produce reproducible configurations, provenance, ablations and exported figures. Write results only after evaluation. Build the portfolio narrative around the question, model, evidence and limitations. Choose a journal or conference after a substantive result exists.

First paper outline: introduction and research gap; related work; belief-state formulation; inference and planning; synthetic verification; historical model validation and model-based counterfactual evaluation; limitations and conclusions.

## Explicitly out of scope for the first milestone

Opponent game theory, weather, safety cars, ERS, reinforcement learning, full-race regulation enforcement and race-win prediction. These may matter later but are unnecessary to verify the core information mechanism.
