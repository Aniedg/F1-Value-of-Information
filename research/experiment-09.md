# Experiment 09 — Uncertain replacement performance

## Design

Synthetic development study extending Experiment 08, not a final frozen evaluation. Keep the current-set regimes 0.04/0.30, equal prior, eight remaining laps, starting age 12, pit loss 18 s and independent lap noise SD 1.5 s. Baseline SD is 0, 3 or 6 s and is correctly specified, static, shared by both sets, and independent of their joint prior.

Four replacement assumptions: known rate 0.06; independent rates 0.02/0.10 with equal probabilities; the same marginal rates positively related to old degradation (conditional high probabilities 0.125/0.875); or negatively related (0.875/0.125). Thus the uncertain cases have the same marginal variance and mean, and all four have the same initial expected pit cost. The assumed relationships are illustrative.

A new `ReplacementSolver` changes the stop payoff to depend on the posterior conditional mean of replacement degradation. Both deployed comparators update identically. Actual sampled replacement rates determine simulation cost. The derivation, including the independent-uncertainty invariance result, is in `paper/methods-working.md`.

## Results

At baseline SD 3, expected gains over the updating frozen-belief comparator are 1.136, 1.136, 1.020 and 1.253 s for known, independent, positive and negative dependence. Exact equality of known/independent Bellman values is also tested across the entire belief/time grid; simulation estimates can differ because independent replacement noise changes realized outcomes.

At baseline SD 0 the corresponding gains are 4.396, 4.396, 4.141 and 4.652 s. At SD 6 they are 0, 0, 0 and 0.0085 s. The negative-dependence SD-6 case is marginal: additional resolution gives 0.0111 s, while the simulation interval includes zero widely. Do not present its nominal action switch as evidence of a meaningful improvement.

Changing dependence changes conditional relative tyre performance as well as cross-set learning. This experiment does not establish that one sign of dependence is generally better, or that physical tyre uncertainty is calibrated from historical data. Independent replacement variance becomes irrelevant only under this restricted linear, risk-neutral, final-stop model.

## Numerical and simulation checks

Base resolution 1,601 belief points/41 quadrature nodes; main resolution 3,201/81 for all 12 cases. Additional 6,401/161 checks cover all four SD-3 cases plus the positive and negative SD-6 cases. The extra SD-6 checks were added after seeing a near-boundary action difference; this is an explicitly adaptive development diagnostic, not preregistration.

Every main case runs 30,000 paired simulations with common random draws across scenarios. A secondary actual-positive-dependence check uses assumed independent, positive and negative relationships. Its intervals are per-comparison sampling intervals, not multiplicity-adjusted claims or uncertainty over model validity.

47 tests pass, including an independent nested-integration three-lap value check, joint four-state Bayes update, independent-variance invariance, known-regime schedule enumeration and physical-trajectory Monte Carlo agreement. Existing frozen historical models were not changed.

## Reproduce

```sh
PYTHONPATH=src .venv/bin/python -m pitvoi.replacement_experiment
PYTHONPATH=src .venv/bin/python -m pitvoi.replacement_report
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests
```

Saved JSON contains parameters, source hashes, numerical reports, seeds, paired intervals and stop-count distributions (last bin means no stop). Outputs: `results/replacement-experiment.json`, `replacement-demo.html`, `replacement-validation.png`, `replacement-validation.svg`.

## Next gate

Stop expanding the toy model by default. Specify and freeze the final synthetic study around the current model: boundary concentration, no-learning controls, shared-baseline sensitivity, replacement dependence, and declared misspecification scenarios. Preserve the historical replay requirement and complete the outstanding literature/as-of-data audit. This development result alone is not a finished research paper.
