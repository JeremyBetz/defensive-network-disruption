# Test scope

Run `uv sync --locked`, then
`uv run --locked python -m unittest discover -s tests -v` from the root.

Two smoke tests check installed namespace imports from an empty working
directory, including a guard against local data reads and network connections.
They run without competition data. Python's standard library provides the test
runner; no scientific or testing dependency is required.

Three tests are deliberately SKIPPED, one each for coordinates, line/segment
geometry, and deterministic graph construction. Their reasons identify missing
contracts. They are not passing tests or scientific validation. Replace a
placeholder only after the associated interface and expected behavior are
specified; then test meaningful edge cases using clearly synthetic geometry.
No real match fixtures or unspecific numerical assumptions belong here.
