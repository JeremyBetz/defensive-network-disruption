"""Prospective terminal routing: one append, one linear review, no legacy replay."""
from pathlib import Path
from .checkpoint_ci_authority import FailureController
from . import r9j_linear_publication as linear
from . import r9j_evidence as evidence


class TerminalClosure:
    def __init__(self, progress, directory):
        self.progress=progress;self.directory=Path(directory);self.controller=FailureController(self.directory)
        self.closed=False

    def _claim(self):
        evidence.put(self.directory/'terminal.marker',{'reserved':True})
        if self.closed:raise RuntimeError('terminal_already_closed')
        self.closed=True

    def fail(self,error,stage,publisher):
        self._claim()
        p=self.progress
        original=self.controller.capture(error,stage,context=p.context)
        try:
            state,edge,candidate=p.context or (None,None,None)
            journal_stage=p.numerical_context if p.context else 'preparation'
            if journal_stage is None:journal_stage='geometry'
            p.journal.append('failure',stage=journal_stage,exception=type(error).__name__,
                state=state,edge=edge,candidate=candidate,traceback_sha256=original['traceback_sha256'])
            authority=linear.review(p.journal.path,expected_head=p.journal.previous)
            evidence.put(self.directory/'linear_authority.json',authority.record())
            return publisher(authority,self.controller.traceback_path)
        except BaseException as publication_error:
            self.controller.publication_failure(publication_error)
            raise

    def succeed(self,publisher):
        self._claim()
        p=self.progress
        if p.context is not None or p._attempts or not p._states or not all(x['done'] for x in p._states.values()):raise ValueError('incomplete_success')
        p.journal.append('success')
        authority=linear.review(p.journal.path,expected_head=p.journal.previous)
        evidence.put(self.directory/'linear_authority.json',authority.record())
        return publisher(authority,None)


def numerical_package(folder,authority,trace):
    folder=Path(folder);accepted=authority.legacy['snapshot']['snapshot']['status']=='success'
    package=linear.old.package(authority.legacy,accepted=accepted,checks={'terminal_valid':True})
    for name in ('qc','manifest','evidence'):evidence.put(folder/(name+'.json'),package)
    return linear.validate_numerical_package(folder,authority,traceback_path=trace)


def failure_package(folder,authority,trace):
    """Write actual prospective failure records and validate unchanged R9J schema."""
    from .r9a_publication import MANIFEST_MEMBERS
    folder=Path(folder);private=folder/'private';public=folder/'public'
    mode='empirical_failure';progress=authority.progress(mode)
    numerical_package(private/'numerical_publication',authority,trace)
    base=dict(schema_version=1,status='failure',progress_authority=progress)
    qc=dict(base,stage=authority.failure['stage'],exception=authority.failure['exception'],scientific_comparisons_available=False)
    evidence.put(private/'qc.json',qc);evidence.put(private/'evidence.json',base)
    evidence.put(private/'progress_authority.json',progress)
    evidence.put(private/'manifest.json',dict(base,outputs={n:evidence.sha(private/n) for n in ('qc.json','evidence.json','progress_authority.json')}))
    evidence.put(public/'qc.json',qc)
    evidence.put(public/'manifest.json',dict(base,start='synthetic',protocol='synthetic',implementation='synthetic',environment={},
        outputs={'qc.json':evidence.sha(public/'qc.json')},unavailable=[n for n in MANIFEST_MEMBERS if n!='qc.json'],
        private_evidence_sha256=evidence.sha(private/'evidence.json'),private_manifest_sha256=evidence.sha(private/'manifest.json')))
    return linear.validate_public(public,private,authority,mode,traceback_path=trace)


def controls(folder):
    """Real journals and publishers; no mock authority or lifecycle results."""
    from contextlib import ExitStack
    from unittest.mock import patch
    from . import r7_execution as old_progress, numerical_failure_publication as old
    from .r5_persistence import Journal
    rows=[]
    for kind in ('success','pre_access','numerical_failure','publication_init','publisher_failure'):
        place=Path(folder)/kind;j=Journal(place/'journal.jsonl');p=old_progress.Progress(j)
        closure=TerminalClosure(p,place)
        with ExitStack() as stack:
            for target,name in ((old_progress.Progress,'failure'),(old_progress.Progress,'succeed'),(old_progress._CoreView,'snapshot'),(old,'replay')):
                stack.enter_context(patch.object(target,name,side_effect=AssertionError('legacy_replay_called')))
            if kind in ('success','numerical_failure'):
                p.authorize_access();p.discover_state('synthetic_state',('synthetic_edge',));p.project('synthetic_state',lambda:None);p.prepare_state('synthetic_state');p.start_state('synthetic_state')
                for candidate in ('isotropic','expanding','constant_width'):
                    p.call_start('synthetic_state','synthetic_edge',candidate)
                    p.numerical_stage(stage='geometry')
                    if kind=='numerical_failure':break
                    p.numerical_stage(stage='accepted');p.call_complete()
                if kind=='success':p.retain_and_complete_edges('synthetic_state');p.complete_state('synthetic_state')
            try:
                if kind=='success':
                    closure.succeed(lambda a,t:numerical_package(place/'package',a,t));passed=True
                else:
                    def publisher(a,t):
                        if kind in ('publication_init','publisher_failure'):raise RuntimeError(kind)
                        return failure_package(place/'package',a,t)
                    try:raise ValueError('synthetic_original')
                    except ValueError as error:closure.fail(error,'synthetic_test',publisher)
                    passed=closure.controller.validate()['status']=='valid'
            except RuntimeError as error:
                if kind not in ('publication_init','publisher_failure') or str(error)!=kind:raise
                passed=closure.controller.validate()['status']=='valid' and (place/'publication_failure.json').exists()
            finally:j.close()
        rows.append(dict(fixture=kind,status='complete',passed=passed,reason='legacy_unreachable',evidence_sha256=evidence.sha(place/'linear_authority.json')))
    return rows
