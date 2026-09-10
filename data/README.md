# Local competition data

No competition data is committed, downloaded automatically, or required for
package imports and scaffold tests. Raw files, derived tables, metadata manifests,
and pose artifacts belong here and remain ignored by Git.

## Obtain and place eligible data

1. Start at the user-supplied official source:
   [SkillCorner Open Data](https://github.com/SkillCorner/opendata).
   Use the [Cup 2.0 dataset description](https://pysport.org/analytics-cup/editions/analytics-cup2/datasets)
   and current rules to verify the eligible release. Public availability alone
   does not authorize extra data for the competition.
2. Finalize the [metadata inventory protocol](../docs/protocols/phase_01_inventory.md)
   before opening records. Select a source commit/release and record its terms
   and acquisition method. The full acquisition command and exact file manifest
   will be written after release identity is resolved; there is no bulk downloader.
3. Put authorized source files under `data/raw/skillcorner/<release>/`, retaining
   their original names and internal structure. Do not flatten different
   products into one directory. Keep source bytes immutable.
4. Put local coverage, checksums, and exposure/split manifests under
   `data/manifests/`. Record source URL/commit, acquisition date, relative path,
   product, size, checksum, and permitted use. Derived intermediate/final inputs
   go under `data/interim/` and `data/processed/`; diagnostics go under `outputs/`.
5. Audit metadata and prior exposure before selecting development/validation
   partitions. Downloading files is not permission to inspect their outcomes.
   Reserve match passages, event tables, aggregate performance values, and pose
   examples for their protocol-defined phase.

These are proposed local storage locations, not confirmed provider schemas.
Create subdirectories only when needed. The source overview and official
competition description differ on tracking coverage; the unresolved release
inventory and documented schema clues are in
[data_dictionary_notes.md](../docs/data_dictionary_notes.md).

Local machine path overrides may live in `configs/paths.local.toml` (ignored).
The committed [example configuration](../configs/paths.example.toml) is
documentation only; no loader consumes it yet. Do not store credentials in
committed configuration.

## Public reproducibility boundary

The eventual public workflow must identify the permitted input release,
acquisition/placement instructions, checksums where allowed, and a command that
reproduces every reported result. Until that exists, only the software scaffold
is reproducible. Do not substitute external providers or pretrained artifacts
to make an example run.

Original project software uses MIT; SkillCorner retains rights to its datasets.
Preserve provider attribution and terms. The public repository excludes data
even when the upstream source is public. Keep data-derived outputs and notebook
results local; publish only reviewed, permitted summaries/figures.

`.gitignore` covers everything here except this README and common data/archive
formats elsewhere. It cannot stop forced additions or data pasted into source
or notebook cells. Inspect staged changes before each commit. Do not use
`git add -f` for competition data or Git LFS to bypass this boundary.
