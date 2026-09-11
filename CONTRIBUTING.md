# Contributing

Contributions should improve the provider-independent software or strengthen a
prospectively governed research question without weakening the evidence record.

## Development setup

Install [uv](https://docs.astral.sh/uv/), clone the repository, then run:

```sh
uv sync --locked --all-extras
uv run --locked python -m unittest discover -s tests
```

Keep changes small, readable and typed where that clarifies public behavior.
Public functions need concise docstrings and actionable errors. Add synthetic
tests for supported behavior and run `git diff --check` before proposing a
change.

## Public software

Prefer neutral, provider-independent geometry, adapters and presentation code.
Do not add a dependency when the standard library or an existing dependency is
sufficient. A new ecosystem adapter should document its semantics, version,
license and reason for inclusion. Public API changes belong in `CHANGELOG.md`.

Only root-package exports are supported. Proposals to expand that surface should
explain the user need and compatibility cost.

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
