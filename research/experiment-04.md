# Experiment 04 — frozen-model replication across races

## Design

The next three chronological 2024 Grands Prix after Saudi Arabia were selected before downloading: Australia, Japan and China, race sessions only. This extends the first held-out test without changing the model. The selection record is `multi-race-protocol.json`; individual ingestion selections are also saved.

Model settings and baseline interval widths remain those chosen on Bahrain in experiment 03. Ingestion uses the same historical quality filters. Before evaluating, the script verifies checksums of the frozen settings, model code, original model protocol, Bahrain data, ingestion code and each processed test dataset. The evaluator's own hash is recorded with the results. The first multi-race result refuses overwrites.

Every race is reported separately. The primary aggregate gives equal weight to each race's metric. For RMSE, this means the arithmetic mean of race-level RMSEs. A secondary pooled result gives equal weight to each forecast and computes RMSE from all squared errors. These are different summaries; the dashboard exposes both and identifies which is primary.

The original Saudi Arabia result remains separate from this new batch because it had already been inspected when the extension was designed. No event is removed based on performance. No model fitting, recalibration or baseline fitting uses the three new races.

## Interpretation

This is a descriptive replication test on three events, not sufficient evidence for population-level significance. Laps are serially dependent, drivers share race conditions and event counts are small. Do not attach confidence intervals that incorrectly treat thousands of laps as independent races.

The target remains the next eligible observation in a recorded continuing stint, after three initial eligible observations. It is not necessarily the immediately next race lap. Green-flag and dry-compound selection excludes other race conditions. Retrospective FastF1 flags are not proven to be available as-of. The model predicts net pace, not physically identified tyre wear or alternate pit-strategy outcomes.

The report retains the five largest model misses in every race and includes them in all scores. Their causes are not inferred from timing errors alone. They may guide later development, but any model changes based on this batch require new evaluation races.

## Reproduction

    PYTHONPATH=src .venv/bin/python -m pitvoi.historical --selection research/selection-australia.json
    PYTHONPATH=src .venv/bin/python -m pitvoi.historical --selection research/selection-japan.json
    PYTHONPATH=src .venv/bin/python -m pitvoi.historical --selection research/selection-china.json
    PYTHONPATH=src .venv/bin/python -m pitvoi.multi_race
    PYTHONPATH=src .venv/bin/python -m pitvoi.multi_report

The final command safely rebuilds the presentation from saved evaluation results. Use a separate experiment record/copy to rerun evaluation; do not overwrite the original record.

## First recorded results

The new batch contains 1,869 scored forecasts: Australia 688, Japan 608 and China 573. All frozen checks passed; 21 software tests pass. Including the original Saudi Arabia test, the unchanged model now has 2,557 scored forecasts across four non-development races. The original and new batch remain separately reported.

- Australia: model MAE 0.3544 s versus last observation 0.3635 s; RMSE 0.5987 versus 0.6407 s; model 90% coverage 89.83%.
- Japan: model MAE 0.6709 s versus 0.4536 s; RMSE 1.1633 versus 0.7018 s; model 90% coverage 77.80%.
- China: model MAE 0.2770 s versus 0.2869 s; RMSE 0.3813 versus 0.4020 s; model 90% coverage 96.51%.

Equal-race mean MAE is 0.4341 s for the model versus 0.3680 s for last observation (17.96% worse). Equal-race mean RMSE is 0.7144 versus 0.5815 s (22.86% worse). Mean model 90% coverage is 88.04%, but this average masks substantial between-race variation. The pooled-lap results are retained separately: MAE 0.4336 versus 0.3693 s; RMSE 0.7853 versus 0.6007 s.

This is a failed generalisation gate for the current model. Two small per-race advantages do not outweigh Japan's large failure. The data do not justify advancing this version to claims about real pit-strategy gains.

## Post-test diagnostic, without altering the test

The processed Japanese race records show GAS's first eligible observation in stint 2 at lap 3 as 138.362 s. Subsequent eligible laps 4 and 5 are 99.925 and 99.473 s. All three pass the existing timing/green-flag filters, and the first three initialise the filter without being scored. By the pre-lap-8 forecast, the model's learned net slope is -3.353 s/lap; it predicts 95.496 s versus an observed 101.363 s. The last-observation baseline at that point is 100.248 s.

This provides a concrete example of an unusual initial observation distorting the trend long after initialization. It shows that a timing-valid observation need not represent ordinary race pace. Timing records alone do not establish the complete physical cause, and this example does not attribute all of Japan's excess error to one mechanism. The first five largest misses for every race are saved in the report; no observations were removed after seeing errors.

FastF1 also warned that China's leader completed the distance 8.313 s before the recorded session end. No alignment adjustment was invented; the exported records and original quality decisions were retained.

## Next research decision

Preserve this model as a failed-but-useful baseline. Investigate initialization and race-interruption context, and compare a model robust to unusual observations with the same naive baselines. Define a new version with settings chosen from the now-inspected development history, and reserve new chronological races before evaluating it. Avoid simply deleting the problematic Japan laps or broadening intervals until the aggregate looks favorable. Physical tyre identifiability and counterfactual strategy validation remain separate unresolved gates.
