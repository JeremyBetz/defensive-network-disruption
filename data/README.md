# Local competition data

Competition data has been acquired locally for governed development and protected
evaluations, but none is committed, downloaded automatically on import, or
required for software tests. Raw files, reconstructed tables, detailed manifests,
and pose artifacts belong in protocol-specific ignored storage under this
directory. The protected and withheld boundaries remain in force.

## Obtain and place eligible data

1. Start at the user-supplied official source:
   [SkillCorner Open Data](https://github.com/SkillCorner/opendata).
   Use the [Cup 2.0 dataset description](https://pysport.org/analytics-cup/editions/analytics-cup2/datasets)
   and current rules to verify the eligible release. Public availability alone
   does not authorize extra data for the competition.
2. Read the current [research log](../docs/research_log.md), relevant protocol,
   and later amendment before any request or file open. Phase 01 resolved the
   selected source identity; later session protocols govern actual acquisition,
   products, partitions, and access boundaries.
3. Retain authorized source bytes under the session-specific ignored location
   named by that protocol. Do not flatten products, substitute revisions, or
   reuse an old downloader outside its authority. Keep verified source bytes
   immutable.
4. Keep detailed identities, checksums, access ledgers, exposure mappings, and
   derived records ignored. Only compact publication-reviewed aggregates and
   provenance summaries may be committed under `outputs/`.
5. Treat downloading, parsing, viewing, and aggregate inspection as distinct
   access events. The former protected set was spent by Session 6e; the remaining
   withheld match and pose data cannot be opened without new prospective
   authority.

Verified schema and convention facts are in
[data_dictionary_notes.md](../docs/data_dictionary_notes.md). Historical storage
proposals in early protocols do not override later session-specific authority.

Local machine path overrides may live in `configs/paths.local.toml` (ignored).
The committed [example configuration](../configs/paths.example.toml) is
documentation only; no loader consumes it yet. Do not store credentials in
committed configuration.

## Public reproducibility boundary

The governed session records identify the permitted release, verified source
identities, acquisition methods, environment, and commands behind reported
results. Submission hardening still requires reproducing that workflow in a clean
environment using separately obtained permitted inputs. Do not substitute
external providers or pretrained artifacts to make an example run.

Original project software uses MIT; SkillCorner retains rights to its datasets.
Preserve provider attribution and terms. The public repository excludes data
even when the upstream source is public. Keep data-derived outputs and notebook
results local; publish only reviewed, permitted summaries/figures.

`.gitignore` covers everything here except this README and common data/archive
formats elsewhere. It cannot stop forced additions or data pasted into source
or notebook cells. Inspect staged changes before each commit. Do not use
`git add -f` for competition data or Git LFS to bypass this boundary.
