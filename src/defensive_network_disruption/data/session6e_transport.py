"""Official, exact-object LFS transport; no scientific parsing or model imports."""
from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import re
import socket
import ssl
import tempfile
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .session6c_source import (
    IntegrityError, TransportError, LfsPointer, TreeEntry, Session6cSourceClient,
    SOURCE_COMMIT, OWNER_REPO, _RejectRedirects, _transport_category,
    source_path, verify_blob, parse_lfs_pointer,
)

BATCH = "https://github.com/SkillCorner/opendata.git/info/lfs/objects/batch"
ORIGIN = "github-cloud.githubusercontent.com"
RESERVED = frozenset({'1874553','1927964','1959846','1986691','1996436','2006363','2007448','2007721','2010085','2016236'})
HEADERS = frozenset({'authorization', 'accept', 'accept-encoding', 'content-type'})


def unique_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise IntegrityError('duplicate_json_key')
            result[key] = value
        return result
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(IntegrityError('nonfinite_json')))
    except (ValueError, UnicodeError):
        raise IntegrityError('invalid_json') from None


def safe_local(path: Path) -> None:
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise IntegrityError('symlink_path')


def check_entry(entry: TreeEntry):
    parts = entry.path.split('/')
    if len(parts) != 4 or parts[:2] != ['data', 'matches']:
        raise IntegrityError('source_path_invalid')
    match = parts[2]
    allowed = {source_path(match, product, RESERVED) for product in ('metadata','events','tracking')}
    if entry.path not in allowed or entry.object_type != 'blob' or re.fullmatch('[0-9a-f]{40}', entry.git_oid) is None or type(entry.git_size) is not int or entry.git_size < 0:
        raise IntegrityError('source_identity_invalid')


def public_dns(host, resolver=socket.getaddrinfo):
    addresses = resolver(host, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise IntegrityError('nonpublic_destination')


@dataclass(frozen=True, repr=False)
class Action:
    url: str
    headers: dict
    expires: float | None


def validate_action(value, pointer, *, now=None, wall=None, resolver=socket.getaddrinfo):
    now = time.monotonic() if now is None else now
    wall = datetime.now(timezone.utc) if wall is None else wall
    if not isinstance(value, dict) or value.get('transfer', 'basic') != 'basic' or value.get('hash_algo', 'sha256') != 'sha256':
        raise IntegrityError('batch_transfer_invalid')
    objects = value.get('objects')
    if not isinstance(objects, list) or len(objects) != 1 or not isinstance(objects[0], dict):
        raise IntegrityError('batch_cardinality_invalid')
    obj = objects[0]
    if obj.get('oid') != pointer.payload_sha256 or type(obj.get('size')) is not int or obj['size'] != pointer.payload_size or 'error' in obj:
        raise IntegrityError('batch_object_identity_invalid')
    actions = obj.get('actions')
    action = actions.get('download') if isinstance(actions, dict) else None
    if not isinstance(action, dict) or not isinstance(action.get('href'), str):
        raise IntegrityError('download_action_missing')
    try:
        parsed = urllib.parse.urlsplit(action['href'])
        valid = parsed.scheme == 'https' and parsed.hostname == ORIGIN and parsed.port in (None, 443) and parsed.username is None and parsed.password is None and not parsed.fragment
    except ValueError:
        valid = False
    if not valid:
        raise IntegrityError('download_action_origin_invalid')
    public_dns(ORIGIN, resolver)
    headers = action.get('header', {})
    if not isinstance(headers, dict) or sum(len(str(k)) + len(str(v)) for k,v in headers.items()) > 8192:
        raise IntegrityError('action_headers_invalid')
    seen = set()
    for key, val in headers.items():
        if not isinstance(key, str) or key.lower() not in HEADERS or key.lower() in seen or not isinstance(val, str) or any(c in val for c in '\r\n') or (key.lower() == 'accept-encoding' and val != 'identity'):
            raise IntegrityError('action_headers_invalid')
        seen.add(key.lower())
    expires = None
    if 'expires_in' in action:
        duration = action['expires_in']
        if type(duration) is not int or duration <= 0:
            raise IntegrityError('action_expiry_invalid')
        expires = now + duration
    if 'expires_at' in action:
        try:
            stamp = datetime.fromisoformat(action['expires_at'].replace('Z', '+00:00'))
            if stamp.tzinfo is None or stamp <= wall:
                raise ValueError()
            if expires is None:
                expires = now + (stamp - wall).total_seconds()
        except (TypeError, ValueError, AttributeError):
            raise IntegrityError('action_expiry_invalid') from None
    return Action(action['href'], dict(headers), expires)


class OfficialLfsClient(Session6cSourceClient):
    """Public products, scoped API auth, sanitized errors and bounded streaming."""
    def __init__(self, token='', *, ledger=None, opener=None, sleeper=time.sleep, resolver=socket.getaddrinfo, clock=time.monotonic):
        super().__init__(token, ledger=ledger, opener=opener or urllib.request.build_opener(_RejectRedirects(), urllib.request.HTTPSHandler(context=ssl.create_default_context())), sleeper=sleeper)
        self.resolver = resolver
        self.clock = clock

    def log(self, label, attempt, status, category=None):
        if self._ledger:
            self._ledger(label, attempt, status, category)

    def _bytes(self, request, label, maximum):
        for attempt in range(1,4):
            self.log(label, attempt, 'started')
            try:
                with self._opener.open(request, timeout=240) as response:
                    if response.geturl() != request.full_url:
                        raise IntegrityError('redirect_or_substitution')
                    declared = response.headers.get('Content-Length')
                    if declared is not None and (not declared.isdecimal() or int(declared) > maximum):
                        raise IntegrityError('response_oversized')
                    raw = response.read(maximum+1)
                    if len(raw) > maximum:
                        raise IntegrityError('response_oversized')
                    if declared is not None and len(raw) != int(declared):
                        raise IntegrityError('completed_response_size_mismatch')
            except Exception as exc:
                category = _transport_category(exc)
                self.log(label, attempt, 'failed', category or (str(exc) if isinstance(exc, IntegrityError) else type(exc).__name__))
                if not category or attempt == 3:
                    raise (TransportError if category else IntegrityError)(category or (str(exc) if isinstance(exc, IntegrityError) else type(exc).__name__)) from None
                self._sleep(attempt)
                continue
            self.log(label, attempt, 'completed')
            return raw
        raise AssertionError('unreachable')

    def _request(self, url, *, label, maximum):
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != 'https' or parsed.netloc != 'api.github.com' or not parsed.path.startswith('/repos/SkillCorner/opendata/git/') or '..' in parsed.path:
            raise IntegrityError('api_endpoint_forbidden')
        headers = {'User-Agent':'defensive-network-disruption-session-6e', 'Accept':'application/vnd.github+json'}
        if self._token:
            headers['Authorization'] = 'Bearer ' + self._token
        return self._bytes(urllib.request.Request(url, headers=headers), label, maximum)

    def _json(self, endpoint, *, label):
        return unique_json(self._request('https://api.github.com'+endpoint, label=label, maximum=16384 if '/git/blobs/' in endpoint else 4000000))

    def pointer(self, entry, *, label):
        check_entry(entry)
        if entry.git_size > 1024 or not entry.path.endswith('_tracking_extrapolated.jsonl'):
            raise IntegrityError('pointer_scope_invalid')
        envelope = self._json(f'/repos/{OWNER_REPO}/git/blobs/{entry.git_oid}', label=label)
        raw = verify_blob(entry, envelope, decoded_limit=1024)
        return parse_lfs_pointer(raw), raw

    def batch(self, pointer, label):
        if re.fullmatch('[0-9a-f]{64}', pointer.payload_sha256) is None or type(pointer.payload_size) is not int or pointer.payload_size < 0:
            raise IntegrityError('pointer_identity_invalid')
        body = json.dumps({'operation':'download', 'transfers':['basic'], 'objects':[{'oid':pointer.payload_sha256,'size':pointer.payload_size}]}, sort_keys=True).encode()
        request = urllib.request.Request(BATCH, data=body, method='POST', headers={'Accept':'application/vnd.git-lfs+json','Content-Type':'application/vnd.git-lfs+json','User-Agent':'defensive-network-disruption-session-6e'})
        raw = self._bytes(request, label, 65536)
        return validate_action(unique_json(raw), pointer, now=self.clock(), resolver=self.resolver)

    def acquire(self, entry, destination, *, pointer, label):
        check_entry(entry)
        safe_local(destination)
        if destination.exists():
            raise IntegrityError('automatic_redownload_forbidden')
        if (pointer is not None) != entry.path.endswith('_tracking_extrapolated.jsonl'):
            raise IntegrityError('product_pointer_mismatch')
        action = self.batch(pointer, label+':batch:0') if pointer else None
        ordinary_url = f'https://raw.githubusercontent.com/{OWNER_REPO}/{SOURCE_COMMIT}/{entry.path}'
        maximum = pointer.payload_size if pointer else entry.git_size
        destination.parent.mkdir(parents=True, exist_ok=True)
        refreshes = 0
        for attempt in range(1,4):
            safe_local(destination)
            if action:
                public_dns(ORIGIN, self.resolver)
            request = urllib.request.Request(action.url if action else ordinary_url, headers=action.headers if action else {'User-Agent':'defensive-network-disruption-session-6e'})
            descriptor, name = tempfile.mkstemp(prefix='.'+destination.name+'.', suffix='.tmp', dir=destination.parent)
            temporary = Path(name)
            self.log(label, attempt, 'started')
            count = 0
            digest = hashlib.sha256()
            git_digest = hashlib.sha1(b'blob '+str(entry.git_size).encode()+b'\0')
            try:
                with os.fdopen(descriptor,'wb') as handle:
                    with self._opener.open(request, timeout=240) as response:
                        if response.geturl() != request.full_url:
                            raise IntegrityError('redirect_or_substitution')
                        declared = response.headers.get('Content-Length')
                        if declared is not None and (not declared.isdecimal() or int(declared) != maximum):
                            raise IntegrityError('declared_size_mismatch')
                        while True:
                            chunk = response.read(min(1024*1024, maximum+1-count))
                            if not chunk:
                                break
                            count += len(chunk)
                            if count > maximum:
                                raise IntegrityError('payload_oversized')
                            handle.write(chunk)
                            digest.update(chunk)
                            git_digest.update(chunk)
                    handle.flush()
                    os.fsync(handle.fileno())
                if count != maximum:
                    raise IntegrityError('completed_payload_size_mismatch')
                if pointer:
                    if digest.hexdigest() != pointer.payload_sha256:
                        raise IntegrityError('payload_sha256_mismatch')
                    receipt = {'lfs_payload_sha256':digest.hexdigest(),'bytes':count}
                else:
                    if git_digest.hexdigest() != entry.git_oid:
                        raise IntegrityError('git_blob_oid_mismatch')
                    receipt = {'git_oid':entry.git_oid,'bytes':count}
                os.replace(temporary,destination)
            except Exception as exc:
                temporary.unlink(missing_ok=True)
                category = _transport_category(exc)
                self.log(label, attempt, 'failed', category or (str(exc) if isinstance(exc, IntegrityError) else type(exc).__name__))
                if not category or attempt == 3:
                    raise (TransportError if category else IntegrityError)(category or (str(exc) if isinstance(exc, IntegrityError) else type(exc).__name__)) from None
                self._sleep(attempt)
                if action and action.expires is not None and self.clock() >= action.expires:
                    refreshes += 1
                    if refreshes > 2:
                        raise IntegrityError('refresh_limit')
                    action = self.batch(pointer,label+':batch:'+str(refreshes))
                continue
            self.log(label, attempt, 'verified')
            return receipt
        raise AssertionError('unreachable')
