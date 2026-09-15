# Phase 14ar — Independent bound for terminal interval 8

Date: 2026-09-15. Planning: ON; Turbo: OFF; Model: Sol Medium.
Starting authority: `03c8d889e5f210af413a77628c302b5e2e411ccf`.
Local, tracking, and live GitHub `main` were clean and synchronized before
mutation. Preserve annotated `v0.1.0` at
`f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`.

## Question and boundary

Session 14aq closed **C — roundoff/subdivision limitation identified /
readiness 2**. Its retained evidence established stable returned values,
reported errors, callback traces, terminal topology, 189 evaluations, nine
terminal intervals, and zero further subdivisions across the frozen requests.
The final request retained SciPy's roundoff warning. Those facts identify the
integrator's reported termination condition but do not independently establish
the accuracy of sanitized terminal interval 8.

This phase asks only: what independently supported bound can be placed on the
integral contribution of terminal interval 8 under the unchanged
`constant_width` field and retained interval geometry?

Only the retained sanitized interval-8 authority may be used. Do not reconstruct
the full empirical edge, decode an original provider row, inspect another
defender or interval, evaluate another state or edge, rerun the full verifier,
open Session 14R scientific products, or access targets, models, option shares,
provider products, protected data, or withheld evidence. No scientific or
football interpretation is authorized.

## Retained authority

Hash-bind these unchanged private records before interpretation:

- selected sanitized geometry:
  `fe39401fee30c197082e5513d376308cdfe3eb8fbf35b7bbc7ddb7a749f41d2e`;
- certified structural record:
  `791ddcd717c5f08d7c834de127388c81012192c859aa20ce0c96f342fbbe69e6`;
- warning-producing interval-8 record:
  `5d86b9e849cdb6708962a2aae47c33b281712fea45b09fb2dc1634c4171abb08`;
- retained canonical-onset record:
  `e4944e3cbe1905dbb5c169cb14ffd7b4775692375bc24bf15e5887a0af6dce26`;
- Session 14ao manifest:
  `367cec3ea22163af15c299b96e3792424707603b5920257eed40b3e06e5335f3`;
- Session 14ao private index:
  `23b4264f0bce761cc17cb61357cd1fd39b6a418e5bce9938314898f8025d3955`;
- Session 14aq manifest:
  `90c000da20f0ce7afd1a626518173a8cc3aeabdcd31681670d3f747a39739eee`;
- lock file:
  `c9e4da0781770b9e72b8a5b10a7c514f2259b7e63dc1b67604ee481934db0a0c`.

The warning record supplies normalized endpoints, retained estimate, retained
reported error, initialized callback evidence, and the historical full-edge
role as metadata only. The structural and onset records must establish one
maximum-field owner throughout the interval, full directional activation for
that owner, no interior switch or tie boundary, finite geometry, and an
origin–defender distance greater than `1e-9` metres. Failure of any obligation
stops with an authority or reconstruction classification before reference
calculation.

Read the retained selected-geometry JSON lexically. Decode only the carrier,
authorized receiver, and the one state-local defender required by the retained
owner record. Other defenders must remain undecoded. Store exact coordinates,
owner ordinal, rational coefficients, callback values, and extraction details
only in ignored private evidence.

## Frozen analytic enclosure

The candidate is the unchanged constant-width directional field with
`sigma=2.0` metres and onset length `a=1.0` metre. When the retained owner is
fully activated over the interval, the edge parameterization
`q(t)=b+t(r-b)` gives

\[
O_{\max}(t)=\exp(-\lambda t^2),\qquad
\lambda=\frac{\operatorname{cross}(r-b,d-b)^2}
{8\lVert d-b\rVert^2}.
\]

Treat every retained binary64 coordinate and endpoint as its exact rational
value using `Fraction.from_float`. Form `lambda` with exact rational arithmetic.
For interval endpoints `x0` and `x1`, calculate

\[
S_N=\sum_{n=0}^{N}\frac{(-\lambda)^n
(x_1^{2n+1}-x_0^{2n+1})}{n!(2n+1)}
\]

and the Lagrange remainder bound

\[
B_N=\frac{\lambda^{N+1}
(x_1^{2N+3}-x_0^{2N+3})}{(N+1)!(2N+3)}.
\]

The rigorous enclosure is `[S_N-B_N, S_N+B_N]`. Starting at `N=0`, advance
sequentially through `N=256`. Accept the first order whose outward-serialized
binary64 enclosure width is at most `1e-10`, the inherited independent-verifier
agreement scale. Convert each exact rational endpoint to binary64 and use
`math.nextafter` when comparison with `Fraction.from_float` shows that rounding
would point inward. Preserve the exact rational endpoints privately.

There is no fallback or confirmation method. Failure to obtain a qualifying
enclosure by order 256 makes the evidence unavailable. Do not call NumPy,
SciPy, adaptive quadrature, production integration, retained callback nodes, or
another numerical reference method when forming the bound. This analytic
series, exact rational arithmetic, and proven remainder are the independence
authority.

Before accepting reconstruction, evaluate the reconstructed scalar formula at
the already-retained interval callback nodes and compare it with the retained
values under the inherited absolute/relative `1e-12` scalar-oracle rule. This is
a reconstruction check, not an input to the independent integral enclosure.

## Comparison and decisions

Compare the retained interval estimate with the independent enclosure using
point-to-interval distance. Report containment, distance, the retained reported
error, enclosure width, and enclosure-width-to-`1e-10` ratio. Introduce no new
acceptance tolerance. The evidence is sufficient only when the enclosure width
is at most `1e-10` and point-to-interval distance is at most `1e-10`.

Choose exactly one classification:

- **A — independent bound confirms retained interval estimate within existing authority**;
- **B — retained estimate is stable but independent bound is too wide to certify**;
- **C — independent reference disagrees materially with retained estimate**;
- **D — sanitized interval reconstruction or authority defect**;
- **E — multiple independently demonstrated issues**;
- **F — evidence unavailable or unresolved**;
- **G — invalid execution or integrity failure**.

Choose readiness independently: 1 ready for a bounded verifier-evidence contract
repair; 2 ready for one additional specific numerical evidence step; 3 numerical
method needs revision; or 4 not ready. Do not force A. A/readiness 1 supports
exactly this recommendation: **separately govern a verifier-evidence contract
repair using the independent terminal-interval bound, without rerunning Session
14R yet.** B or F names one missing evidence item; C recommends numerical-method
review. No recommendation is executed here.

## Execution, outputs, and closure

Add one unreleased standard-library reference module and a runner exposing only
`preflight`, `reference`, and `publication-check`. The runner uses the locked
project interpreter, an exclusive create-once marker, atomic writes, and an
independent immutable failure record. The single governed `reference` command
validates authority, constructs the interval-only scalar function, executes one
analytic enclosure calculation, compares retained evidence, closes outputs,
and classifies. An unexpected post-exposure failure is preserved without repair
or rerun.

Create exactly these public files under
`outputs/continuous_occlusion_terminal_interval_reference/`:

- `interval_authority.json`
- `reference_method.json`
- `reference_result.json`
- `retained_comparison.json`
- `qc.json`
- `manifest.json`

Public evidence may contain sanitized normalized endpoints and width, field
parameters, retained estimate and error, reference bounds, enclosure width,
comparison flags, classification, and hashes. Geometry, exact rational
coefficients, owner identity, callback traces, and extraction details remain in
ignored `local/` evidence and are bound through a private index.

Before execution test restricted extraction, sentinel rejection, reconstruction,
zero-lateral and zero-width cases, exact monomial integration, Taylor remainder
containment, outward serialization, point-to-interval distance, signed zero,
nonfinite rejection, malformed or changed authority, marker collision, failure
closure, strict persisted schemas and prohibited routes. Run focused, relevant,
and full tests because code changes are introduced, plus compilation, schema and
hash checks, privacy guards, links, historical preservation, staged inspection,
and `git diff --check`.

Preserve exactly three commits: this frozen protocol; tested interval-only
tooling; closed evidence, report, and one append-only research-log entry. Push,
require green Python 3.11, Python 3.13, and distribution CI, verify synchronized
heads and the unchanged release tag, deliver the 26 requested handoff items,
and stop. No public API, dependency, field formula, verifier, scientific result,
claim ledger, or historical artifact changes.
