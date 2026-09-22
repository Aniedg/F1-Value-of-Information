# Paper completion plan — scope anchored to the supplied outline

Updated 22 September 2026. Historical replay remains required; it is not silently replaced by a purely synthetic paper. Working title: The Value of Information in Formula One Pit Strategy: Bayes-Adaptive Decision-Making Under Uncertain Tyre Degradation. Title and novelty remain provisional.

## Required answers and evidence

1. Does uncertainty matter? Separate parameter estimation, predictive noise and planning for future learning. Preserve the linear-model equivalence of posterior-mean and frozen-belief planning. Compare fixed-prior, updating frozen-belief, adaptive and latent-regime oracle policies; do not double-count equivalent policies.
2. Does anticipating learning improve decisions? Measure paired deployed-policy cost differences and oracle regret under an explicitly specified simulator. Correct-model adaptive dominance is a mathematical property, not the novel empirical finding.
3. When is waiting valuable? Use the waiting-margin condition in `paper/methods-working.md`. Freeze the state grid and margin bins before the final study; report all cells, including zero/negative stress-test results. Examine horizon, age, observation noise, prior, pit loss and replacement uncertainty without assuming monotonicity.
4. How costly are wrong beliefs? Prespecify true-versus-assumed baseline, degradation prior and noise scenarios. Evaluate all comparators on common trajectories. Keep posterior calibration separate from predictive coverage.
5. Does the mechanism occur in historical race states? Audit field availability and retrospective filtering, freeze training/development/test race assignments, estimate nuisance effects without future observations, then replay every eligible decision state. Report disagreements with denominators and a prespecified example-selection rule. After a counterfactual stop differs from history, do not continue treating the factual observations as observations from the alternative policy. Counterfactual time gains require a validated simulator and must remain labelled model-based.

## Completion gates, in execution order

A. Literature and formulation: targeted source review underway; dynamic-programming paper full text and broader optimal-stopping/dual-control search still outstanding. No priority claim. An elementary waiting condition is now drafted and numerically audited.
B. Joint inference and planning: Experiment 08 now implements and checks the common-static-baseline case with identical observation models and priors for both comparators. Its exact conditional-Gaussian reduction preserves a scalar decision belief. Reduced-case integration, dense-likelihood posterior checks and three numerical resolutions are complete. This gate is satisfied for the declared shared-baseline model; changing baselines and tyre-specific offsets remain outside its assumptions. Experiment 09 adds uncertain replacement degradation, including cross-set dependence, and verifies independent-variance invariance for linear expected-time costs. The current model is sufficient to define the final synthetic study; stop adding mechanisms without a research need.
C. Final synthetic study: freeze settings after development, run paired evaluation with known/unknown baseline and replacement sensitivity, quantify numerical and sampling uncertainty separately, include misspecification and no-learning controls.
D. Historical decision replay: existing multi-race forecasting is preliminary feasibility evidence. Resolve as-of availability and degradation identification before claiming leakage-free strategy replay. All eleven races already inspected are development history for a new design. Select any new test races before inspecting them.
E. Manuscript and release: write introduction/related work/methods/results/discussion from verified artifacts; reproduce main claims from a clean environment; assess data reuse and cite sources; package portfolio separately; choose venue once contribution is clear. Submission/publication has not occurred.

## Existing evidence to retain

Experiments 01–02 establish the simplified learning mechanism and computational checks. Experiments 03–06 document mixed historical forecasts, initialization failure, robust improvement and insufficient predictive coverage. Experiment 07 distinguishes predictive variance from learning value and demonstrates nuisance sensitivity. These are development findings, not a frozen final evaluation. Methods and negative findings can enter the paper; no invented summary effect sizes or retrospective claim of preregistration.

## Hypotheses repaired

H1 (uncertainty versus posterior mean): equality in the current linear model; strict improvement is not expected by construction.
H2 (anticipating learning): nonnegative expected benefit under correct exact optimisation; magnitude, decision changes and robustness are the research targets.
H3 (boundary concentration): empirical hypothesis, tested on a declared state distribution and margin bins.
H4 (monotonicity in variance): exploratory conditional question, not a universal law.

Primary strategy metrics: paired expected cost difference, oracle regret and action disagreement. Pit-lap difference is secondary and must handle no-stop outcomes explicitly; reproducing an observed human pit lap is not an optimality criterion. Positive information value uses cost_without_learning minus cost_with_learning.

## Manuscript v1 completion

The 12-page manuscript is complete in `paper/manuscript.md` and `output/pdf/value-of-information-f1-paper.pdf`, supported by the locked 2,187-state study, 24 selected paired validations and a disclosed post-run numerical audit. The empirical scope is historical forecasting feasibility, not historical policy replay. The original stronger goal of an as-of historical strategy replay remains unachieved and is explicitly not claimed in this manuscript. This is a finished model-based paper with stated limitations, not a record of submission or acceptance.
