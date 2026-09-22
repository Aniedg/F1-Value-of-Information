# Experiment 02 — learning from continuous lap observations

## What changed

Replace the binary diagnostic with y_t = b_t + a_t theta + epsilon_t, where epsilon_t is independent N(0, sigma^2). theta still has two possible values (0.04 and 0.30); the observation is continuous, not the latent parameter. The offset b_t represents base pace plus known corrections. In the illustrative trace it is 90 + (2 - 0.04t) - 0.015t seconds. These corrections are synthetic inputs, not estimated fuel loads or fitted track effects.

The update multiplies the current odds by the Gaussian likelihood ratio. Predictions and central 90% mixture-normal intervals are computed before each lap is observed. Observed lap residuals, not latent noiseless costs, reach the controller. The scorer evaluates conditional excess pace; independent action-invariant additive lap noise cancels in paired policy differences over the fixed horizon.

The adaptive planner integrates future posterior updates with Gauss–Hermite quadrature and interpolates a grid of 1,601 beliefs. The comparator updates after each actual observation but holds beliefs fixed during lookahead. Its evaluated cost is calculated separately from its frozen internal planning value. Posterior-mean planning still coincides with the frozen-belief baseline under linear costs.

## Reproducibility and numerical accuracy

Five predeclared observation standard deviations: 0.5, 1.0, 1.5, 2.5 and 4.0 seconds. Otherwise keep experiment 01's initial state: eight laps remaining, age 12, prior high probability 0.5, pit loss 18 seconds and replacement degradation 0.06.

Primary integration uses 41 Gaussian nodes per regime; refinement uses 3,201 beliefs and 81 nodes. The largest change in initial adaptive cost across this grid is approximately 0.0231 seconds. This is an empirical resolution check, not a rigorous error bound. Kinks at decision boundaries can make quadrature convergence non-monotonic. Do not interpret three decimal places in the dashboard as certified millisecond accuracy.

Evaluate each deployed policy independently on 20,000 common latent trajectories and continuous Gaussian observation streams (seed 20260922). The paired mean gain's normal-approximation interval is mean +/- 1.96 times its paired standard error. This measures Monte Carlo error under the generating model, not model uncertainty, historical generalisation or publication-level confidence.

At noise SD 1.5 seconds, the numerical adaptive advantage is about 4.37 seconds. The independent rollout's 95% interval is approximately [4.24, 4.51] seconds. The initial comparator pits while the adaptive policy stays. These are illustrative model-based numbers, not F1 performance claims.

## Calibration and model error

For each noise setting, generate 10,000 independent sequences by drawing the latent regime from the stated prior (seed 20260923). Score each next-lap predictive interval before updating. At the default noise, coverage by prediction step ranges from 89.82% to 90.52% for nominal 90% intervals. This is prior-predictive self-consistency under the correct model, not validation on real data.

The predeclared stress test doubles actual observation noise to 3.0 seconds while the controller assumes 1.5. Coverage then falls to 57.63%–69.68%. This exposes the effect of unmodelled variability: a Bayesian posterior can be confident and wrong. The results file also records paired policy performance under that mismatch, without claiming any universal dominance.

The displayed sequential trace fixes the low regime and seed 42. It is an observation-only illustration and deliberately continues all eight laps; it must not be read as a trajectory followed by either pit policy.

## Historical feasibility pilot

Event and inclusion policy were saved before downloading: 2024 Bahrain race, every driver, development use only. FastF1 3.8.3 supplied 1,129 laps for 20 drivers. Initial filters retain 1,006 laps across 62 stints. Exclude missing/invalid timing or age, pit in/out, non-green track status, non-dry compounds, inaccurate/generated timings and race lap 1. Reasons overlap, so exclusion counts must not be summed.

Raw lap and weather exports, the cache and audited CSV remain local in `data/`. Summary provenance records retrieval time, FastF1 version and SHA-256 hashes. Source timestamps are race-relative lap ends, not proven feed-arrival timestamps. FastF1 retrospective accuracy checks can use later information, so these filters must not be presented as a leakage-free online policy evaluation.

Traffic, warm-up, fuel mass and track evolution are not estimated. No historical posterior has been fitted and no real-race policy gains are reported. The plot shows ALB, chosen alphabetically, and does not imply those raw lap times are pure tyre degradation. Historical data redistribution permissions remain unassessed; do not publish raw exports by default.

## Next gate: identifiability before strategy validation

Within an uninterrupted stint, tyre age and race lap both increase by one. With a linear fuel/track trend, y_t = beta + theta(a_0+t) - c(l_0+t) + error only identifies the combined slope theta-c. More laps do not independently identify both slopes. A future fit therefore needs external information or explicit priors for nuisance trends, multiple stints/drivers and sensitivity analyses. Do not learn the correction using the full held-out stint, then claim online degradation inference.

Next implement an observation model with uncertain baseline and degradation, select its nuisance assumptions using development data, and validate sequential predictions on entire held-out races. Keep the historical observation-validation milestone separate from counterfactual strategy evaluation.
