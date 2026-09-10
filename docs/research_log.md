# Research log

Append-only record. Correct errors with dated amendments; preserve the original
entry. Link each empirical run to its prospective protocol and claim IDs. Use
local manifest references where identifiers cannot be published.

## 2026-09-09 — L000: Initialization

- **Request:** create a new USA/Football Analytics Cup 2.0 project around the
  attacking-connection measurement question and defensive structural tradeoff.
- **Work:** created the charter, phased roadmap, governance, UNTESTED claim
  ledger, rules record, methodological/data notes, and draft P01 inventory
  protocol. Added an importable namespace with five empty domain modules,
  local-only data/output conventions, and minimal environment/test scaffolding.
- **Design decisions:** no runtime dependencies; standard-library tests;
  Python >=3.11 declared, Python 3.13 selected for development; MIT for original
  code/docs. Both `LICENSE` and the officially required `LICENSE.md` use identical
  text. Dependency candidates remain in a review rather than becoming imports.
- **Scientific status:** C01–C08 remain UNTESTED. No edge definition, estimand,
  parameter, split, reference configuration, structure score, fitted model, or
  scientific result was selected. No competition files were downloaded or opened.
- **Provenance:** new files authored specifically for this entry. No sister-project
  code, figures, data, estimates, weights, or tuned settings were imported.
- **Git reference:** the initial commit containing this entry. Subsequent runs
  must record their exact code and protocol SHAs before execution.

## 2026-09-09 — L001: User-supplied source review

The user supplied SkillCorner Open Data, eleven software/research/archive links,
and the sister-project URL. Reviewed public documentation and repository
overviews only, including primary loading documentation where available.
[library_review.md](../references/library_review.md) records all sources and
integration decisions. No reference notebooks or model code were executed.

The text browser could not render PySport's JavaScript pages; a browser read of
the current Cup 2.0 page then confirmed the rules, dataset description, and
dates. The source check added the `LICENSE.md` requirement and documented the
permission to use licensed/disclosed general-purpose prior code, while retaining
the substantial-new-work boundary. No registration, external message, publication,
or submission was performed.

The official page describes 20 XY games including 10 new games; the upstream
repository overview describes 10. This is an unresolved release/coverage issue,
not a local audit finding. It must be reconciled before split assignment.

### Exposure record

| Scope | What was visible | What happened | Validation implication |
| --- | --- | --- | --- |
| This project's competition records | No raw tracking, event, aggregate, or pose files. | No acquisition or empirical run. | No project validation partition has been selected or evaluated. |
| Public vendor/library documentation | Schema descriptions; some pages include illustrative examples. | Documentation-level review only; no example data loaded or executed. | Log this context; no claim of independent validation follows. |
| `moving-the-defense` public README | Framing and published result summaries, including mention of SkillCorner use. | Reviewed at user's request; no numerical result adopted or copied into this study. | Prior-data overlap/exposure is UNKNOWN and must be audited before labeling holdouts untouched. |
| Related research overviews | Published methodological/result summaries. | Used for literature discovery and scope differentiation only. | External findings are not validation evidence for this project. |

Future exposure entries must include timestamp, operator, protocol/version,
partition and local match reference, exact fields/outcomes viewed, reason,
whether validation is spent, and any corrective action. This initialization
entry records the scope of the source review; it is not an empirical access log
claiming that prior knowledge has been absent.

## 2026-09-09 — L002: Scaffold verification

- Environment: macOS arm64, CPython 3.13.15, uv 0.12.6. Other supported Python
  versions/platforms have not been tested.
- `uv sync --locked` installed the editable package. The initial sandboxed
  build-tool fetch failed on DNS access; an authorized network retry succeeded.
  The build backend is pinned to setuptools 80.9.0. No analytics libraries or
  competition datasets were installed/downloaded.
- `uv run --locked python -m unittest discover -s tests -v`: **2 passed, 3
  explicitly skipped** (coordinates, line/segment geometry, graph construction).
- `uv build --offline` produced a source archive and a wheel. Installed that
  wheel into a fresh temporary Python environment and ran the same suite:
  **2 passed, 3 skipped**. Imports run in isolated subprocesses outside the
  source directory; the data/network guard passed.
- Inspected both distribution inventories: no data records, outputs, virtual
  environment, or build cache included. The build warned about the local cache
  location; inspection confirmed it was absent from the distributions.
- Git ignore probes covered nested data, manifests, outputs, accidental common
  exports/archives, credentials, local path overrides, and the environment.
  `LICENSE` and `LICENSE.md` are identical. README: 500 whitespace-delimited
  words, zero figures/tables at this check.
- These are software-foundation checks only. There is no empirical pipeline or
  scientific validation result to reproduce yet.

## Immediate next decision

Finalize and commit P01 Stage A's release identifier, metadata field allowlist,
access/terms record, and explicit inventory command. Inventory only allowed
metadata; reconcile coverage and sister-project exposure, then choose deliberate
development/validation partitions. Stage B passage inspection and all behavioral
validation remain pending their own frozen decisions.

## 2026-09-10 — L003: Session 1 metadata and originality audit

- **Protocols:** Stage A1 ran after commit `23b9359`; the exact Stage A2 value
  allowlist ran after commit `b60d079`. Source revision
  `02a396ffd09b283c9f092fdedeff11da6d535b66`, tree
  `44fd5081d0e6a441dbafadd12c51d6ffca8ab98b`.
- **Access:** public repository paths/object metadata, LFS pointer identities,
  JSON field paths/types, CSV headers, and only the committed match-metadata
  values. No tracking payload, event row, aggregate row, pose record, passage,
  animation, label value, completeness result, join, or performance was viewed.
- **Inventory:** 20 unique match directories each expose metadata, tracking,
  Dynamic Events, and phases file entries. Four metadata schema variants, two
  Dynamic Events header variants, and one phases header were found. File
  presence is not usable record coverage.
- **Exposure:** nine matches were previously analyzed in the sister project;
  ten additions are prospectively reserved from this stage with prior exposure
  unverified; one prior match remains withheld for metadata review. Exact local
  membership is untracked. Published sister-project summaries were already
  visible during provenance review.
- **Receiver schema:** six target/receipt/outcome fields are present in every
  Dynamic Events header. Values, completeness, joins, and timing were not
  inspected. Vendor Passing Option events remain model-derived comparison
  evidence, not availability truth or candidate membership.
- **Scientific decision:** the project is currently a transparent receiver-
  ranking benchmark and geometric reformulation. Accessibility requires separate
  construct validation; suppression is unsupported; mathematical novelty is not
  established. No claim status changed.
- **Local artifacts:** detailed manifest SHA-256
  `44c6f495344b27b51ac5b153633722a3d61c2705dc167342bc2e9d749c5cacb0`;
  detailed inventory SHA-256
  `cd575389290bd9e0f384fccbd5c9f50d70f0f1c83e90b0000f1a1cbb5ff97b62`.
  Both are ignored. Compact summary SHA-256
  `650943d0c904ddf3b5e4da43e7228bbddfcdcb4e41d21b1fac39bd32bb59cbed`.
- **Deviation/status:** no reserved value-level exposure and no protocol
  deviation. Session 1 closed before payload acquisition or model development.

## Future run record template

Record ID and timestamp; question/claim IDs; protocol version/SHA; code SHA;
source release and manifest; partition and previous exposure; command/config;
environment/seed; planned comparisons and decision rules; observations and
uncertainty; exclusions; deviations and access ledger update; result status
(including negative/mixed/invalid/stopped); permitted interpretation; claim
ledger change; artifacts; next decision.
