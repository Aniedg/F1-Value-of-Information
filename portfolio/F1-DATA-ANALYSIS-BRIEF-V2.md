# F1 data analysis research portfolio

This project demonstrates the analysis of noisy sequential data and the consequences for decisions. The question is when an additional lap of evidence justifies delaying a stop. The result is conditional: learning can help in the mathematical model, but a new three-race replay exposes poor predictive transfer and sensitivity to nuisance assumptions.

## Evidence to present

The version 2 paper contains a corrected 2,187-state study, a frozen replay with 2,173 forecasts and 526 decision states, synthetic identification stresses, nine assumption combinations per replay event, and 59 passing tests. All 24 numerical validation cases agree with fresh simulation intervals. Eleven historical initial recommendations differ between the policies, but those differences are not real-race improvements.

The most valuable interview example is the numerical discrepancy: a comparator chose actions using one planning cost but incurred another continuation cost once it updated. Its deployed value could jump at the action boundary. Preserving those jumps and integrating each segment analytically stabilized evaluation. Another strong example is the historical negative result: a last-lap predictor beat the observation model on all three new events, so strategy claims were restricted rather than overstated.

## Five minute walkthrough

Explain the pit/stay tradeoff and one belief update. Show that both planners receive identical actual observations. Explain the difference between updating now and planning to learn later. Show the numerical correction, then one historical forecast comparison. End with the distinction between a simulated advantage and an observed race outcome.

Be ready to derive the update, run a selected case, change a nuisance assumption and explain why the action changes. Explain how training and test events were separated, why corrected historical flags may differ from live availability, and why a low forecast error does not identify tyre degradation. The previous brief contains more interview questions.

## Resume draft

Use under Projects and adapt it to your actual contribution after personally reviewing and reproducing the work:

**Bayesian pit timing and race data analysis | Python, NumPy, SciPy, pandas, FastF1**

- Investigated the value of information in pit timing across 2,187 simulated states, with Bayesian updates, matched-information policy comparisons and independent numerical validation.
- Built a frozen three-event historical replay covering 2,173 forecasts and 526 decision states; quantified forecast failure and recommendation sensitivity to nuisance assumptions.
- Diagnosed discontinuous policy-value integration and verified the revised calculation through analytic checks, grid refinement and paired simulation; maintained 59 tests and reproducible experiment records.

The manuscript is not yet published. List it as a research manuscript only after accepting authorship responsibility; change its status only when a submission, preprint or acceptance actually exists. AI assistance is disclosed, and personal contribution wording must be accurate.

## Positioning

This is directly relevant to an interest in race-strategy data analysis: sequential inference, probabilistic validation, reproducibility, numerical investigation and explaining decision limits. It does not establish experience with proprietary telemetry or team operations. A publication can be useful, but understanding and defending the analysis is essential to presenting this project convincingly.
