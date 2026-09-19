"""R9Q observational diagnosis and exact-input expanding-field bounds.

No empirical loader, certificate registration, quadrature, or repair route.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import fields
from fractions import Fraction as F
import hashlib
import json
import math
import signal
import struct
import sys
import time
import traceback

from .r9j_reference import Bounds, down, up, rational, sqrt_bounds, exp_negative, smooth


FAILURE = "nonzero_inside_switch_equality_interval"


def bits(x):
    return struct.pack(">d", float(x)).hex()


def primitive(value):
    """Only explicitly supported numerical records; floats carry their exact bits."""
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is F:
        return {"numerator_hex": format(value.numerator, "x"), "denominator_hex": format(value.denominator, "x")}
    if isinstance(value, float):
        value = float(value)
        if not math.isfinite(value):
            raise ValueError("nonfinite_capture")
        return {"binary64": value, "bits": bits(value)}
    if type(value) in (list, tuple):
        return [primitive(x) for x in value]
    if type(value) is dict:
        if any(type(k) is not str for k in value):
            raise TypeError("string_capture_keys")
        return {k: primitive(v) for k, v in value.items()}
    if type(value) is Bounds:
        return {"lower": primitive(value.lo), "upper": primitive(value.hi)}
    # Whitelist classes rather than silently serializing arbitrary solver objects.
    from .verification_repair import VerifiedSwitch, VerifiedEnvelope, CertifiedTieInterval, CertifiedBoundary
    from .root_partition_determinism import CertifiedOnset, CertifiedRootTransition
    from .onset_owner_certification import OwnerWitness
    if type(value) in (VerifiedSwitch, VerifiedEnvelope, CertifiedTieInterval, CertifiedBoundary,
                       CertifiedOnset, CertifiedRootTransition, OwnerWitness):
        return {f.name: primitive(getattr(value, f.name)) for f in fields(value)}
    raise TypeError("unsupported_capture:" + type(value).__name__)


def square(x):
    products = (x.lo*x.lo, x.hi*x.hi)
    return Bounds(down(min(products) if x.lo*x.hi > 0 else F(0)), up(max(products)))


def gaussian(x):
    if x.lo < 0:
        raise ValueError("negative_exponent")
    return Bounds(exp_negative(x.hi).lo, exp_negative(x.lo).hi)


class Expanding:
    def __init__(self, origin, receiver, defender):
        b, r, d = [tuple(rational(x) for x in point) for point in (origin, receiver, defender)]
        v = tuple(y-x for x, y in zip(b, r, strict=True))
        u = tuple(y-x for x, y in zip(b, d, strict=True))
        q = sum(x*x for x in u)
        if q <= F.from_float(1e-9)**2:
            raise ValueError("origin_exclusion")
        dot = sum(x*y for x, y in zip(v, u, strict=True))
        cross = v[0]*u[1]-v[1]*u[0]
        self.identity = (q, dot, cross*cross)
        self.rho = sqrt_bounds(q)
        self.alpha = Bounds.point(dot)/self.rho
        self.beta = Bounds.point(abs(cross))/self.rho
        self.tangent = Bounds.point(F.from_float(math.tan(math.radians(10.0))))

    def bounds(self, left, right):
        t = Bounds(F(left), F(right))
        ell = self.alpha*t-self.rho
        gate = Bounds(down(smooth(ell.lo)), up(smooth(ell.hi)))
        width = 2+Bounds(max(F(0), ell.lo), max(F(0), ell.hi))*self.tangent
        exponential = gaussian(square(self.beta*t/width)*F(1, 2))
        value = gate*exponential
        derivative = None
        if ell.hi <= 0:
            derivative = Bounds.point(0)
        elif ell.lo >= 0 and (ell.hi <= 1 or ell.lo >= 1):
            gp = 6*ell*(Bounds.point(1)-ell)*self.alpha if ell.hi <= 1 else Bounds.point(0)
            zp = square(self.beta)*t*(width-t*self.alpha*self.tangent)/(width*width*width)
            derivative = exponential*(gp-gate*zp)
        return value, derivative


def sign(bounds):
    return 1 if bounds.lo > 0 else -1 if bounds.hi < 0 else 0


class DeadlineExceeded(TimeoutError):
    pass


@contextmanager
def deadline_limit(deadline):
    remaining = deadline-time.monotonic()
    if remaining <= 0:
        raise DeadlineExceeded("numerical_deadline")
    if signal.getitimer(signal.ITIMER_REAL)[0]:
        raise RuntimeError("nested_timer")
    previous = signal.getsignal(signal.SIGALRM)
    def expired(*_):
        raise DeadlineExceeded("numerical_deadline")
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, remaining)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def reference(first, second, left, right, *, deadline, sink, max_depth=80, max_leaves=65536):
    """Retain a complete disjoint partition. Never equate a small interval with zero."""
    left, right = rational(left), rational(right)
    if not 0 <= left <= right <= 1:
        raise ValueError("reference_domain")
    if not 0 <= max_depth <= 80 or not 1 <= max_leaves <= 65536:
        raise ValueError("reference_limits")
    pending = [(left, right, 0)]
    counts = {"leaves": 0, "signed": 0, "crossings": 0, "equal": 0, "unresolved": 0}
    previous = left
    identity = first.identity == second.identity
    root_intervals = []
    while pending:
        with deadline_limit(min(deadline, time.monotonic()+900)):
            a, b, depth = pending.pop()
            x, dx = first.bounds(a, b); y, dy = second.bounds(a, b)
            difference = x-y
            derivative = None if dx is None or dy is None else dx-dy
            endpoints = []
            for point in (a, b):
                endpoints.append(first.bounds(point, point)[0]-second.bounds(point, point)[0])
            inactive = x.lo == x.hi == y.lo == y.hi == 0
            same_sign = sign(endpoints[0]) != 0 and sign(endpoints[0]) == sign(endpoints[1])
            monotone = derivative is not None and sign(derivative) != 0
            crossing = monotone and sign(endpoints[0])*sign(endpoints[1]) == -1
            excluded = sign(difference) != 0 or (monotone and same_sign)
            limited = a == b or depth >= max_depth or counts['leaves']+len(pending)+1 >= max_leaves
            if not (identity or inactive or crossing or excluded or limited):
                middle = (a+b)/2
                pending.extend(((middle, b, depth+1), (a, middle, depth+1)))
                continue
            status = "equal" if identity or inactive else "crossings" if crossing else "signed" if excluded else "unresolved"
            if a != previous:
                raise ValueError("reference_coverage")
            previous = b
            row = dict(left=a, right=b, depth=depth, difference=difference,
                       derivative=derivative, endpoints=endpoints, status=status)
            sink("reference_cell", primitive(row))
            counts['leaves'] += 1; counts[status] += 1
            if crossing:
                root_intervals.append((a, b))
    complete = previous == right and counts['unresolved'] == 0
    root_count = counts['crossings'] if complete and not counts['equal'] else None
    # A singleton disputed set is a point observation, never an interval proof.
    if left == right and complete and counts['equal'] and not identity:
        root_count = 1
    topology = "A" if identity else "F" if left == right and complete and counts['equal'] else "G" if complete and counts['equal'] == counts['leaves'] else "B" if complete and root_count == 1 else "E" if complete and root_count == 2 else "I" if complete and root_count == 0 else "H"
    result = dict(complete=complete, topology=topology, root_count=root_count,
                  identity=identity, counts=counts, root_intervals=root_intervals,
                  equality_refuted=bool(counts['signed'] or counts['crossings']))
    sink("reference_result", primitive(result))
    return result


class Observer:
    """Python observer only. Does not replace functions or make field calls."""
    def __init__(self, sink):
        from . import onset_owner_certification as owner, root_partition_determinism as old
        self.localize = owner.localize.__code__
        self.pair = old._pair.__code__
        self.row = old._row.__code__
        self.structure = owner.canonical_geometry.__code__
        self.sink = sink
        self.active = None
        self.failed = None
        self.calls = 0
        self.io = 0.0
        self.error = None

    def write(self, label, value):
        start = time.monotonic()
        try:
            self.sink(label, primitive(value))
        except DeadlineExceeded:
            raise
        except Exception as error:
            # An observer cannot replace the solver's original return/exception.
            self.error = dict(exception=type(error).__name__,message=str(error),
                              traceback=''.join(traceback.format_exception(error)))
        finally:
            self.io += time.monotonic()-start

    def __call__(self, frame, event, arg):
        code = frame.f_code
        if code is self.localize:
            if event == 'call':
                self.calls += 1
                self.active = dict(switch=frame.f_locals['switch'], probes=[], rows=[])
            elif event == 'return' and self.active is not None:
                if arg is None:
                    self.active['locals'] = {k: frame.f_locals[k] for k in
                        ('lower','upper','pair','before','after','last','first','start','end','point') if k in frame.f_locals}
                    self.failed = self.active
                    self.write('failed_localization', self.failed)
                self.active = None
        elif self.active is not None and event == 'return':
            if code is self.pair and arg is not None:
                self.active['probes'].append(dict(point=float(frame.f_locals['point']), value=float(arg)))
            elif code is self.row and arg is not None:
                self.active['rows'].append(dict(point=float(frame.f_locals['point']), values=[float(x) for x in arg]))
        if code is self.structure and event == 'return' and arg is None:
            captured = {k:frame.f_locals[k] for k in ('onsets','envelope') if k in frame.f_locals}
            self.write('uncertified_structure', captured)

    @contextmanager
    def enabled(self):
        if sys.getprofile() is not None:
            raise RuntimeError("existing_observer")
        sys.setprofile(self)
        try:
            yield self
        finally:
            sys.setprofile(None)


def probe_audit(capture):
    locals_ = capture['locals']
    by_point = {}
    for probe in capture['probes']:
        t, value = probe['point'], probe['value']
        if t in by_point and bits(by_point[t]) != bits(value):
            raise ValueError('nondeterministic_pair_probe')
        by_point[t] = value
    ordered = [(t, (1 if v > 0 else -1 if v < 0 else 0)) for t, v in sorted(by_point.items())
               if locals_['lower'] <= t <= locals_['upper']]
    before = [s == locals_['before'] for _, s in ordered]
    after = [s == locals_['after'] for _, s in ordered]
    before_violation = any(not a and b for a, b in zip(before, before[1:]))
    after_violation = any(a and not b for a, b in zip(after, after[1:]))
    return dict(monotone_predicate_refuted=before_violation or after_violation,
                before_refuted=before_violation, after_refuted=after_violation,
                ordered_probes=ordered, unique_probes=len(ordered),
                interior_nonzero_observed=locals_['start'] <= locals_['point'] <= locals_['end'] and by_point[locals_['point']] != 0)


def reproduce(row, root, sink, deadline, capture_original=lambda error,stage:None):
    from . import r9k_comparator as route
    observer = Observer(sink)
    stage = None
    start = time.monotonic()
    def record(**detail):
        nonlocal stage
        stage = detail['stage']
        sink('numerical_stage', detail)
    try:
        with deadline_limit(deadline), observer.enabled():
            route.evaluate_edge('expanding', row['carrier'], row['receiver'], row['defenders'],
                root=root, authority_context={'alias': row['alias'], 'state': '5', 'edge': '8'}, record=record)
    except Exception as error:
        capture_original(error,stage)
        sink('numerical_exception', dict(exception=type(error).__name__,message=str(error),stage=stage,
             traceback=''.join(traceback.format_exception(error))))
        exact = type(error).__name__ == 'VerificationError' and str(error) == FAILURE and stage == 'owner_certification' and observer.failed is not None and observer.error is None
        return dict(reproduced=exact, capture=observer.failed, stage=stage,
                    exception=type(error).__name__, timeout=isinstance(error, TimeoutError),
                    seconds=time.monotonic()-start, observer_io=observer.io, observer_error=observer.error)
    return dict(reproduced=False,capture=None,stage=stage,exception=None,timeout=False,
                seconds=time.monotonic()-start,observer_io=observer.io,observer_error=observer.error)


def numerical_decision(reproduced, ref, audit, scalar_valid):
    if not reproduced or ref is None or not ref['complete'] or not scalar_valid:
        return 'NF'
    if audit['monotone_predicate_refuted'] and audit['interior_nonzero_observed']:
        return 'NC'
    # Nonzero interior is not alone proof of point-to-interval promotion.
    if ref['equality_refuted'] and audit['interior_nonzero_observed']:
        return 'NE'
    return 'NF'


def controls(sink):
    """Prospectively frozen analytic controls; observe unchanged localization twice."""
    import numpy as np
    from .onset_owner_certification import localize
    from .verification_repair import VerifiedSwitch
    from .occlusion_fields import CarrierOriginField
    names = ('duplicates','simple_crossing','tangent','near_double','nearby_roots','endpoint',
             'true_interval','onset_switch','tiny_interval','nonzero_interior','multiway')
    topologies = ('A','B','C','D','E','F','G','G','B','F','B')
    roots = (None,1,1,0,2,1,None,None,1,2,1)
    differences = (None,lambda t:t-.5,lambda t:(t-.5)**2,lambda t:(t-.5)**2+2.**-100,
                   lambda t:(t-.5)**2-2.**-40,lambda t:t,None,lambda t:np.maximum(t-.5,0),
                   lambda t:(t-.5)+2.**-60,lambda t:t*(1-t),lambda t:2*(t-.5))
    expected_behavior = {
        'simple_crossing': ('returned', 'localized'),
        'tiny_interval': ('returned', 'localized'),
        'multiway': ('returned', 'localized'),
        'nearby_roots': ('rejected', 'switch_witnesses_unavailable'),
    }
    rows = []
    for i, name in enumerate(names):
        trace = []
        def function(t):
            trace.extend(float(x) for x in t)
            if name in ('duplicates','true_interval'):
                defenders = [(5.,1.),(5.,-1.)] if name == 'duplicates' else [(5.,1.),(6.,2.)]
                return CarrierOriginField('expanding').individual_values((0.,0.), defenders,
                     np.column_stack((20*t,np.zeros_like(t))))
            if name == 'multiway':
                return np.column_stack((t-.5,.5-t,np.zeros_like(t)))
            return np.column_stack((differences[i](t),np.zeros_like(t)))
        location = 0. if name == 'endpoint' else .05 if name == 'true_interval' else .5
        switch = VerifiedSwitch(location,(1,),(0,1),(0,),((0,1),),False,name=='multiway',0.)
        def call():
            trace.clear()
            try:
                result = localize(function,switch);status='returned';reason='localized'
            except ValueError as error:
                result=None;status='rejected';reason=str(error)
            return status,reason,primitive(result),list(trace)
        plain = call()
        with Observer(lambda *_:None).enabled():
            observed = call()
        preserved = plain == observed
        # Independent algebraic identities defining the frozen controls.
        u=F(1,2); eps=F(1,2**20)
        analytic = {
            'simple_crossing': u-F(1,2)==0,
            'tangent': (u-F(1,2))**2==0 and (u-F(1,2)+eps)**2>0,
            'near_double': F(1,2**100)>0,
            'nearby_roots': eps**2-F(1,2**40)==0,
            'endpoint': F(0)==0 and F(1)>0,
            'onset_switch': max(F(-1),F(0))==0 and max(F(1),F(0))>0,
            'tiny_interval': F.from_float(math.nextafter(.5,-math.inf)) < F(1,2)-F(1,2**60) < F.from_float(math.nextafter(.5,math.inf)),
            'nonzero_interior': F(0)*(1-F(0))==0 and u*(1-u)>0 and F(1)*(1-F(1))==0,
            'multiway': u-F(1,2)==F(1,2)-u==0,
        }
        if name in ('duplicates','true_interval'):
            first=Expanding((0.,0.),(20.,0.),(5.,1.))
            second=Expanding((0.,0.),(20.,0.),(5.,-1.) if name=='duplicates' else (6.,2.))
            ref=reference(first,second,.5 if name=='duplicates' else 0.,.75 if name=='duplicates' else .1,
                          deadline=time.monotonic()+60,sink=lambda *_:None)
            reference_passed=ref['complete'] and ref['topology']==topologies[i]
        else:
            reference_passed=analytic[name]
        expected = expected_behavior.get(name, ('rejected', 'switch_sign_transition_invalid'))
        behavior_valid = plain[:2] == expected
        # Test the actual engineering function against exact polynomial evaluations.
        # Quarter/half/endpoints and dyadic root offsets have exact input meanings.
        if name not in ('duplicates', 'true_interval'):
            def exact_difference(t):
                u = t-F(1,2)
                return {
                    'simple_crossing': u, 'tangent': u*u,
                    'near_double': u*u+F(1,2**100),
                    'nearby_roots': u*u-F(1,2**40), 'endpoint': t,
                    'onset_switch': max(u,F(0)), 'tiny_interval': u+F(1,2**60),
                    'nonzero_interior': t*(1-t), 'multiway': 2*u,
                }[name]
            points = (F(0),F(1,4),F(1,2)-F(1,2**20),F(1,2),F(1,2)+F(1,2**20),F(1))
            matrix = function(np.array([float(t) for t in points]))
            for t, evaluated in zip(points,matrix,strict=True):
                expected_float = float(exact_difference(t))
                reference_passed &= float(evaluated[0]-evaluated[1]) == expected_float
        evidence=dict(fixture=name,plain=plain,observed=observed,analytic_topology=topologies[i],expected_roots=roots[i],expected_behavior=expected,behavior_valid=behavior_valid)
        h=sink('control_'+name,evidence)
        rows.append(dict(fixture=name,family='expanding' if i in (0,6) else 'engineering',
          topology=topologies[i],expected_roots=roots[i],observed_status=plain[0],observed_reason=plain[1],
          reference_passed=bool(reference_passed),observation_preserved=preserved,
          passed=bool(reference_passed and preserved and behavior_valid),evidence_sha256=h))
    return rows
