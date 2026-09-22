# Experiment 05 — robust pace estimation

## Design before the new test

All five previously inspected races (Bahrain, Saudi Arabia, Australia, Japan, China) are now development history. The next three chronological Grands Prix—Miami, Emilia Romagna and Monaco 2024—are reserved as new test races before downloading. Race sessions only; sprint sessions are not included. No changes to historical quality-control or target selection are made.

The original v0.3 estimator remains unchanged. The new version is a robust state estimator, **not an exact Bayesian posterior**. It uses a Gaussian filter's covariance as a working uncertainty scale, subject to empirical predictive calibration.

## Candidate safeguards

- Median warm-start: after the first three eligible observations, initialise pace to their median, slope to zero, and working covariance to diagonal entries observation-noise variance and 0.15 squared. Those three observations are already available before the first scored prediction. This deliberately avoids treating the first unusual lap as a permanent anchor.
- Clipped innovation: cap each later update's residual at a selected multiple of its pre-observation predictive standard deviation. The actual observation remains the scored target. No difficult lap is deleted from evaluation.
- Optional gap reset: when elapsed tyre age jumps by more than one between eligible observations, reset pace to the last available observation and slope to zero before propagating across the gap. This is a gap heuristic, not verified interruption detection.

Fifty-four configurations combine three observation-noise scales, three level-process scales, three clipping thresholds (including effectively no clipping), and gap reset on/off. Select minimum equal-race mean absolute error on development data. The selected configuration is noise SD 0.6 s, level-process SD 0.6 s per square-root lap, innovation clip 2.5 predictive standard deviations, and **gap reset disabled**. Development did not support automatically resetting on gaps.

## Predictive intervals

The working covariance is not assumed calibrated. Compute the equal-race-weighted empirical 90th percentile of absolute standardised development residuals. Divide by the Gaussian central-90% multiplier (1.64485) to obtain a scale applied to prediction standard deviations. The frozen scale is approximately 0.4614. It changes reported intervals, not point forecasts or updates.

For the last-observation comparator, calibrate a constant-width interval from the same development races using the weighted 90th percentile of its absolute errors. The original model keeps its original interval settings. This asymmetry is explicit: the new estimator and current naive comparator have development-calibrated intervals; the old model is preserved for comparison. Gaussian negative log scores in JSON are working-density diagnostics, not a claim that robust updates imply a Gaussian posterior or that one calibrated quantile calibrates the whole distribution.

These are empirical intervals, not guaranteed conformal intervals. Temporal and cross-driver dependence violate a simple independent-observation argument; the new races supply the actual predictive-coverage check.

## Development ablations

Turn off median initialisation, clipping or gap resets one at a time while holding other selected settings fixed. These are exploratory development comparisons, not held-out causal attribution or independently retuned competitors. Because the selected configuration disables gap resets, its no-gap-reset ablation must be identical.

## Test integrity and limits

Settings, source hashes, development-data hashes and the original frozen record's hash are saved before downloading the three reserved races. Evaluation verifies the record and compares identical driver/lap targets across robust, original and last-observation predictors. The first result refuses overwrites. Race-level summaries are primary; aggregate metrics are arithmetic means of race-specific metrics, including RMSE.

The target remains net pace under retrospective filtering, conditional on the same recorded stint and an eligible observation. It is not physically identified degradation, a verified live/as-of system or evidence of counterfactual pit gains. Three test races permit a useful replication but not a strong population-level significance claim.

## Reproduce

    PYTHONPATH=src .venv/bin/python -m pitvoi.robust_experiment train
    PYTHONPATH=src .venv/bin/python -m pitvoi.robust_experiment download
    PYTHONPATH=src .venv/bin/python -m pitvoi.robust_experiment evaluate
    PYTHONPATH=src .venv/bin/python -m pitvoi.robust_report

The first three commands are for a fresh versioned experiment copy; saved freeze/evaluation records intentionally prevent overwriting. The report command rebuilds the display without refitting.

## Verification

Twenty-six tests pass. New tests check that the median start rejects a synthetic first-lap contamination without inventing a trend, current/future values cannot alter earlier forecasts, gap resets use only past observations, clipping limits a later outlier's influence, and weighted quantile calculation behaves correctly. Original model and evaluation tests remain intact.

## Recorded fresh-race results

The frozen version was evaluated on 2,922 target observations: Miami 793, Emilia Romagna 1,027 and Monaco 1,102. Each target matches the original model's driver/lap target. Source-data hashes match the ingestion manifests, all retrieval times follow the freeze time, and no model settings were changed after evaluation.

- Miami: robust MAE 0.3065 s, original 0.3159 s, last observation 0.3174 s. Robust 90% interval coverage 92.43%.
- Emilia Romagna: robust MAE 0.3796 s, original 0.3889 s, last observation 0.4088 s. Robust coverage 86.76%.
- Monaco: robust MAE 0.5844 s, original 0.6291 s, last observation 0.6299 s. Robust coverage 75.77%.

Equal-race mean MAE is 0.4235 s for the robust estimator, 0.4446 s for the original and 0.4520 s for last observation. That is 4.75% lower than the original and 6.31% lower than last observation. Mean race RMSE is 0.6602 s versus 0.6842 and 0.7306 s respectively. The robust estimator has lower MAE and RMSE than both comparators in all three races, but this remains a descriptive three-event result, not a significance claim.

Uncertainty does not pass the desired validation gate. Mean race coverage for nominal 90% intervals is 84.99%, despite empirical development calibration. Mean robust interval width is 1.511 s; original and last-observation widths are 1.659 and 1.572 s. Monaco is particularly under-covered. A lower point-error metric must not be presented as successful calibration of the full predictive distribution.

On development ablations, mean MAE was 0.3375 s for the selected estimator, 0.3508 without median initialisation, and 0.3401 without clipped updates. Disabling gap reset produces the identical selected model because resets were already disabled. These findings motivated the design but are not new evidence independent of selection.

## Next gate

Preserve this as the first robust baseline with an encouraging fresh-race point-prediction result. Before integrating its uncertainty into information-aware pit decisions, investigate race-dependent variability and a probabilistic observation likelihood that can represent both routine noise and large deviations. Fixing interval coverage by using inspected test outcomes would consume those races as development data; any subsequent calibration claim needs newly reserved events. Tyre/fuel/traffic identifiability and counterfactual strategy validation are still unresolved.
