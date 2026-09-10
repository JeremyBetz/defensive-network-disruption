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

## 2026-09-10 06:53:44 CDT — L004: Session 1 access-boundary correction

- **Supersedes:** L003's statement that no protocol deviation occurred. The
  historical entry remains intact as the contemporaneous record.
- **Protocol stage and intended boundary:** P01 Stage A1 allowed CSV header names
  across all 20 matches without reading, retaining, or printing data rows.
- **Actual behavior:** the retained reader issued `Range: bytes=0-65535`, called
  `response.read(65536)`, partitioned the result at the first LF, and retained the
  remainder in process memory. This affected Dynamic Events and phases-of-play
  CSVs for all 20 matches: 18 files in the nine-match development group, 20 files
  in the ten-match reserved group, and two files for the unresolved match.
- **Emitted and persisted content:** only parsed column names and header hashes
  entered the retained inventory. The reader source has no path that prints,
  logs, serializes, or consumes the `remainder`; no retained output contains it.
  The in-memory buffers ended with the process. Transport or OS buffering beyond
  bytes returned to the application cannot be reconstructed.
- **Known/unknown:** post-header bytes were mechanically acquired into process
  memory. No evidence indicates that their values were displayed, persisted, or
  used analytically. The original shell invocation was not retained verbatim;
  execution order is reconstructed from the scripts, timestamps, artifacts and
  earlier log. This limits provenance precision but does not create evidence of
  analytical use.
- **Reservation verdict:** **A — PRESERVED**. Reserved files were mechanically
  over-read, but available code and artifact evidence supports that no value-level
  content was surfaced, persisted, selected, or analyzed. Prior exposure remains
  unverified, and prospective protection continues from 2026-09-10.
- **Scientific effect:** none of the originality, product-presence, header-field,
  or provisional-partition conclusions depends on post-header values. Strict
  header-only acquisition is downgraded from VERIFIED to DEVIATION RECORDED.
- **Corrective action:** preserved the exact original schema reader under
  `docs/provenance/session_01/`; its SHA-256 is
  `b20e34acc1d4ad794ad6f1aab39125246e1276e6779ed710bc00bd742cba8e7c`.
  Added a future schema helper that requests one byte at a time and stops at LF,
  plus synthetic sentinel tests. No provider request was made during repair.
- **Repaired artifacts:** corrected ignored inventory SHA-256
  `732db83cc1847870740fa1aa8a8ee6ffe0356363e0166ad54a4a5f7f18f7c027`;
  corrected compact summary SHA-256
  `6c5ceeb6da793daab01333a3d9daf0197997a7a81b0b4d6e5f2214c3815980f1`.

## Future run record template

Record ID and timestamp; question/claim IDs; protocol version/SHA; code SHA;
source release and manifest; partition and previous exposure; command/config;
environment/seed; planned comparisons and decision rules; observations and
uncertainty; exclusions; deviations and access ledger update; result status
(including negative/mixed/invalid/stopped); permitted interpretation; claim
ledger change; artifacts; next decision.

## 2026-09-10 — L005: Session 2 development compatibility

- **Protocol/access:** P02 was committed as `d76068e` before value access. A
  preflight implementation bug then stopped before any request; correction
  `55a4e78` was committed before retry. Source was pinned to
  `02a396ffd09b283c9f092fdedeff11da6d535b66`. Access was limited by code to the
  nine development matches and metadata, Dynamic Events, and tracking products.
- **Integrity/schema:** 27 files passed pinned Git/LFS identity and size checks.
  Nine V3 JSONL tracking payloads contain 583,437 records at verified 10 Hz across
  two periods. Two event schema widths occur, 294 and 322 columns.
- **Compatibility:** Kloppy 3.19.0 matched native player sets and player/ball
  coordinates on the fixed 5,400-frame comparison. Native detection, possession
  player, and image-projection fields require a sidecar.
- **Labels/alignment:** 7,292 structural pass attempts include successful,
  unsuccessful, and offside outcomes. Target player ID is present on 7,237;
  6,757 option links resolve uniquely. All attempts map to an equal same-frame
  timestamp; the strictly prior frame is 100 ms earlier. The tolerance remains a
  prospective cadence-based draft.
- **Candidates:** independent candidates contain the target for 7,227/7,237
  labeled attempts. Ten labeled targets fall outside for missing coordinate or
  validity reasons; 55 attempts lack a target label. No rule was tuned to coverage.
- **Decision:** Tier B, useful vendor target with limitations. Accessibility is
  proxy only; suppression is not supportable. No M0/M1/M2, model fit, ranking,
  metric, or scored passage was produced.
- **Protected data/deviation:** no reserved or unresolved value was requested or
  opened. Session 1's A verdict and L004 qualification remain in force. No Session
  2 access deviation occurred.

## 2026-09-10 — L006: Session 3 frozen M0/M1 development comparison

- **Chronology:** P03 was committed as `1dddb6f`; the score-free population,
  environment, production implementation, and tests were committed as `54dc4f8`
  before fitting. The pinned provider revision and nine-match development
  allowlist were unchanged.
- **Population:** 7,292 pass attempts yielded 7,227 common evaluation/fit states.
  The waterfall excluded 56 unusable target labels and nine invalid carriers.
  The former single target/candidate mismatch was a provider self-target and is
  included in the 56 unusable labels. Population SHA-256:
  `cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d`.
- **Execution:** unregularized conditional softmax, nine leave-one-match-out
  folds, equal match weighting, analytic gradients, training-only preprocessing,
  and identical M0/M1 populations. All rank, separation, finite-value,
  optimization, and gradient gates passed.
- **Results:** match-macro MRR was 0.48177 for M0 and 0.56779 for M1. The mean
  paired difference was 0.08602, median 0.08373, with 9/0/0 positive/negative/tied
  matches. Match-macro Hit@1 and Hit@3 differences were 0.10219 and 0.10221.
- **Interpretation:** consistent development-only incremental ranking information;
  no practical-effect or external-validity claim. Accessibility remains PROXY
  ONLY; suppression remains NOT SUPPORTABLE; M2 is deferred pending a specific
  prospective hypothesis.
- **Post-score record:** the initial formatter omitted pooled descriptive metrics
  and a public parameter record. Initial scored files were hash-preserved locally;
  the missing summaries were derived without refitting or rescoring. No scored
  football passage was inspected. Future corrective reruns are blocked while
  scored outputs exist.
- **Protection:** reserved and unresolved value-level products remained unopened.
  Session 1's A verdict with the L004 mechanical over-read qualification remains
  in force. No new access-boundary deviation occurred.

## 2026-09-10 — L007: Session 4 M1 failure-mode audit

- **Protocol/access:** P04 was committed as `8fc0630`. Before new event-row
  access, Amendment 1 was committed as `212a223` to permit eight projected event
  fields needed to recover closed decision-frame keys. The public Session 3
  coefficients had already been inspected during planning; no new row-level
  development values were opened before the amendment.
- **Stopped attempt:** the first aggregate run stopped during JSON serialization
  on a NumPy boolean after diagnostics were computed in memory. Only a local
  coefficient summary duplicating closed QC values was written; no new feature or
  geometry result was displayed. Atomic serialization and the scalar conversion
  were fixed before rerunning the unchanged audit.
- **Coefficient behavior:** both defensive coefficients were positive in all nine
  folds. This is conditional model behavior, not causal importance.
- **Complementarity:** defensive-feature pooled Pearson correlation was 0.3312,
  within-choice centered correlation 0.3882, and equal-match candidate-order
  disagreement 34.78%. The two-feature condition number was 2.27 with full rank.
- **Failure modes:** M1 cannot distinguish toward/away velocity under identical
  static geometry, has no length-by-obstruction interaction, and exactly collapses
  one versus three defenders when their two minima match. Second/third segment-
  distance gap distributions were non-degenerate in all nine matches.
- **Velocity feasibility:** a prior same-identity frame existed for 79,442/79,497
  defender instances, but only 67.77% of current instances were detected and
  provider-causal processing remains unestablished. The strict reachability gate
  therefore failed.
- **Decision:** **B — SPECIFIC MULTI-DEFENDER FAILURE MODE IDENTIFIED.** The sole
  next question is whether one prospectively specified continuous multi-defender
  attenuation summary adds ranking information beyond frozen M1 minima. No kernel,
  parameter, model, or evaluation was selected or run.
- **Protection/claims:** no reserved, withheld, pose, vendor-score, passage, error,
  or new model access. Accessibility remains PROXY ONLY; suppression remains NOT
  SUPPORTABLE; the Session 3 result is unchanged.

## 2026-09-10 — L008: License-file housekeeping amendment

- **Scope:** repository housekeeping only; no Session 4 science or Session 5
  planning was changed.
- **Audit:** no CI, build tool, packaging workflow, repository instruction, or
  competition rule independently required a root file named `LICENSE`. The
  competition rules specifically require `LICENSE.md`.
- **Change:** retained `LICENSE.md` as the canonical MIT license, removed the
  byte-identical bare `LICENSE`, updated the README link, and limited package
  license metadata to `LICENSE.md`.
- **Historical note:** earlier entries describing both files remain unchanged
  under this log's append-only policy. This entry supersedes their instruction
  to retain the duplicate.
