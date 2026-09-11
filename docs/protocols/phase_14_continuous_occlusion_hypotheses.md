# Phase 14 — Bounded continuous occlusion hypothesis study

Prospective authority, 2026-09-11. Start: clean local/tracking/live main
`9754a03abc5701934313432e815b4bc29e39ee7b`; preserve v0.1.0 at
`f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`.

## Scope and inputs

Compare three fixed fields for representation plausibility, not behavioral
validation: isotropic proximity, expanding directional, constant-width
directional. The canonical carrier is an explicit origin proxy, not measured
ball position. Use only the canonical development population SHA-256
`cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d`,
7,227 states and match counts 885,801,952,877,861,629,764,734,724. Membership
and duplicate keys may support integrity checks only. Targets and event
references never enter analytical records. No model artifact is loaded.

No provider product, reserved detail, withheld, pose, fitted model, utility,
option share, outcome, progression, external xT, empirical image or boundary
remedy is permitted. Sessions 12b/12c remain parked. Session 13 stays historical;
its published gap quantiles describe state-average gaps, not individual edges.
All claims remain unchanged: accessibility PROXY ONLY; suppression NOT SUPPORTABLE.

## Candidate contract

For origin b, defender d and query q: r=norm(d-b), u=(d-b)/r,
ell=(q-d) dot u, h=abs((q-d)_x*u_y-(q-d)_y*u_x).
Freeze sigma=2 metres, onset a=1 metre, alpha=10 degrees, as synthetic conventions.
G(ell)=0 for ell<=0, 3t^2-2t^3 for t=ell/a in (0,1), and 1 for ell>=a.

- Isotropic: exp(-norm(q-d)^2/(2*sigma^2)).
- Expanding: G(ell)*exp(-h^2/(2*(sigma+max(ell,0)*tan(alpha))^2)).
- Constant-width: G(ell)*exp(-h^2/(2*sigma^2)).

No fourth family, alternate scale, sensitivity search or longitudinal attenuation.
Directional fields vanish at/before the defender plane and persist behind it;
these are assumptions, not field-marking or football truths. r<=1e-9 metres
blocks directional use and the common empirical population. No direction repair
or defender omission. Empty/nonfinite inputs fail; coincident defenders remain
distinct when they do not coincide with the origin.

Primary combination: 1-product(1-O_d). Comparator: max(O_d). Use sorted numerical
values, stable log1p/expm1, explicit zero/one handling. Bounds are [0,1], not
probabilities. No modification of option weights or networks.

## Edge sampling and numerical gate

Retain receiver field and normalized segment integral integral_0^1 O(b+t*(r-b))dt
for both combinations and individual defenders. A segment <=1e-9 metres uses its
endpoint. Composite Simpson uses even n with length/n<=0.25 m, independently
even n with length/n<=0.125 m; retain finer result only when absolute difference
<=1e-6 for every integral. This is numerical accuracy only. A failed convergence
check stops this execution; do not change spacing, split points or tolerance.

Synthetic checks precede empirical preparation. Fixed fixture order: origin
(0,0), receiver (20,0), single defenders (-5,0),(5,0),(20,0),(25,0); lateral
sweep x=5,10,15 with y=0,1,2,5; receiver depth x=4,5,5.5,6,10,20,40 with y=0,2
and defender (5,0); equal-minimum one (15,2) versus three (5,2),(10,2),(15,2);
then the Session 13 synthetic star. Candidates are evaluated in the fixed order
isotropic, expanding, constant_width. A failing scientific gate records the
first failing fixture and completed checks, stops further field evaluation and
permits only integrity/testing/report closure. Failed candidate mathematics are
not silently treated as engineering bugs.

Test rotation by 0.7 radians, translation (11,-7), reflection, permutation,
duplicate defenders, bounds, all-zero support, degenerate edges, overlap
monotonicity and deterministic evaluation. Invariant numeric comparisons use
absolute 1e-12 and relative 1e-12; this is not a football threshold. Query-point
lateral monotonicity holds at fixed ell; defender movements also rotate the axis
and are hypotheses, not universal monotonicity gates.

Smoothness records changes at perturbations .1,.01,.001,.0001 metres in x/y
around q=(5,0),(6,0),(10,0),(10,2), origin (0,0), defender (5,0). Rank swaps near
ties do not establish field discontinuity. Equal-minimum stress tests are
synthetic only; no empirical matching or threshold selection.

## Empirical structural summaries

For each candidate and combination report receiver/segment distributions;
union-minus-max overlap; within-state Spearman using average exact-tie ranks
for receiver versus negative receiver-nearest distance, segment versus negative
segment-nearest, and segment overlap versus d2-d1/d3-d1. Constant/insufficient
comparisons are unavailable with explicit denominators. Average assessable
states within match, then equally over represented matches.

Rank individual endpoint and segment-average fields with descending absolute
1e-12 block-high ties. All-zero edges are unavailable. Report distinct maximum-
block defenders per star, multi-edge maximum involvement, overlap with receiver/
segment nearest sets, and fraction of total individual field carried by geometric
top-1/2/3 using Phase 13 fractional tie membership. No causal contribution.

States are equally weighted within each match, matches equally; edges equally
within state. Report mean, extrema and weighted inverse-ECDF 5/25/50/75/95
percentiles. No bins, fitted regressions, significance tests or outcome analysis.

## Software, visual and checkpoints

Internal geometry-only numerical API supports individual/combined point and
edge evaluation. Reuse NumPy and finite-segment geometry; no released API,
dependency, lockfile, version or historical source changes. Root-package imports
may expose historical symbols transitively; Session 14 must not call/load them.

Runner: preflight, synthetic-checks, render-synthetic, prepare, analyze,
publication-check. Verify committed prerequisite bytes, exclusive stage markers,
ignored append-only access/failure logs. Preparation cannot evaluate fields;
analysis cannot acquire, load models or fit. Publication validates stored hashes,
never rebinds them. Unknown post-access cases stop without repair/rerun.

Static 1800x800 SVG only, three equal-aspect panels, shared [0,1] scale, primary
union. Origin (0,0), defenders (5,0),(18,-9),(18,9),(-7,4), receivers (20,-10),
(25,0),(20,10),(-10,5); x extent [-15,35], y [-20,20]. Synthetic origin, edges,
anonymous labels; no pitch marks. Locked Matplotlib, fixed metadata/hash salt;
double render byte equality and full-frame visual QA before empirical access.
Label SYNTHETIC / GEOMETRIC OCCLUSION HYPOTHESIS /
NOT VALIDATED COVER SHADOW / NOT SUPPRESSION. No animation.

Commit protocol/contract first; tested implementation, synthetic evidence and
approved visual second; prepared/analysis authority third; closed results/report
fourth. If an earlier gate blocks, later checkpoints/artifacts are explicitly
unavailable and closure preserves that chronology without inventing completion.
Outputs under outputs/continuous_occlusion_hypotheses include contract,
implementation/population authorities, synthetic checks, structural comparison,
overlap sensitivity, smoothness, QC, manifest and synthetic SVG. Details ignored.

## Closure and interpretation

Choose A one candidate merits later behavioral validation; B multiple plausible;
C insufficient additional description; D blocked/invalid. Highest correlation,
visual appeal or guaranteed union response alone selects no winner. Readiness:
1 later governed behavioral hypothesis test only; 2 descriptor/visualization only;
3 representation revision; 4 not justified. No classification is forced.

Use all 25 requested report items, with unavailable evidence explicit. Record
carrier-origin uncertainty, fixed scales, persistent tails, shared-origin geometry,
union saturation and offline tracking. Future behavioral/pose/value/sister-project
links are conceptual; formerly reserved matches are spent, not fresh validation.
Append research/library logs; leave claims/history unchanged. Focused/full active
synthetic tests, compile, schemas/hashes, links, privacy, staged/history/diff review
precede commit/push. Exactly one next action; no automatic continuation.
