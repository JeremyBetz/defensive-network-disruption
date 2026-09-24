"""One R9AD acceptance; retained access follows every observed checkpoint gate."""
from pathlib import Path
import time
from .r9j_evidence import put,sha
from . import r9ad_evidence as evidence
from . import r9j_linear_publication as linear
from .r9v_publication_ownership import TerminalClosure,persist_authority,controls as publication_controls
from .r9ad_controls import controls,negatives
from .r9ad_acceptance import historical_regression
from .r9t_acceptance import primitive
from .r9ac_run import operation_deadline
from .r5_persistence import Journal
from .r7_execution import Progress


def acceptance_valid(rows):
    h=rows['history']
    return (len(rows['topology'])==14 and all(x['passed'] for x in rows['topology'])
        and len(rows['negative'])==10 and all(x['blocked'] for x in rows['negative'])
        and len(rows['publication'])==9 and all(x['passed'] for x in rows['publication'])
        and (len(h),sum(x['components'] for x in h),sum(x['permutations'] for x in h))==(108,366,399)
        and all(x['status']=='passed' for x in h))


def execute(root,folder,*,gate,load_inputs,binding,fault=lambda stage:None):
    """Private callbacks permit synthetic testing; CLI never accepts callbacks."""
    root=Path(root);folder=Path(folder);local=folder/'local'
    if (local/'acceptance.marker').exists() or any((folder/n).exists() for n in evidence.FILES):
        raise FileExistsError('governed_attempt_exists')
    if gate()!=binding or not binding.get('ci_receipt_sha256'):
        raise PermissionError('checkpoint_gate_required')
    put(local/'acceptance.marker',{'schema_version':1,'reserved':True,'authorizes_access':False})
    put(local/'binding.json',binding)
    started=time.monotonic();cpu=time.process_time();deadline=started+3600
    rows={'topology':[],'negative':[],'history':[],'publication':[],
          'retained':{'attempted':False,'materialized':False,'completed':False,
                      'candidate_invocations':0,'uncertain_exposure':False},
          'performance':{},'failure':None}
    journal=Journal(local/'journal.jsonl');progress=Progress(journal)
    active='synthetic_controls';serial=0
    work={'maximality_reviews':0,'bound_calls':0,'subdivisions':0,'maximum_depth':0,'unresolved_regions':0}
    def sink(label,value):
        path=local/'records'/(label+'.json');put(path,value);return sha(path)
    def observe(**kw):
        nonlocal serial
        sink('observation_'+str(serial),primitive(kw));serial+=1
        if kw.get('kind')=='tie_coverage':
            proof=kw['value'];work['maximality_reviews']+=1
            work['bound_calls']+=proof.bound_calls;work['subdivisions']+=proof.subdivisions
            work['maximum_depth']=max(work['maximum_depth'],max(c.depth for c in proof.cells))
            work['unresolved_regions']+=sum(c.relation=='unresolved' or c.maximality=='unresolved' for c in proof.cells)
    def save_observations():
        rows['retained']['attempted']=(local/'access_attempt.json').exists()
        rows['retained']['materialized']=(local/'access_materialized.json').exists()
        rows['retained']['uncertain_exposure']=bool(progress._attempts) or (rows['retained']['attempted'] and not rows['retained']['materialized'])
        rows['performance']={'inclusive_seconds':time.monotonic()-started,
                             'process_cpu_seconds':time.process_time()-cpu,
                             'exclusive_computation_seconds':None,'io_seconds':None,
                             'unattributed_seconds':None,'proof_records':serial,**work}
        put(local/'observations.json',rows)
    def publish(authority,descriptor,trace):
        fault('publication_initialization')
        if trace is not None:
            from .checkpoint_ci_authority import FailureController
            rows['failure']=FailureController(local/'failure').validate()
        save_observations();fault('publication')
        return evidence.close(folder,authority,descriptor)
    try:
        fault(active)
        rows['topology']=controls(sink);rows['negative']=negatives(sink)
        active='historical_regression';fault(active)
        rows['history']=historical_regression(root,sink,deadline=deadline)
        active='publication_controls';fault(active)
        rows['publication']=publication_controls(local/'publication_controls')
        if not acceptance_valid(rows):raise ValueError('preaccess_acceptance_blocked')
        active='retained_materialization';fault(active)
        put(local/'retained_attempt.marker',{'schema_version':1,'reserved':True,'authorizes_access':False})
        put(local/'access_attempt.json',{'schema_version':1,'selected_sha256':binding['selected_sha256']})
        progress.authorize_access();progress.discover_state('selected_state',('selected_edge',))
        attempt=progress.begin_projection('selected_state')
        row=load_inputs()
        fault('materialization_receipt')
        journal.append('projection_materialized',attempt=attempt,edges=['selected_edge'])
        progress._states['selected_state']['opened'].add('selected_edge');del progress._attempts[attempt]
        progress.prepare_state('selected_state');progress.start_state('selected_state')
        journal.append('diagnostic_started',state='selected_state',edge='selected_edge',candidate='constant_width')
        progress.context=('selected_state','selected_edge','constant_width')
        active='retained_candidate';fault(active)
        put(local/'candidate_invocation.json',{'schema_version':1,'candidate':'constant_width','invocations':1})
        rows['retained']['candidate_invocations']=1
        from ..geometry import r9ad_adapter
        with operation_deadline(min(600,max(0.001,deadline-time.monotonic()))):
            edge,result=r9ad_adapter.evaluate('constant_width',row['carrier'],row['receiver'],row['defenders'],
                root=root,authority_context={'alias':row['alias'],'state':'10','edge':'2'},
                record=progress.numerical_stage,localization_sink=observe,
                deadline=min(deadline,time.monotonic()+600))
        put(local/'retained_result.json',primitive(result));rows['retained']['completed']=True
        journal.append('diagnostic_completed',state='selected_state',edge='selected_edge',candidate='constant_width')
        progress.context=None;journal.append('diagnostic_success')
    except BaseException as error:
        closure=TerminalClosure(progress,local/'failure')
        try:return closure.fail(error,active,publish)
        finally:journal.close()
    else:
        try:
            authority=linear.review(journal.path,expected_head=journal.previous)
            descriptor=persist_authority(local,authority)
            return publish(authority,descriptor,None)
        except BaseException as error:
            from .checkpoint_ci_authority import FailureController
            controller=FailureController(local/'publication_failure')
            controller.capture(error,'diagnostic_success_publication')
            raise
        finally:journal.close()
