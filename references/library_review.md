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
