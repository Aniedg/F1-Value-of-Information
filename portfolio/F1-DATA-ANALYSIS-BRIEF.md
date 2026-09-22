# Bayesian pit-timing research: data-analysis portfolio brief

## Project positioning

A research project on when an extra lap of information can justify delaying a pit stop. The portfolio combines Bayesian inference, sequential forecast validation, decision analysis, numerical verification and honest reporting of negative results. It is currently a local research manuscript and reproducible codebase, not a peer-reviewed publication or a validated team strategy tool.

The strongest fit is race-strategy analytics and performance-data analysis. This is my assessment of the project's content. Williams describes technical work spanning predictive models, performance systems and race-strategy optimization in its [official early-careers overview](https://careers.williamsf1.com/early-careers). That supports the relevance of the subject; it does not establish eligibility for a role or predict a hiring outcome. The project does not yet demonstrate aerodynamic design, mechanical design or telemetry-based vehicle dynamics.

## The evidence a reviewer can inspect

The manuscript separates an analytically tractable decision model from historical forecasting experiments. It reports a 2,187-state synthetic parameter study and preserves both failed and improved forecasting models. A robust revision lowered equal-race mean absolute error by 6.3% against a last-observation baseline on three later events; a subsequent uncertainty study still under-covered at 85.6% for nominal 90% intervals. These are separate sequential experiments, not one unchanged model evaluated on every event.

The numerical follow-up diagnoses a discontinuous deployed-policy value and adds analytic integration over explicitly split decision regions. It checks three refinement-sensitive states at three resolutions and against 600,000 fresh paired trajectories. The full suite has 53 tests. This is a useful example of investigating a discrepancy rather than hiding it behind a visually polished result.

## A five-minute project walkthrough

1. State the decision: an extra lap has an immediate cost but may change the next stop decision. Show why uncertain tyres alone do not make waiting valuable.
2. Explain one posterior update and distinguish observable lap pace from latent degradation. Name the assumptions needed to turn one into evidence about the other.
3. Show the comparison: both policies update from actual observations; only one accounts for future learning when planning. This isolates the intended mechanism.
4. Show the historical failure before the improvement. Explain the initialization problem, how the robust revision was selected on development data, and what the new event results did and did not establish.
5. Show the numerical discrepancy, its diagnosis and the independent check. Finish with the empirical gap: historical pit decisions do not reveal unobserved alternative outcomes.

Use one selected case and one historical diagnostic. Do not walk through every dashboard or every parameter. Be ready to reproduce the case and explain the plotted quantities without reading the manuscript.

## Questions to prepare for an interview

**Why not train a model to predict the team's pit lap?** That is a different supervised task. It measures similarity to observed decisions, which may depend on unavailable information; it does not estimate the benefit of another observation.

**Why did you use two degradation regimes?** They make the belief state and information mechanism inspectable and allow independent verification. Their discrete support limits physical realism. Continuous or hierarchical degradation inference is a future empirical extension, not something already validated here.

**What stops the model from confusing traffic with degradation?** The current historical filters do not fully solve that problem. The paper separates net-pace forecasting from tyre identification, and the controlled model studies a shared-baseline nuisance. A credible extension needs parameter-recovery and contamination checks.

**Why can an uncertainty model look good on average and fail strategically?** Forecast calibration can vary across conditions; decisions are particularly sensitive near pit/stay boundaries. Overall error or interval coverage can conceal failures at the states where the policy changes.

**How do you know the policy-gain calculation is right?** Analytic limiting cases, independent integration, grid refinement and paired trajectory simulation provide complementary checks. None of these establishes real-world model validity.

**What would you improve next with team data?** Establish the actual available information at each decision, include trustworthy context for traffic and fuel effects, test a tyre-specific observation model, and evaluate decision stability on held-out events. Richer inputs help only if their timing and interpretation are reliable.

## Resume wording

Use this under **Projects**, and use only after you can explain and reproduce the work:

**Bayesian pit-timing and race-data analysis — Python, NumPy, SciPy, pandas, FastF1**

- Developed a reproducible Bayesian stopping study across 2,187 simulated race states, comparing information-aware pit timing with an updating certainty-equivalent baseline.
- Evaluated sequential lap-time forecasts on staged held-out events; documented a failed baseline and a robust revision with 6.3% lower equal-race MAE across three later races.
- Investigated numerical instability at decision boundaries and validated a separate integration method using analytic checks and 600,000 paired simulated trajectories.

Do not describe the manuscript as published or accepted until it is. Do not turn simulated gains into claims of actual race-time savings. AI assistance is disclosed in the manuscript; your contribution statement should accurately describe your own design, implementation, interpretation and verification work. The bullet wording is a draft for adaptation, not a determination of personal authorship.

## Publication readiness

A detailed manuscript is available, but the original aim of historically grounded decision validation is still unfinished. The remaining substantive gates are a defensible empirical degradation model, an availability-aware replay, and a clear contribution relative to the closest literature. The new numerical method needs a full-grid rerun before it can replace all original aggregate estimates.

The [Journal of Sports Analytics guidelines](https://journals.sagepub.com/author-instructions/san) require original research advancing knowledge, a reported methodology and discussion in the literature context. They also specify a 200-word abstract, Harvard references, author declarations and data availability information. The present research draft is not yet formatted as a complete submission package. A venue decision should follow a novelty review and supervisor or subject-specialist feedback. No journal submission or public release has been made.

## Reading order

Start with the expanded manuscript, then the reproduction guide and the saved diagnostic results. The interactive forecasting and strategy demos provide explanations, while the paper and machine-readable outputs supply the evidence. For a public portfolio release, add a clean repository, an accurate contribution statement, a short recorded walkthrough and a verified reproduction run on a fresh machine. Those release tasks are not yet completed.
