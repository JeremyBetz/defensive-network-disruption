"""One-shot R9AC execution and capture-first, zero-exposure closure."""
from __future__ import annotations
from pathlib import Path
import time
import signal
from contextlib import contextmanager


@contextmanager
def operation_deadline(seconds):
    """Interrupt even one expensive arithmetic call at the frozen deadline."""
    def expired(signum,frame):raise TimeoutError("refinement_deadline")
    previous=signal.getsignal(signal.SIGALRM)
    old_timer=signal.getitimer(signal.ITIMER_REAL)
    if old_timer[0]:raise RuntimeError("overlapping_operation_timer")
    signal.signal(signal.SIGALRM,expired)
    signal.setitimer(signal.ITIMER_REAL,seconds)
    try:yield
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,previous)

from .checkpoint_ci_authority import durable_json, durable_bytes
from .r9aa_failure import AcquisitionFailureBoundary
from .r9v_publication_ownership import persist_authority
from . import r9j_linear_publication as linear
from . import r9ac_evidence as evidence
from .r9ac_authority import sha
from .r9ac_controls import controls
from ..geometry.r9ac_terminal_bound import bound, Limits


def execute(folder, *, gate, load_inputs, binding, limits=Limits(), fault=lambda stage:None):
    """Dependency injection is internal, for provider-free entrypoint tests only."""
    folder=Path(folder);local=folder/'local'
    if (local/'attempt.marker').exists() or any((folder/name).exists() for name in evidence.FILES):
        raise FileExistsError('governed_attempt_exists')
    durable_json(local/'attempt.marker',{'schema_version':1,'reserved':True})
    durable_json(local/'binding.json',binding)
    active='prerequisites'; authority=descriptor=None; wall=time.monotonic()
    def closure_authority():
        nonlocal authority,descriptor
        if authority is None:
            durable_bytes(local/'empirical_journal.jsonl',b'')
            authority=linear.review(local/'empirical_journal.jsonl')
            descriptor=persist_authority(local,authority)
        return authority,descriptor
    try:
        fault(active); gate()
        evidence.stage(local,'authorized',0)
        active='synthetic_controls';fault(active)
        rows,details=controls()
        durable_json(local/'controls.json',rows);durable_json(local/'control_details.json',details)
        evidence.stage(local,'controls_passed',1,sha(local/'controls.json'))
        active='authority_load';fault(active)
        record,statuses=load_inputs()
        durable_json(local/'authority.json',record);durable_json(local/'historical_status.json',statuses)
        evidence.stage(local,'authority_loaded',2,sha(local/'authority.json'))
        active='independent_bound';fault(active)
        with operation_deadline(limits.seconds):
            result,nodes=bound(record,limits=limits,session_deadline=wall+7200,
                sink=lambda item:durable_json(local/'nodes'/f"{item['id']:06d}.json",item))
        durable_json(local/'result.json',result)
        evidence.stage(local,'bound_completed',3,sha(local/'result.json'))
        active='publication_initialization';fault(active)
        a,d=closure_authority()
        active='publication';fault(active)
        return evidence.close(folder,a,d)
    except BaseException as error:
        boundary=AcquisitionFailureBoundary(local/'failure')
        def qc(captured):
            fault('blocked_qc')
            durable_json(local/'blocked_qc.json',{'schema_version':1,'stage':captured.stage,
                'traceback_sha256':captured.traceback_sha256,'execution_valid':False})
        def publish(captured):
            fault('failure_publication')
            a,d=closure_authority()
            return evidence.close(folder,a,d)
        boundary.close(error,active,write_blocked_qc=qc,publish=publish,reraise=True)
        raise AssertionError('unreachable')
