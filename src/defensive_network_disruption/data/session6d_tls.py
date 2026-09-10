"""Bounded TLS/HEAD/LFS-metadata probes; no football payload reader."""
from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import re
import socket
import ssl
import urllib.error
import urllib.parse
import urllib.request

LIMIT = 65536
SOURCE = "02a396ffd09b283c9f092fdedeff11da6d535b66"
BATCH = "https://github.com/SkillCorner/opendata.git/info/lfs/objects/batch"
TUPLES = {
    "reserved_01": {
        "revision": SOURCE,
        "path": "data/matches/1874553/1874553_tracking_extrapolated.jsonl",
        "pointer": "7439f0ba7da6bc03625258b98fe84a5bf770b72e",
        "oid": "ea97f58f8eaad925feaeacc6395ec24860dd80027af8a89450276adebd29d265",
        "size": 90729279,
    },
    "development_01": {
        "revision": SOURCE,
        "path": "data/matches/1886347/1886347_tracking_extrapolated.jsonl",
        "pointer": "6c1d01ae3bafa28cf94e4b7a581fb3779effe4bd",
        "oid": "3577e2803da95390f8b2f85d47829eb55fbbfee6211c94adc65db0dc78e46b41",
        "size": 89280839,
    },
}
DOCS = (
    "https://raw.githubusercontent.com/git-lfs/git-lfs/main/docs/api/batch.md",
    "https://raw.githubusercontent.com/git-lfs/git-lfs/main/docs/api/basic-transfers.md",
    "https://raw.githubusercontent.com/git-lfs/git-lfs/main/docs/man/git-lfs-fetch.adoc",
)
ENV_KEYS = (
    "HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY", "NO_PROXY", "SSL_CERT_FILE",
    "SSL_CERT_DIR", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE", "GIT_SSL_CAINFO",
)


def identity(alias, value):
    if alias not in TUPLES or value != TUPLES[alias]:
        raise ValueError("frozen_source_identity_changed")
    return dict(value)


def origin(url):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("unsafe_origin")
    if parsed.port not in (None, 443) or any(c in url for c in '\r\n"\\'):
        raise ValueError("unsafe_origin")
    return "https://" + parsed.hostname


def approved_delivery(url, official_origins, addresses=None):
    value = origin(url)
    if value not in official_origins:
        raise ValueError("delivery_origin_not_officially_established")
    host = urllib.parse.urlsplit(url).hostname
    if host in {"localhost"} or host.endswith((".localhost", ".local")):
        raise ValueError("private_destination")
    if addresses is None:
        addresses = {item[4][0] for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)}
    if not addresses or any(not ipaddress.ip_address(addr).is_global for addr in addresses):
        raise ValueError("private_destination")
    return value


def redact(message):
    text = str(message)
    text = re.sub(r"https?://[^\s<>]+", lambda m: safe_origin(m.group()), text)
    text = re.sub(r"/(?:Users|home)/[^\s:]+", "[private-path]", text)
    text = re.sub(r"(?i)(authorization|cookie|token|signature|password)\s*[:=]\s*\S+", r"\1=[redacted]", text)
    return text[:1200]


def safe_origin(url):
    try:
        return origin(url)
    except ValueError:
        return "[redacted-url]"


def failure(exc):
    reason = exc.reason if isinstance(exc, urllib.error.URLError) else exc
    if isinstance(reason, ssl.SSLCertVerificationError):
        code = getattr(reason, "verify_code", None)
        kind = {62: "hostname_mismatch", 10: "expired_certificate", 20: "untrusted_issuer", 21: "untrusted_issuer"}.get(code, "certificate_validation_failure")
        return {"status": "failed", "category": kind, "exception_class": type(reason).__name__, "message": redact(str(reason)), "verification_code": code, "retryable": False}
    kind = "timeout" if isinstance(reason, (TimeoutError, socket.timeout)) else "connection_reset" if isinstance(reason, ConnectionResetError) else type(reason).__name__
    return {"status": "failed", "category": kind, "message": redact(str(reason)), "retryable": False}


def environment_presence(environ):
    result = {}
    for key in ENV_KEYS:
        names = (key, key.lower()) if key.endswith("PROXY") else (key,)
        result[key] = {
            "present": any(bool(environ.get(name)) for name in names),
            "category": "proxy_routing" if key.endswith("PROXY") else "custom_trust_path",
        }
    return result


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def opener():
    context = ssl.create_default_context()
    if not context.check_hostname or context.verify_mode != ssl.CERT_REQUIRED:
        raise RuntimeError("normal_tls_verification_required")
    return urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(context=context))


def tls_probe(host):
    context = ssl.create_default_context()
    with socket.create_connection((host, 443), timeout=15) as connection:
        with context.wrap_socket(connection, server_hostname=host) as secured:
            cert = secured.getpeercert()
            return {
                "status": "verified", "hostname": host, "sni": host,
                "tls_version": secured.version(), "hostname_validated": True,
                "certificate_subject": [list(pair) for item in cert.get("subject", ()) for pair in item],
                "certificate_issuer": [list(pair) for item in cert.get("issuer", ()) for pair in item],
                "certificate_san": [list(item) for item in cert.get("subjectAltName", ())],
                "route": "direct_socket_without_proxy",
            }


def head_probe(url):
    origin(url)
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "dnd-session6d-tls-audit"})
    try:
        response = opener().open(request, timeout=15)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        headers = str(response.headers).encode()
        if len(headers) > LIMIT:
            raise ValueError("headers_oversized")
        result = {"status": "verified", "hostname_validated": True, "http_status": response.code, "origin": origin(url), "body_read": False}
        location = response.headers.get("Location")
        if location:
            result["redirect_origin"] = safe_origin(urllib.parse.urljoin(url, location))
            result["redirect_followed"] = False
        return result


def metadata_read(response, maximum=LIMIT):
    length = response.headers.get("Content-Length")
    if length is not None and int(length) > maximum:
        raise ValueError("metadata_oversized")
    raw = response.read(maximum + 1)
    if len(raw) > maximum:
        raise ValueError("metadata_oversized")
    return raw


def project_batch(document, alias):
    expected = TUPLES[alias]
    objects = document.get("objects")
    if not isinstance(objects, list) or len(objects) != 1:
        raise ValueError("batch_object_count")
    item = objects[0]
    if item.get("oid") != expected["oid"] or item.get("size") != expected["size"]:
        raise ValueError("batch_identity_mismatch")
    if "error" in item:
        return {"status": "object_error", "error_code": item["error"].get("code"), "identity_matches": True}, None
    action = item.get("actions", {}).get("download")
    if not isinstance(action, dict) or not isinstance(action.get("href"), str):
        raise ValueError("batch_download_action_missing")
    url = action["href"]
    action_origin = origin(url)
    result = {
        "status": "official_action_returned", "identity_matches": True,
        "delivery_origin": action_origin, "signed_query_present": bool(urllib.parse.urlsplit(url).query),
        "action_headers_present": bool(action.get("header")),
        "expiry_metadata_present": "expires_at" in action or "expires_in" in action,
        "authentication_category": "action_headers" if action.get("header") else "signed_query" if urllib.parse.urlsplit(url).query else "none_declared",
    }
    return result, url


def batch_metadata(alias):
    expected = identity(alias, TUPLES.get(alias))
    body = json.dumps({"operation": "download", "transfers": ["basic"], "objects": [{"oid": expected["oid"], "size": expected["size"]}]}).encode()
    request = urllib.request.Request(BATCH, data=body, method="POST", headers={
        "Accept": "application/vnd.git-lfs+json", "Content-Type": "application/vnd.git-lfs+json",
        "User-Agent": "dnd-session6d-tls-audit",
    })
    with opener().open(request, timeout=15) as response:
        document = json.loads(metadata_read(response))
    return project_batch(document, alias)


def doc_metadata(url):
    if url not in DOCS:
        raise ValueError("documentation_not_allowlisted")
    with opener().open(urllib.request.Request(url), timeout=15) as response:
        raw = metadata_read(response, 262144)
    # Official explanatory prose only; no source products are reachable here.
    return {"url": url, "sha256": hashlib.sha256(raw).hexdigest(), "text": raw.decode("utf-8")}


def worker(payload):
    try:
        kind = payload["kind"]
        if kind == "tls":
            return tls_probe(payload["host"])
        if kind == "head":
            return head_probe(payload["url"])
        if kind == "batch":
            projected, url = batch_metadata(payload["alias"])
            if url:
                # Transient pipe-only value; runner removes it before any logging.
                projected["_private_url"] = url
            return projected
        if kind in {"delivery_tls", "delivery_head"}:
            approved_delivery(payload["url"], {payload["official_origin"]})
            if kind == "delivery_tls":
                return tls_probe(urllib.parse.urlsplit(payload["url"]).hostname)
            return head_probe(payload["url"])
        if kind == "documentation":
            return doc_metadata(payload["url"])
        raise ValueError("probe_kind_not_allowed")
    except Exception as exc:
        return failure(exc)
