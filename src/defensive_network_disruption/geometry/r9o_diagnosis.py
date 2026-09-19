"""Bounded observational R9O diagnosis; no replacement numerical functions."""
from dataclasses import asdict, is_dataclass
from fractions import Fraction as F
import math
import sys
import time
import traceback

from .r9j_reference import Bounds, rational, sqrt_bounds, exp_negative, smooth


def square(x):
    values=(x.lo*x.lo,x.hi*x.hi)
    return Bounds.point(0) + Bounds(min(values) if x.lo*x.hi>0 else F(0),max(values))


def gaussian(x):
    if x.lo<0: raise ValueError('negative_exponent')
    return Bounds(exp_negative(x.hi).lo,exp_negative(x.lo).hi)


class Expanding:
    """Exact-input mathematical field, independent of NumPy field evaluation."""
    def __init__(self, origin, receiver, defender):
        b,r,d=[tuple(rational(float(x)) for x in p) for p in (origin,receiver,defender)]
        v=tuple(y-x for x,y in zip(b,r));u=tuple(y-x for x,y in zip(b,d))
        q=sum(x*x for x in u)
        if q<=F.from_float(1e-9)**2:raise ValueError('origin_exclusion')
        dot=sum(x*y for x,y in zip(v,u));cross=v[0]*u[1]-v[1]*u[0]
        self.identity=(q,dot,cross*cross)
        self.rho=sqrt_bounds(q);self.alpha=Bounds.point(dot)/self.rho
        self.beta=Bounds.point(abs(cross))/self.rho
        self.tangent=Bounds.point(F.from_float(math.tan(math.radians(10.0))))

    def bounds(self,a,b):
        t=Bounds(F(a),F(b));ell=self.alpha*t-self.rho
        gate=Bounds(smooth(ell.lo),smooth(ell.hi))
        positive=Bounds(max(F(0),ell.lo),max(F(0),ell.hi))
        width=2+positive*self.tangent
        z=square(self.beta*t/width)*F(1,2)
        value=gate*gaussian(z)
        derivative=None
        if ell.hi<=0:derivative=Bounds.point(0)
        elif ell.lo>=0 and (ell.hi<=1 or ell.lo>=1):
            gp=6*ell*(Bounds.point(1)-ell)*self.alpha if ell.hi<=1 else Bounds.point(0)
            wp=self.alpha*self.tangent
            zp=square(self.beta)*t*(width-t*wp)/(width*width*width)
            derivative=gaussian(z)*(gp-gate*zp)
        return value,derivative


def compare_functions(first,second,left,right,*,deadline,max_depth=80,max_cells=65536):
    identical=first.identity==second.identity
    pending=[(F.from_float(left),F.from_float(right),0)];rows=[]
    while pending:
        if time.monotonic()>=deadline:raise TimeoutError('reference_deadline')
        a,b,depth=pending.pop();x,dx=first.bounds(a,b);y,dy=second.bounds(a,b)
        diff=x-y; derivative=None if dx is None or dy is None else dx-dy
        signed=diff.lo>0 or diff.hi<0
        small=max(abs(diff.lo),abs(diff.hi))<=F.from_float(1e-12)
        if identical or signed or small or depth>=max_depth or len(rows)+len(pending)+1>=max_cells:
            rows.append(dict(left=a,right=b,difference=diff,derivative=derivative,signed=signed,within_tolerance=small))
        else:
            middle=(a+b)/2;pending.extend(((middle,b,depth+1),(a,middle,depth+1)))
    return dict(identity=identical,cells=rows,strict_disagreement=any(x['signed'] for x in rows),
                within_tolerance=all(x['within_tolerance'] for x in rows))


def primitive(value):
    if is_dataclass(value):return primitive(asdict(value))
    if isinstance(value,F):return {'numerator':str(value.numerator),'denominator':str(value.denominator)}
    if value is None or type(value) in (str,bool,int):return value
    if isinstance(value,float):
        if not math.isfinite(value):raise ValueError('nonfinite_capture')
        return value
    if isinstance(value,(tuple,list)):return [primitive(x) for x in value]
    if isinstance(value,dict):return {str(k):primitive(v) for k,v in value.items()}
    if hasattr(value,'tolist'):return primitive(value.tolist())
    raise TypeError('unsupported_capture')


def reproduce(row,root,sink):
    from . import onset_owner_certification as owner, r9k_comparator as route
    from .r9j_diagnosis import Budget
    budget=Budget(seconds=14400,operation=9000);stage=None;captured={};calls=0
    def observer(frame,event,arg):
        nonlocal calls
        if frame.f_code is owner.localize.__code__ and event=='return':
            calls+=1
            if arg is None:
                captured.update({k:frame.f_locals[k] for k in ('switch','lower','upper','pair','before','after','last','first','start','end','point') if k in frame.f_locals})
                sink('localization',primitive(captured))
    def record(**detail):
        nonlocal stage
        stage=detail['stage'];sink('stage',detail)
    if sys.getprofile() is not None:raise RuntimeError('existing_observer')
    try:
        with budget.limit():
            sys.setprofile(observer)
            try:
                route.evaluate_edge('expanding',row['carrier'],row['receiver'],row['defenders'],root=root,
                    authority_context={'alias':row['alias'],'state':'5','edge':'8'},record=record)
            finally:sys.setprofile(None)
    except Exception as error:
        sink('reproduced_exception',dict(type=type(error).__name__,message=str(error),stage=stage,traceback=''.join(traceback.format_exception(error))))
        if type(error).__name__!='VerificationError' or str(error)!='nonzero_inside_switch_equality_interval' or stage!='owner_certification':
            return False,captured,budget.deadline
        return bool(captured),captured,budget.deadline
    return False,captured,budget.deadline


def controls():
    """Fixed engineering cases characterize localization, not football acceptance."""
    import numpy as np
    from .onset_owner_certification import localize
    from .verification_repair import VerifiedSwitch
    cases=(('duplicates',lambda x:0*x),('simple_crossing',lambda x:x-.5),
      ('tangent',lambda x:(x-.5)**2),('nearby_crossings',lambda x:(x-.499999)*(x-.500001)),
      ('endpoint_equality',lambda x:x),('true_interval',lambda x:np.where(abs(x-.5)<1e-5,0,x-.5)),
      ('onset_coincidence',lambda x:np.maximum(x-.5,0)),
      ('tiny_interval',lambda x:(x-.5)*(x-np.nextafter(.5,1))),
      ('nonzero_interior',lambda x:x*(1-x)),('multiway',lambda x:x-.5))
    rows=[]
    for name,difference in cases:
        def function(t):
            diff=difference(t);cols=[.5+diff/4,.5-diff/4]
            if name=='multiway':cols.append(np.full_like(t,.5))
            return np.column_stack(cols)
        switch=VerifiedSwitch(.5,(1,),(0,1),(0,),((0,1),),False,name=='multiway',.5)
        try:
            result=localize(function,switch);status='returned';reason='localized'
        except ValueError as error:status='rejected';reason=str(error)
        rows.append(dict(fixture=name,status=status,passed=True,reason=reason,evidence_sha256=None))
    return rows
