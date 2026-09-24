"""Actual R9AD adapter against immutable R9T/R9K synthetic authority."""
import math
from pathlib import Path
import time
import numpy as np
from ..geometry import r9ad_adapter as adapter
from ..geometry import r9t_adapter as prior
from ..geometry import r9k_comparator as baseline
from ..geometry import r9t_transition as r
from ..geometry.r9q_diagnosis import deadline_limit
from .r9r_acceptance import historical_cases
from .r9t_acceptance import primitive
from .r9j_evidence import digest

def historical_regression(root,sink=lambda label,value:digest(value),*,deadline=math.inf):
    rows=[]
    for index,(label,case) in enumerate(historical_cases(root)):
        start=time.monotonic();stage=None;localizations=[];previous_structures=[]
        def record(**kw):
            nonlocal stage
            stage=kw['stage']
        kwargs=dict(root=Path(root),authority_context={'alias':'synthetic_r9r'},synthetic=True,
                    historical_failure=case['historical_failure'])
        args=(case['candidate'],case['origin'],case['receiver'],case['defenders'])
        with deadline_limit(min(deadline,time.monotonic()+600)):old_edge,old=prior.evaluate(*args,**kwargs,localization_sink=lambda **kw: previous_structures.append(primitive(kw)) if kw.get("kind")=="raw_structures" else None)
        with deadline_limit(min(deadline,time.monotonic()+600)):base_edge,base=baseline.evaluate(*args,**kwargs)
        if old!=base:raise ValueError('inherited_authority_disagreement')
        expected=case['historical_vector'];new=None;reason='accepted'
        try:
            with deadline_limit(min(deadline,time.monotonic()+600)):
                new_edge,new=adapter.evaluate(*args,**kwargs,record=record,localization_sink=lambda **kw:localizations.append(primitive(kw)))
        except (r.VerificationError,r.pv.GateFailure,TimeoutError) as error:
            reason=type(error).__name__
        structural=('partitions','canonical_onsets','canonical_switches')
        structure=new is not None and all(new.get(k)==old.get(k) for k in structural) and previous_structures == [x for x in localizations if x.get('kind')=='raw_structures']
        production=new is not None and new['intervals']==old['intervals']==expected['intervals'] and tuple(new['estimates'])==tuple(old['estimates'])==tuple(expected['estimates'])
        if production:
            for key,value in new['estimates'].items():
                for previous in (old['estimates'][key],expected['estimates'][key]):
                    production &= math.isfinite(value) and abs(value-previous)<=64*np.finfo(float).eps*max(1.,abs(value),abs(previous))
        verification=new is not None and new['maximum_interval']==old['maximum_interval'] and new['certificate_evidence']==old['certificate_evidence']
        valid=structure and production and verification
        detail=dict(fixture=label,component_order={'old':list(old['estimates']),'expected':list(expected['estimates']),'new':None if new is None else list(new['estimates'])},old=primitive(old),baseline=primitive(base),new=primitive(new),expected=primitive(expected),localizations=localizations,previous_structures=previous_structures,reason=reason,stage=stage,
                    seconds=time.monotonic()-start)
        h=sink('historical_'+str(index),detail)
        rows.append(dict(fixture=label,candidate=case['candidate'],status='passed' if valid else 'blocked',
            components=len(expected['estimates']),permutations=new['permutations'] if new is not None else 0,
            structure_exact=bool(structure),production_preserved=bool(production),verification_preserved=bool(verification),
            reason=reason if not valid else 'accepted',evidence_sha256=h))
    return rows
