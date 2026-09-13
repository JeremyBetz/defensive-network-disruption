"""Discoverable synthetic checks; no empirical geometry is opened."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from defensive_network_disruption.geometry import onset_owner_certification as owner
from defensive_network_disruption.geometry.verification_repair import VerifiedSwitch, VerificationError
from defensive_network_disruption.validation import numerical_failure_publication as pub
from defensive_network_disruption.validation.r5_persistence import Journal, durable_write


def crossing(root=.5, multi=False):
    def function(t):
        delta=.25*(t-root)
        columns=[.5+delta,.5-delta]
        if multi: columns.append(np.full_like(t,.5))
        return np.column_stack(columns)
    return function


def switch(function, root=.5):
    return VerifiedSwitch(root,owner.owners(function(np.array([root-1e-7]))[0]),
        owner.owners(function(np.array([root]))[0]),owner.owners(function(np.array([root+1e-7]))[0]),
        ((0,1),),False,False,.5)


def events(*,diagnostic=False,success=False):
    rows=[]
    def add(action,**payload): rows.append({'action':action,'payload':payload})
    add('initialized');add('access_authorized');add('state_discovered',state='s',edges=['e'])
    add('projection_attempt',state='s',attempt='a');add('projection_materialized',attempt='a',edges=['e'])
    add('state_prepared',state='s');add('state_evaluation_started',state='s')
    for candidate in (('constant_width',) if diagnostic else pub.CANDIDATES):
        ctx=dict(state='s',edge='e',candidate=candidate)
        add('diagnostic_started' if diagnostic else 'field_started',**ctx)
        add('numerical_stage',**ctx,detail={'stage':'geometry'})
        if candidate=='constant_width' and not success:
            add('failure',**ctx,stage='geometry',exception='RuntimeError',traceback_sha256=hashlib.sha256(b'synthetic traceback').hexdigest())
            return rows
        add('numerical_stage',**ctx,detail={'stage':'accepted'})
        add('diagnostic_completed' if diagnostic else 'field_completed',**ctx)
    if diagnostic: add('diagnostic_success')
    else:
        add('edge_completed',state='s',edge='e');add('state_completed',state='s');add('success')
    return rows


def persist(folder,rows,accepted=False):
    path=folder/'journal';j=Journal(path)
    for r in rows:j.append(r['action'],**r['payload'])
    head=j.previous;j.close()
    trace=folder/'trace';trace.write_bytes(b'synthetic traceback')
    auth=pub.authority(path,head);record=pub.package(auth,accepted=accepted,checks={'controls':True})
    for name in ('qc','manifest','evidence'):durable_write(folder/(name+'.json'),record)
    return path,head,trace


class Session14aiTests(unittest.TestCase):
    def test_ordinary_region(self):
        f=crossing();s=switch(f);t=owner.localize(f,s)
        result,w=owner.certify_in_region(f,s,t,0,1)
        self.assertEqual(result.canonical,t[3]);self.assertTrue(0<w.before<w.canonical<w.after<1)

    def test_coincidence_and_no_interior(self):
        for left in (.5,float(np.nextafter(.5,-np.inf))):
            with self.assertRaises(VerificationError):owner.interior_probes(.5,left,1)

    def test_few_float_probe(self):
        left=.5
        for _ in range(4):left=float(np.nextafter(left,-np.inf))
        a,b=owner.interior_probes(.5,left,1)
        self.assertTrue(left<a<.5<b<1)

    def test_onset_and_neighbor_regions(self):
        for left,right in ((.5-2e-8,1),(0,.5+2e-8),(0,.500001)):
            a,b=owner.interior_probes(.5,left,right)
            self.assertTrue(left<a<.5<b<right)

    def test_multiway_and_endpoint(self):
        for root,multi in ((.5,True),(2e-7,False)):
            f=crossing(root,multi);s=switch(f,root)
            result,_=owner.certify_in_region(f,s,owner.localize(f,s),0,1)
            self.assertIn(0,result.owners_at)

    def test_mismatch_rejected(self):
        f=crossing();s=switch(f)
        from dataclasses import replace
        with self.assertRaisesRegex(VerificationError,'owner_semantics'):
            owner.certify_in_region(f,replace(s,owners_before=(0,)),owner.localize(f,s),0,1)

    def test_valid_failure_and_success(self):
        for diag in (False,True):
            for success in (False,True):
                with tempfile.TemporaryDirectory() as d:
                    folder=Path(d).resolve();path,head,trace=persist(folder,events(diagnostic=diag,success=success),success)
                    result=pub.validate_persisted(folder,path,head,traceback_path=trace)
                    self.assertEqual(result['snapshot']['snapshot']['counters']['edges_opened'],1)

    def test_stage_controls(self):
        rows=events();index=next(i for i,r in enumerate(rows) if r['action']=='numerical_stage')
        for detail in ({},{'stage':'unknown'},{'stage':True},{'stage':'geometry','extra':1},
                       {'stage':'routing','pieces':True,'bounded':0,'quadrature':1}):
            modified=copy.deepcopy(rows);modified[index]['payload']['detail']=detail
            with self.assertRaises(pub.LifecycleError):pub.replay(modified)

    def test_early_late_missing_stage(self):
        rows=events();idx=next(i for i,r in enumerate(rows) if r['action']=='numerical_stage')
        for modified in ([rows[idx],*rows],rows+[rows[idx]],
                         [r for r in rows if not(r['action']=='numerical_stage' and r['payload']['candidate']=='constant_width')]):
            with self.assertRaises(pub.LifecycleError):pub.replay(modified)

    def test_context_and_terminal(self):
        rows=events();idx=next(i for i,r in enumerate(rows) if r['action']=='numerical_stage')
        for key,value in (('state',False),('edge','other'),('candidate','unknown')):
            altered=copy.deepcopy(rows);altered[idx]['payload'][key]=value
            with self.assertRaises(pub.LifecycleError):pub.replay(altered)
        altered=events();altered[-1]={'action':'success','payload':{}}
        with self.assertRaises(pub.LifecycleError):pub.replay(altered)

    def test_cross_file_and_false_gate(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d).resolve();path,head,trace=persist(folder,events())
            records={k:json.loads((folder/(k+'.json')).read_text()) for k in ('qc','manifest','evidence')}
            for name in records:
                bad=copy.deepcopy(records);bad[name]['authority']['snapshot']['snapshot']['counters']['edges_opened']=0
                with self.assertRaises(pub.LifecycleError):pub.validate_package(path,head,bad,traceback_path=trace)
            for r in records.values():r['accepted']=True;r['checks']['controls']=False
            with self.assertRaises(pub.LifecycleError):pub.validate_package(path,head,records,traceback_path=trace)

    def test_corrupt_journal_and_marker(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d).resolve();path,head,trace=persist(folder,events())
            with path.open('ab') as f:f.write(b'{')
            with self.assertRaises(pub.LifecycleError):pub.authority(path,head)
            marker=folder/'marker';durable_write(marker,{})
            with self.assertRaises(FileExistsError):durable_write(marker,{})

    def test_independent_emergency(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d).resolve()/'emergency'
            try:raise RuntimeError('synthetic original')
            except RuntimeError as error:pub.emergency(path,error,stage='geometry',before=None,terminal=None,publication_error='replay failed')
            record=json.loads(path.read_text());self.assertFalse(record['accepted'])
            self.assertIn('synthetic original',record['traceback']);self.assertIsNone(record['terminal'])

    def test_restricted_selection(self):
        from defensive_network_disruption.validation.empirical_switch_diagnosis import project_prepared_edge
        row=json.dumps({'alias':'development_01','carrier':[0,0],'receivers':[{'sentinel':'forbidden'},[20,0]],'defenders':[[5,0]]})
        self.assertEqual(project_prepared_edge(row,1)['receiver'],(20.,0.))

class Session14aiProductionTests(unittest.TestCase):
    def test_frozen_topology_and_publication_controls(self):
        from defensive_network_disruption.validation.onset_owner_acceptance import topology_oracles,publication_controls
        topology=topology_oracles();controls=publication_controls()
        self.assertEqual(len(topology),12)
        self.assertTrue(all(x['passed'] for x in topology),topology)
        self.assertTrue(all(x['passed'] for x in controls),controls)

    def test_full_historical_production_path(self):
        from defensive_network_disruption.validation.onset_owner_acceptance import historical_regression
        rows=historical_regression(Path(__file__).resolve().parents[1])
        self.assertEqual(len(rows),108,rows[-1])
        self.assertTrue(all(x['passed'] for x in rows),rows[-1])
        self.assertEqual(sum(x['components'] for x in rows),366)
        self.assertEqual(sum(x['permutations'] for x in rows),399)

    def test_ordinary_numerical_path_and_warning(self):
        from unittest.mock import patch
        args=('isotropic',(0.,0.),(20.,0.),((10.,2.),))
        result=owner.evaluate(*args)
        self.assertIn('maximum_interval',result)
        with patch('defensive_network_disruption.geometry.representation_retry.independent_maximum',side_effect=RuntimeWarning('synthetic')):
            with self.assertRaises(RuntimeWarning):owner.evaluate(*args)

    def test_partition_consumption(self):
        from unittest.mock import patch
        from defensive_network_disruption.geometry import representation_retry as original
        captured=[];fn=original.independent_maximum
        def collect(f,partitions,*args):
            captured.append(partitions);return fn(f,partitions,*args)
        with patch.object(original,'independent_maximum',side_effect=collect):
            result=owner.evaluate('isotropic',(0.,0.),(20.,0.),((10.,2.),))
        self.assertEqual(captured,[result['partitions']])

    def test_new_stage_order_and_failure_context(self):
        rows=events(diagnostic=True)
        rows=rows[:-1]
        ctx=dict(state='s',edge='e',candidate='constant_width')
        for stage in pub.STAGES[1:-1]:
            detail={'stage':stage}
            if stage=='routing':detail.update(pieces=2,bounded=0,quadrature=2)
            rows.append({'action':'numerical_stage','payload':dict(**ctx,detail=detail)})
        rows.append({'action':'failure','payload':dict(**ctx,stage='direct_simpson',exception='RuntimeError',traceback_sha256='a'*64)})
        self.assertEqual(pub.replay(rows)['failure_stage'],'direct_simpson')
        rows[-1]['payload']['stage']='geometry'
        with self.assertRaises(pub.LifecycleError):pub.replay(rows)

    def test_missing_traceback_and_missing_persisted_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d).resolve();path,head,trace=persist(folder,events())
            trace.write_bytes(b'changed')
            with self.assertRaises(pub.LifecycleError):pub.validate_persisted(folder,path,head,traceback_path=trace)
            (folder/'evidence.json').unlink()
            with self.assertRaises(FileNotFoundError):pub.validate_persisted(folder,path,head,traceback_path=trace)

    def test_runner_preaccess_block_preserves_zero_access(self):
        import importlib.util
        from unittest.mock import patch
        path=Path(__file__).resolve().parents[1]/'scripts/session_14ai_onset_owner_repair.py'
        spec=importlib.util.spec_from_file_location('ai_test_runner',path);runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d).resolve();out=folder/'output';local=out/'local'
            with patch.object(runner,'ROOT',folder),patch.object(runner,'OUT',out),patch.object(runner,'LOCAL',local),\
                 patch.object(runner,'CODE',()),patch.object(runner,'PROTOCOL','protocol'),\
                 patch.object(runner,'preflight',return_value={'synthetic':True}),\
                 patch.object(runner,'git',return_value='synthetic_commit'),\
                 patch.object(runner,'topology_oracles',return_value=[dict(fixture='synthetic_failure',expected='accepted',observed='failure',passed=False)]),\
                 patch.object(runner,'empirical') as access:
                (folder/'protocol').write_text('synthetic')
                runner.audit();access.assert_not_called()
                qc=json.loads((out/'qc.json').read_text())
                self.assertFalse(qc['accepted']);self.assertEqual(qc['real_edges_opened'],0)
                runner.publication_check()
                with self.assertRaises(FileExistsError):runner.audit()

    def test_runner_preserves_synthetic_access_on_unexpected_failure(self):
        import importlib.util
        from unittest.mock import patch
        path=Path(__file__).resolve().parents[1]/'scripts/session_14ai_onset_owner_repair.py'
        spec=importlib.util.spec_from_file_location('ai_failure_runner',path);runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
        def fail_after_access(journal):
            for row in events(diagnostic=True)[:-1]:
                if row['action']!='initialized':journal.append(row['action'],**row['payload'])
            raise RuntimeError('synthetic numerical failure')
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d).resolve();out=folder/'output';local=out/'local'
            fake=[dict(fixture='synthetic_'+str(i),candidate='isotropic',passed=True,components=3,permutations=1,error='') for i in range(108)]
            with patch.object(runner,'ROOT',folder),patch.object(runner,'OUT',out),patch.object(runner,'LOCAL',local),\
                 patch.object(runner,'CODE',()),patch.object(runner,'PROTOCOL','protocol'),\
                 patch.object(runner,'preflight',return_value={'synthetic':True}),\
                 patch.object(runner,'git',return_value='synthetic_commit'),\
                 patch.object(runner,'historical_regression',return_value=fake),\
                 patch.object(runner,'empirical',side_effect=fail_after_access):
                (folder/'protocol').write_text('synthetic')
                runner.audit();runner.publication_check()
                q=json.loads((out/'qc.json').read_text())
                self.assertEqual(q['real_edges_opened'],1);self.assertFalse(q['accepted'])
                self.assertEqual(json.loads((out/'empirical_edge_regression.json').read_text())['reason'],'audit_failed')
                self.assertIn('synthetic numerical failure',(local/'traceback').read_text())
                self.assertTrue((local/'emergency.json').exists())

if __name__=='__main__':unittest.main()
