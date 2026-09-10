# Scripts

Reserved for explicit acquisition, inventory, diagnostics, evaluation, and
reproduction entry points after their protocols exist. No downloader or analysis
command is implemented at initialization.

Each future command must state required inputs, permitted partition, output
locations, configuration, and failure behavior. Avoid hidden downloads, model
fitting during imports, hard-coded personal paths, and outcome-dependent defaults.
Scaffold checks currently use Python's standard library test runner:

```sh
uv run --locked python -m unittest discover -s tests -v
```
