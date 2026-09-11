# Session 11 — Experimental v0.1.0 release

## Outcome

**Execution: VALID.**

**Release classification: B — GITHUB EXPERIMENTAL RELEASE COMPLETE.**

The first experimental public software release was created from audited release
commit `f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`. The annotated tag `v0.1.0`
peels exactly to that commit. The public GitHub prerelease is available at
[v0.1.0](https://github.com/JeremyBetz/defensive-network-disruption/releases/tag/v0.1.0).
PyPI publication was deliberately deferred because the repository and execution
host had no established authenticated trusted-publishing or credential-backed
workflow. No TestPyPI or PyPI upload was attempted.

## Authority and chronology

- Starting HEAD: `584e792337d926f10e13eb2870c95f45cb070aa5`.
- Release-document commit and immutable release HEAD: `f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`.
- Annotated tag: `v0.1.0`, message `Experimental public API v0.1.0`.
- The tag object and peeled commit were verified locally and from the live remote.
- The GitHub release is public, non-draft and marked as a prerelease.
- Ending HEAD is the later documentation commit containing this report and is
  reported in the final handoff because a commit cannot record its own hash.

Before tagging, the changelog received the release date and its pending wording
was removed. README and API installation text now distinguish GitHub release
artifacts from the unavailable PyPI distribution. No source, package metadata,
scientific output, protocol, model, or numerical implementation changed.

## Release audit

The complete Session 10 release checklist was rerun from the clean release HEAD.

- Focused Session 9/10 suite: 21 passed, 0 skipped.
- Full active suite: 219 passed, 3 retained historical scaffold skips, 222 total.
- Source, scripts and examples compiled successfully.
- GitHub Actions run `34555724135` passed distribution and the full suite on
  Python 3.11 and Python 3.13 for the release HEAD.
- Session 10 API, publication, metadata and distribution checks passed.
- README: 662 words, one figure and no table.
- Repository-local Markdown links passed.
- Credential, private-path, archive-member and publication scans passed.
- Core, interop, dataframe, visualization and public clean-install profiles
  passed on Python 3.13; the public workflow also passed on Python 3.11.
- The quickstart ran from an empty working directory.
- The synthetic SVG and 80-frame GIF reproduced byte-for-byte against the
  committed Session 9 assets.

Two candidate wheel builds and two candidate source builds were byte-identical.
After tagging, the release archives were rebuilt from the unchanged tagged tree
and matched the candidate builds byte-for-byte. The wheel contains package code,
metadata and `LICENSE.md`. The source archive contains the controlled release
materials. Neither archive contains repository data, outputs, caches, access
records, credentials, private files, or reconstructive records.

## Public artifacts and verification

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `defensive_network_disruption-0.1.0-py3-none-any.whl` | 63,591 | `b397fd19c33f86cb8574b9947ea88e63f79a47aeb8aabdf051b400db1eb0ca35` |
| `defensive_network_disruption-0.1.0.tar.gz` | 87,294 | `8b2f778926ed49384830823dac536592b78df2ad480311c0b12af6755acbeb1c` |

GitHub reports both assets as uploaded with matching SHA-256 digests and byte
counts. Both were downloaded from the public release into temporary storage and
hashed again successfully. The downloaded wheel was installed with the complete
`public` extra in a fresh Python 3.13 environment. Package metadata reported
`0.1.0`, import succeeded, a synthetic M1 evaluation succeeded, and the complete
synthetic quickstart produced its SVG.

## Scientific and publication boundaries

This was a software-release session. No model was fitted, no empirical population
or scientific output was recomputed, and no competition, protected, withheld, or
pose data was accessed. C01/C02, C09/C10 and all other claim statuses are
unchanged. Receiver-option shares remain model-implied. Accessibility remains
**PROXY ONLY** and suppression remains **NOT SUPPORTABLE**. The release makes no
causal defensive-value, attribution, pass-success, or best-pass claim.

The release notes describe the supported provider-independent API, M0/M1
comparison, Kloppy interoperability, pandas export, mplsoccer/Matplotlib
visualization, deterministic animation, optional extras, quickstart and API
guide. They label the software experimental and pre-1.0 without promising stable
compatibility.

## Deferred publication and next direction

PyPI currently has no project page for this distribution name, but name status
alone is insufficient authority to publish. No repository trusted-publishing
workflow, GitHub Actions publishing secret, host `.pypirc`, or other secure
authenticated normal release path was available. PyPI publication is therefore
deferred without requesting, printing, or storing credentials.

The single recommended future research phase is **Threat-weighted defensive
reshaping of the attacking option network**, comparing M0 and M1 modeled option
distributions under the same established open destination-threat surface. It
requires separate prospective governance and was not begun here.
