# Ecosystem review and integration decisions

Reviewed 2026-09-09 in response to the user's links. Scope: official documentation
and public repository overviews; no package execution, scientific reproduction,
code audit, or competition data download. Versions on moving `latest` pages are
not dependency pins. All adoption decisions below are provisional project
judgments, not claims that a library's methods work on the selected release.

## Data source and software candidates

| Resource and source | Documented role | Project decision / integration gate |
| --- | --- | --- |
| [SkillCorner Open Data](https://github.com/SkillCorner/opendata) | User-supplied data/documentation source. | Use as acquisition entry point after P01. Verify the competition release and coverage; details in the data dictionary. No clone or data fetch yet. |
| [floodlight](https://floodlight.readthedocs.io/en/latest/) and [SkillCorner I/O index](https://floodlight.readthedocs.io/en/latest/modules/io/io.html) | Standard sports objects, transforms, and a documented SkillCorner position reader. | Strong alternative for the Phase 1 data layer and coordinate cross-checks. Verify current JSONL compatibility and retention of quality flags, identities, clocks, and ball state. Avoid maintaining two permanent internal representations without a demonstrated need. |
| [kloppy](https://kloppy.pysport.org/) and [SkillCorner loading](https://kloppy.pysport.org/user-guide/loading-data/skillcorner/) | Provider-neutral event/tracking objects with a SkillCorner loading route and coordinate transforms. | First candidate for a thin loading adapter after the contract is specified. Check lossless field retention, extrapolation flags, direction, time, in-play filtering, and release compatibility before adoption. No auto-loader runs at import. |
| [DataBallPy](https://databallpy.readthedocs.io/en/latest/) and [Kloppy integration](https://databallpy.readthedocs.io/en/latest/getting_started/loading_in_a_game_page.html#databallpy-kloppy-integration) | Combines event/tracking streams; documents synchronization, pressure/space methods, and `get_game_from_kloppy`. | Consider downstream of Kloppy if synchronization or a justified baseline needs it. Native provider support is not a blanket SkillCorner guarantee. Check GI event semantics, filtering, frame alignment, and inherited model parameters. Existing pressure, accessible-space, xT, or optimization methods do not define our edge. |
| [skillcornerviz](https://github.com/SkillCorner/skillcornerviz) | Standard summary charts and SkillCorner normalization utilities. | Useful candidate for later reporting, not presumed to be a tracking-animation engine. Audit normalization and bundled asset licenses. Examples use a credentialed client; adapt only to locally supplied eligible files, without a paid service dependency. |
| [mplsoccer](https://mplsoccer.readthedocs.io/en/latest/) | Matplotlib pitch/chart tools, multiple pitch types, coordinate standardization, and data loaders. | First candidate for Phase 4 overlays after coordinate verification. Specify actual pitch conventions; do not accept defaults from another provider. Its external-data loaders are outside this project's input workflow. |
| [unravelsports](https://unravelsports.readthedocs.io/en/latest/) | Tracking-to-Polars conversion, graph tooling, pressing intensity, and formation/position identification. | Review pressing and structural methods as possible later baselines. Defer graph conversion and GNN training until edge validity and incremental need exist. Its graph representation is not a definition of pass viability. Check optional dependencies before any installation. |

## Research collections and related projects

These links are not all installable libraries. Read the relevant paper and code
before deciding what to integrate; do not install an entire ecosystem by default.

- **[ML-KULeuven](https://github.com/ML-KULeuven/):** the organization page did not
  load in the text browser. The directly reviewed
  [socceraction repository](https://github.com/ML-KULeuven/socceraction) provides
  event representations (SPADL) and on-ball valuation tools (VAEP/xT). Use these
  as methodological context for action semantics and the distinction between
  accessibility and value. Any GI-to-SPADL conversion needs evidence that its
  action semantics match. No external training data, pretrained value surface,
  or event model is adopted.
- **[Hyunsung Kim](https://github.com/hyunsungkim-ds):** the profile identifies
  several relevant projects. [DEFCON](https://github.com/hyunsungkim-ds/defcon)
  studies defensive contribution through opposing EPV reduction using GNNs and
  requires tracking/event representations; its README says the original Ajax
  data cannot be publicly released. This is a priority originality and
  attribution reference, not an implementation template or source of weights.
  [ELASTIC](https://github.com/hyunsungkim-ds/elastic) is an event/tracking
  synchronization method that avoids annotated event locations; consider it
  only if the audit establishes a synchronization problem.
  [SoccerCPD](https://github.com/hyunsungkim-ds/soccercpd) targets formation/role
  changes and may inform Phase 8. These require separate scientific and license
  review before integration; no GNN or change-point model is selected.
- **[Soccer Analytics Handbook](https://github.com/devinpleuler/analytics-handbook):**
  a learning and research-discovery reference. Its examples use other providers'
  open data. Follow primary citations on passing, space, and networks; do not
  execute example acquisition code or treat historical software advice as a
  current dependency requirement.
- **[U.S. Soccer Visual Exploratory Behavior](https://github.com/USSoccerFederation/ssac26_visual_exploratory_behavior):**
  describes a continuous pose-informed vision layer combining field of view and
  player occlusion. It is directly relevant to the optional orientation branch.
  Visual obstruction differs from physical pass interception and defensive
  reach. Review assumptions and independent validation before adapting any
  geometry; no coefficients, data, or claimed effects are transferred.
- **[PySport submissions](https://pysport.org/analytics-cup/submissions):** the
  rendered page is an archive of earlier submissions, with links to project
  repositories and presentations. Use for originality and communication review,
  not as the rulebook for Cup 2.0. No linked entry was reproduced or its data
  fetched during initialization. Current rules were read on the
  [Cup 2.0 page](https://pysport.org/analytics-cup/editions/analytics-cup2/rules).
- **[moving-the-defense](https://github.com/JeremyBetz/moving-the-defense):** the
  user's sister project on the attacking side. Its public README bounds its
  findings as observational defensive reorganization rather than established
  value or causality. We reviewed that framing; published result summaries were
  visible in the page returned by the browser. Nothing was copied as evidence,
  a parameter, or an analysis module. Record possible shared SkillCorner match
  exposure before selecting holdouts. This project's estimand remains to be
  defined around attacking-connection accessibility under defensive positioning.

## Integration order and acceptance criteria

1. Complete P01 metadata and convention work. Compare a minimal explicit reader
   with Kloppy; consider floodlight as an alternative or focused cross-check.
2. On protocol-selected development records, require faithful identifiers,
   dimensions, clocks, quality flags, missingness, and provider extras. Document
   every transform/filter and test against the raw contract. Library agreement
   alone is not ground truth if they share assumptions.
3. Add mplsoccer only when a diagnostic is ready; consider DataBallPy for a
   demonstrated synchronization/analysis need. Keep report tooling optional.
4. Read the directly overlapping defensive/pose research before freezing edge
   candidates. Defer network/valuation tooling to the roadmap's evidence gates.

Before adding any dependency, pin a compatible version in the project lockfile,
record its license and citation, examine relevant source/defaults, verify a clean
install on the chosen Python version, and add a narrowly scoped adapter test.
Use only permissible SkillCorner inputs. Package availability, pre-existing code
permission, and scientific suitability are three separate questions.

## Session 1 closest-prior-work audit

Reviewed 2026-09-10 as a bounded originality check; no paper code, weights, or
external match data were executed or imported.

| Prior object | Relationship to this project |
| --- | --- |
| [Physics-Based Modeling of Pass Probabilities in Soccer](https://www.researchgate.net/publication/315166647_Physics-Based_Modeling_of_Pass_Probabilities_in_Soccer), Spearman et al. (2017) | Establishes time-to-intercept/time-to-control pass probabilities and hypothetical-pass analysis. A reachability model is not itself novel here. |
| [Who can receive the pass?](https://link.springer.com/article/10.1007/s10618-022-00827-2), Dick, Link, and Brefeld (2022) | Closest mathematical object: receiver Availability aggregates pass success across trajectories using ball dynamics, receiver reachability, opponent interception, and technical skill. |
| [SoccerMap](https://www.lukebornn.com/papers/fernandez_ecml_2020.pdf) and [un-xPass](https://github.com/ML-KULeuven/un-xPass) | Separate pass selection, success, and value. Their target separation is a design requirement; external data and learned models are not adopted. |
| [Temporal Graph Network reception model](https://link.springer.com/article/10.1007/s10994-025-06935-6) | Jointly predicts which teammate or opponent receives a pass against defensive structures. It makes raw receiver-ranking novelty implausible. |
| [GAPP](https://github.com/Sentient-Sports/EvaluatingDefensiveInfluenceUsingGATs) | Uses reception prediction and defender masking/attention for defensive influence. Model perturbation is a comparison point, not identified causation. |
| [DEFCON](https://arxiv.org/abs/2512.10355) | Combines action selection, success, value, and defender responsibility into defensive credit. Its scope and attribution assumptions bound our narrower diagnostic. |

### Originality decision

The likely contribution is a transparent benchmark and geometric reformulation
with an analyst-facing passage diagnostic. It asks how much incremental receiver-
ranking information simple defensive geometry adds beyond a credible defender-
free comparator, and whether a graded representation adds more than elementary
distances. A new mathematical construct is not established.

Behavioral ranking is not construct validation. The term accessibility requires
synthetic and structured football validation; suppression requires evidence that
distinguishes an unavailable option from one that was merely unchosen. Vendor
Passing Option events are model-derived and cannot provide independent ground
truth for that distinction.

## Session 4 bounded failure-mode reuse audit

Reviewed 2026-09-10. No package was installed, imported, or run; no external data,
weights, parameters, or code were adopted.

- [Floodlight `VelocityModel`](https://floodlight.readthedocs.io/en/latest/modules/models/kinematics.html)
  supports central and backward differences. Backward difference is a candidate
  primitive for a future timestamp-causal implementation; central difference is
  incompatible with the project's decision-time firewall.
- [DataBallPy space occupation](https://databallpy.readthedocs.io/en/latest/features/space_occupation.html)
  documents player influence using position, velocity, and ball distance, followed
  by summed team influence. It is a useful comparison for continuous aggregation,
  not an established finite-pass-route or receiver-selection implementation.
- [Dick, Link and Brefeld](https://link.springer.com/article/10.1007/s10618-022-00827-2)
  combines ball dynamics, player movement/reachability, opponent interception,
  and technical skill. It remains the closest prior mathematical object if a later
  reachability branch becomes causally supportable.
- [DEFCON](https://github.com/hyunsungkim-ds/defcon) combines learned action,
  outcome, value, and defender-responsibility components. It is a broader
  downstream framework rather than a reusable primitive for the selected
  multi-defender geometry question.

Session 4 selected multi-defender aggregation as the next prospective question.
Reuse should begin by benchmarking conceptual behavior against DataBallPy's summed
influence, while retaining the project's finite-connection semantics. No library
choice, kernel, or parameter is authorized by this review.

## Session 5 bounded primitive review

Reviewed prospectively before implementation. DataBallPy documents Voronoi and
Gaussian player/team influence over pitch locations; that is a useful conceptual
neighbor but not the frozen sum of exponential distances to a finite passing
segment. Floodlight's relevant primitives concern spatial containers and
kinematics, mplsoccer provides presentation and pitch geometry, and UnravelSports
focuses on learned graph representations. None exposes an exact dependency-light
primitive with the required finite-segment semantics. Session 5 therefore uses
the existing local segment projection plus a small local `math.exp`/`math.fsum`
implementation. No package, parameter, code, or alternate model was adopted.


## Session 8 — Local star representation and software reuse

Reviewed 2026-09-10 before empirical network analysis. The installed Kloppy
3.19.0 distribution records a BSD-3-Clause license. Its Frame, Player and
PlayerData types are reused through a thin optional adapter, tested on synthetic
frames. Caller-provided selections and verified centred metric coordinates are
required; the adapter does not infer active intervals, timing, or missing
direction. Native-sidecar limitations from Session 2 still apply. No external
football data, models or code were imported.

[mplsoccer 1.8.0 documentation](https://mplsoccer.readthedocs.io/en/latest/gallery/pitch_setup/plot_pitches.html)
provides pitch layouts and arrows/lines; its source is
[MIT licensed](https://github.com/andrewRowlinson/mplsoccer/blob/main/LICENSE).
Defer installation: canonical snapshots omit pitch dimensions and this phase
requires only one synthetic Cartesian diagram. Its rendering does not justify a
new dependency. Reuse mplsoccer later when a governed pitch context exists.

[matplotvideo](https://github.com/PySport/matplotvideo) documents synchronization
of matplotlib with a video player, requiring cv2/OpenCV; the repository records
MIT licensing. The reviewed README was the master-branch documentation, not a
verified/pinned release; a direct setup.py fetch was unavailable. No version was
installed or claimed tested. Defer: no video or temporal input is authorized.

Use the already locked NumPy 2.5.3 (BSD-3-Clause) implementation for features and
matrix utilities. No new SciPy, pandas, graph-library, or lockfile requirement
is introduced. Local software is limited to the project-specific option-state
contract, frozen utility-to-share calculation, and descriptive summaries.
A local star carries no extra information beyond its complete edge vector.

Upstream contribution opportunity: none established. Explicit metric-coordinate
context validation could eventually motivate a generic Kloppy helper, but this
audit does not demonstrate a missing upstream capability. No external PR is
authorized. Existing license notices remain intact; general-purpose library use
is consistent with the recorded competition rule, without importing external
competition data or promising cross-provider empirical validation.

## Session 9 — Public tooling and animation

Reviewed and locked 2026-09-10. Kloppy 3.19.0 (BSD-3-Clause) remains the
optional provider-neutral frame/player layer. The public adapter now has clearer
typing and errors but retains explicit player selections and verified centred
metric coordinates. It does not replace Kloppy abstractions or infer eligibility.

mplsoccer 1.8.0 (MIT) is adopted as an optional visualization dependency for the
football pitch canvas. Its documented custom/tracking pitches require explicit
length and width, which matches the public API's fail-closed dimension contract.
All option edges, share encodings, labels and scientific caveats remain
project-owned. Matplotlib 3.11.1 supplies figure/animation primitives and Pillow
12.3.0 (MIT-CMU) supplies deterministic GIF encoding. pandas 3.0.5
(BSD-3-Clause) is used only by the lazy dataframe export. NumPy 2.5.3 remains
the core numerical dependency; its installed metadata records a composite
BSD/0BSD/MIT/Zlib/CC0 expression. Resolved versions are frozen in `uv.lock`.

matplotvideo remains deferred. Its documented purpose is synchronizing a
Matplotlib plot with an existing video player and it requires OpenCV. Session 9
has no video input and directly generates a synthetic `FuncAnimation`, so adding
matplotvideo would not simplify the implemented workflow. No NetworkX, Polars,
OpenCV, FFmpeg or web-service dependency was added.

Upstream contribution assessment: **NO — none established**. The stricter
coordinate/selection checks and local-star rendering are specific to this
project's analytical contract. No generic missing Kloppy, mplsoccer or
matplotvideo primitive was demonstrated, and no upstream change was made.

## Session 10 — Package-readiness review

No dependency was added. NumPy remains the core numerical requirement; Kloppy,
pandas, Matplotlib, mplsoccer and Pillow remain in their existing optional
extras at the locked Session 9 versions. The clean-install matrix confirmed that
each extra supplies its documented workflow and that root-package import remains
safe without optional packages.

The wheel and source archive vendor none of these dependencies, so their BSD,
MIT, MIT-CMU and project-specific open-source notices remain with their own
distributions. `LICENSE.md` is present in both project archives and covers only
original project code and documentation. SkillCorner data is absent and is not
relicensed. No new ecosystem gap or upstream contribution target was established.

## 2026-09-10 — Session 12a external xT prerequisite audit

Reviewed socceraction 1.5.3 at immutable source
`3ca3ce0b0163352b84a0f7665c647fb4f3f9c3ad`, without installing it or requesting
surface values. Its MIT code license does not establish redistribution rights
for the external Karun Singh 12-by-8 surface linked by its loader. The associated
article describes 2017–18 Premier League methodology with a different illustrated
grid resolution; exact artifact lineage and licensing remain unresolved.
Declared Python/NumPy/pandas constraints conflict with the current environment.
The library's normalized rectangle and reversed row lookup require an explicit
mapping from this project's centred, x-only-reflected coordinates. Actual
per-match dimensions and lateral correspondence are not fully evidenced here.
Official additional-data restrictions do not explicitly settle pretrained-grid
eligibility. No alternative model search, code adoption or dependency change.
See the [Session 12a audit](../docs/session_12a_threat_prerequisite_audit.md) and
its pinned-source citations for the separate rights, eligibility and geometry
gates. Result: **BLOCKED — MULTIPLE PREREQUISITES**.

## 2026-09-10 — Session 12b formula-only progression interface

Implemented an internal provider-independent surface protocol and normalized
linear goalward progression, reusing the existing frozen NumPy-backed option
core and standard-library arithmetic. No new dependency, copied external
surface, learned external parameter or ecosystem integration was added.
Socceraction and the external xT branch remain deferred with Session 12a's
blockers preserved. The metadata dimension projection retains only permitted
fields. Synthetic core tests pass, but canonical longitudinal boundary violations
blocked empirical use of the bounded surface. Keep the interface internal; no
release or generic upstream gap is claimed. See the
[Session 12b report](../docs/session_12b_internal_threat_baseline_report.md).

## 2026-09-10 — Session 12c coordinate-support semantics

The pinned SkillCorner README documents centred metres and the detected versus
extrapolated flag, but does not establish clipping or legitimate coordinate
support beyond field markings. Session 2's historical observation of out-of-pitch
positions is not a provider guarantee. The coordinate review used existing pure
clock, transform and integrity helpers with a separate selective syntax reader;
no package, external surface or learned parameter was adopted. No ecosystem gap
or release claim is established. Provider-coordinate support and the analytical
value domain remain distinct questions. See the
[Session 12c report](../docs/session_12c_coordinate_boundary_review.md) for the
F/2 conclusion and bounded clarification recommendation.

## 2026-09-11 — Session 13 defender-edge relation layer

The provider-independent relation layer reuses the project-owned finite-segment
primitive, NumPy-backed frozen M1 option-network implementation and established
aggregation conventions. No external football package, graph library, kernel,
field model or parameter was adopted. The abstraction remains internal because
its evidence is development-only and its synthetic renderer failed final
presentation QA. No generic upstream ecosystem gap is established. See the
[Session 13 report](../docs/session_13_defender_edge_influence_report.md).

## 2026-09-11 — Session 14 fixed-field prerequisite

The internal geometric fields use locked NumPy 2.5.3 and standard-library
float64 summation/logarithmic union; no dependency, external model or parameter
was adopted. The planned locked-Matplotlib visual was not implemented after the
synthetic Simpson acceptance gate failed. No upstream capability gap, package
readiness or field-validity claim follows. A separate numerical-contract review
is recommended before further use. See the
[Session 14 report](../docs/session_14_continuous_occlusion_hypothesis_report.md).
