"""Frozen provider-free trace controls. No retained-file access."""
from fractions import Fraction as F
import time
import numpy as np

from ..geometry import r9r_localization as original
from ..geometry import r9s_trace as trace
from .r9j_evidence import digest

FIXTURES=('clean_adjacent','isolated_zero','zero_block','negative_zero_positive',
          'positive_zero_negative','reversals','no_transition','rounded_plateau',
          'rounded_oscillation','adjacent_branch')
PATTERNS=('A','D','C','C','D','E','G','C','F','D')
SEQUENCES=('NNNNPPPPP','NNNNZPPPP','NNNZZZPPP','NNNNZZPPP','PPPPZNNNN',
           'NNPNPNPPP','NNNNNNNNN','NNZZZZPPP','NNPPZNPPP','NNNNZPPPP')
OUTCOMES=('returned','returned','returned','returned','returned',
          'binary64_nonmonotone_unresolved','binary64_bracket_unavailable','returned',
          'binary64_nonmonotone_unresolved','returned')


def collect(function,pair,a,b,lower,upper,before,after,reference,structures,sink,*,engineering=False,deadline=None):
    observer=trace.Observer(sink,reference,structures,engineering=engineering)
    error=None;result=None
    try:
        with observer.enabled():
            result=original.inspect_production(function,pair,a,b,lower,upper,before,after,
                        deadline=time.monotonic()+600 if deadline is None else deadline)
    except BaseException as caught:
        error=caught
    outcome={'returned':error is None,'exception':None if error is None else type(error).__name__,
             'message':None if error is None else str(error)}
    value={'schema_version':1,'arguments':observer.arguments,'reference':reference,
           'structures':structures,'windows':observer.windows,'attempts':observer.attempts,
           'probes':observer.probes,'final':observer.final,
           'sorted_ordinals':sorted(range(len(observer.probes)),key=lambda i:observer.probes[i]['key']),
           'outcome':outcome,'observer_errors':observer.errors}
    return value,error,result


def control(name,sink=lambda *_:None):
    ordinal=FIXTURES.index(name);mid=original.old._bits(.5)
    low,high=original.old._float(mid-4),original.old._float(mid+4)
    def function(ts):
        values=[]
        for t in ts:
            t=float(t);k=original.old._bits(t)-mid
            if name=='rounded_plateau':value=((1+t)-1)-.5
            elif name=='rounded_oscillation':value=(((1+t)-1)-t)+(t-.5)*2.**-40
            elif name=='adjacent_branch':value=max(0.,t-original.old._float(mid-1))-(.5-original.old._float(mid-1))
            else:
                s=SEQUENCES[ordinal][k+4];value={'N':-1.,'P':1.,'Z':0.}[s]
                if name=='negative_zero_positive' and k==0:value=-0.
            values.append(value)
        return np.column_stack((values,np.zeros_like(ts)))
    before=1 if name=='positive_zero_negative' else -1
    ref={'enclosure':[trace.rational(F(1,2))]*2,'outer':[trace.binary(low),trace.binary(high)],
         'one_crossing':name in ('rounded_plateau','rounded_oscillation','adjacent_branch'),
         'strict_derivative':name in ('rounded_plateau','rounded_oscillation'),
         'authority_valid':True,'boundary_refuted':False,'excluded':None}
    structures={'onsets':[trace.binary(original.old._float(mid-1))] if name=='adjacent_branch' else [],
                'ties':[],'status':'engineering'}
    value,error,result=collect(function,(0,1),F(1,2),F(1,2),low,high,before,-before,
                               ref,structures,sink,engineering=True)
    summary=trace.summarize(value)
    observed='returned' if error is None else str(error)
    sequence=''.join({-1:'N',0:'Z',1:'P'}[value['probes'][i]['sign']] for i in value['sorted_ordinals'])
    detail={'fixture':name,'trace':value,'summary':summary,'sequence':sequence,
            'outcome':observed,'expected_outcome':OUTCOMES[ordinal]}
    passed=(summary['complete'] and summary['pattern']==PATTERNS[ordinal] and
            sequence==SEQUENCES[ordinal] and observed==OUTCOMES[ordinal])
    return detail,passed


def controls(save):
    rows=[]
    for i,name in enumerate(FIXTURES):
        detail,passed=control(name)
        h=save('control_'+name,detail)
        rows.append({'fixture':name,'expected':PATTERNS[i],'observed':detail['summary']['pattern'],
                     'expected_outcome':OUTCOMES[i],'observed_outcome':detail['outcome'],
                     'passed':bool(passed),'evidence_sha256':h})
    return rows
