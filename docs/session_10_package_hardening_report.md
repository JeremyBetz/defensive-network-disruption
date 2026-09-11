# Session 10 — Package hardening and release readiness

## Outcome

**Execution: VALID.**

**Public release: A — READY FOR EXPERIMENTAL 0.1.0 RELEASE.**

**Portfolio: 1 — STRONG PORTFOLIO ARTIFACT NOW.**

Session 10 began from clean synchronized
`506891ace7c7cff5b3e9e5e0e54667252bd91a15`. It hardened the existing
provider-independent local option-network package without changing M0/M1
mathematics, network summaries, empirical results or scientific claims. The
ending and live remote hashes are reported in the final handoff because a commit
cannot contain its own hash.

## Requested handoff

1. **Starting HEAD:** `506891ace7c7cff5b3e9e5e0e54667252bd91a15`.
2. **Ending HEAD:** supplied after the closure commit.
3. **Protocol:** [Phase 10](protocols/phase_10_package_hardening_and_release_readiness.md),
   commit `f56a704`, SHA-256
   `fa05a37faeaad397082d57c06c3455e51e5d49d186ab36f575ff0468f498d169`.
4. **Version:** promoted from `0.0.0` to `0.1.0` under an experimental,
   pre-1.0 compatibility contract. No tag or release was created.
5. **Release classification:** A. The API, archive, clean-install,
   documentation and privacy gates passed.
6. **Portfolio classification:** 1. The repository now combines a bounded
   scientific result, coherent API, visual story, runnable example, CI,
   reproducible distributions and contributor/release documentation.
7. **Public API:** the ten root exports are unchanged. Public annotations,
   docstrings and argument-specific errors were improved; Session 9 numerical
   outputs remain exact.
8. **Metadata:** `0.1.0`, Jeremy Betz, MIT, Python 3.11+, alpha/science
   classifiers, football-data keywords and verified repository, docs, issue and
   changelog URLs are present.
9. **Extras:** NumPy remains the only core requirement. `interop`, `dataframe`,
   `visualization` and `public` retain their Session 9 package sets. No runtime
   dependency was added.
10. **Clean installs:** core, interop, dataframe, visualization and public
    profiles passed on Python 3.13. The complete public workflow also passed on
    the minimum supported Python 3.11.
11. **Quickstart:** ran from an empty directory against the installed wheel. It
    constructs a synthetic Kloppy frame, evaluates and compares M0/M1, exports
    M1 rows and writes a side-by-side SVG.
12. **Distributions:** two wheel builds were byte-identical at 63,566 bytes and
    SHA-256 `1de87e6befd4df7ba84469642cc16d64f8df53ca88d6622a214ce24248874f42`.
    Two canonical sdists were byte-identical at 87,204 bytes and SHA-256
    `329799ebbc895cf2845ca0d7ffef5a8e82a7b8e9b4b3b30dff1a32f0f83179c9`.
    Archives were inspected and not committed.
13. **Release documents:** [changelog](../CHANGELOG.md),
    [contributing guide](../CONTRIBUTING.md) and
    [release checklist](release_checklist.md) are present. Publishing steps stay
    unchecked and require separate authorization.
14. **README:** 653 words, one synthetic figure and no table. It states that the
    package is unpublished, gives source-install instructions and keeps the
    scientific limitations prominent.
15. **Visuals:** two temporary renders of both the SVG and 80-frame GIF were
    byte-identical to each other and the committed Session 9 assets. No visual
    byte changed.
16. **Tests:** focused Session 9/10 checks passed 21 with no skips. The full
    active suite passed 219 with three retained historical scaffold skips, 222
    total. Compilation, package metadata, archive contents, links, README limits,
    privacy, history and diff checks passed. GitHub Actions run `34555022748`
    passed the distribution job and the full suite on Python 3.11 and 3.13.
17. **Claims:** C01/C02, C09/C10 and all other claim statuses are unchanged.
    Accessibility remains **PROXY ONLY**; suppression remains **NOT SUPPORTABLE**.
18. **Data access:** no empirical population, raw provider product, protected or
    withheld detail, pose data, identity mapping or scientific output was opened.
    Only repository source, synthetic fixtures and committed public assets were
    used.
19. **Commits/push:** protocol `f56a704`, implementation `d53db2d`, release docs
    `6a7e976`, deterministic-archive fix `4bb92bf`, closure `495f368`, CI
    portability `73638c1`, and completed cross-platform checks `9474f36` precede
    this evidence update. Push and remote synchronization are reported in the
    final handoff.
20. **Next direction:** run one separately authorized experimental `0.1.0`
    release phase covering the tag, GitHub release, hashes and staged
    TestPyPI/PyPI verification. It is not executed here.

## Audit detail and qualifications

The first distribution rehearsal exposed two package-only issues. The archive
guard confused the import package's legitimate `data` namespace with the raw
repository data directory, and setuptools did not produce byte-identical sdists
from `SOURCE_DATE_EPOCH` alone. The guard now distinguishes those paths. A small
standard-library builder canonicalizes sdist member order, ownership and times;
the historical wheel behavior was already deterministic. Both corrections were
tested and committed before final builds.

The wheel intentionally contains the repository's research modules because
moving frozen helpers would create avoidable scientific risk. They remain
unsupported deep imports. Inspection found source code only: no provider data,
player/event identity records, credentials, private paths, access ledgers or
generated scientific artifacts. Historical match-level allowlist constants
remain in two internal research modules exactly as already published in the
repository; they are code provenance, not bundled match records or mappings.

The source archive contains the controlled release documents, quickstart, build
audit, source and tests. Repository-level `data/`, `outputs/`, caches and local
artifacts are excluded. Dependencies are referenced through package metadata and
are not vendored; their existing licenses remain their own. The project MIT
license applies to original code and documentation and does not relicense
SkillCorner data.

The engineering sanity check completed 1,000 four-candidate M1 evaluations far
below the frozen ten-second guard in the locked environment. This is only a
regression safeguard and supports no performance or scientific claim.

The first pushed workflow, run `34554608033`, preserved a clean-environment
failure: historical tests placed temporary fixtures under the macOS-only
temporary root, and one Session 10 compatibility fixture required bit equality
for derived floating-point shares. Run `34554921441` confirmed the portable
temporary-file correction, then exposed GitHub's shallow checkout and one
remaining exact comparison for effective option count. The final workflow uses
full Git history because the release preflight verifies its frozen starting
commit. Derived share and effective-count fixtures allow four float64 epsilons;
feature matrices, utilities, ordering, ties, summaries, and production code are
unchanged. Run `34555022748` passed distribution and both supported Python jobs.
The failed runs remain part of the public GitHub Actions history.

The compact [manifest](../outputs/package_release_readiness/manifest.json) binds
the protocol, environment, release contract, distribution inventory, QC and
historical claim/result authorities. Manifest SHA-256:
`bde662509b4ab4ff2065a514dc6940be2dc9aae77d3198e9c23d9231780c61f2`.

No package was uploaded, no release or tag was created, and no scientific work
was begun.
