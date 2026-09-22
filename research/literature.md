# Initial literature leads

Initial search: 22 September 2026. This is a starting bibliography, not a systematic review. No “first” or novelty claim is justified yet.

## Bayesian tyre modelling

Cole Cappello and Andrew Hoegh, *A State-Space Approach to Modeling Tire Degradation in Formula 1 Racing*, arXiv:2512.00640, submitted 29 November 2025.

https://arxiv.org/abs/2512.00640

Abstract and data/model sections inspected. It describes Bayesian latent tyre modelling using FastF1 timing data, fuel effects, pit resets and several observation/degradation extensions. Its fuel series is assumed rather than directly observed. This directly overlaps the proposed inference component. Remaining methods and code still need review; these inspected sections do not establish whether future learning is included in strategy optimisation.

Full-text source: https://arxiv.org/html/2512.00640v1

## Pit-stop dynamic programming

*Optimizing pit stop strategies in Formula 1 with dynamic programming and game theory*, European Journal of Operational Research, 319(3), 908–919, 2024.

https://www.sciencedirect.com/science/article/pii/S0377221724005484

Publisher search excerpt inspected; full-page access returned HTTP 403. Treat this as a lead, not a reviewed method. Obtain an accessible author manuscript, verify full citation metadata, and inspect the treatment of uncertainty and online observations.

## Bayes-adaptive foundations

Stéphane Ross, Brahim Chaib-draa and Joelle Pineau, *Bayes-Adaptive POMDPs*, NeurIPS 2007.

https://papers.nips.cc/paper_files/paper/2007/file/3b3dbaf68507998acd6a5a5254ab2d76-Paper.pdf

Abstract and introductory formulation inspected. The paper explicitly integrates model learning and action planning, motivating why the belief belongs in the state. Our first experiment is a much smaller Bayesian stopping problem with a known observation likelihood and a two-point latent parameter, not an implementation of their general algorithm.

## Review checklist

For each relevant paper record: latent uncertainty; online versus retrospective inference; observations available to each action; objective; planning horizon; whether hypothetical observations update future beliefs; baselines; counterfactual validity; code/data access; and precise overlap with this project. Search also for optimal stopping with costly information, dual control, and maintenance decisions before finalising the novelty statement.

## Targeted update — 22 September 2026

This is a source-screening update, not a completed systematic review. Findings below are limited to the versions and sections inspected.

- **Cappello and Hoegh (2026), published version.** [Publisher full text](https://journals.sagepub.com/doi/full/10.1177/22150218261446170), DOI 10.1177/22150218261446170. Inspected introduction, data, model, evaluation description and conclusion. The published study expands validation to 19 race sessions and uses an AR(1) comparator; the older preprint description above should not substitute for the published result. It models latent tyre pace with fuel covariates and pit resets, with Gaussian and skewed observation alternatives. Fuel is assumed rather than measured. Our inference work therefore overlaps substantially. The inspected material centers on estimation and prediction; it does not establish an acquisition-of-information pit policy. This is a candidate distinction, not proof of novelty. Some equations are missing from the extracted HTML; inspect the PDF/code before attempting reproduction.

- **Fieni et al., Towards Learning-Based Formula 1 Race Strategies, arXiv:2512.21570v1.** [Primary manuscript](https://arxiv.org/html/2512.21570v1). Abstract and introduction inspected. It combines tyre wear, energy allocation and pit timing using mixed-integer nonlinear programming and an RL environment. “Learning-based” alone does not establish Bayesian learning about hidden degradation. Need to inspect observation/state definitions and transition assumptions before classifying it as a future-information comparator.

- **Opponent State Inference Under Partial Observability: An HMM–POMDP Framework for 2026 Formula 1 Energy Strategy, arXiv:2603.01290v1.** [Primary manuscript](https://arxiv.org/html/2603.01290v1). Inspected abstract, belief update and policy sections. It uses an HMM belief over opponent energy/tyre states and a proposed DQN energy-deployment policy; the version explicitly distinguishes synthetic inference evaluation from deferred empirical policy comparisons. Relevant partial-observability overlap, but not evidence that our pit-delay question is already answered. Treat as a preprint, not independently validated evidence. Do not copy its technical claims without checking them.

- **2024 dynamic-programming/game-theory paper:** publisher full-page access again failed. It remains an unresolved closest-work review item; do not infer absence of learning from a search excerpt.

Next review actions: accessible full text for the 2024 paper; complete state/action/observation audit of the two preprints; optimal stopping with costly observations, Bayesian maintenance, and dual-control foundations. No “first,” “novel framework,” or publication-readiness claim is supported yet.

## Manuscript v1 references

The final manuscript uses seven verified references, recorded in `paper/references.bib`. The 2024 game-theory paper's publisher abstract and section summaries were available during this pass, including authors Felipe Aguad and Charles Thraves and DOI 10.1016/j.ejor.2024.07.011; direct full-page requests still returned 403. The manuscript limits its comparison accordingly. Added primary-author records for Ross et al.'s Bayes-adaptive framework, Harrison and Sunar's costly-learning stopping problem, and Gneiting and Raftery's scoring rules. No systematic search completeness or priority claim is made.
