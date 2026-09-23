"""Explicit-attempt CI authority. Historical v1 behavior is untouched."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess

from .checkpoint_ci_authority import canonical_bytes, durable_json, durable_bytes, REQUIRED_JOBS


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError('ci_v2_' + reason)


def timestamp(value):
    require(isinstance(value, str) and value.endswith('Z'), 'timestamp')
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        raise ValueError('ci_v2_timestamp') from None
    require(result.year >= 2008, 'timestamp')
    return result


@dataclass(frozen=True)
class Expectation:
    checkpoint_commit: str
    protocol_sha256: str
    runner_implementation_sha256: str
    lockfile_sha256: str
    workflow_sha256: str
    run_id: int
    run_attempt: int
    workflow_id: int = 355427402
    repository: str = 'JeremyBetz/defensive-network-disruption'
    workflow_name: str = 'CI'
    workflow_path: str = '.github/workflows/ci.yml'


@dataclass(frozen=True)
class VerifiedAuthority:
    receipt_sha256: str
    checkpoint_commit: str
    run_id: int
    run_attempt: int
    jobs: tuple[tuple[str, int], ...]


def expectation_valid(expected):
    require(re.fullmatch('[0-9a-f]{40}', expected.checkpoint_commit) is not None, 'commit')
    for name, value in asdict(expected).items():
        if name.endswith('_sha256'):
            require(re.fullmatch('[0-9a-f]{64}', value) is not None, 'binding_hash')
    for value in (expected.run_id, expected.run_attempt, expected.workflow_id):
        require(type(value) is int and value > 0, 'identifier')
    require(re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', expected.repository) is not None, 'repository')


def source_summary(source, expected):
    expectation_valid(expected)
    require(set(source) == {'run', 'job_pages'}, 'source_schema')
    run = source['run']
    require(run['id'] == expected.run_id and run['run_attempt'] == expected.run_attempt, 'attempt')
    require(run['head_sha'] == expected.checkpoint_commit, 'commit')
    require(run['repository']['full_name'] == expected.repository, 'repository')
    require(run['workflow_id'] == expected.workflow_id and run['name'] == expected.workflow_name
            and run['path'] == expected.workflow_path, 'workflow')
    base = f'https://api.github.com/repos/{expected.repository}/actions/runs/{expected.run_id}'
    require(run['jobs_url'] == f'{base}/attempts/{expected.run_attempt}/jobs', 'attempt_endpoint')
    require(run['status'] == 'completed' and run['conclusion'] == 'success', 'run_not_successful')
    require(timestamp(run['created_at']) <= timestamp(run['updated_at']), 'run_chronology')
    pages = source['job_pages']
    require(type(pages) is list and bool(pages), 'pages')
    jobs = []
    total = pages[0]['total_count']
    require(type(total) is int and total > 0, 'job_count')
    for i, page in enumerate(pages):
        require(set(page) == {'total_count', 'jobs'} and page['total_count'] == total
                and type(page['jobs']) is list, 'page_schema')
        require(len(page['jobs']) <= 100 and (i == len(pages)-1 or len(page['jobs']) == 100), 'pagination')
        jobs.extend(page['jobs'])
    require(len(jobs) == total, 'pagination')
    require(sorted(j['name'] for j in jobs) == sorted(REQUIRED_JOBS), 'job_set')
    require(len({j['id'] for j in jobs}) == len(jobs), 'duplicate_job')
    result = []
    for job in sorted(jobs, key=lambda j: j['name']):
        require(type(job['id']) is int and job['id'] > 0, 'job_id')
        require(job['run_id'] == expected.run_id and job['run_attempt'] == expected.run_attempt,
                'mixed_attempt')
        require(job['head_sha'] == expected.checkpoint_commit, 'job_commit')
        require(job['run_url'] == base and job['url'] ==
                f'https://api.github.com/repos/{expected.repository}/actions/jobs/{job["id"]}', 'job_repository')
        require(job['status'] == 'completed' and job['conclusion'] == 'success', 'job_not_successful')
        require(timestamp(run['created_at']) <= timestamp(job['started_at']) <=
                timestamp(job['completed_at']) <= timestamp(run['updated_at']), 'job_chronology')
        result.append({k: job[k] for k in ('id','name','status','conclusion','started_at','completed_at')})
    return result


def build_receipt(source, expected, environment, captured_at):
    jobs = source_summary(source, expected)
    timestamp(captured_at)
    require(set(environment) == {'python_version','python_implementation','platform'}
            and all(type(x) is str and x for x in environment.values()), 'environment')
    record = {'schema_version':2,'authority_id':'checkpoint_ci_authority_v2',
              'expectation':asdict(expected),'required_jobs':list(REQUIRED_JOBS),'jobs':jobs,
              'source_sha256':digest(source),'environment':environment,
              'provenance':{'method':'authenticated_github_cli_explicit_attempt','captured_at':captured_at}}
    record['provenance_sha256'] = digest(record)
    return record


def read_canonical(path):
    raw = Path(path).read_bytes()
    value = json.loads(raw)
    require(canonical_bytes(value) == raw, 'noncanonical')
    return value


def validate_receipt(path, expected, *, expected_sha256):
    path = Path(path)
    require(sha(path.read_bytes()) == expected_sha256, 'receipt_hash')
    record = read_canonical(path)
    require(set(record) == {'schema_version','authority_id','expectation','required_jobs','jobs',
                           'source_sha256','environment','provenance','provenance_sha256'}, 'receipt_schema')
    source = read_canonical(path.with_suffix('.source.json'))
    rebuilt = build_receipt(source, expected, record['environment'], record['provenance']['captured_at'])
    require(record == rebuilt, 'receipt_binding')
    return VerifiedAuthority(expected_sha256, expected.checkpoint_commit, expected.run_id,
                             expected.run_attempt, tuple((j['name'],j['id']) for j in record['jobs']))


def validate_selected(path, bindings, *, expected_sha256):
    """Shared R9AC gate: immutable selection supplies independent run/attempt."""
    path = Path(path)
    # Retain hash-first rejection before reading companion records.
    if sha(path.read_bytes()) != expected_sha256:
        raise ValueError('ci_receipt_hash')
    selection = read_canonical(path.with_suffix('.selection.json'))
    require(set(selection) == {'schema_version','run_id','run_attempt','receipt_sha256'}, 'selection_schema')
    require(selection['schema_version'] == 2 and selection['receipt_sha256'] == expected_sha256, 'selection_hash')
    values = asdict(bindings)
    values.pop('required_jobs', None)
    expected = Expectation(**values,run_id=selection['run_id'],run_attempt=selection['run_attempt'])
    return validate_receipt(path, expected, expected_sha256=expected_sha256)


def capture(path, expected, *, command=subprocess.check_output):
    path = Path(path)
    marker = path.with_suffix('.capture.marker')
    durable_json(marker, {'schema_version':2,'expectation':asdict(expected)})
    endpoint = f'repos/{expected.repository}/actions/runs/{expected.run_id}/attempts/{expected.run_attempt}'
    try:
        run = json.loads(command(('gh','api',endpoint)))
        pages = json.loads(command(('gh','api',endpoint+'/jobs?per_page=100','--paginate','--slurp')))
        source = {'run':run,'job_pages':pages}
        durable_json(path.with_suffix('.source.json'), source)
        environment = {'python_version':platform.python_version(),
                       'python_implementation':platform.python_implementation(),'platform':platform.platform()}
        record = build_receipt(source,expected,environment,datetime.now(timezone.utc).isoformat().replace('+00:00','Z'))
        durable_json(path, record)
        h = sha(path.read_bytes())
        durable_bytes(path.with_suffix('.json.sha256'), (h+'\n').encode())
        durable_json(path.with_suffix('.selection.json'), {'schema_version':2,'run_id':expected.run_id,
                     'run_attempt':expected.run_attempt,'receipt_sha256':h})
        return validate_receipt(path,expected,expected_sha256=h)
    except BaseException as error:
        from .checkpoint_ci_authority import FailureController
        FailureController(path.with_suffix('.failure')).capture(error,stage='attempt_capture',context={})
        raise
