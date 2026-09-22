# Experiment 08 — Unknown shared baseline in the decision planner

## Scope

This synthetic development experiment implements the next gate from Experiment 07. Both policy comparators now use a joint baseline/regime observation model. A shared static baseline is integrated out exactly; numerical integration and interpolation approximate the subsequent decision optimisation. The derivation and manuscript-ready model description are in `paper/methods-working.md`.

The baseline is common to old and replacement tyres for all remaining laps. It therefore cancels from strategy costs but obscures observations. It is not an independent new offset each lap, not fitted fuel correction, and not a tyre-specific reset. Unknown replacement degradation and time-varying confounding remain unresolved.

## Design

Use the original eight-lap, age-12, equal-prior two-regime example: degradation 0.04/0.30 s per lap of age, independent lap noise SD 1.5 s, known replacement degradation 0.06, pit loss 18 s. Baseline SD is 0, 1.5, 3 or 6 s. These illustrative settings are not empirically fitted. Both policies update from actual observations; only the adaptive planner anticipates future updates.

Each correct-model central case uses three numerical resolutions and 30,000 paired rollouts. An exploratory 4 × 6 grid combines baseline SD with pit losses 8, 12, 18, 24, 32 and 40 s. Every grid cell is retained. A misspecification arm fixes actual baseline SD at 6 and assumed SD at 0, 1.5 or 6; both comparators share each assumed model. Saved stop counts use index 8 for no stop, not a stop after the finish.

## Results

Fine-resolution gains are 4.387, 2.673, 1.146 and 0.000 s as baseline SD increases. The initial action changes from stay to pit at the sampled SD 6 state. This does not locate an exact threshold or prove monotonicity in all parameters. Zero gain arises because both policies stop immediately; continued hypothetical observations can still be informative.

When baseline uncertainty is ignored despite actual SD 6, gain is −0.145 s, with a 95% paired simulation interval from −0.273 to −0.017 s. Underestimated SD 1.5 yields −0.070 s with interval −0.199 to 0.058 s. The matched SD 6 case yields zero. The figure presents raw development comparisons; there is no corrected population-level significance or real-race gain claim.

Numerical central-case gains from intermediate to finest resolution differ by at most 0.010 s. Quadrature changes are not a certified convergence bound. Sampling intervals exclude numerical, parameter and structural model uncertainty. Rollouts integrate baseline/noise by independent simulation instead of reusing the planner's quadrature nodes. Common random draws across assumptions improve comparability but do not make cases independent replications.

## Checks and limitations

41 tests pass. New checks include exact recovery of the original solver at zero offset, sequential posterior equality with an independently calculated dense multivariate Gaussian likelihood, a two-lap scalar-integration value check, no-learning limits, independent paired rollout agreement, and cancellation of common baseline costs for every stop schedule.

The historical forecasting work is not a validation of this baseline model. Future work must address replacement-tyre uncertainty, observation availability, nuisance identification and a frozen final experiment before a practical strategy claim. The paper's requested historical decision replay remains required.

## Reproduce

```sh
PYTHONPATH=src .venv/bin/python -m pitvoi.nuisance_experiment
PYTHONPATH=src .venv/bin/python -m pitvoi.nuisance_report
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests
```

Results and hashes: `results/nuisance-experiment.json`. Dashboard: `results/nuisance-demo.html`. Figure: `results/nuisance-validation.svg` and PNG. These files are versioned development outputs, not a preregistered final study; the experiment command rebuilds them.
