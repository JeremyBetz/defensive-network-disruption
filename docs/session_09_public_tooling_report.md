# Session 9 — Public tooling, animation, and network storytelling

## Outcome

**Execution: VALID.** **Software B — PUBLIC CORE READY WITH EXPERIMENTAL LABEL.**
**Visual 1 — HERO STATIC + ANIMATION READY.**

The provider-independent local-star representation now has a coherent public
API, explicit Kloppy interoperability, lazy dataframe export, mplsoccer pitch
presentation, a proprietary-free quickstart, a polished synthetic hero, and an
eight-second synthetic animation. The API remains version `0.0.0` because its
surface and construct semantics still warrant an experimental stability label.

The session began from clean, synchronized
`645f282402c4fccf6117186381a1212b56f11be9`. Local `HEAD`, `origin/main`, and
live GitHub `main` matched before work. The ending commit and synchronized remote
hash are reported in the final handoff because a commit cannot contain its own
hash.

## Authority and chronology

The [Phase 09 protocol](protocols/phase_09_public_tooling_and_storytelling.md)
and [software contract](../outputs/public_examples/software_contract.json) were
committed first at `89995c8`. The tested API, dependencies, quickstart, runner,
tests and environment authority were committed at `a383519`.

The first post-commit preflight found a self-referential safety-check defect: it
matched forbidden path names inside the guard itself. No asset or scientific
result had been rendered. The correction changed the guard to inspect callable
routes, refreshed the implementation hash, passed 12 focused tests, and was
preserved separately at `39ab1f1`. Preflight then passed before rendering.

## Public API

The root package exports `OptionState`, `FrozenOptionModel`, `OptionEdge`,
`OptionNetwork`, `evaluate_options`, `compare_options`,
`option_state_from_kloppy`, `plot_option_network`, and
`animate_option_network_comparison`. Imports perform no data loading, coefficient
discovery, plotting, or network access.

`OptionEdge` exposes utility, model-implied share, tie block and expected rank.
`OptionNetwork` exposes immutable edges and option weights, the complete tied top
set, a unique-only `top_option`, and direct access to the six frozen summaries.
`to_pandas()` lazily returns the frozen seven-column edge schema and gives a
specific extra-install message when pandas is unavailable. Records and
dataframes are detached from the immutable result.

Plotting remains outside the numerical core. `plot_option_network(...)` requires
explicit pitch dimensions, validates exact state/network alignment and rejects
out-of-pitch geometry. `animate_option_network_comparison(...)` accepts explicit
M0/M1 models and identical states for both panels, returning a Matplotlib
animation without saving or loading anything automatically. The numerical
features, preprocessing, utilities, softmax, ties and summaries are unchanged.

The [API guide](public_api.md) places limitations beside direct-state, Kloppy,
dataframe, plotting and animation examples. The runnable
[quickstart](../examples/quickstart.py) constructs a synthetic Kloppy Frame,
passes explicit selections and coordinate context, evaluates an explicit demo
model, exports a dataframe and writes an SVG. It uses no proprietary software or
data.

## Ecosystem and packaging

NumPy 2.5.3 is now a declared core dependency. Optional extras separate Kloppy
3.19.0 interoperability, pandas 3.0.5 dataframe export, and Matplotlib 3.11.1,
mplsoccer 1.8.0 and Pillow 12.3.0 visualization. The `public` extra combines
them; all versions are resolved in the lockfile.

Kloppy remains the football-data abstraction and the project adapter retains
explicit eligibility and coordinate responsibility. mplsoccer draws only the
custom 105×68 metre synthetic pitch. Project code owns every network encoding.
matplotvideo was not adopted because it synchronizes plots with existing video
and requires OpenCV, while this workflow directly generates synthetic animation.

Upstream contribution assessment: **NO — none established**. The implemented
checks and drawing layer are tied to this local analytical contract; no generic
missing capability in Kloppy, mplsoccer or matplotvideo was demonstrated. No
upstream PR or external publication occurred.

## Public assets and portfolio story

The [static hero](../outputs/public_examples/synthetic_option_network.svg) is a
16:9 vector, with a 1600×900 design target, showing a side-by-side M0/M1 comparison. The
[animation](../outputs/public_examples/synthetic_option_network_animation.gif)
is a looping 960×540 GIF with 80 frames at 10 fps and eight seconds of smooth,
deterministic motion. Both use the same stationary anonymous carrier, four
candidate receivers and three defenders in each panel. Edge width and opacity
show model-implied receiver-option shares; annotations show receiver share,
top-two share and effective option count. A visible caveat denies accessibility
and pass-probability interpretation.

Both outputs were rendered twice in independent temporary directories and were
byte-identical. The SVG is 80 KiB and the GIF 1.6 MiB. Native-aspect inspection
showed complete labels, clear contrast and no clipping. A contact sheet covering
frames 1, 21, 41, 61 and 80 confirmed readable, continuous movement. The static
hero is the README's only figure; the GIF is linked, keeping one competition
figure/table slot unused. README is 882 words.

The public story remains bounded: a carrier has modeled receiver options;
attacking geometry defines M0; defender geometry reshapes the M1 distribution;
and the closed development description changed effective modeled option count
from `7.165293607` to `5.980391018`. This is in-sample descriptive compression.
A star adds no information beyond its complete edge vector, and software
presentation does not create new predictive or practitioner evidence.

## Verification

- Focused Session 9 suite: **12 passed, 0 skipped**.
- Full active suite: **210 passed, 3 skipped, 213 total**. The skips are retained
  historical scaffold placeholders rather than Session 9 tests.
- Compilation passed for source, scripts, tests and examples.
- Core wheel clean install passed with NumPy only; isolated import exposed all
  ten public names without optional dependencies.
- Public-extra wheel clean install passed with 34 open-source packages; the
  quickstart ran from an empty directory and produced its SVG.
- Exact 80-frame/10-fps/looping GIF structure, SVG annotations and native output
  sizes passed.
- Deterministic render hashes, manifest cross-checks, public schemas, package
  metadata, README limits, documentation links, publication/privacy scans,
  historical preservation, staged review and `git diff --check` passed before
  final commit.

The [manifest](../outputs/public_examples/manifest.json) binds the protocol,
contract, implementation authority, frozen public model authority and output
hashes. Manifest SHA-256:
`a5710b88cb17fd4d294e284b02a24999b336573cb8689d8f92bbcbf944633baa`.

## Scientific boundary and next direction

No empirical population, target, outcome, provider product, reserved detail,
withheld match, pose, or temporal reconstruction was opened. No M0/M1 refit, M2
computation, new edge transformation, metric, prediction, reviewer study, or
scientific analysis occurred. C09/C10 remain SUPPORTED WITHIN SCOPE, C01/C02
remain IN PROGRESS, and other claim statuses are unchanged.

Accessibility remains **PROXY ONLY**. Suppression remains **NOT SUPPORTABLE**.
The artifacts do not establish causal defender effects, true pass availability,
best-pass judgments, defensive value, network value, or analyst usefulness.

Recommend exactly one next phase: **separately governed package hardening and
release preparation** covering API stability review, versioning, distribution
metadata, public CI and release rehearsal. Do not execute it in Session 9.
