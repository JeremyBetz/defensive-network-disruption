# Scripts

This directory contains explicit, protocol-bound entry points for metadata
inventory, compatibility checks, population construction, model comparisons,
source integrity, protected evaluation, and construct diagnostics. Historical
session runners are preserved because stopped and invalid executions are part of
the scientific record.

Do not treat a script's existence as authority to run it. Read the corresponding
committed protocol, later amendments, decision brief, and research-log entries;
verify the permitted partition and current checkpoint first. In particular,
Phase 07a withdrew the Session 7 human-review commands before any response was
collected.

Each governed command states its inputs, partition, outputs, prerequisites, and
failure behavior. Data acquisition and empirical commands require separately
obtained competition-permitted files and must not be invoked as demonstrations.
Imports must not trigger downloads, hidden fitting, or data access.

The active synthetic/software test suite runs with:

```sh
uv run --locked python -m unittest discover -s tests -v
```

See the [research log](../docs/research_log.md),
[protocols](../docs/protocols/), and [output guide](../outputs/README.md) before
using a session runner.
