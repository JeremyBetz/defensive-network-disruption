# Phase 06d: LFS delivery / TLS identity audit

Status: frozen for transport and metadata diagnostics only.
Starting authority: `72908fe5cab983e6c30f99fc63fea7fa3bb61589`.
Source revision: `02a396ffd09b283c9f092fdedeff11da6d535b66`.

## Authority, evidence, and scope

Preserve closed Session 2/3/4/5/6a/6/6b/6c tracked authorities byte-for-byte.
Session 6 and 6c remain D / 4 INVALID; Session 6b remains B recoverable.
Separate contemporaneous evidence, current reproduction, and future proposals.
Session 6c built its media URL directly; it neither requested an official LFS
batch action nor received a delivery URL. A successful probe now cannot explain
the historical failure by itself. Historical ignored ledgers are checked only
against actually committed hashes where those exist.

Use exactly these frozen tuples from Session 6c repair authority:

| Alias | Match | Git pointer OID | LFS SHA-256 | Declared bytes |
| --- | --- | --- | --- | ---: |
| reserved_01 | 1874553 | 7439f0ba7da6bc03625258b98fe84a5bf770b72e | ea97f58f8eaad925feaeacc6395ec24860dd80027af8a89450276adebd29d265 | 90729279 |
| development_01 | 1886347 | 6c1d01ae3bafa28cf94e4b7a581fb3779effe4bd | 3577e2803da95390f8b2f85d47829eb55fbbfee6211c94adc65db0dc78e46b41 | 89280839 |

Their paths are `data/matches/<match>/<match>_tracking_extrapolated.jsonl`.
No other identity, withheld match, or football product may be inspected.
Do not read existing payloads, parse tracking, construct populations, fit/score
models, inspect passages, install software, change trust/configuration, or begin
Session 6e. Do not edit AGENTS.md, licenses, or unrelated governance.

## Commands and chronology

Commit this protocol first, then the tested separate audit implementation before
new diagnostics. The runner exposes `preflight`, `inspect-environment`,
`inspect-endpoint`, `compare-git-lfs`, and `publication-check`. No scientific
module imports or execution routes are permitted. Provider access is confined to
the committed audit client, not ad hoc shell probes. Repository synchronization
is a separate operational checkpoint, not a provider diagnostic.

Record new probes immediately in an ignored append-only ledger under
`outputs/lfs_tls_integrity_review/local/`, with phase, command, probe number,
protocol/implementation identity, sanitized endpoint, and outcome. Before network
execution create persistent command markers; an interrupted command cannot
automatically repeat its probes.

## Environment projection

Inspect venv/system Python versions, SSL library and default trust-source
categories; certifi metadata if installed; Git/curl/Git-LFS versions and visible
TLS backends. Search Git-LFS only through PATH, `/opt/homebrew/bin/git-lfs`, and
`/usr/local/bin/git-lfs`; do not install or execute a payload operation.

Inspect presence/category only for upper/lowercase proxy variables HTTP_PROXY,
HTTPS_PROXY, ALL_PROXY, NO_PROXY and CA variables SSL_CERT_FILE, SSL_CERT_DIR,
REQUESTS_CA_BUNDLE, CURL_CA_BUNDLE, GIT_SSL_CAINFO. Inspect only relevant Git
HTTP/proxy/SSL/url-rewrite keys and `/etc/hosts` entries for audited hosts.
Never print credentials or raw configuration values. Report configured trust
locations as system/runtime/custom/unavailable categories, not private paths.
Proxy presence alone does not prove interception; no configuration is altered.

## Network boundaries

All probes retain normal chain and hostname verification, including SNI.
Never use unverified contexts, insecure flags, HTTP, trust-all roots, certificate
pinning to bypass PKI, or warning suppression.

Each probe has a 15-second connection timeout and 30-second overall timeout;
retain at most 64 KiB of headers or LFS response metadata. One attempt per probe,
no certificate retries, at most 24 diagnostic operations. Each operation makes
one HTTP request or one TLS connection, except system Git ref advertisement,
which reserves two requests conservatively. Never automatically follow redirects.

Allowed initial origins: `https://media.githubusercontent.com` for the two exact
historical paths and TLS-only certificate comparison; `https://github.com` for
official repository ref advertisement and
`/SkillCorner/opendata.git/info/lfs/objects/batch` metadata POST. Venv Python,
system Python, and installed curl may HEAD the two exact media URLs; no GET,
Range, body reader, or method fallback is allowed for payload routes. System Git
may run one bounded `ls-remote` for HEAD only; this proves Git-host connectivity,
not media delivery. No clone/fetch/checkout/smudge/LFS retrieval is allowed.

Permit one LFS batch POST per tuple with operation download, basic transfer, and
only that frozen OID/size. The response is metadata only, capped at 64 KiB. Verify
OID and size before examining actions. Retain sanitized download origin,
expiry/authentication category and header-presence only. Do not persist query
secrets, cookies, action headers, tokens, or credentials, even in local logs.

A returned action may receive one HEAD and one verified TLS-only probe if it is
HTTPS, has no userinfo, resolves only to public addresses, and came directly from
the verified official LFS batch response. Send no repository credentials to that
origin. If authentication prevents a credential-free HEAD, report that limit.
Record redirect destination origin only; do not follow unless separately
established by the official action, and do not expand the frozen probe set.

Certificate subject/SAN/issuer may be retained only if exposed by a
verification-enforcing handshake. Failed certificate details are unavailable if
normal verification prevents access; never obtain them through an insecure
connection. Bound and redact exception messages before output.

Retrieve at most these three official documentation resources, separately from
the diagnostic request budget (maximum 256 KiB each, once, HTTPS):
`https://raw.githubusercontent.com/git-lfs/git-lfs/main/docs/api/batch.md`,
`https://raw.githubusercontent.com/git-lfs/git-lfs/main/docs/api/basic-transfers.md`,
`https://raw.githubusercontent.com/git-lfs/git-lfs/main/docs/man/git-lfs-fetch.adoc`.
Documentation is explanatory evidence, never authority for a new football source.

## Identity invariant and operational decisions

Any future transport must preserve revision -> exact path -> Git pointer -> LFS
OID/size. Independent actual payload SHA-256 and size verification remains
mandatory before projected parsing. Client success alone is insufficient.

Choose exactly one: A demonstrated Python-specific configuration defect with a
secure standard correction; B official LFS protocol establishes a secure delivery
architecture and exact identity remains enforceable; C demonstrated local
trust/proxy/routing defect requires repair first; D secure delivery remains
unresolved. B may be supported by verified official protocol evidence while
live git-lfs remains explicitly unavailable/untested. Installation absence must
never be presented as a successful client test. Use B only after a valid returned
origin passes ordinary TLS validation. TLS failure of the historical constructed
host need not invalidate a separately verified official delivery architecture.

For A/C recommend one bounded later configuration protocol, without applying it.
For B recommend one later official-protocol/client transport replacement,
preserving repaired identity checks and independent payload verification; flag
client installation as a later prerequisite if needed. For D recommend no
protected rerun until independently resolved. No protected rerun is authorized
by any Session 6d classification. Certificate errors remain non-retryable.

## Tests, outputs, and stop

Test trusted-host success, hostname mismatch, untrusted issuer, expiration,
official/unapproved redirect destinations, proxy/custom CA presence, timeout,
reset, signed-query redaction, and mutation rejection for every frozen tuple
component. Prove no payload body-reader/science route, no secret leakage, normal
TLS verification, finite budget, one-shot markers, and independent integrity
requirement. Run focused/full non-provider tests, compile, schema/hash checks,
publication and historical-change guards, staged review, and diff checks.

Produce `environment_summary.json`, `endpoint_summary.json`,
`transport_comparison.json`, and `manifest.json` under
`outputs/lfs_tls_integrity_review/`. JSON permits only projected public fields and
explicit unavailable/untested states. Hash closed outputs before interpretation.
Write `docs/session_06d_lfs_tls_integrity_review.md` with all 49 requested evidence
items and the external manifest hash; append only to the research log.

Commit reviewed diagnostics/report, push, and verify synchronized clean heads.
Record closure commit and remote evidence in the final response; the report may
identify its own enclosing commit by an exact Git retrieval command to avoid a
self-referential commit hash. Stop after classification/recommendation.
