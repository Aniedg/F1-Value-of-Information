# Reproducing manuscript version 2

## Read and inspect

The main outputs are `output/pdf/value-of-information-f1-paper-v2.pdf`, `output/docx/value-of-information-f1-paper-v2.docx` and `paper/manuscript-v2.md`. The numerical and empirical claims are traceable to the JSON records below. This is a completed model-based mechanism study with a negative historical forecasting result; submission and acceptance are not claimed.

## Evidence map

- `results/segmented-study.json`: 2,187 states, 24 refinements, 1.2 million fresh paired trajectories. Supersedes the original full-grid values in the version 2 paper.
- `research/segmented-study-protocol.json`: source hashes, dimensions, thresholds and the same 24 validation indices retained from version 1.
- `results/historical-decisions.json`: 2,173 before-update forecasts, 526 central decision states, nine sensitivity combinations per event and 36 prespecified refinements.
- `research/historical-decisions-frozen.json`: eleven development-input hashes, four noise candidates, fixed rate hypotheses, selected noise, reserved events and source hashes.
- `research/replay-ingestion-amendment.json`: correction of FastF1's fuzzy event-name match; explicit round and event-name checks were used before replay evaluation.
- `results/global-change-audit.json`: post-run check of the state with the largest original-to-revised gain correction (index 2160). Its refined gain of 1.334572 s lies within the 200,000-pair interval [1.305796, 1.374810] s. This is a diagnostic selected after the grid, not a confirmatory sample.
- `results/history-policy-audit.json`: post-test checks of the largest central gain in each reserved event, using 300,000 paired conditional trajectories in total.
- `results/recovery-study.json`: 20,000 matched latent trajectories reused across four nuisance settings and evaluated at four observation counts. Do not count the correlated settings as independent races.
- `results/segmented-audit.json`: earlier three-case diagnostic with 600,000 pairs, retained as development history.
- Earlier forecast and interval JSON records: version-specific historical evidence in Sections 7.1-7.3.

## Rebuild the paper without downloads

Use Python 3.13 with `requirements-research.txt` and `paper/requirements-publication.txt`. The tested research environment and frozen versions are retained in prior manifests. Run the commands in the main README. `verify_v2.py` checks source hashes, numeric identities, reported counts and protocol consistency from archived outputs. It does not substitute for running the test suite or for checking the physical model.

The Word builder uses `python-docx`; the body and tables are editable, while display equations are images generated from the retained mathematical source. The PDF builder uses ReportLab and Matplotlib. The convenience HTML is generated during the build and references intermediate equation images; it is not a standalone web publication.

## Recompute the synthetic studies

Work in a separate copy of the project. Preserve the existing result JSON under a reference filename before running an experiment, because scientific commands intentionally refuse to overwrite results. Keep the supplied full-grid protocol unchanged, then use:

```sh
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 python -m pitvoi.segmented_study run
```

Do not call `freeze` again to reproduce the existing study. The source and protocol hashes must match. Runtime depends on the machine; numerical values can differ at floating-point precision. Recompute the parameter-recovery diagnostic in a separate copy without its existing `research/recovery-protocol.json` or `results/recovery-study.json`; the script writes its fixed settings before generating results. Compare numerical outputs to the reference, allowing metadata timestamps to differ.

## Historical input reproduction

The replay model was frozen before the three reserved events were loaded. Event identity is recorded explicitly: British Grand Prix round 12, Hungarian Grand Prix round 13 and Belgian Grand Prix round 14 of 2024. A fuzzy-name lookup initially returned a duplicate of Austria; its rejected manifest is preserved, and that data was not evaluated as a new test event.

Strict ingestion commands use `pitvoi.strict_ingestion` with `research/selection-replay-EVENT.json`. They require network access. The raw and audited input hashes are recorded in each event manifest. Original raw timing caches are not distributed in the source archive. Recomputing the inference also requires the eleven original development input snapshots because the frozen evaluator checks those hashes. If upstream records have changed, preserve both snapshots and report the difference; do not disable hash checks to make a changed dataset look like the original experiment.

`PYTHONPATH=src python -m pitvoi.historical_decisions evaluate` reconstructs the forecast/decision output when the original matching inputs are present. `PYTHONPATH=src python paper/history_policy_audit.py` recomputes its separate conditional simulation check after preserving the old audit file. The per-target predictions in the release support independent recomputation of the reported forecast metrics even without retrieving raw feeds.

## What is complete and what is outside the claim

The local paper, calculations, held-out conditional replay, recovery study, sensitivity results and source package are complete. The historical result is unfavourable for the simple observation model and is retained as a result, not hidden as unfinished work. The study does not identify physical tyre truth, demonstrate causal race savings, reproduce live timing availability or provide a team-ready strategy engine. Those are stronger future research claims, not prerequisites for reporting this bounded study honestly.

A submission still needs author-approved identity, contribution, funding, conflict, ethics and data-availability declarations, a venue decision and an actual submission action. The manuscript uses a 200-word abstract and author-date references, but a journal decides scope, novelty and acceptance. Independent expert review is advisable and has not been represented as completed.
