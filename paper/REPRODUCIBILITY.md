# Reproducing the manuscript

The PDF is a complete model-based research manuscript. It does not claim real-race pit savings, successful latent-tyre identification from historical observations, submission, acceptance or an externally preregistered experiment.

## Contents and main claim mapping

- `manuscript.md`: complete editable text (assembled from `manuscript-template.md` and saved results).
- `figures/`: publication figures as PNG and SVG.
- `../research/final-study-protocol.json`: locked scientific settings and source hashes.
- `../results/final-study.json`: all 2,187 states and 24 validation records, with 50,000 paired trajectories each.
- `../results/final-study-numerical-audit.json`: additional post-run checks of three refinement-sensitive states and a separate 200,000-pair evaluation of the largest discrepancy.
- `../results/nuisance-experiment.json` and `replacement-experiment.json`: illustrative development sensitivities and misspecification checks.
- `../results/forecast-evaluation.json`, `multi-race-evaluation.json`, `robust-evaluation.json`, `interval-evaluation.json`: historical results in manuscript Section 7.
- `../tests/`: 47 numerical, inference, limiting-case and sequential-evaluation tests.
- `references.bib`: citation metadata.

## Install in a clean environment

Create a Python 3.13 virtual environment, then install `requirements-research.txt` at the project root. Install `paper/requirements-paper.txt` to build the manuscript PDF. The project is imported through `PYTHONPATH=src`.

## Check and reproduce without race downloads

From the project root:

```sh
PYTHONPATH=src python -m unittest discover -s tests
python paper/verify_release.py
python paper/assemble.py
python paper/build_pdf.py
```

`assemble.py` and `build_pdf.py` rebuild text, figures and PDF from saved evidence. They do not refit historical models. Math figures and PDF intermediates are written to `tmp/pdfs`; the final PDF is written to `output/pdf/value-of-information-f1-paper.pdf`. PDF fonts come from Matplotlib's bundled DejaVu fonts.

To recompute the final study, work in a separate copy, preserve the existing `results/final-study.json` under another filename, and run:

```sh
PYTHONPATH=src python -m pitvoi.final_study run
PYTHONPATH=src python paper/numerical_audit.py
python paper/assemble.py
```

The run verifies locked source hashes and refuses to overwrite the main result. Keep the supplied protocol; running `freeze` again is neither necessary nor appropriate for reproducing this release. The audit is explicitly post-run and overwrites its own diagnostic output. Timestamps can differ on reproduction while numerical values and seeds remain the same up to platform-level floating-point variation.

## What the numerical audit does and does not establish

The main grid uses 1,601 belief points and 81 quadrature nodes. Twenty-four states use 6,401/161 and independent paired rollouts. No selected first action changes under refinement. The largest main-to-refined gain difference is about 0.0545 s. A further 12,801/321 calculation of the largest-discrepancy state still differs from a fresh 200,000-pair simulation interval. The manuscript discloses that residual numerical sensitivity. Do not present tiny gains, the 0.05 s count, or all-grid means as certified exact values. The stated propositions are analytic model results; numerical values are approximate.

The first final-study run failed only when serializing NumPy integer indices. Its protocol, source snapshot and partial output are retained. `final-study-run-note.md` documents the correction. All scientific settings were unchanged and the full run was repeated. This is transparent post-development protocol control, not a claim of external preregistration.

## Historical reproduction and scope

The archive retains ingestion scripts, race selections, frozen-model records and evaluation summaries. Raw timing caches and the local virtual environment are omitted. Historical commands and split details are documented in `research/experiment-03.md` through `experiment-06.md`; these commands also preserve original records rather than silently replacing them. A new ingestion depends on external service availability and may not reproduce exactly the same vendor-corrected data snapshot. Historical eligibility was retrospective and has not been established as the exact live information set.

Do not combine the ten historical test events as if one unchanged model had been tested on all 7,752 targets. Development proceeded in stages; every newly inspected test event became development history for subsequent revisions. No historical counterfactual strategy reward was evaluated.

## Source and manuscript provenance

The release manifest records file hashes and tool/runtime versions. This is a local source package, not a public repository or data-license grant. No raw third-party timing cache is redistributed. The manuscript discloses AI assistance and does not invent an author, affiliation or review status. A human author must accept responsibility for the work and provide the appropriate authorship and venue declarations before submission.
