# Session 6d — LFS delivery / TLS identity audit

**B — OFFICIAL GIT LFS PROTOCOL IS THE APPROPRIATE SECURE TRANSPORT PATH.**

The historical hand-built media endpoint fails hostname validation today in
venv Python, system Python, and curl for both frozen comparator objects. This is
not a demonstrated Python-only defect. By contrast, the official repository LFS
batch endpoint returned an exact OID/size match for both objects and supplied
signed actions at `https://github-cloud.githubusercontent.com`. That origin
passed normal certificate-chain and hostname verification; both action URLs
returned HTTP 200 to HEAD. No tracking response body was requested or read.

Official Git LFS protocol is the appropriate transport architecture; live
git-lfs client execution was unavailable because the binary is not installed.
This audit does not authorize a protected rerun or installation.

## Evidence and limits

The contemporaneous Session 6c exception was an `urllib.error.URLError` wrapping
`ssl.SSLCertVerificationError`:

```text
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostname mismatch, certificate is not valid for 'media.githubusercontent.com'. (_ssl.c:1032)
```

The historical source helper constructed the URL directly from the source
revision/path. It did not make a batch request, receive a GitHub action URL,
or encounter an HTTP redirect before the failed handshake. Its generic ledger
record retained `URLError`; the exact TLS detail is also present in the execution
transcript. Session 6c's already-recorded outcome is not changed by this audit.

Current reproduction gives verification code 62 in both Python stacks and curl
exit code 60, with no HTTP response. A separate verification-enforcing handshake
also failed. The failed endpoint's exact SAN names and issuer remain unavailable:
no insecure connection was made to obtain them. Accordingly, this audit cannot
assign the mismatch to a particular historical certificate, backend, DNS route,
or interception mechanism. The immediate failure is an authenticated-hostname
mismatch on the manually selected endpoint; the deeper infrastructure cause
remains unresolved.

No allowlisted proxy variables, CA override variables, relevant Git configuration
overrides, or hosts-file overrides were present. This does not prove that no
VPN, network appliance, or transparent routing layer exists. No such layer or
required CA repair was demonstrated. The successful official delivery connection
provides an independently validated operational route without weakening trust.

| Connection | Venv Python | System Python | curl / Git |
| --- | --- | --- | --- |
| Historical media, reserved_01 | Hostname mismatch | Hostname mismatch | curl hostname mismatch |
| Historical media, development_01 | Hostname mismatch | Hostname mismatch | curl hostname mismatch |
| Official Git repository | Not separately tested | Not separately tested | Git ref advertisement succeeded |
| Official batch-returned action, reserved_01 | TLS verified; HEAD 200 | Not separately tested | Git-LFS client unavailable |
| Official batch-returned action, development_01 | TLS verified; HEAD 200 | Not separately tested | Git-LFS client unavailable |

The verified action origin negotiated TLS 1.3. Its subject CN was `*.github.io`,
and the issuer was Let's Encrypt YR1. Its SAN list included
`*.githubusercontent.com`, which covers `github-cloud.githubusercontent.com`,
alongside the reported GitHub names. Certificate validity was determined by the
normal SSL verifier, not by trusting an issuer name or subject CN alone. These
details apply only to the successfully verified official action origin; they are
not asserted to describe the failed media endpoint's certificate.

## Official protocol and prospective repair recommendation

The official Batch API accepts object OIDs/sizes and returns per-object download
actions, optional request headers, and expiry metadata. Both audited actions
contained signed queries and expiry metadata, with no action headers. No
repository credentials were sent or forwarded. Neither signed query values nor
action URLs were retained in public files or the local ledger. Expiry cannot
explain the historical failure: Session 6c did not obtain a signed action and
failed before HTTP. See the [official Batch API](https://raw.githubusercontent.com/git-lfs/git-lfs/main/docs/api/batch.md).

The Basic transfer protocol uses the server-returned action for an eventual
download. Session 6d deliberately stopped at TLS/HEAD. The two HEAD 200 responses
establish current metadata-level reachability, not proof that full bytes will
download or match their expected hash. See the [official Basic Transfer API](https://raw.githubusercontent.com/git-lfs/git-lfs/main/docs/api/basic-transfers.md).

Recommend one separately frozen Session 6e transport-replacement protocol, with
the official Git-LFS client as the intended future acquisition backend, subject
to explicit tooling authorization and version/behavior verification. Git-LFS
installation and an exact-object, metadata-only rehearsal are prerequisites;
neither was performed here. The client has documented exact-ref and path-filter
controls and a dry-run mode; those controls must be checked in the actual
installed version before acquisition. See the [official git-lfs-fetch reference](https://raw.githubusercontent.com/git-lfs/git-lfs/main/docs/man/git-lfs-fetch.adoc).

That future protocol should retire manually constructed media delivery URLs,
while retaining the repaired Git-tree/pointer verification and all frozen source
tuples. It must explicitly bind the repository pin, exact authorized path,
pointer OID, expected LFS SHA-256 and size; disable broader recent/all-object
selection; and inspect the planned object set before download. After any future
materialization, project code must independently verify actual SHA-256 and byte
size before parsing. Git-LFS transport success alone is insufficient.

Use a fresh ignored namespace, preserve all prior failure packages, and preserve
all thirty-product, population, model, timing, tie, and metric rules. Reuse the
frozen final development models. Any future population preparation and single
scoring execution require separate explicit authority and prospective commit
checkpoints. Certificate/hostname errors remain non-retryable; this audit offers
no evidence to reclassify them as transient transport failures.

## Evidence map: 49 requested items

1. **Starting HEAD:** `72908fe5cab983e6c30f99fc63fea7fa3bb61589`; clean local state and live origin/main equality verified before the audit.
2. **Ending HEAD:** the enclosing diagnostic/report commit, retrievable with `git log --diff-filter=A -1 --format=%H -- docs/session_06d_lfs_tls_integrity_review.md`; its exact hash and live synchronization are recorded in the delivery response, avoiding a self-referential hash.
3. **Protocol:** `docs/protocols/phase_06d_lfs_tls_integrity_review.md`; commit `a38638dc20dddb38a0e49ec1da0ce1d611dc86bd`; SHA-256 `21a93732d7ebaa057d1587396f6932788f60622f0e1588dbee94a6e4ff6e38f1`.
4. **Implementation:** commit `918106232ac809aaa3d8eff60f850b4055b8e4f1`; runner SHA-256 `82a34c6edbfa6d7cb9007bb1931b651e21eb389060e0ecedc41340f95d7c5ab3`; helper `1cafb84f7500c3fbf077bf83ffca63cf0b918166c5006f5a20abae7240804549`; tests `15d8753a2406c6ef539ef781e13b27934d5de87a418ce18cd868275b856fab7f`.
5. **Historical exception:** exact hostname-verification error quoted above, wrapped in URLError.
6. **Historical hostname:** `media.githubusercontent.com`.
7. **Historical host source:** directly constructed by Session 6c; not returned by an official LFS action.
8. **Current reproduction:** both identities fail in both Python stacks and curl; direct verified TLS also fails.
9. **Official batch result:** one request for each frozen object; both returned exactly the expected OID and size.
10. **Official origin:** `https://github-cloud.githubusercontent.com`; both verified TLS and HEAD 200.
11. **Redirects:** no HTTP response before historical-host failures; no redirect was returned by successful action HEAD probes; no redirect followed automatically.
12. **SAN:** failed host SAN unavailable; official action SAN includes matching `*.githubusercontent.com` and passed standard validation.
13. **Issuer:** failed host issuer unavailable; official action issuer Let's Encrypt YR1, US.
14. **Venv runtime:** Python 3.13.15, OpenSSL 3.5.8 (25 Aug 2026).
15. **System runtime:** Python 3.9.6, LibreSSL 2.8.3.
16. **CA source:** both Python runtimes report default CA file and directory present; no override variable is active. Private runtime paths are not published. Trust-store content equivalence was not established. certifi is absent and was not the historical urllib trust provider.
17. **Proxy/CA environment:** all requested upper/lowercase proxy and CA override variables absent; no environment change.
18. **Git configuration:** no relevant HTTP proxy/SSL/url-rewrite overrides; no insecure override observed. No relevant hosts-file entries.
19. **Redaction:** no authorization, cookie, signed query value, username, or private CA path retained in public outputs or diagnostic ledger.
20. **System Git:** 2.50.1; normal-verification ref advertisement succeeded against github.com only. TLS backend was not exposed by the version check.
21. **Git-LFS availability/version:** unavailable on PATH and the two standard installation locations.
22. **Git-LFS live result:** unavailable; no client transport demonstration is claimed.
23. **curl:** 8.7.1, SecureTransport/LibreSSL 3.3.6; both historical-host HEAD probes failed with exit 60.
24. **Python-specific:** not supported; the failure reproduces outside Python and across two Python SSL stacks.
25. **Proxy/interception:** not demonstrated. Absent configuration is not proof against transparent network routing or interception.
26. **Custom CA:** no active override found; no custom-CA cause demonstrated.
27. **Remote identity:** manually selected media-host identity fails current validation; the official action origin passes. The failed certificate's exact names remain unknown.
28. **Secure architecture:** official batch flow establishes a currently verified action origin for both frozen identities, without asserting full-download success.
29. **Exact identity enforcement:** immutable tuple checks reject changes to revision, path, pointer, OID, or size; batch OID/size matched frozen Session 6c authority.
30. **Independent integrity:** remains possible and mandatory after future materialization; no new payload integrity is claimed now.
31. **Development comparator:** development_01 shows the same failed historical-host behavior and successful official-flow behavior.
32. **Retry recommendation:** TLS certificate/hostname failures remain non-retryable.
33. **Classification:** **B — OFFICIAL GIT LFS PROTOCOL IS THE APPROPRIATE SECURE TRANSPORT PATH**.
34. **Rationale:** official action provenance, exact OID/size agreement, ordinary validated TLS, and HEAD 200 for both objects establish a secure prospective route; manually built endpoint delivery failed in every tested stack.
35. **Protected rerun authorized:** **NO**.
36. **Prospective recommendation:** one Session 6e protocol replacing hand-built delivery with official Git-LFS transport, after tooling authorization and exact-object rehearsal; preserve independent verification and all scientific rules.
37. **Retire hand-built media URLs:** yes for future acquisition; preserve historical code untouched.
38. **Environment repair:** no required CA/proxy repair demonstrated. Git-LFS tooling availability is a distinct future prerequisite, not a proven trust defect.
39. **Changes:** new protocol, runner, helper, tests, this report, four compact JSON outputs; append-only research-log entry. No historical scientific implementation changed.
40. **Tests:** 19 focused tests passed; full suite 133 passed and 3 planned scaffold skips; compilation passed. Full-suite fitting tests use synthetic data only; no empirical model was fitted or scored.
41. **Publication:** output schemas/hashes, redaction, historical authority, and 15-of-24 diagnostic request-budget checks passed; staged/diff review is required before the closure commit.
42. **Reserved tracking downloaded/parsed:** no payload GET or Range request, no response-body reads on HEAD, no existing tracking file access.
43. **Population prepared:** no.
44. **Empirical model fitted/scored:** no.
45. **Passage inspected:** no.
46. **History preserved:** all historical tracked files verified byte-identical; research log append-only. Session 6 and 6c ledgers match their committed hashes. No new retrospective byte authority assigned to Session 6b's ignored ledger.
47. **Commit/push:** separate protocol, tested implementation, and enclosing report commits; push and live remote check are closure operations, with exact results in the delivery response. No amendment or squash.
48. **Final Git status:** verified at delivery after pushing the enclosing report commit; ignored diagnostics remain local.
49. **Next authorized step:** stop this audit and present the prospective transport-replacement recommendation. A new Session 6e plan/tooling authorization is required before installation, acquisition, population preparation, or scoring.

## Closed output identities

| Artifact | SHA-256 |
| --- | --- |
| environment_summary.json | `8a027552566168ac630cf014b8ff8cafc9875dc824f836ec6f9b5ebb3deb3362` |
| endpoint_summary.json | `b9ccffc08e745eea1c5face18689863b6a023fd615850286aecc9092acbb11ae` |
| transport_comparison.json | `f3c86dceab0d4078639149625a5552029aad3047a81c249306db1c1b20d99be0` |
| manifest.json | `3932a84cfc6552cf946478d4d4ed8e97c26d0b03e359dcbe2fb6424b088b0277` |

The manifest binds the implementation, protocol, output hashes, and new local
ledger hash. Fifteen diagnostic operations were budgeted (including two reserved
for Git ref advertisement), plus three official documentation requests. All
probes were one-attempt operations. No Session 6e action has begun.
