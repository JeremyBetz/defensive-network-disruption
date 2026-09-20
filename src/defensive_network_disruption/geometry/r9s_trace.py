"""R9S observation and retained-record analysis; no numerical repair or loader."""
from contextlib import contextmanager
from fractions import Fraction
import math
import struct
import sys


def binary(value):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError('nonfinite_trace')
    return {'value': value, 'bits': struct.pack('>d', value).hex()}


def number(value):
    if set(value) != {'value', 'bits'} or type(value['value']) is not float:
        raise ValueError('binary_schema')
    if binary(value['value']) != value:
        raise ValueError('binary_bits')
    return value['value']


def key(value):
    if not 0 <= value <= 1 or not math.isfinite(value):
        raise ValueError('parameter_domain')
    return int(binary(value)['bits'], 16)


def fraction(value):
    if set(value) != {'numerator_hex', 'denominator_hex'}:
        raise ValueError('rational_schema')
    a, b = int(value['numerator_hex'], 16), int(value['denominator_hex'], 16)
    if b <= 0:
        raise ValueError('rational_denominator')
    return Fraction(a, b)


def rational(value):
    return {'numerator_hex': format(value.numerator, 'x'),
            'denominator_hex': format(value.denominator, 'x')}


def sign(value):
    return 0 if value == 0 else -1 if value < 0 else 1


def relation(point, reference):
    """Compare stored coordinates only; never evaluate a reference function."""
    t = Fraction.from_float(point)
    a, b = map(fraction, reference['enclosure'])
    lower, upper = (Fraction.from_float(number(x)) for x in reference['outer'])
    root_relation = 'outside_authority' if not lower <= t <= upper else (
        'before' if t < a else 'after' if t > b else 'inside')
    excluded = reference.get('excluded')
    return {'root_relation': root_relation,
            'excluded_region': None if excluded is None else
            fraction(excluded[0]) <= t <= fraction(excluded[1])}


class ObservationFailure(RuntimeError):
    pass


class Observer:
    """Scoped profile hook; reads actual return values and does not add probes."""
    def __init__(self, sink, reference, structures, *, engineering=False):
        from . import r9r_localization as original
        from .occlusion_fields import CarrierOriginField
        self.original = original
        self.codes = {'inspection': original.inspect_production.__code__,
                      'pair': original.old._pair.__code__,
                      'row': original.old._row.__code__,
                      'field': CarrierOriginField.individual_values.__code__}
        self.sink, self.reference, self.structures = sink, reference, structures
        self.engineering = engineering
        self.active = None
        self.pending = None
        self.windows = []
        self.probes = []
        self.attempts = []
        self.errors = []
        self.arguments = self.final = None
        self.inspections = 0

    def write(self, label, value, *, original_unwinding=False):
        try:
            self.sink(label, value)
        except BaseException as error:
            self.errors.append({'type': type(error).__name__, 'message': str(error)})
            if not original_unwinding:
                raise ObservationFailure('trace_persistence_failed') from error

    def __call__(self, frame, event, arg):
        code = frame.f_code
        if code is self.codes['inspection']:
            if event == 'call':
                self.inspections += 1
                if self.inspections != 1:
                    raise ObservationFailure('second_inspection')
                self.active = frame
                f = frame.f_locals
                self.arguments = {'pair': list(f['pair']), 'enclosure': [rational(f['a']), rational(f['b'])],
                                  'outer': [binary(f['lower']), binary(f['upper'])],
                                  'before': f['before_sign'], 'after': f['after_sign']}
                self.write('arguments', self.arguments)
            elif event == 'return':
                f = frame.f_locals
                cache = f.get('cache', {})
                self.final = {'lo': f.get('lo'), 'hi': f.get('hi'),
                              'cache': [[k, v] for k, v in sorted(cache.items())],
                              'returned': arg is not None,
                              'transition': None if arg is None else {
                                  name: binary(getattr(arg, name)) if getattr(arg, name) is not None else None
                                  for name in ('last_pre', 'zero_start', 'zero_end', 'first_post')}}
                self.write('final_cache', self.final, original_unwinding=arg is None)
                self.active = None
        elif self.active is not None:
            if code is self.codes['pair'] and event == 'call':
                caller = frame.f_back
                if caller is not self.active:
                    raise ObservationFailure('unexpected_pair_caller')
                f = caller.f_locals
                window = [f['lo'], f['hi']]
                if not self.windows or self.windows[-1]['bounds'] != window:
                    row = {'ordinal': len(self.windows), 'bounds': window}
                    self.write('window', row)
                    self.windows.append(row)
                point = float(frame.f_locals['point'])
                attempt = {'ordinal': len(self.attempts), 'window': len(self.windows)-1,
                           'key': key(point), 'parameter': binary(point)}
                self.write('probe_attempt', attempt)
                self.attempts.append(attempt)
                self.pending = {'attempt': attempt, 'values': None, 'owners': None,
                                'branches': None}
            elif code is self.codes['field'] and event == 'return' and arg is not None and self.pending:
                f = frame.f_locals
                if f['self'].candidate != 'expanding':
                    raise ObservationFailure('wrong_candidate')
                self.pending['branches'] = [
                    {'ell': binary(f['ell'][0, i]), 'clipped': binary(f['t'][0, i]),
                     'branch': 'inactive' if f['ell'][0, i] <= 0 else
                               'full' if f['ell'][0, i] >= 1 else 'smoothstep'}
                    for i in self.arguments['pair']]
            elif code is self.codes['row'] and event == 'return' and arg is not None and self.pending:
                self.pending['values'] = [binary(arg[i]) for i in self.arguments['pair']]
                self.pending['owners'] = list(self.original.owner.owners(arg))
            elif code is self.codes['pair'] and event == 'return' and arg is not None and self.pending:
                p = self.pending
                t = number(p['attempt']['parameter'])
                if p['values'] is None or (p['branches'] is None and not self.engineering):
                    raise ObservationFailure('missing_observation')
                branch = p['branches'] if not self.engineering else {'kind': 'engineering'}
                row = {**p['attempt'], 'values': p['values'], 'difference': binary(arg),
                       'sign': sign(arg), 'branches': branch, 'owners': p['owners'],
                       'structural': structural_relation(t, self.structures),
                       'reference': relation(t, self.reference)}
                self.write('probe', row)
                self.probes.append(row)
                self.pending = None
        return None

    @contextmanager
    def enabled(self):
        if sys.getprofile() is not None:
            raise ObservationFailure('existing_profile')
        sys.setprofile(self)
        try:
            yield self
        finally:
            sys.setprofile(None)


def structural_relation(t, structures):
    return {'onset_equal': [i for i, x in enumerate(structures['onsets']) if t == number(x)],
            'tie_memberships': [i for i, pair in enumerate(structures['ties'])
                                if number(pair[0]) <= t <= number(pair[1])],
            'status': structures['status']}


def check_trace(trace):
    """Independent stored-record checks; no field call, root search or geometry."""
    required = {'schema_version', 'arguments', 'reference', 'structures', 'windows',
                'attempts', 'probes', 'final', 'sorted_ordinals', 'outcome', 'observer_errors'}
    if set(trace) != required or trace['schema_version'] != 1:
        raise ValueError('trace_schema')
    outcome=trace['outcome']
    if set(outcome)!={'returned','exception','message'} or type(outcome['returned'])is not bool or (outcome['returned'] and (outcome['exception'] is not None or outcome['message'] is not None)) or (not outcome['returned'] and (type(outcome['exception'])is not str or type(outcome['message'])is not str)):raise ValueError('outcome_schema')
    ref=trace['reference'];structures=trace['structures']
    if set(ref)!={'enclosure','outer','one_crossing','strict_derivative','authority_valid','boundary_refuted','excluded'} or any(type(ref[k])is not bool for k in ('one_crossing','strict_derivative','authority_valid','boundary_refuted')):raise ValueError('reference_schema')
    if set(structures)!={'onsets','ties','status'} or structures['status']not in ('engineering','uncertified'):raise ValueError('structure_schema')
    a, w, probes, final = (trace[x] for x in ('arguments', 'windows', 'probes', 'final'))
    if set(a) != {'pair', 'enclosure', 'outer', 'before', 'after'}:
        raise ValueError('argument_schema')
    if a['before'] not in (-1, 1) or a['after'] != -a['before']:
        raise ValueError('orientation')
    if len(a['pair']) != 2 or len(set(a['pair'])) != 2 or any(type(x) is not int or x < 0 for x in a['pair']):
        raise ValueError('pair_schema')
    outer = [key(number(x)) for x in a['outer']]
    isolated = list(map(fraction, a['enclosure']))
    if not 0 <= isolated[0] <= isolated[1] <= 1 or not outer[0] < outer[1]:
        raise ValueError('argument_domain')
    initial = [max(outer[0], key(float(isolated[0]))-16),
               min(outer[1], key(float(isolated[1]))+16)]
    if len(trace['attempts']) < len(probes) or len(trace['attempts']) > len(probes)+1:
        raise ValueError('attempt_count')
    seen = set(); expected = []; previous = None
    for ordinal, window in enumerate(w):
        if set(window) != {'ordinal', 'bounds'} or window['ordinal'] != ordinal:
            raise ValueError('window_schema')
        lo, hi = window['bounds']
        if any(type(x) is not int for x in (lo, hi)) or not outer[0] <= lo <= hi <= outer[1] or hi-lo+1 > 65536:
            raise ValueError('window_bounds')
        if previous is None:
            if [lo, hi] != initial: raise ValueError('initial_window')
        else:
            width = max(16, previous[1]-previous[0]+1)
            if [lo, hi] != [max(outer[0], previous[0]-width), min(outer[1], previous[1]+width)]:
                raise ValueError('widening_rule')
        expected.extend((ordinal, k) for k in range(lo, hi+1) if k not in seen)
        seen.update(range(lo, hi+1)); previous = [lo, hi]
    keys = []
    for ordinal, p in enumerate(probes):
        if set(p) != {'ordinal','window','key','parameter','values','difference','sign','branches','owners','structural','reference'}:
            raise ValueError('probe_schema')
        if p['ordinal'] != ordinal or ordinal >= len(expected) or (p['window'], p['key']) != expected[ordinal]:
            raise ValueError('probe_order')
        attempt = {k:p[k] for k in ('ordinal','window','key','parameter')}
        if trace['attempts'][ordinal] != attempt or key(number(p['parameter'])) != p['key']:
            raise ValueError('probe_attempt')
        if len(p['values']) != 2:
            raise ValueError('pair_values')
        x,y = map(number,p['values']); delta=number(p['difference'])
        if type(p['sign'])is not int or binary(x-y) != p['difference'] or p['sign'] != sign(delta):
            raise ValueError('probe_difference')
        if p['reference'] != relation(number(p['parameter']), trace['reference']) or p['structural'] != structural_relation(number(p['parameter']),trace['structures']):
            raise ValueError('probe_relation')
        if type(p['owners']) is not list or p['owners'] != sorted(set(p['owners'])) or any(type(x)is not int or x<0 for x in p['owners']):
            raise ValueError('owner_schema')
        if p['branches'] != {'kind':'engineering'}:
            if type(p['branches']) is not list or len(p['branches']) != 2: raise ValueError('branch_schema')
            for item in p['branches']:
                if set(item) != {'ell','clipped','branch'}:raise ValueError('branch_schema')
                ell,u=number(item['ell']),number(item['clipped'])
                branch='inactive' if ell<=0 else 'full' if ell>=1 else 'smoothstep'
                if item['branch']!=branch or u!=min(1.,max(0.,ell)):raise ValueError('branch_value')
        keys.append(p['key'])
    for ordinal,attempt in enumerate(trace['attempts']):
        if set(attempt)!={'ordinal','window','key','parameter'} or attempt['ordinal']!=ordinal or ordinal>=len(expected) or (attempt['window'],attempt['key'])!=expected[ordinal] or key(number(attempt['parameter']))!=attempt['key']:raise ValueError('attempt_schema_or_order')
    if len(keys)!=len(set(keys)) or trace['sorted_ordinals']!=sorted(range(len(probes)),key=lambda i:keys[i]):
        raise ValueError('sorted_trace')
    complete = not trace['observer_errors'] and final is not None and len(probes)==len(expected)==len(trace['attempts']) and bool(w)
    if final is not None:
        if set(final)!= {'lo','hi','cache','returned','transition'} or type(final['returned'])is not bool:raise ValueError('final_schema')
        if final['cache'] != sorted([[p['key'],p['sign']] for p in probes]):raise ValueError('final_cache')
        complete &= [final['lo'],final['hi']]==w[-1]['bounds'] if w else False
    signs=[probes[i]['sign'] for i in trace['sorted_ordinals']]
    zero_runs=sum(s==0 and (i==0 or signs[i-1]!=0) for i,s in enumerate(signs))
    nonzero=[s for s in signs if s]
    reversals=sum(a!=b for a,b in zip(nonzero,nonzero[1:]))
    full_outer=bool(w) and w[-1]['bounds']==outer and complete
    limited=trace['outcome']['exception'] in ('TimeoutError','DeadlineExceeded','ObservationFailure') or trace['outcome']['message']=='binary64_inspection_limit'
    pattern=pattern_for(signs,complete and not limited,full_outer)
    return {'complete':bool(complete),'count':len(probes),'attempts':len(trace['attempts']),
            'windows':len(w),'zeros':signs.count(0),'zero_runs':zero_runs,'reversals':reversals,
            'ternary_changes':sum(x!=y for x,y in zip(signs,signs[1:])),
            'pattern':pattern,'outer_covered':bool(full_outer),'limited':limited}


def pattern_for(signs,complete,full_outer):
    if not complete or not signs or not signs[0] or not signs[-1]:return 'H'
    nz=[s for s in signs if s]; reversals=sum(a!=b for a,b in zip(nz,nz[1:]))
    zeros=[i for i,s in enumerate(signs) if s==0]
    if not zeros:
        if reversals==0:return 'G' if full_outer else 'H'
        if reversals==1:return 'A' if signs[0]<0 else 'B'
        return 'E'
    first,last=zeros[0],zeros[-1]
    clean=(zeros==list(range(first,last+1)) and len(set(signs[:first]))==1 and len(set(signs[last+1:]))==1)
    if clean and len(zeros)==1:return 'D'
    if clean and signs[0]!=signs[-1]:return 'C'
    return 'F'


def summarize(trace,*,retained=False):
    result=check_trace(trace);pattern=result['pattern'];ref=trace['reference']
    supported=ref['one_crossing'] and ref['strict_derivative'] and ref['authority_valid']
    reproduced=(trace['outcome']=={'returned':False,'exception':'VerificationError','message':'binary64_nonmonotone_unresolved'} and result['count']==65)
    clean=pattern in ('A','B','C','D')
    probes=[trace['probes'][i] for i in trace['sorted_ordinals']]
    oriented=bool(probes) and probes[0]['sign']==trace['arguments']['before'] and probes[-1]['sign']==trace['arguments']['after']
    inside=all(p['reference']['root_relation']!='outside_authority' for p in probes)
    incompatible=bool(ref['boundary_refuted'])
    compatibility='INCOMPATIBLE' if incompatible else 'COMPATIBLE' if clean and supported and oriented and inside else 'AMBIGUOUS'
    # Mechanism claims require positive evidence. No convenience BA/BB fallback.
    if retained and reproduced and result['complete'] and supported and oriented and inside and not incompatible and pattern in ('E','F'):
        diagnosis,readiness='BC',1
    elif retained and reproduced and result['complete'] and incompatible:
        diagnosis,readiness='BD',1
    else:
        diagnosis,readiness='BF',2 if result['complete'] else 3
    return {**result,'reproduced':reproduced if retained else None,
            'mathematical_support':bool(supported),'compatibility':compatibility,
            'diagnosis':diagnosis,'readiness':readiness,
            'causal_attribution':'unavailable','operational_repair':'unresolved'}
