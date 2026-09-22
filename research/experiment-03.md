# Experiment 03 — first held-out race forecast

## Question and split

Can a sequential Bayesian pace model, with settings selected on Bahrain 2024, predict the next eligible within-stint observation in Saudi Arabia 2024? The second race was chosen chronologically before download, not for a favorable result. This is a first transfer test, not sufficient evidence of broad generalisation.

The machine-readable protocol is `forecast-protocol.json`. Forty-eight candidates combine observation noise and process noise settings. Select once by mean Gaussian negative log predictive density on the development race. Save the selected settings, every candidate, data and code hashes before downloading the test race. Evaluation checks those hashes and refuses to overwrite its first saved result. Presentation code is separate and may change without refitting.

## Observation model

The latent state is current pace and net slope. Across a gap of d laps, predict with F=[[1,d],[0,1]]. A local-level random walk and an integrated random slope give process covariance Q=[[q_level*d+q_slope*d^3/3,q_slope*d^2/2],[q_slope*d^2/2,q_slope*d]]. Observe pace plus independent Gaussian noise. A Kalman update conditions on the newly observed lap. The static linear model is the special case of zero process noise.

Each driver/stint starts from a diffuse pace prior and a zero-mean slope prior with standard deviation 0.15 seconds per lap. No future observations initialise the intercept. The first three eligible observations update the state without being scored. Every subsequent forecast is saved before updating with its target. Missing/filtered laps advance the elapsed tyre-age gap, with corresponding propagation of uncertainty.

Comparators predict the last eligible observation or the expanding mean of earlier observations in that stint. Their Gaussian interval widths are fitted only to Bahrain forecast errors. Every method scores identical target observations. Metrics are mean absolute error, root mean squared error, bias, negative log predictive density, empirical 90% predictive coverage and mean interval width.

## Interpretation and identifiability

The model estimates **net pace**, not separately identified tyre degradation. If fuel and track effects improve pace by c seconds per lap, then the conditional tyre interpretation is net slope + c. The demo shows predeclared scenarios c=0,0.04,0.08,0.12. Those are illustrative assumptions, not measured fuel corrections or literature-derived estimates. Holding c fixed shifts the slope's interval but excludes uncertainty about c.

Within a stint, tyre age and race lap are affine functions of one another; no regression can separate their linear effects from these observations alone. The stochastic level may absorb traffic, management, warm-up and track effects, but that does not identify their physical causes. Good net-pace predictions would not, by themselves, validate counterfactual fresh-tyre pace or a pit policy.

## Scope of the held-out claim

The race is held out from parameter selection, but the model updates on earlier observations within that race. This is sequential adaptation, not predicting a whole race before it starts. Predictions are conditional on remaining in the recorded stint and on the next observation satisfying retrospective quality filters. Future pit actions are not used as features, but this conditional subset is not an unconditional live forecasting task.

Historical eligibility can incorporate retrospective FastF1 checks. Therefore target-time arithmetic is prefix-safe, while the full data selection is **not established as live/as-of valid**. No pace-based trimming removes difficult observations. No iid-lap significance interval is reported because laps are serially dependent and drivers share a race environment. More held-out races are needed to assess between-race uncertainty.

## Reproduce

From a fresh project copy with the data and research dependencies:

    PYTHONPATH=src .venv/bin/python -m pitvoi.forecast_experiment train
    PYTHONPATH=src .venv/bin/python -m pitvoi.historical --selection research/holdout-selection.json
    PYTHONPATH=src .venv/bin/python -m pitvoi.forecast_experiment evaluate
    PYTHONPATH=src .venv/bin/python -m pitvoi.forecast_report

Existing frozen/evaluation files intentionally block overwriting. Inspect the saved outputs, or reproduce in a separate copy with a new experiment record. After this test has been inspected, Saudi Arabia is not an untouched test set for future design choices.

## Verification

The tests compare the static filter with an independent batch Bayesian regression, check that current/future observations cannot change earlier predictions, verify stint resets and warm-up handling, test propagation across lap gaps, and reject invalid parameters and observation order. Frozen hashes verify that test evaluation uses the recorded model and protocol.

## Recorded first test result

The selected model uses observation SD 0.3 seconds, level-process SD 0.3 seconds per square-root lap, and zero slope-process noise. It therefore learns a constant uncertain slope within a stint while allowing random shifts in pace. Selection used 820 scored Bahrain forecasts. Its development MAE was 0.279 s and 90% interval coverage was 93.4%; these are selection-set metrics, not unbiased performance estimates.

The Saudi Arabia ingestion returned 901 laps, of which 802 passed the existing filters. After three initial observations per stint, 688 forecasts across 19 drivers were scored. FastF1 emitted an alignment warning for driver number 10 during ingestion; the data-quality inventory retains the exclusions. The 20-driver entry list must not be confused with the 19 drivers contributing scored predictions.

On the held-out forecasts:

- Bayesian pace trend: MAE 0.37494 s, RMSE 0.70180 s, mean negative log predictive density 1.17702, empirical 90% coverage 88.66%, average interval width 1.65910 s.
- Last observation: MAE 0.37207 s, RMSE 0.73255 s, mean negative log predictive density 1.27262, empirical 90% coverage 89.53%, average interval width 1.68501 s.
- Expanding mean: MAE 0.89056 s, RMSE 1.10353 s, mean negative log predictive density 2.42598, empirical 90% coverage 54.80%, average interval width 1.75717 s.

The model has approximately 0.77% higher MAE but 4.20% lower RMSE than the last-observation baseline. It has lower MAE for 10 of 19 scored drivers. These are descriptive comparisons, not significant universal improvements. The model's signed error (observed minus predicted) averages +0.115 s, which is another reason not to describe it as fully validated. Settings were not revised after observing this result.

Inspecting multiple interval levels also matters: nominal 50% intervals cover 67.3%, while nominal 99% intervals cover only 95.1%. Thus the near-90% headline does not imply the whole predictive distribution is calibrated. This pattern is consistent with a misspecified error distribution (many small errors plus large misses), but does not identify the cause. Any subsequent heavy-tailed or traffic-aware model must be evaluated on newly reserved races.

This passes the engineering milestone of a frozen, separately tested forecasting pipeline, but does not establish an overall predictive advantage, physical degradation identification or useful pit-strategy gains. Before further model redesign, preserve this baseline and define additional chronological evaluation races. If Saudi Arabia informs new design choices, treat it as development history and reserve new events for subsequent tests.
