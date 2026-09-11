# Feedback and participation

This project is being developed independently for an individual competition
submission. Issues, questions, bug reports and general feedback are welcome.

To preserve clear independent authorship of the competition entry, external
code, analysis, methodological work or other substantive contributions intended
for inclusion in the submission are not being accepted during the competition
period. This is a project policy based on the competition's individual-entry and
original-work requirements; it does not restrict discussion or open-source use.
The released software may still be viewed, used and forked under the MIT License.

The development guidance below records the project's standards and may support
post-competition participation. It is inactive as an invitation for substantive
external work during the competition period.

## Development setup

Install [uv](https://docs.astral.sh/uv/), clone the repository, then run:

```sh
uv sync --locked --all-extras
uv run --locked python -m unittest discover -s tests
```

Project changes are kept small, readable and typed where that clarifies public behavior.
Public functions need concise docstrings and actionable errors. Add synthetic
tests for supported behavior and run `git diff --check` before proposing a
change.

## Public software

Prefer neutral, provider-independent geometry, adapters and presentation code.
Do not add a dependency when the standard library or an existing dependency is
sufficient. A new ecosystem adapter should document its semantics, version,
license and reason for inclusion. Public API changes are recorded in `CHANGELOG.md`.

Only root-package exports are supported. Any later proposal to expand that
surface should explain the user need and compatibility cost.

## Scientific and data changes

Changes to features, model semantics, candidate definitions, preprocessing,
metrics or interpretation require a prospective protocol under
`docs/protocols/`. Preserve negative and invalid results; never rewrite historical
authority to make a result cleaner.

Do not commit raw or reconstructive competition data, provider identities,
coordinates, timestamps, credentials, signed URLs, access ledgers or private
paths. Synthetic fixtures must be clearly artificial and cannot serve as
football-validation evidence. Read `AGENTS.md`, `docs/research_governance.md` and
`docs/competition_rules.md` before research-facing work.
