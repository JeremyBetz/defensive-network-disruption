"""Observe the unchanged R9I numerical route; no empirical loading or repair."""
from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
from dataclasses import asdict
from fractions import Fraction
import math
import signal
import sys
import time
import traceback

import numpy as np

from . import r9e_representation as route
from . import onset_owner_certification as owner
from . import production_verification as pv
from .comparator_reproduction import structure_record, partition_audit
from .integration_review import values_for_components
from .verification_audit import controlled_vector, scalar_oracle
from .micro_interval_verifier import IntegralInterval
from ..validation.independent_certificate_verifier import PieceEvidence


class DiagnosticTimeout(RuntimeError):
    pass


class Budget:
    def __init__(self, seconds=3600, operation=600):
        self.started = time.monotonic()
        self.deadline = self.started+seconds
        self.operation = operation

    def arm(self):
        remaining = self.deadline-time.monotonic()
        if remaining <= 0: raise DiagnosticTimeout("numerical_budget")
        signal.setitimer(signal.ITIMER_REAL, min(self.operation, remaining))

    @contextmanager
    def limit(self):
        if signal.getitimer(signal.ITIMER_REAL)[0]: raise RuntimeError("nested_timer")
        previous = signal.getsignal(signal.SIGALRM)
        def expired(*_): raise DiagnosticTimeout("operation_or_global_budget")
        signal.signal(signal.SIGALRM, expired)
        self.arm()
        try: yield
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous)


def primitive(value):
    if type(value) is Fraction:
        return {"numerator_hex": format(value.numerator, "x"), "denominator_hex": format(value.denominator, "x")}
    if value is None or type(value) in (bool, str, int): return value
    if isinstance(value, (float, np.floating)):
        x = float(value)
        if not math.isfinite(x): raise ValueError("nonfinite_capture")
        return x
    if isinstance(value, np.integer): return int(value)
    if isinstance(value, np.ndarray): return primitive(value.tolist())
    if type(value) in (IntegralInterval, PieceEvidence): return primitive(asdict(value))
    if isinstance(value, (list, tuple)): return [primitive(x) for x in value]
    if type(value) is dict: return {str(k): primitive(v) for k, v in value.items()}
    raise TypeError("unsupported_diagnostic_type:"+type(value).__name__)


def pairwise_differences(estimates):
    """Private point-estimate diagnostics, distinct from interval gate decisions."""
    names=tuple(estimates)
    result={}
    for i,first in enumerate(names):
        for second in names[i+1:]:
            a,b=float(estimates[first]),float(estimates[second])
            if not math.isfinite(a) or not math.isfinite(b):raise ValueError('nonfinite_comparison')
            absolute=abs(a-b);scale=max(abs(a),abs(b))
            result[first+'_vs_'+second]={'absolute':absolute,'relative':None if scale==0 else absolute/scale}
    return result


class Observer:
    def __init__(self, sink):
        self.sink = sink; self.saved = {}; self.calls = Counter(); self.inclusive = Counter()
        self.starts = {}; self.pieces = []; self.quad = []; self.integrals = []; self.gates = []
        self.vectors = []; self.stage = None; self.stage_times = []; self.stage_start = None
        self.codes = {controlled_vector.__code__: "controlled", values_for_components.__code__: "vector",
            owner.canonical_geometry.__code__: "structure", route._piece.__code__: "piece",
            route._integrate.__code__: "integrate", route.independent_maximum.__code__: "maximum",
            route.quad.__code__: "quad", pv.require.__code__: "require",
            route._runtime_request.__code__: "request", route._certify_observation.__code__: "certificate"}

    def save(self, label, value): self.sink(label, primitive(value))

    def profile(self, frame, event, arg):
        name = self.codes.get(frame.f_code)
        if name is None: return
        key = id(frame); local = frame.f_locals
        if event == "call":
            self.calls[name] += 1; self.starts[key] = time.perf_counter()
            if name == "require" and local.get("reason") == "piecewise_unsplit":
                parent = frame.f_back
                if parent.f_code is not route.independent_maximum.__code__:
                    raise RuntimeError("incorrect_gate_route")
                data = {k: parent.f_locals[k] for k in ("strict", "repeat", "onset_interval", "structural", "onset_partitions")}
                data["condition"] = bool(local["condition"])
                self.gates.append(data); self.save("gate_inputs", data)
        elif event == "return":
            self.inclusive[name] += time.perf_counter()-self.starts.pop(key, time.perf_counter())
            if name == "piece" and "caught" in local:
                evidence = {"stage": self.stage, "lower": local["lower"], "upper": local["upper"],
                            "tolerance": local["tolerance"], "estimate": local.get("value"), "error": local.get("error"),
                            "warnings": [{"class": f"{x.category.__module__}.{x.category.__name__}", "message": str(x.message)} for x in local["caught"]],
                            "result": arg}
                self.pieces.append(evidence); self.save("piece", evidence)
            if arg is None: return
            if name == "controlled":
                self.saved["controlled"] = arg; self.save("controlled", {"resolution": arg[0], "estimates": arg[1], "change": arg[2]})
            elif name == "vector":
                data = {"resolution": local["intervals"], "estimates": arg}
                self.vectors.append(data); self.save("vector", data)
            elif name == "structure":
                self.saved["structure"] = arg; self.sink("structure", structure_record(arg))
            elif name == "integrate":
                data = {"stage": self.stage, "partitions": local["partitions"], "interval": arg[0], "evidence": arg[1], "pieces": local["evidence"]}
                self.saved[self.stage] = arg
                self.integrals.append(data); self.save("integral", data)
            elif name == "quad":
                data = {k: local[k] for k in ("a", "b", "epsabs", "epsrel", "limit")}
                data.update(stage=self.stage, estimate=arg[0], error=arg[1])
                self.quad.append(data); self.save("quad_return", data)
            elif name == "certificate":
                self.save("certificate", {"estimate": local["estimate"], "warning_class": local["warning_class"], "warning_hash": local["warning_hash"], "result": arg})

    @contextmanager
    def observing(self):
        old = sys.getprofile()
        if old is not None: raise RuntimeError("existing_profile_hook")
        sys.setprofile(self.profile)
        try: yield
        finally: sys.setprofile(old)


def reproduce(candidate, row, root, sink, budget):
    observed = Observer(sink)
    def stage(**detail):
        now = time.perf_counter()
        if observed.stage_start is not None:
            observed.stage_times.append({"stage": observed.stage, "seconds": now-observed.stage_start})
        observed.stage = detail["stage"]
        observed.save("stage", detail)
        budget.arm(); observed.stage_start = time.perf_counter()
    failure = None; result = None; started = time.perf_counter()
    with budget.limit(), observed.observing():
        try:
            result = route.evaluate_edge(candidate, row["carrier"], row["receiver"], row["defenders"],
                root=root, authority_context={"alias": row["alias"], "state": "4", "edge": "7"}, record=stage)
        except pv.GateFailure as error:
            failure = str(error)
            observed.save("original_failure", {"exception": type(error).__name__, "message": failure,
                                              "traceback": "".join(traceback.format_exception(error)), "stage": observed.stage})
    if observed.stage_start is not None:
        observed.stage_times.append({"stage": observed.stage, "seconds": time.perf_counter()-observed.stage_start})
    reproduced = (failure == "piecewise_unsplit" and observed.stage == "onset_adaptive" and
                  len(observed.gates) == 1 and observed.gates[0]["condition"] is False and
                  observed.calls["controlled"] == 1 and observed.calls["structure"] == 2)
    observed.save("reproduction", {"reproduced": reproduced, "candidate": candidate, "failure": failure,
        "returned": result is not None, "calls": dict(observed.calls), "inclusive": dict(observed.inclusive),
        "stage_times": observed.stage_times, "wall": time.perf_counter()-started})
    return reproduced, observed, failure


def audit(observed, row):
    structure = observed.saved["structure"]
    result = partition_audit(structure)
    parts = structure[2]
    result["exact_coverage"] = sum((Fraction.from_float(b)-Fraction.from_float(a) for a,b in zip(parts, parts[1:])), Fraction(0)) == 1
    routing = observed.saved["strict_piecewise"][0]
    result["routing_valid"] = (routing.structural_piece_count == result["pieces"] and
        routing.bounded_piece_count == result["bounded"] and
        routing.quadrature_piece_count + routing.bounded_piece_count == result["pieces"])
    field = route.CarrierOriginField("constant_width")
    b = np.asarray(row["carrier"]); r = np.asarray(row["receiver"]); ds = np.asarray(row["defenders"])
    points = {0.0, 1.0}
    for onset in structure[0]:
        points.update((float(np.nextafter(onset.canonical, -math.inf)), onset.canonical,
                       float(np.nextafter(onset.canonical, math.inf))))
    for witness in structure[4]: points.update((witness.before, witness.canonical, witness.after))
    samples = []
    for t in sorted(points):
        q = b+t*(r-b); values = field.individual_values(b, ds, q[None, :])[0]
        oracle = np.asarray([scalar_oracle("constant_width", b, d, q) for d in ds])
        # Preserve the existing scalar-oracle absolute/relative authority.
        agree = bool(np.allclose(values, oracle, atol=1e-12, rtol=1e-12))
        samples.append({"t": t, "values": values, "oracle": oracle, "agree": agree})
    observed.save("oracle_samples", samples)
    result["scalar_oracle"] = all(x["agree"] for x in samples)
    result["passed"] = bool(result["passed"] and result["exact_coverage"] and result["routing_valid"] and result["scalar_oracle"])
    observed.save("partition_audit", result)
    return result
