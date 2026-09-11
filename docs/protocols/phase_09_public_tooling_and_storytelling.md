# Phase 09 — Public tooling, animation, and network storytelling

Prospectively frozen from clean local/tracking/live GitHub commit
`645f282402c4fccf6117186381a1212b56f11be9` on 2026-09-10.

## Purpose and authority

Turn the closed Session 8 carrier-centred star into a coherent experimental
public API, quickstart, static hero, and synthetic animation. This is software
productization and storytelling, not a new predictive or construct-validity
analysis. Preserve the frozen M0/M1 features, preprocessing semantics, linear
utility operation, temperature-one option-share transform, `1e-12` block-high
tie rule, and six distribution summaries. M2 is excluded.

No canonical population row, provider product, empirical passage, reserved or
withheld detail, pose, target, outcome, or fitted-model result may be opened or
computed. Historical source, protocol, output, and claim-ledger bytes remain
unchanged except for append-only research-log and library-review entries.
Accessibility remains **PROXY ONLY** and suppression **NOT SUPPORTABLE**. The
software must use “model-implied receiver-option share,” “modeled attacking
option,” “defense-conditioned option structure,” and similarly bounded terms.

## Frozen public contract

The supported experimental surface exports `OptionState`, `FrozenOptionModel`,
`OptionEdge`, `OptionNetwork`, `evaluate_options`, `compare_options`,
`option_state_from_kloppy`, `plot_option_network`, and
`animate_option_network_comparison`. Callers always supply a model. Importing
the package loads no data, coefficient artifact, network resource, plot backend,
or optional dependency.

`OptionEdge` adds tie-aware `expected_rank`. `OptionNetwork` adds an immutable
receiver-to-share view, a unique-only `top_option`, direct read-only properties
for the six frozen summaries, and `to_pandas()`. The dataframe columns and order
are `carrier_id`, `receiver_id`, `utility`, `option_share`, `expected_rank`,
`tie_block`, and `is_top_option`. A missing pandas extra raises a concise
installation error. Detached records/dataframes cannot mutate the network.

Visualization stays outside the numerical module. `plot_option_network(state,
network, *, pitch_length, pitch_width, ax=None, title=None)` validates exact
candidate correspondence, finite positive dimensions, and containment inside a
centred metric pitch, then returns `(figure, axes)`. It uses mplsoccer only for
the custom pitch canvas. Project code owns edge widths, opacity, colors, labels,
top-set display, and summary annotations. `animate_option_network_comparison`
takes a nonempty sequence of states plus explicit M0/M1 models, dimensions, and
10 fps, and returns a Matplotlib animation without saving automatically.

Kloppy remains an optional adapter. Carrier, candidate and defender selections
and a verified centred-metric coordinate context remain mandatory. Eligibility,
direction and missing coordinates are never inferred or repaired.

The package stays at version `0.0.0` with an experimental label. NumPy becomes a
core runtime dependency. Optional extras are `interop` (Kloppy), `dataframe`
(pandas), `visualization` (Matplotlib, mplsoccer, Pillow), and `public` (all
three). Resolved versions are locked. matplotvideo is not adopted: it attaches
plots to existing video and requires OpenCV, while this session generates
synthetic animation directly. No graph dependency or service API is added.

## Frozen synthetic examples

All coordinates are synthetic centred metres on a 105 by 68 metre pitch. The
static state uses carrier `(0, 0)`, candidates A `(12, 8)`, B `(22, 0)`, C
`(10, -12)`, D `(30, 15)`, and defenders `(8, 3)`, `(16, -2)`, `(24, 10)`.
The hero uses the explicit public Session 8 M0/M1 model authority only in its
generator; the numerical API never discovers it automatically.

The animation contains 80 frames at 10 fps. For normalized time `t=i/79`, the
carrier stays `(0,0)`. Candidate paths are A `(12+2t, 8)`, B
`(22, 2 sin(2*pi*t))`, C `(10+3t, -12+2t)`, and D `(30-2t, 15-3t)`.
Defender paths are `(8+4t, 3-4t)`, `(16-2t, -2-4 sin(pi*t))`, and
`(24-5t, 10-3t)`. Both panels receive the identical state at each frame.
Motion is illustrative, not a physical simulator or empirical evidence.

Publish one 1600 by 900 side-by-side SVG and one looping 960 by 540, eight-second
GIF. Draw a neutral pitch, anonymous carrier/candidates/defenders, shares, tied
top state, top-two share, effective option count, and a visible non-probability
caveat. Edge width and opacity vary continuously with share; no edge disappears.
Embed only the SVG in README and link the GIF, leaving the README below 1,000
words and using one of the two allowed figure/table slots.

`examples/quickstart.py` uses a synthetic Kloppy Frame, explicit selections and
context, explicitly constructed demo models, evaluation, dataframe export and
plotting. It requires no proprietary data. Public API documentation must place
scientific limitations beside usage, not only in the research report.

## Commands, outputs, and validation

Session 9 uses `scripts/session_09_public_tooling.py` with `preflight`,
`render-examples`, and `publication-check`. Public outputs live under
`outputs/public_examples/`: `software_contract.json`,
`implementation_authority.json`, `synthetic_option_network.svg`,
`synthetic_option_network_animation.gif`, `qc.json`, and `manifest.json`.
Temporary comparison renders and logs stay ignored. Generated bytes are never
manually edited.

Commit protocol/contract first and tested implementation/environment authority
second. Render twice to temporary locations and require byte equality before the
single public render. Test immutable/permutation-stable construction, frozen
numerical equivalence, ties/ranks/properties, pandas schema and missing-extra
error, Kloppy validation, plot/animation structure, exact synthetic sequence,
full-frame bounds, import side effects, absence of fitting/acquisition/M2 routes,
quickstart, wheel installs in fresh core/public environments, README limits,
links, privacy, output hashes, historical preservation and `git diff --check`.

Software classification A requires a clean public install and no material API
stability concern; B is usable but explicitly experimental; C is demo-ready with
an unresolved contract; D has a correctness/architecture blocker. Visual 1
requires both SVG and GIF to generate deterministically and pass native-aspect
visual review; 2 means static ready only; 3 is prototype only; 4 is not ready.
Execution validity is separate.

Append the report and bounded log/reuse entries only after closure. Record an
upstream opportunity only if a concrete generic gap is demonstrated; otherwise
record `NO — none established`. Recommend exactly one next phase and stop. Do
not publish a package, open an upstream PR, animate empirical data, expand the
network, modify a model, or begin another session.
