# Session 12a — Threat prerequisite audit

Date: 2026-09-10. Result: **BLOCKED — MULTIPLE PREREQUISITES**.
This is a documentation/provenance finding, not a negative scientific result.

## Authority and scope

Starting local, tracking and live remote main agreed at
`5b72645a1a6d10b94f4f747e7a34978e98d6e7ba`. The annotated release remains at
`f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`.
[Phase 12a](protocols/phase_12a_threat_prerequisites.md) was committed as
`283ac4a` before new public evidence was collected. Only public documentation,
selected public library source, and committed repository records were read.
No surface values, population rows, provider products or mixed manifests were
opened. No dependency was installed or library executed. No alternative surface
search, organizer message, release or scientific escalation occurred.

## One baseline, distinct authorities

The reviewed library is socceraction 1.5.3. Its annotated tag object is
`c4849f7eaa4191e2e19a6f8238f84583edb93a2e`, peeled to source commit
`3ca3ce0b0163352b84a0f7665c647fb4f3f9c3ad`. Selected source-file SHA-256
identities are recorded in the [compact summary](../outputs/threat_weighted_option_network/prerequisite_summary.json).

The [load_model documentation](https://socceraction.readthedocs.io/en/stable/api/generated/socceraction.xthreat.load_model.html)
links Karun Singh's named `open_xt_12x8_v1.json` baseline. That is an external
precomputed surface, not a set of coefficients bundled and licensed by the
library. Its numerical bytes were not requested; shape, values and immutable
surface hash are therefore **unverified**. The filename advertises 12 columns by
8 rows. The loader actually derives dimensions from the loaded matrix.

[Singh's methodology article](https://karun.in/blog/expected-threat.html)
describes 2017–18 Premier League event data and a possession-position value
model. Its illustrated derivation uses a 16-by-12 grid, not the linked 12-by-8
artifact. Thus the article documents the methodological/training context; it
does not establish an exact training recipe or byte-level lineage for that
separate file. Training provider, exact training snapshot, reproduction recipe
and artifact-specific provenance remain **unavailable in the inspected sources**.

The [pinned code license](https://github.com/ML-KULeuven/socceraction/blob/3ca3ce0b0163352b84a0f7665c647fb4f3f9c3ad/LICENSE.rst)
is MIT, copyright KU Leuven Machine Learning Research Group. This verifies code
reuse permission subject to its notice; it does not license the external training
data or surface. Neither the reviewed article nor loader documentation establishes
an explicit artifact redistribution license. Public availability and a filename
containing “open” do not establish that right. Surface use/redistribution remains
**unresolved**, not proven forbidden. No surface is vendored or relicensed.

## Library geometry and compatibility

The [pinned xthreat source](https://github.com/ML-KULeuven/socceraction/blob/3ca3ce0b0163352b84a0f7665c647fb4f3f9c3ad/socceraction/xthreat.py)
uses a matrix indexed by row and column. Default noninterpolated lookup converts
nonnegative x/y to integer cells, clips to the grid bounds, then selects row
`w-1-y_cell` and column `x_cell`. Upper endpoints map to the final cell.
Out-of-range clipping is library behavior, not authorization to silently clip
this project's future inputs. Interpolation is optional and is not selected here.
`rate` evaluates successful ball-moving actions; it is not a candidate-receiver
availability API. `load_model` reads a matrix without establishing its provenance.

[SPADL configuration](https://github.com/ML-KULeuven/socceraction/blob/3ca3ce0b0163352b84a0f7665c647fb4f3f9c3ad/socceraction/spadl/config.py)
uses a normalized 105-by-68 metre rectangle. Its schema requires x in [0,105]
and y in [0,68].
[Direction normalization](https://github.com/ML-KULeuven/socceraction/blob/3ca3ce0b0163352b84a0f7665c647fb4f3f9c3ad/socceraction/spadl/utils.py)
orients actions left to right and reflects both axes for the away side of its
SPADL input convention. That differs from this project's x-only reflection.
Neither a y reflection nor assumed surface symmetry may be silently introduced.

[Pinned package metadata](https://github.com/ML-KULeuven/socceraction/blob/3ca3ce0b0163352b84a0f7665c647fb4f3f9c3ad/pyproject.toml)
requires Python >=3.9,<3.13, NumPy ^1.26.0 and pandas ^2.1.1, plus scikit-learn,
lxml and pandera. The existing project requires NumPy >=2.4.6 and locks pandas
3.0.5; its public workflow includes Python 3.13. Direct installation into the
governed environment is incompatible by declared constraints. This is a static
metadata conclusion, not an installation test. No downgrade, new environment,
dependency, port or lookup implementation is authorized. A future dependency-free
surface consumer would need a separately governed contract and resolved rights.

## Competition eligibility

The current [official rules](https://pysport.org/analytics-cup/editions/analytics-cup2/rules)
were inspected in the rendered browser on 2026-09-10 after the text-fetch tool
failed. Submission requirements allow properly licensed/disclosed existing code
and libraries, but prohibit additional data beyond supplied/prior Cup datasets.
The page's resources include KU Leuven research code; this does not explicitly
permit external learned parameters. No inspected rule resolves whether this
particular pretrained grid is permitted. Eligibility is **unresolved**; an
explicit ban on additional data must not be misreported as an explicit ruling
on this artifact. The project's [governance](research_governance.md) also requires
eligibility to be established before external empirical parameters enter use.

Organizer clarification draft, **not sent**:

> May an Analytics Cup 2.0 submission apply the fixed Karun Singh 12-by-8 xT
> grid linked by socceraction, associated with external 2017–18 Premier League
> training data, solely as pretrained parameters to the permitted SkillCorner
> states, without importing those training events, provided separate surface
> licensing and attribution requirements are satisfied, or does this violate
> the additional-data rule?

## Coordinate lineage and missing prerequisites

| Prerequisite | Evidence and state |
| --- | --- |
| Origin and units | **Documented:** [data dictionary](data_dictionary_notes.md) records pitch-centred metres, x along length and y along width. No provider record was reopened. |
| Frozen transformation | **Verified in code:** [receiver_choices](../src/defensive_network_disruption/data/receiver_choices.py) uses `x'=s*x, y'=y`; sign derives from carrier team and period direction. [Session 3 runner](../scripts/session_03_benchmark.py) calls this population builder. |
| Strict adapter continuity | **Verified in code:** [Session 6 population adapter](../src/defensive_network_disruption/data/session6_population.py) retains the same transform. Unknown direction is not guessed. |
| Actual dimensions | **Verified aggregate record only:** [Session 2 schema summary](../outputs/development_compatibility/tracking_schema_summary.json) records (104,68), (105,68), (106,68). Its [producer](../scripts/session_02_compatibility.py) collects distinct pairs from `pitch_length`/`pitch_width`; the public summary omits per-match assignment. |
| Per-state dimensional mapping | **Unavailable:** the canonical population contract contains coordinates but no pitch dimensions. Distinct aggregate sizes cannot identify each state's match dimensions. |
| Lateral surface alignment | **Ambiguous:** native physical y is retained, whereas SPADL direction handling can reflect y. The exact external surface's lateral orientation/symmetry is not evidenced sufficiently to choose a mapping. |
| Boundary handling | **Unresolved future contract:** actual extent and out-of-bounds handling must be specified; do not infer dimensions from extrema or copy library clipping silently. |

If actual length L and width W and a compatible lateral axis were established,
translation/scaling would have the form `X=105*(x'/L+1/2)` and
`Y=68*(y'/W+1/2)` for an aligned y axis. This is conditional algebra, not an
approved mapping. The synthetic 105-by-68 pitch is no empirical authority.
The canonical omission of per-state direction metadata also prevents casually
reconstructing a different lateral convention. Changing frozen model inputs is
not a remedy authorized by this audit.

Smallest prospective restricted-metadata follow-up, **not executed**: separately
authorize only the historical nine-match development partition at the existing
pinned source. Verify each existing match-metadata object's identity and project
only root `pitch_length` and `pitch_width`, keyed internally by the already
governed match path/alias mapping. Reject missing, nonnumeric, nonpositive or
unrecognized values; retain the mapping ignored and publish aggregate verification
states only. No events, tracking, scores, rosters, targets, protected or withheld
matches are needed. Public coordinate documentation must separately settle
lateral correspondence; dimensions alone would not settle it. This proposal
grants no access authority.

## Formal mathematical findings — no empirical calculation

Retain signed destination changes, including negative ones:

`ΔT_j = T(r_j) - T(c)` and `H_m = Σ_j p_mj ΔT_j`.

Because `Σ_j p_mj = 1`, `H_1-H_0 = Σ_j (p_1j-p_0j) T(r_j)`.
The carrier baseline cancels from the shift but is necessary for either horizon.
The receiver bookkeeping term `(p_1j-p_0j)*(T(r_j)-T(c))` sums to that shift.
Its sign depends on both factors: a positive term may reflect less share on a
below-carrier receiver, rather than more share on a high-threat receiver.
Individual signs therefore do not identify a unique transfer between receivers.

Use **defense-conditioned model comparison**: M0/M1 differ in shared-feature
coefficients as well as defensive terms. Their difference is not an isolated
defender effect. Conditional receiver-choice shares and possession-based xT are
different constructs. Their product defines a descriptive model-based index,
not pass success, calibrated expected threat, causal suppression or player value.

A later protocol must replace overlapping example labels with mutually exclusive
mathematical cases, explicitly handling zero shifts, equal destination values,
and unavailable mappings before any frequencies or examples are inspected. No
empirical thresholds, tolerances or category frequencies are selected here.

## Decision, unexecuted items and closure

Readiness fails on eligibility, artifact-specific provenance/rights, and complete
coordinate mapping. Package incompatibility is an additional engineering finding.
There is no Session 12 scientific A/B/C/D or software 1/2/3/4 classification.
Accessibility remains **PROXY ONLY**; suppression remains **NOT SUPPORTABLE**.
The claim ledger and all historical authorities are unchanged.

Every requested empirical item—surface-value verification, threat lookup,
individual horizons, horizon shifts, receiver contributions, distribution or
match summaries, category frequencies, selections, figures, predictive or
practitioner evaluation—is **not executed in prerequisite audit**. Threat API,
dependency installation and new release are also not executed.

Exactly one next action: obtain written organizer clarification using the question
above, under separate authorization to send it. A favorable answer would not
waive surface rights/provenance or coordinate gates. This audit stops here.

Validation: source revision and selected file hashes verified; citations and
repository links reviewed; compact JSON parsed; append-only logs and unchanged
historical bytes checked; publication and staged-content scans and
`git diff --check` passed. Software tests were intentionally not run because
only documentation/provenance changed. No empirical test was run.

The compact summary binds source/protocol identities; its SHA-256 is
`0ced2c858239041809b2f5052ff23e021a5f53e23b18e87c7131843542ad09b1`.
Final commit and synchronized heads are supplied in the
delivery handoff rather than recursively embedded in this committed report.
