# Session 14ar — Independent bound for terminal interval 8

Date: 2026-09-15. **A — independent bound confirms retained interval estimate
within existing authority / readiness 1**.

Session 14ar supplied the one missing numerical item identified by Session
14aq. On sanitized terminal interval 8, the retained structural authority shows
one fully activated maximum-field owner and no interior onset, switch, or tie
boundary. That reduces the unchanged constant-width maximum field to
`exp(-lambda*t^2)` on the interval.

The new reference does not use adaptive quadrature. It converts the retained
binary64 coordinates and endpoints to exact rational values, integrates the
exponential Taylor polynomial exactly, and attaches the integrated Lagrange
remainder. Order 6 was the first order whose outward-rounded enclosure met the
existing `1e-10` independent-verifier agreement scale.

The resulting bound is
`[0.21369535129402328, 0.21369535131181636]`, with width
`1.7793072570881918e-11`. The retained warning-producing SciPy estimate,
`0.21369535129415176`, lies inside that enclosure, so its point-to-interval
distance is zero. The enclosure occupies about `0.1779307257` of the existing
agreement allowance. SciPy's retained reported error was
`2.3724949926212853e-15`.

This establishes the bounded conclusion sought here: the warning is consistent
with roundoff preventing the adaptive routine from certifying its requested
tolerance even though the retained interval contribution is accurate within the
project's existing `1e-10` independent-verification authority. It does not
change the warning-free contract, repair the verifier, validate the full edge,
or establish any scientific property of the continuous-field candidate.

## Numbered handoff

1. **Starting HEAD:** `03c8d889e5f210af413a77628c302b5e2e411ccf`.
2. **Ending HEAD:** the closure commit containing this report; its exact
   identifier is supplied in the delivery response.
3. **Protocol:** [Phase 14ar](protocols/phase_14ar_terminal_interval_reference.md),
   commit `92f9d6e`, SHA-256
   `2f2bf4a80da93afdfe553768b9cdcfc208683c72251bf35c7709fe6ee3c38ee1`.
4. **Interval authority:** retained interval record SHA-256
   `5d86b9e849cdb6708962a2aae47c33b281712fea45b09fb2dc1634c4171abb08`;
   selected geometry, structure, onset, manifests, private index, lock, and
   implementation are separately bound in the
   [manifest](../outputs/continuous_occlusion_terminal_interval_reference/manifest.json).
5. **Sanitized interval:** normalized endpoints `0.763171118147611` and `1.0`;
   width `0.23682888185238904`.
6. **Field:** constant-width maximum, `sigma=2.0` metres and onset length `1.0`
   metre. The retained owner is fully active throughout the interval.
7. **Independent method:** exact rational integration of the exponential Taylor
   polynomial plus its integrated Lagrange absolute remainder, with outward
   binary64 serialization.
8. **Independence:** the reference uses `Fraction` arithmetic and an analytic
   remainder proof. It calls no NumPy, SciPy, adaptive quadrature, production
   integration, or retained callback values when calculating the bound.
9. **Known-function oracle:** focused controls covered exact zero-lateral and
   zero-width cases, exact monomial antiderivatives, and containment of the
   closed-form error-function value. All passed.
10. **Retained SciPy estimate:** `0.21369535129415176`.
11. **Retained SciPy error:** `2.3724949926212853e-15`.
12. **Independent enclosure:** lower `0.21369535129402328`; upper
    `0.21369535131181636`.
13. **Independent bound width:** `1.7793072570881918e-11`; the exact rational
    endpoints and remainder remain private under private-index SHA-256
    `59f83bee090434aebcf645d88114b6e8ccf6ce6ff315d6ca6126e2366b65ed11`.
14. **Distance:** point-to-interval distance is exactly `0.0`.
15. **Containment:** yes; the retained estimate lies inside the independent
    enclosure.
16. **Judgment authority:** the inherited `1e-10` independent-verifier
    agreement scale. No new tolerance was introduced.
17. **Roundoff verdict:** roundoff prevented adaptive certification despite an
    interval estimate independently bounded within existing authority.
18. **Classification:** **A — independent bound confirms retained interval
    estimate within existing authority**.
19. **Readiness:** **1 — ready for bounded verifier-evidence contract repair**.
20. **Recommendation:** separately govern a verifier-evidence contract repair
    using the independent terminal-interval bound, without rerunning Session 14R
    yet.
21. **Full-edge execution:** none; `full_edges_recomputed=0`.
22. **Additional access:** no other interval, state, or edge was accessed;
    exactly one retained interval was evaluated.
23. **Scientific products:** no Session 14R partial scientific output was opened
    or interpreted.
24. **Prohibited evidence:** no target, model, option share, acquisition route,
    provider product, or protected/withheld evidence was accessed.
25. **Validation:** focused Session 14ar tests passed 13/13; focused plus
    relevant Session 14ao–14aq tests passed 91/91; compilation, persisted
    publication validation, schemas/hashes, privacy, links, history, staging,
    and diff checks passed. The full suite passed 887 run / 884 passed / 3
    retained skips. CI status is supplied in the final delivery response.
26. **Commits and push:** protocol `92f9d6e`, implementation `31bbcd6`, and this
    closure commit, exactly three. Push, CI, and synchronization are final
    delivery gates.

## Scope and integrity

The six-file public package is under
`outputs/continuous_occlusion_terminal_interval_reference/`. Its exact rational
authority is ignored and hash-bound. Scalar reconstruction matched all 21
retained callback values under the inherited `1e-12` absolute/relative rule;
the maximum observed difference was below `8e-16`. This check established the
sanitized scalar reconstruction but did not determine or tune the independent
bound.

The claim ledger, scientific summaries, field and verifier implementations,
dependencies, public API, historical artifacts, and release remain unchanged.
No football, accessibility, suppression, attribution, causal, or value claim
follows from this interval-specific numerical evidence.
