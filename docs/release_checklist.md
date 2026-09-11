# Experimental release checklist

Use this checklist only after explicit authorization to release. Session 10
assesses readiness; it does not complete the tag, GitHub release or PyPI steps.

## Source and evidence

- [ ] Working tree is clean and local, tracking and live remote heads match.
- [ ] Version and pre-1.0 stability language agree across metadata and docs.
- [ ] Changelog contains the intended version and release date.
- [ ] Scientific outputs, protocols, claims and historical authorities are unchanged.
- [ ] Publication scan finds no raw data, identities, credentials or private paths.
- [ ] `LICENSE.md` is present and third-party/data terms remain distinct.

## Software and distributions

- [ ] Focused and full active tests pass; skips are reported.
- [ ] Source, scripts and examples compile.
- [ ] Wheel and sdist build twice with identical hashes under the frozen epoch.
- [ ] Archive inventories contain required files and no prohibited material.
- [ ] Core, interop, dataframe, visualization and public clean installs pass.
- [ ] Quickstart runs from an empty working directory.
- [ ] Public imports, metadata, project URLs and optional-extra errors are correct.
- [ ] Synthetic SVG and GIF reproduce byte-identically.

## Communication

- [ ] README remains below 1,000 words and within the two-visual/table limit.
- [ ] Documentation links resolve and limitations are prominent.
- [ ] Public API guide and contribution instructions match the release.
- [ ] Final clean-environment empirical reproduction is handled separately if required.
- [ ] One-minute competition pitch is complete if this is a submission release.

## Explicitly authorized release actions

- [ ] Create the signed or annotated git tag.
- [ ] Build final archives from that exact tag.
- [ ] Publish the GitHub release with hashes and changelog excerpt.
- [ ] Publish to TestPyPI, verify installation, then publish to PyPI if authorized.
- [ ] Recheck public repository rendering and package-index metadata.
