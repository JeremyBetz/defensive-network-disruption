# Disrupting the Network

**Measuring Off-Ball Defensive Positioning in Football** — a working title.

Exploratory research for the **PySport Analytics Cup 2.0, USA region, Football
challenge**, on defensive positioning using the permitted SkillCorner Australia
A-League 2024/25 data. This project is under development: no attacking-connection
measure, cover-shadow measure, network-disruption metric, or defensive-value
model has been validated or implemented.

The first question is: **At a given moment, what makes a connection between two
attacking players viable, and how might defender positioning continuously weaken
it?** A later question is how a defense might suppress attacking options while
preserving its own support and cover. Graphs will follow a defensible football
measurement; they are not evidence that the measurement works.

The intended audience is analysts and coaches interested in positioning before
an on-ball defensive event. Player attribution and recruitment use would require
additional evidence. This is substantial new work with a different question from
the separate `moving-the-defense` project; no prior code, data, or results have
been imported.

## Run the scaffold

Use Python 3.11+ and the open-source `uv` environment manager. The development
interpreter is selected by `.python-version`; dependencies are recorded in
`uv.lock`. From the repository root:

```sh
uv sync --locked
uv run --locked python -m unittest discover -s tests -v
```

The package has no runtime dependencies. Setup may download the Python
interpreter and build tools; it does not download competition data. Tests run
without data. Coordinate, segment-geometry, and graph tests are explicitly
skipped until their contracts exist. Passing smoke tests is not scientific
validation. There is no analysis pipeline yet.

## Repository

```text
configs/       Non-sensitive configuration and future frozen specifications
data/          Local-only competition data; see data/README.md
docs/          Charter, roadmap, governance, protocols, and evidence ledgers
notebooks/     Future protocol-linked exploration; no saved data outputs
outputs/       Ignored local results and diagnostics
references/    Source records and planned literature review
scripts/       Future explicit, reproducible entry points
src/defensive_network_disruption/
               Empty data, geometry, networks, validation, visualization modules
tests/         Import checks and deferred scientific-contract tests
```

Start with the [project charter](docs/project_charter.md),
[research roadmap](docs/research_roadmap.md), and
[research governance](docs/research_governance.md). The supplied libraries and
related projects have a [documented integration review](references/library_review.md).
All candidate claims are [UNTESTED](docs/claim_status.md).

## Next step and submission

Finalize the [Phase 1 inventory protocol](docs/protocols/phase_01_inventory.md),
confirm the permitted release and access terms, then inventory metadata without
opening outcome-bearing records. Establish deliberate development and validation
partitions before viewing match passages or evaluating candidate measures.

The confirmed submission constraints are a public GitHub repository, an open-source
license, reproducible execution without proprietary software, a YouTube pitch of
at most one minute, and a README of at most 1,000 words with at most two figures
and tables combined. The deadline is **18 December 2026**; the USA final
is **24 February 2027 in Boston**. See the
[rules and verification status](docs/competition_rules.md) before submission.

Code and original documentation are released under the [MIT License](LICENSE).
SkillCorner data remains subject to its own terms and is not included or
relicensed. Obtain and place eligible data as described in
[data/README.md](data/README.md). This scaffold is local; public GitHub publication
and the empirical reproduction workflow remain future deliverables.
