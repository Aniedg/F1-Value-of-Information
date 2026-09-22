# Working methods — waiting for information

Status: partial manuscript material, not a completed paper. The following proposition is an elementary consequence of Bayesian optimal stopping, not a novelty claim. Its scope is the current finite-horizon, one-optional-last-stop model.

## Question

When is it strategically optimal to delay a Formula One pit stop in order to gain additional information about uncertain tyre degradation?

We first answer this within an explicit model. Historical replay will assess decision relevance under stated assumptions; it cannot directly observe outcomes of unchosen strategies.

## A condition for information-induced delay

Let n laps remain, a denote current tyre age and b the belief about the current set's static degradation parameter. Let c(a,b) be expected excess cost of the next lap, P_n the known cost of pitting immediately and completing the remaining race, F_n(a,b) the optimal cost when future observations are ignored throughout planning, and V_n(a,b) the optimal cost when future observations update the belief. Both terminal values are zero. Ties select pit.

F_n(a,b) = min{P_n, c(a,b) + F_(n−1)(a+1,b)}.

V_n(a,b) = min{P_n, c(a,b) + E_y V_(n−1)(a+1,b_y)}.

Define the frozen-planning disadvantage of waiting:

M_n(a,b) = c(a,b) + F_(n−1)(a+1,b) − P_n.

Define the continuation benefit from learning:

B_n(a,b) = F_(n−1)(a+1,b) − E_y V_(n−1)(a+1,b_y).

Then the adaptive stay cost minus pit cost is exactly M_n − B_n. Consequently, at a state where the frozen-belief planner pits (M_n ≥ 0), the adaptive planner strictly prefers to stay if and only if B_n > M_n.

This is a necessary and sufficient condition within the stated model. B is not the deployed-policy performance gain: F is an internal frozen planning value, whereas the deployed comparator updates and replans after actual observations. Report these quantities separately.

## Decomposing the learning benefit

Adding and subtracting E_y F_(n−1)(a+1,b_y) gives:

B = [F_(n−1)(a+1,b) − E_y F_(n−1)(a+1,b_y)]
  + E_y [F_(n−1)(a+1,b_y) − V_(n−1)(a+1,b_y)].

The first term values the next observation followed by a commitment to ignore later observations. The second values additional learning opportunities after that update. A next-observation benefit is not generally the entire benefit of an adaptive continuation.

Under a correct likelihood and prior, F is the minimum over fixed-schedule expected costs, each affine in the belief, so F is concave. Since E_y b_y = b, Jensen's inequality makes the first term nonnegative. The adaptive policy may ignore information and reproduce a fixed schedule, so V ≤ F; the second term is also nonnegative. These are exact-model properties. Numerical approximations need tolerance checks, and misspecified beliefs do not guarantee superiority under the true data-generating process.

At n=1 both continuation values vanish: B=0. Learning cannot justify delay if no later decision remains. With known degradation, or observations that do not change the relevant belief, B=0 in this model.

## What this does not prove

It does not prove that benefits increase monotonically with posterior variance, or that action differences concentrate near a fixed universal boundary. Large B can overcome large M. Boundary concentration must be measured using prespecified margin bins and a reported state distribution. Nor does it establish practical F1 gains, replacement-tyre robustness, or successful inference of physical degradation from historical lap times.

For linear fixed-schedule costs, evaluating expected cost over b equals evaluating cost at E_b theta. Therefore certainty-equivalent and frozen-belief planning coincide in this model. They must not be presented as independent successful baselines. Nonlinear extensions require a physical justification rather than an aim of separating preferred comparators.

## Computational verification

`src/pitvoi/waiting_condition.py` evaluates the identity and its decomposition using the continuous-observation solver. The saved experiment spans three noise levels and six pit losses. Tests additionally inspect five beliefs at every decision time across nine configurations, verify action equivalence away from numerical ties, nonnegative components within tolerance, and zero final-lap information value. These are implementation checks, not independent scientific validation of the model assumptions.

Numerical caveat: the nonnegativity audit found a smallest component of −0.000083 s using 41 quadrature nodes and −0.0000047 s using 81 nodes (801 belief points). The test uses 81 nodes and a 0.00001 s tolerance; this is an observed approximation artifact, not a negative exact value of information. Action-equivalence identities are checked separately from nonnegativity.

In the illustrative age-12, eight-lap case with 18 s pit loss and 1.5 s observation noise, M=1.400 s and B=5.773 s. The next-observation and later-learning components are 4.969 s and 0.804 s. Hence adaptive waiting beats immediate pitting by 4.373 s in this synthetic model. This example is inherited from the development experiments, not independently selected evidence.

## Unknown shared baseline: exact reduction of the decision belief

Extend the observation equation to y_t = b + a_t theta + epsilon_t, where b ~ N(0,tau²), epsilon_t ~ N(0,sigma²), theta has the existing two-point prior, and the three are initially independent. The baseline b is fixed throughout the remaining horizon and applies to both the current and replacement tyres. Replacement degradation remains known. All actions finish the same fixed number of laps.

For every latent trajectory, the contribution of b to total remaining time is n*b, regardless of the stopping rule. Subtract this common term before comparing policies. This also applies under correlation between b and theta in a posterior: the full-horizon common cost is still action-independent. Conditional observation noise is likewise treated as an action-independent contribution; the evaluation scores conditional excess pace, with shared noise used for information.

After t consecutive observations on the current tyres, write S_y = sum(y_i) and S_a = sum(a_i) = t*a_0 + t(t−1)/2. Within each regime,

v_t = sigma²*tau² / (sigma² + t*tau²),
k_t = tau² / (sigma² + t*tau²),
b | theta, history ~ N(k_t*(S_y − theta*S_a), v_t).

Define z_t = y_t − k_t*S_y. Its conditional distribution is

z_t | theta, history ~ N(h_t*theta, sigma² + v_t),
h_t = a_t − k_t*S_a.

The coefficients h_t and v_t depend on observation count and known parameters, not observation values. Although the full joint posterior includes more than the regime probability p_t, the transition distribution of the cost-relevant p_(t+1) depends only on p_t and t after this centering. Thus p_t is sufficient for the reduced decision problem. During a real replay, S_y is still retained to center the actual next observation; p alone is not a claim of sufficiency for reconstructing the entire joint posterior.

Use the original likelihood-ratio update with age replaced by h_t and observation noise SD replaced by sqrt(sigma²+v_t). Continue to use the physical age a_t, not h_t, in the lap-cost function. This yields the same one-dimensional Bellman grid with a time-dependent observation kernel. When tau=0, the original known-baseline solver is recovered exactly. This reduction fails for a tyre-specific baseline that changes the relative cost after a stop, uncertain time-varying offsets, or additional replacement-set decisions; those require a richer formulation.

## Development result: common-baseline sensitivity

Experiment 08 holds physical degradation regimes, prior, independent lap noise, pit loss and horizon fixed while varying shared baseline SD over 0, 1.5, 3 and 6 seconds. At the finest numerical resolution the adaptive policy's expected gain over the deployed updating frozen-belief policy is 4.387, 2.673, 1.146 and 0.000 seconds. The first action is stay for the first three assumptions and pit for the fourth. This result concerns the fixed illustrative initial state, not all states or real races.

With actual baseline SD 6 s but assumed SD zero, a 30,000-trajectory paired stress test estimates gain −0.145 s (95% sampling interval −0.273 to −0.017 s). Assuming SD 1.5 gives −0.070 s (−0.199 to 0.058 s); correctly assuming SD 6 leads both policies to pit immediately, with zero paired difference. These are development sensitivities, not multiple-testing-adjusted or held-out real-world claims. The stress test uses the intermediate solver resolution.

The four central correct-model cases were checked at 1,601/41, 3,201/81 and 6,401/161 belief points/quadrature nodes. The largest intermediate-to-fine gain change is about 0.010 s; this is not a rigorous numerical-error bound. Paired Monte Carlo independently draws physical baseline offsets and lap noise and executes the finest-grid policies. Source hashes and seeds are saved in `results/nuisance-experiment.json`. The 24-cell pit-loss sweep uses the base resolution and is exploratory.

## Uncertain replacement tyres and cross-set learning

Let phi denote the replacement degradation rate, taking values phi_L and phi_H. Specify q_L = P(phi=phi_H | theta=theta_L) and q_H = P(phi=phi_H | theta=theta_H). The shared baseline remains independent of the joint tyre prior. Pre-stop observations depend on the current regime and shared baseline, not directly on phi. Therefore:

P(phi=phi_H | history) = (1−p) q_L + p q_H,
mu_phi(p) = phi_L + (phi_H−phi_L)[(1−p)q_L + p q_H].

The pit cost becomes belief-dependent:

P_n(p) = L + n(n−1) mu_phi(p)/2.

Use this cost in both the adaptive and frozen-belief Bellman recursions. The existing old-regime observation kernel is unchanged. The waiting-margin condition still holds, with P_n replaced by P_n(p) at the current state. A scalar old-regime belief remains sufficient for decisions because conditional replacement probabilities are fixed and only the old set is observed before the final commitment.

If q_L=q_H, mu_phi is constant. Under linear replacement costs, a risk-neutral objective, and no later decision after the stop, the entire Bellman recursion is identical to that for a known replacement rate equal to this mean. Independent, mean-preserving replacement uncertainty therefore changes neither policy nor expected cost. This does not say realized costs are identical, nor does it cover nonlinear losses, risk constraints, or additional decisions. Fixed-schedule costs remain affine in both tyre parameters, so certainty-equivalent and frozen-belief planning still coincide when supplied the same posterior means.

If q_L differs from q_H, old-set observations change the anticipated replacement cost. In Experiment 09, the three uncertain cases share the same marginal replacement distribution: probability 1/2 at 0.02 and 1/2 at 0.10 s per lap of age. Independent, positive and negative dependence use (q_L,q_H) = (0.5,0.5), (0.125,0.875) and (0.875,0.125). The corresponding binary-regime correlations at the equal old-regime prior are 0, +0.75 and −0.75. These are design choices, not estimated physical correlations. A known-rate control uses phi=0.06. All four cases have the same initial expected replacement rate and immediate pit cost.

## Development result: replacement dependence

At baseline SD 3 s, main-resolution expected gains are 1.136 s for known and independent replacement cases, 1.020 s for positive dependence, and 1.253 s for negative dependence. Positive dependence makes the replacement relatively worse when observations suggest the old set degrades quickly; negative dependence changes this contrast in the opposite direction. This changes both what observations imply and the conditional physical payoffs, so it is not an isolated manipulation of observation quality.

At baseline SD 6 s, only the negative-dependence case selects stay, with a predicted gain of 0.0085 s at the main resolution and 0.0111 s at the additional resolution. Its paired simulation estimate is −0.0068 s with 95% interval [−0.1452, 0.1315]. The nominal policy difference is documented, but independent simulation does not resolve such a small benefit at this sample size. No practically robust improvement is claimed for that case.

The evaluator samples both tyre regimes from the joint prior and scores actual replacement degradation, not its posterior mean. Thirty thousand paired trajectories are used per case. The main grid has four replacement assumptions and three baseline SDs (0,3,6), with all 12 cells retained. A diagnostic fixes actual positive dependence and compares three assumed relationships at baseline SD 3; its row-wise gain is not a direct paired estimate of misspecification cost against the correctly specified adaptive policy.

Two oracle definitions are retained: an old-regime-only oracle knows theta and uses E(phi|theta), while a full oracle knows both theta and phi. Neither knows future lap noise. Their costs happen to coincide in these selected states; implementations do not assume equality. When the joint prior changes, oracle costs can change as well, so regret comparisons across priors require care.
