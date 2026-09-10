import ast
import copy
import hashlib
import json
import math
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import numpy as np
from defensive_network_disruption.validation import construct_diagnostics as c
from defensive_network_disruption.validation.ranking_metrics import expected_credits
import scripts.session_07_construct_validity as r


def geometry():return c.Geometry((0.,0.),((5.,0.),(10.,3.),(-8.,4.)),((4.,1.),(8.,2.),(12.,-3.)))


def models():
    return {m:{'mean':[0.]*n,'scale':[1.]*n,'coefficients':([-.2,0.,0.] if m=='m0' else [.2,0.,0.,-.1,.3] if m=='m1' else [.18,0.,0.,-.1,.3,-.2])} for m,n in (('m0',3),('m1',5),('m2',6))}


class DiagnosticMathTests(unittest.TestCase):
    def test_feature_oracles_and_nesting(self):
        geo=c.Geometry((0.,0.),((10.,0.),(-5.,0.)),((4.,3.),))
        x,mass=c.feature_matrices(geo)
        np.testing.assert_array_equal(x['m0'],[[10,10,0],[5,-5,0]])
        np.testing.assert_array_equal(x['m0'],x['m1'][:,:3]);np.testing.assert_array_equal(x['m1'],x['m2'][:,:5])
        self.assertEqual(x['m1'][0,3],math.hypot(6,3));self.assertEqual(x['m1'][0,4],3)
        self.assertEqual(x['m2'][0,5],math.exp(-3/5));self.assertEqual(mass,0)

    def test_component_reconstruction_and_signs(self):
        matrix=np.array([[1.,2.,3.],[4.,5.,6.]])
        a={'mean':[1.,1.,1.],'scale':[1.,2.,4.],'coefficients':[2.,-3.,4.]}
        u,columns,grouped,residual=c.decompose(matrix,a)
        np.testing.assert_array_equal(columns,[[0,-1.5,2],[6,-6,5]])
        np.testing.assert_array_equal(u,[.5,5]);np.testing.assert_array_equal(grouped[:,0],u)
        self.assertEqual(residual,0)

    def test_between_model_shared_shift_is_distinct(self):
        row=c.diagnose(geometry(),0,models(),0,'development_01')
        for pair,left,right in (('m1_m0','m0','m1'),('m2_m1','m1','m2')):
            b=row['bookkeeping'][pair]
            np.testing.assert_allclose(np.array(b['shared'])+b['added'],np.array(row['models'][right]['utility'])-row['models'][left]['utility'])
            self.assertAlmostEqual(sum(b['centered_shared']),0)
        self.assertTrue(any(abs(v)>0 for v in row['bookkeeping']['m2_m1']['shared']))

    def test_block_high_ties_expected_ranks(self):
        u=[1.,1.-.75e-12,1.-1.5e-12,0.]
        result=c.rank_blocks(u)
        self.assertEqual(result['top'],[0,1]);self.assertEqual(result['ranks'],[1.5,1.5,3.,4.])
        self.assertEqual(expected_credits(u,0)['rr'],.75)
        np.testing.assert_array_equal(c.rank_blocks([0,1,1])['ranks'],[3,1.5,1.5])

    def test_pair_changes_and_empty_pairs(self):
        d=c.pair_comparison([0,1,2],[1,0,2]);self.assertEqual(d['strict_reversal'],1)
        self.assertEqual(c.pair_comparison([0,1],[0,0])['tie_created'],1)
        self.assertEqual(c.pair_comparison([0,0],[0,1])['tie_removed'],1)
        self.assertIsNone(c.pair_comparison([0],[0])['changed_fraction'])

    def test_disagreement_omits_raw_ties(self):
        x=np.zeros((3,5));x[:,3]=[1,2,2];x[:,4]=[3,1,1]
        eligible,discordant=c.disagreement(x)
        self.assertEqual(eligible,[(0,1),(0,2)]);self.assertEqual(discordant,eligible)

    def test_inverse_weighted_cdf_and_boundary_collapse(self):
        self.assertEqual(c.quantiles([1,2,3,4],[1]*4,(.25,.5,.75)),[1,2,3])
        self.assertEqual(c.quantiles([0,10],[9,1],(.5,)),[0])
        self.assertEqual(c.bin_name(2,[1,2,3]),'bin_2')
        cuts=c.prepare_cuts({'a':[geometry()],'b':[geometry()]})
        self.assertEqual(cuts,c.prepare_cuts({'b':[geometry()],'a':[geometry()]}))
        self.assertFalse(hasattr(geometry(),'target_index'))

    def test_direction_convention_and_degenerate(self):
        self.assertEqual(c.direction(0,0),'degenerate');self.assertEqual(c.direction(10,10),'forward');self.assertEqual(c.direction(10,-10),'backward');self.assertEqual(c.direction(10,0),'approximately_lateral')
        self.assertEqual(c.direction(10,10*math.sin(math.radians(10))),'approximately_lateral')

    def test_non_nearest_mass_is_not_new_feature(self):
        geo=c.Geometry((0,0),((20,0),),((5,2),(10,2),(15,2)))
        x,mass=c.feature_matrices(geo)
        self.assertEqual(mass,math.fsum([math.exp(-2/5)]*2));self.assertEqual(x['m2'][0,5],math.fsum([math.exp(-2/5)]*3))
        x2,mass2=c.feature_matrices(c.Geometry(geo.carrier_xy,geo.candidate_xy,tuple(reversed(geo.defender_xy))))
        np.testing.assert_array_equal(x['m2'],x2['m2']);self.assertEqual(mass,mass2)

    def test_empty_weighted_distribution_and_validation(self):
        self.assertEqual(c.distribution([],[])['count'],0)
        with self.assertRaises(ValueError):c.quantiles([1],[0])
        with self.assertRaises(ValueError):c.rank_blocks([float('nan')])

    def test_equal_match_weights_not_pooled_counts(self):
        rows=[{'alias':'a'}]*9+[{'alias':'b'}]
        w=r.weighted_rows(rows);self.assertAlmostEqual(sum(w[:9]),.5);self.assertEqual(w[9],.5)


class SelectionTests(unittest.TestCase):
    def rows(self):
        rows=[]
        for ordinal in range(36):
            category=ordinal%4;model={m:{'top':[0]} for m in ('m0','m1','m2')}
            if category==1:model['m1']['top']=[1]
            if category==2:model['m2']['top']=[1]
            rows.append({'ordinal':ordinal,'alias':f'development_{ordinal//4+1:02d}','tie_key':hashlib.sha256(str(ordinal).encode()).hexdigest(),'m1_delta':3 if category==0 else 0,'m2_delta':3 if category==0 else -1,'disagreement_fraction':.8 if category==1 else 0,'m2_m1_pairs':{'changed_fraction':.8},'models':model,'target_index':0})
        return rows

    def test_quotas_caps_dedup_and_determinism(self):
        rows=self.rows();selected,counts=c.select_cases(rows)
        self.assertEqual(counts,{'failure':3,'feature_disagreement':3,'m2_ordering_change':3,'agreement':3})
        self.assertEqual(len({x['ordinal'] for x in selected}),12)
        self.assertLessEqual(max(Counter(x['alias'] for x in selected).values()),2)
        self.assertEqual((selected,counts),c.select_cases(list(reversed(rows))))
        self.assertEqual([x['tie_key'] for x in selected],sorted(x['tie_key'] for x in selected))

    def test_shortfalls_no_relaxation(self):
        selected,counts=c.select_cases(self.rows()[:2]);self.assertLessEqual(len(selected),2);self.assertLess(sum(counts.values()),12)


class ReviewAndFirewallTests(unittest.TestCase):
    def test_svg_geometry_masking_equal_scale(self):
        text=r.svg_geometry(geometry(),'case_01');ET.fromstring(text)
        for word in ('target','utility','rank','category','development_','1886347'):
            self.assertNotIn(word,text)
        self.assertIn('C01',text);self.assertIn('5 m',text)
        self.assertEqual(text,r.svg_geometry(geometry(),'case_01'))
        ns={'s':'http://www.w3.org/2000/svg'};root=ET.fromstring(text)
        for element in root.findall('s:circle',ns):
            self.assertTrue(0<float(element.attrib['cx'])<1000);self.assertTrue(0<float(element.attrib['cy'])<1000)

    def test_module_graph_excludes_fitting_acquisition(self):
        code="import sys; import scripts.session_07_construct_validity; assert not any(n.endswith(('choice_model','session5','session6_source','session6c_source','session6e_transport')) or n.startswith('scipy.optimize') for n in sys.modules)"
        subprocess.run([sys.executable,'-c',code],check=True,cwd=r.ROOT)
        tree=ast.parse(Path(r.__file__).read_text())
        imports=[n.module or '' for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
        self.assertFalse(any('session5' in x or 'choice_model' in x for x in imports))

    def test_path_escape_and_symlink_rejection(self):
        with tempfile.TemporaryDirectory(dir='/private/tmp') as d,patch.object(r,'ROOT',Path(d)):
            with self.assertRaises(PermissionError):r.safe(Path('/etc/passwd'))
            p=Path(d)/'link';p.symlink_to('/etc/passwd')
            with self.assertRaises(PermissionError):r.safe(p)

    def test_publication_rejects_nested_reconstructive_fields(self):
        obj={'schema_version':'1','components':[{'model':'m0','component':'attacking','kind':'components','distribution':{'candidate_xy':[[1,2]]}}],'between_model_bookkeeping':[]}
        with self.assertRaises(ValueError):r.validate_public('contribution_summary.json',obj)
        obj['components'][0]['distribution']={'count':1,'mean':0,'minimum':0,'maximum':0,'quantiles':{'q05':0,'q25':0,'q50':0,'q75':0,'q95':0},'extra':2}
        with self.assertRaises(ValueError):r.validate_public('contribution_summary.json',obj)

    def test_actual_canonical_reader_firewall_and_projection(self):
        with tempfile.TemporaryDirectory(dir='/private/tmp') as d:
            root=Path(d);pop=root/'population.jsonl'
            one={'match_id':'1886347','event_id':'synthetic','candidate_ids':['c1'],'candidate_xy':[[1.,2.]],'defender_xy':[[2.,3.]],'carrier_xy':[0.,0.],'target_index':0,'target_outside':False}
            with patch.object(r,'ROOT',root),patch.object(r,'POPULATION',pop),patch.object(r,'log'):
                rows=[]
                ids=sorted(r.DEV)
                for i in range(7227):rows.append(dict(one,match_id=ids[i%9],event_id='synthetic_'+str(i)))
                pop.write_text(''.join(json.dumps(x)+'\n' for x in rows))
                with patch.object(r,'POPULATION_SHA',hashlib.sha256(pop.read_bytes()).hexdigest()):
                    actual=r.read_population(geometry_only=True);self.assertEqual(len(actual),7227);self.assertNotIn('target_index',actual[0])
                for bad in ('1953632','1874553','../1886347'):
                    pop.write_text(json.dumps(dict(one,match_id=bad))+'\n')
                    with patch.object(r,'POPULATION_SHA',hashlib.sha256(pop.read_bytes()).hexdigest()),self.assertRaises(PermissionError):r.read_population()
                pop.write_text(json.dumps(dict(one,sentinel=1))+'\n')
                with patch.object(r,'POPULATION_SHA',hashlib.sha256(pop.read_bytes()).hexdigest()),self.assertRaises(PermissionError):r.read_population()


class LifecycleTests(unittest.TestCase):
    def sandbox(self,d):
        stack=ExitStack();root=Path(d);output=root/'outputs';local=output/'local';(root/'docs').mkdir()
        for name,path in {'ROOT':root,'OUTPUT':output,'LOCAL':local,'PROTOCOL':root/'protocol.md','MODELS':root/'models.json','POPULATION':root/'population.jsonl'}.items():stack.enter_context(patch.object(r,name,path))
        r.PROTOCOL.write_text('synthetic protocol');r.MODELS.write_text(json.dumps({'models':models()}));r.POPULATION.write_text('synthetic')
        raw=[{'ordinal':i,'alias':f'development_{i%9+1:02d}','geometry':geometry(),'target_index':0} for i in range(27)]
        stack.enter_context(patch.object(r,'authority',return_value={'models':models(),'environment':{'synthetic':True}}));stack.enter_context(patch.object(r,'clean'));stack.enter_context(patch.object(r,'committed',return_value='synthetic'));stack.enter_context(patch.object(r,'git',return_value='synthetic'));stack.enter_context(patch.object(r,'impl_hashes',return_value={'synthetic':'a'*64}));stack.enter_context(patch.object(r,'read_population',side_effect=lambda geometry_only=False:[{k:v for k,v in row.items() if not geometry_only or k!='target_index'} for row in raw]))
        return stack

    def reviewed(self,stage):
        p=r.LOCAL/f'stage_{stage.lower()}_responses.json';obj=json.loads(p.read_text());obj['reviewer']={'experience':'Synthetic test only','prior_familiarity':'Synthetic fixture only'}
        for case in obj['cases']:
            if stage=='A':
                case['candidate_accessibility']={k:'not_assessable' for k in case['candidate_accessibility']}
                for key in ('receiver_pressure','corridor_constraints','missing_context'):case[key]='Synthetic not assessable'
                case['confidence']='low';case['practitioner_meaningful']='uncertain'
            else:
                for i in range(1,8):case['q'+str(i)]='Synthetic not assessable'
                case['q8']='ambiguous'
        p.write_text(json.dumps(obj));return p

    def test_end_to_end_pending_then_human_review_closure(self):
        with tempfile.TemporaryDirectory(dir='/private/tmp') as d:
            stack=self.sandbox(d)
            with stack:
                r.preflight();r.prepare_diagnostics();r.summarize();r.select_passages();r.render_passages()
                self.assertEqual(r.read_json(r.OUTPUT/'review_summary.json')['status'],'AWAITING INDEPENDENT REVIEW')
                self.assertFalse((r.LOCAL/'stage_b').exists())
                with self.assertRaises(FileNotFoundError):r.reveal_passages()
                with self.assertRaises(ValueError):r.record_review('A',r.LOCAL/'stage_a_responses.json')
                r.record_review('A',self.reviewed('A'));locked=r.sha(r.LOCAL/'stage_a_locked.json')
                r.reveal_passages();self.assertEqual(r.sha(r.LOCAL/'stage_a_locked.json'),locked)
                r.record_review('B',self.reviewed('B'))
                r.write_json(r.LOCAL/'interpretation.json',{'primary':'C','secondary':'2','rationale':'Synthetic ambiguous review only.','alternative_explanations':'Synthetic uncertainty, not a real result.','next_question':'Synthetic follow-up, not executed.','human_reviewed':True})
                r.close_review();r.publication_check()
                self.assertEqual(r.read_json(r.OUTPUT/'manifest.json')['status'],'complete')
                for name in ('feature_disagreement.csv','stratified_diagnostics.csv'):self.assertNotIn(b'\r',(r.OUTPUT/name).read_bytes())

    def test_committed_selection_required_before_render(self):
        with tempfile.TemporaryDirectory(dir='/private/tmp') as d:
            stack=self.sandbox(d)
            with stack:
                r.prepare_diagnostics();r.summarize();r.select_passages()
                with patch.object(r,'committed',side_effect=RuntimeError('not committed')),self.assertRaises(RuntimeError):r.render_passages()
                self.assertFalse((r.LOCAL/'stage_a').exists())

    def test_marker_rejects_rerun_and_packet_tampering(self):
        with tempfile.TemporaryDirectory(dir='/private/tmp') as d:
            stack=self.sandbox(d)
            with stack:
                r.prepare_diagnostics();r.summarize();r.select_passages();r.render_passages()
                with self.assertRaises(FileExistsError):r.summarize()
                svg=next((r.LOCAL/'stage_a').glob('*.svg'));svg.write_text(svg.read_text()+'\n')
                with self.assertRaises(RuntimeError):r.verify_packet()

    def test_review_path_and_immutable_locked_answer(self):
        with tempfile.TemporaryDirectory(dir='/private/tmp') as d:
            stack=self.sandbox(d)
            with stack:
                r.prepare_diagnostics();r.summarize();r.select_passages();r.render_passages()
                with self.assertRaises(PermissionError):r.record_review('A',Path('/private/tmp/unapproved.json'))
                r.record_review('A',self.reviewed('A'))
                p=r.LOCAL/'stage_a_locked.json';p.write_text(p.read_text()+'\n')
                with self.assertRaises(RuntimeError):r.locked_review('A')

if __name__=='__main__':unittest.main()
