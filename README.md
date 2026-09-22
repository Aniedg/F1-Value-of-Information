# The value of information in Formula One pit strategy

A completed research manuscript and reproducible data-analysis project investigating when an additional lap of information can justify delaying a pit stop.

Start with the [version 2 PDF](output/pdf/value-of-information-f1-paper-v2.pdf), [editable Word manuscript](output/docx/value-of-information-f1-paper-v2.docx), and [reproduction guide](paper/REPRODUCIBILITY-V2.md). The manuscript is a model-based study with a held-out conditional historical replay. It has not been submitted or accepted for publication.

## Research result

Within the declared stopping model, waiting is optimal when the expected continuation benefit of learning exceeds the frozen planner's cost disadvantage of waiting. An unknown baseline can obscure the information; independent replacement uncertainty with the same mean does not change risk-neutral decisions. Correct-model gains can disappear or reverse under misspecification.

The corrected 2,187-state study changes initial decisions in 319 states and estimates an equal-state mean simulated benefit of 0.376543 seconds. The full grid uses analytic integration across policy boundaries. Twenty-four refined cases agree with new paired simulations; these comparisons are conditional on the model.

The separately frozen Great Britain, Hungary and Belgium 2024 replay contains 2,173 forecasts and 526 late-race decision states. Eleven initial decisions differ, but the observation model is worse than the last-lap baseline on MAE in every event. Recommendations are sensitive to nuisance assumptions. The project does not demonstrate real-race time savings.

## What an evaluator can inspect

- Bayesian posterior updates and finite-horizon stopping decisions.
- An independent integration method addressing discontinuous deployed-policy values.
- Frozen protocols, source hashes, retained failed experiments and ingestion corrections.
- Chronological forecast scoring and tests against using future observations.
- A matched-information comparator, oracle bounds and paired Monte Carlo checks.
- Historical model failure, sensitivity analysis and synthetic parameter recovery.
- Fifty-nine tests and machine-readable results behind the manuscript.

## Reproduce

Install `requirements-research.txt` and `paper/requirements-publication.txt` in a Python 3.13 environment. From this directory:

```sh
PYTHONPATH=src python -m unittest discover -s tests
python paper/verify_v2.py
python paper/prepare_v2.py
python paper/assemble_v2.py
python paper/build_pdf_v2.py
python paper/docx_payload.py
python paper/build_docx_v2.py
```

These commands rebuild the manuscript from saved results without downloading race data. The guide explains recomputing experiments and the limits of reproducing vendor-corrected historical inputs. Display equations in Word are high-resolution images; their editable mathematical source is retained in Markdown. Body text and tables are editable.

## Portfolio

The [data-analysis brief](portfolio/F1-DATA-ANALYSIS-BRIEF-V2.md) explains the project, suggested resume wording, a five-minute walkthrough and interview preparation. It distinguishes your demonstrated work from claims the study cannot support. Earlier standalone demos remain in `results/`; their version-specific numbers have not been silently rewritten to match the new paper.

The source package omits raw third-party timing caches and credentials. A public repository, permanent archive and final authorship declarations have not been created.
