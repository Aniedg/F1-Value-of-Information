# Experiment 06 — sequential predictive-interval adaptation

## Question and frozen split

Can prediction intervals adapt to changing error scales without modifying the point estimator? All eight previously inspected races become development history. Canada, Spain and Austria 2024 race sessions are reserved before download. The robust v0.5 point configuration is unchanged. The same historical filters and warm-up targets apply.

This is **predictive uncertainty about observed pace**, not epistemic uncertainty about tyre degradation. Traffic, driving choices and other sources of lap variation contribute to these residuals. These intervals cannot be inserted directly as a posterior over tyre parameters in a value-of-information controller.

## Method

For each scored observation, compute absolute prediction error divided by the point filter's uncalibrated working standard deviation. Construct a development residual distribution with each race receiving equal total weight. Approximate it with 201 equally weighted midpoint quantiles. Before each new prediction, mix that distribution with the driver's previous scored standardized errors in the same race, retaining history across stints but resetting it between races. The central interval is symmetric about the fixed point prediction, with half-width equal to the mixture's empirical 90th percentile times the working standard deviation.

Crucially, the current observed lap updates the residual history only after its interval is recorded. No other driver's errors influence a driver's intervals. Only previously scored eligible observations contribute; the first three eligible observations per stint still initialise the point estimator and are not scored.

Six candidates combine history windows 20/40 with prior masses 5/15/30. Selection uses equal-race mean interval score with leave-one-development-race-out residual priors. This is internal development selection, not independent validation of the point model: several of these races previously informed that model. The final selected window is 20 errors and prior mass is 15. Rebuild the final prior using all eight development races, then freeze before test download.

The 90% interval score is width + 20 times distance outside the interval. A lower score balances narrowness and missed outcomes, rather than rewarding unlimited widening. This empirical procedure has no exchangeability-based coverage guarantee and is not an exact Bayesian posterior.

## Comparators

- Original static: preserve the v0.5 interval multiplier learned from its original five development races.
- Recalibrated static: use the same expanded eight-race residual prior as the adaptive method, but no online adaptation.
- Adaptive: update mixture weights using only past errors from the same driver.

All three share exactly the same target observations, point predictions and mean absolute errors. Equal-race metrics are primary. No confidence interval treats serially dependent laps as independent races.

## Fresh test results

There are 2,273 scored forecasts: Canada 190, Spain 1,020 and Austria 1,063. Canada contributes only its eligible dry-compound subset (257 of 1,272 ingested laps pass filters before warm-up exclusions). The result is not whole-race or all-weather validation. No event or difficult scored observation was dropped after inspecting performance.

- Canada: adaptive coverage 77.37%, recalibrated static 59.47%, original static 57.37%. Adaptive mean width 3.620 s versus recalibrated 1.846 s. Interval scores 9.487 versus 10.978.
- Spain: adaptive coverage 88.73%, recalibrated static 87.84%, original static 86.47%. Adaptive width 1.677 s versus recalibrated 1.663 s. Interval scores 3.099 versus 3.272.
- Austria: adaptive coverage 90.69%, recalibrated static 92.57%, original static 91.44%. Adaptive width 1.454 s versus recalibrated 1.677 s. Interval scores 2.317 versus 2.534.

Equal-race mean adaptive coverage is 85.59%, compared with 79.96% for recalibrated static and 78.43% for original static. Adaptive mean width is 2.250 s versus 1.729 and 1.570 s. Mean interval score is 4.968 versus 5.595 and 5.787: approximately 11.2% lower than recalibrated static. It improves that score in every race, yet does not establish 90% coverage, especially in Canada. Austria illustrates that lower coverage is not inherently worse when it is closer to the target and intervals are narrower.

## Verification and remaining research gate

Twenty-nine tests pass, including checks that present/future outcomes do not change earlier interval widths, drivers' histories remain isolated, past errors can widen later intervals, and interval scoring penalises both misses and width. Freeze checks cover protocol, point-model record, source files and development inputs; held-out file hashes match their ingestion manifests and download times follow the freeze. Original result records remain intact.

Adaptive predictive uncertainty is a better benchmark, not a finished tyre belief model. The next scientific step is to distinguish learnable degradation uncertainty from irreducible observation variation, with explicit identifiability assumptions and synthetic parameter-recovery checks. That connection to the original pit-decision question matters more than indefinitely optimising one-step forecasts. Any further empirical calibration redesign consumes these test races as development history and needs new reserved events for claims of transfer.

## Reproduce

    PYTHONPATH=src .venv/bin/python -m pitvoi.interval_experiment train
    PYTHONPATH=src .venv/bin/python -m pitvoi.interval_experiment download
    PYTHONPATH=src .venv/bin/python -m pitvoi.interval_experiment evaluate
    PYTHONPATH=src .venv/bin/python -m pitvoi.interval_report

Freeze/evaluation commands refuse to overwrite existing records. Use a new versioned experiment copy for reproduction; the report command only regenerates display files.
