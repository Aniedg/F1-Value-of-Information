# Expanded manuscript v1.1

This version preserves the original 2,187-state results and adds a post-development numerical diagnostic plus detailed empirical-validation requirements. It is a research draft, not a submission or acceptance record. The original v1 PDF, sources and frozen scientific protocols remain available.

## Reproduce the additions

From the project root, with the dependencies in `requirements-research.txt` and `paper/requirements-paper.txt` installed:

```sh
PYTHONPATH=src python -m unittest discover -s tests
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 python paper/segmented_audit.py
python paper/assemble_extended.py
python paper/build_pdf_extended.py
python paper/verify_expanded.py
```

The audit writes `results/segmented-audit.json`. It deliberately selects the three cases from the earlier discrepancy audit and uses 801, 1,601 and 3,201 belief points, then 200,000 paired trajectories per case. Recorded source hashes and seeds permit inspection and reproduction. Runtime measurements are descriptive and machine dependent. The diagnostic is not a prospective confirmatory experiment and must not be described as one.

The expanded builder creates `paper/manuscript-expanded.md`, the new figure, a convenience HTML preview and `output/pdf/value-of-information-f1-paper-expanded.pdf`. The editable additional text is in `paper/extended-appendix.md`; its numerical passages are filled from the saved diagnostic output. The original four manuscript tables still describe the original integration method. A complete grid rerun with analytic segment integration is required before replacing their aggregate estimates.

## Verification and scope

The expanded source suite contains 53 passing tests, including six new tests for the integration method and its limiting properties. All three new finest-grid gains are inside their independent paired Monte Carlo intervals. These are checks on three chosen synthetic cases. They neither certify all grid values nor validate a physical tyre model from historical lap times.

The PDF has 7,318 whitespace-separated words including references and labels. The release includes a portfolio brief oriented toward data analysis, with suggested presentation and resume wording conditional on the author's actual contribution and understanding. No raw timing caches, virtual environment, personal credentials, invented affiliations or publication claims are included.

The current historical evidence supports staged forecasting results, including failures and calibration shortfalls. A real-data decision replay, identifiable tyre-specific observation model, full-grid numerical rerun, independent scientific review, venue-specific formatting and public release remain outstanding. See Appendix C for the empirical study design and the portfolio brief for accurate project positioning.
