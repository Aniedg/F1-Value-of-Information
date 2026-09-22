# Experiment 07 — Predictive uncertainty versus learnable degradation

## Design and scope

Controlled synthetic mechanism study, not a historical validation or preregistered empirical result. Reuses Experiment 02's one-optional-last-stop solver without modifying prior frozen models. Initial tyre age 12, horizon 8, equal regime probabilities, mean degradation 0.17 s per lap of age, replacement degradation 0.06, pit loss 18 s.

Three regime half-spreads (0.02, 0.08, 0.13) hold initial predictive mean at 2.04 s and variance at 4.6836 s² by setting observation variance to 4.6836 − 12² × spread². With known baseline, Var(y) = age² Var(theta) + observation variance. Full predictive distributions are not equal; neither are their future variances. Regime spread also changes physical decision stakes. This is not an isolated causal estimate of information quality with all costs held fixed.

## Decision results

Expected adaptive gains against the deployed, updating frozen-belief planner are 0.000, 0.402 and 4.373 s respectively. Numerical refinement from 1,601 belief points/41 quadrature nodes to 3,201/81 changes gains by 0.000, 0.0006 and 0.0230 s. Independently sampled 30,000 paired policy rollouts per case provide sampling intervals in the saved results. Those intervals exclude numerical and model uncertainty. The additional pit-loss grid is 8, 12, 18, 24, 32, 40 s; all cells are retained, including zero gains. Refinement checks apply to the central 18 s cases, not every grid cell.

## Recovery with an unknown baseline

For a separate diagnostic, simulate y_i = age_i theta + b + epsilon_i. One persistent b per trajectory is drawn from N(0, 6²); epsilon is independent Gaussian with the case-specific observation variance. Integrating b yields covariance sigma² I + 36 11'. Equal-prior regime posterior odds follow the two multivariate-normal likelihoods with that covariance. A zero-offset arm uses a known baseline. Each arm contains 20,000 independent trajectories; seeds are saved, and common random draws support comparison between arms.

After eight observations in the widest-regime case, classification accuracy is 99.99% with a known baseline and 74.03% with the unknown offset. Correctly integrating the offset gives Brier score 0.174; incorrectly assuming zero offset gives 0.365 (the uninformative 50% prior scores 0.25). In the narrowest case, correct inference gives Brier 0.249 with the unknown offset: almost no learning.

Recovery observes all eight laps irrespective of a pit policy. It does not establish learning available before an actual stopping decision. The offset model is deliberately simple and does not identify fuel, track evolution, traffic or tyre degradation in real data. Its prior is illustrative, not estimated.

## Interpretation and next gate

Equal initial predictive variance does not imply equal value of information. Strong known-baseline recovery is fragile to persistent nuisance uncertainty. The decision solver has NOT yet been extended to the nuisance model; its reported gains cannot be claimed for that setting. Next implement joint baseline/regime belief-state planning or a validated approximation, with the same nuisance model for both policy comparators, before attempting historical strategy claims. Literature-based novelty assessment and as-of historical observation auditing remain outstanding.

## Reproduction

From the project root:

```sh
PYTHONPATH=src .venv/bin/python -m pitvoi.information_experiment
PYTHONPATH=src .venv/bin/python -m pitvoi.information_report
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests
```

Outputs: results/information-experiment.json and results/information-demo.html. Thirty-two tests pass, including comparison with an independent dense covariance likelihood, equivalence to sequential known-baseline updates, and a constant-age/nonidentified diffuse-offset limit.
