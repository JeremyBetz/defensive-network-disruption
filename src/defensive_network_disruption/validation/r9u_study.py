#!/usr/bin/env python3
"""One-shot Session 14R9U label-free empirical execution."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import importlib.util
import itertools
import io
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
from importlib.metadata import version

ROOT = Path(__file__).resolve().parents[3]

from defensive_network_disruption.data.representation_projection import ALIASES, COUNTS, project_line
from defensive_network_disruption.geometry.occlusion_fields import CANDIDATES
from defensive_network_disruption.geometry import production_verification as pv
from defensive_network_disruption.geometry.r9t_adapter import evaluate_edge
from defensive_network_disruption.geometry.representation_study import (
    block_ranks, discordant_pairs, follows, maximum_set, order_categories, spearman)
from defensive_network_disruption.networks.defender_edges import map_defender_edges, summarize_edge_involvement
from defensive_network_disruption.networks.options import OptionState
from defensive_network_disruption.validation.launch_enforcement import EnvironmentObservation, PrerequisiteExpectation
from defensive_network_disruption.validation.r3_launch import test_record, strict_prerequisite
from defensive_network_disruption.validation.r7_execution import Journal, Launch, Progress, durable_write
from defensive_network_disruption.validation import numerical_failure_publication as numerical_publication
from defensive_network_disruption.validation.r9a_publication import PUBLIC_ARTIFACTS
from defensive_network_disruption.validation.r9j_linear_publication import review as linear_review, validate_public as validate_linear_public
from defensive_network_disruption.validation.checkpoint_ci_authority import (
    CIExpectation, FailureController, validate_receipt)
from defensive_network_disruption.validation.r9o_terminal import TerminalClosure


START = "5fb13b22f18c52498c88533314fd5f265493dc0e"
TAG = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
POP_SHA = "cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d"
POP = Path("outputs/receiver_ranking_m0_m1/local/population.jsonl")
PROTOCOL = Path("docs/protocols/phase_14r9u_empirical_representation_retry.md")
OUT = Path(os.environ.get("SESSION14R9U_OUTPUT", "outputs/continuous_occlusion_empirical_retry_r9u"))
LOCAL = OUT / "local"
R9 = Path("outputs/continuous_occlusion_empirical_retry_r9")
R9A = Path("outputs/continuous_occlusion_empirical_retry_r9a")
TEST_COMMAND = ("-m", "unittest", "discover", "-s", "tests", "-p", "test_session14r9u.py")
CI_RECEIPT = LOCAL / "checkpoint_ci_receipt.json"
CI_RECEIPT_HASH = LOCAL / "checkpoint_ci_receipt.json.sha256"
INHERITED_PUBLIC = (
    "preaccess_contract.json", "retained_observation_certificate_gate.json",
    "runner_failure_oracles.json", "runner_success_oracle.json",
    "synthetic_acceptance.json", "evidence_type_summary.json", "visual_qa.json",
    "synthetic_stress_summary.json", "synthetic_field_comparison.svg",
)
CSV_FILES = (
    "candidate_pair_comparison.csv", "structural_correspondence.csv",
    "receiver_corridor_ordering.csv", "union_vs_max.csv", "overlap_redundancy.csv",
    "multi_edge_summary.csv", "match_summary.csv",
)
FINAL_FILES = tuple(name for name in PUBLIC_ARTIFACTS if name != "manifest.json")
CODE = (
    "scripts/session_14r9u_empirical_representation_retry.py",
    "src/defensive_network_disruption/validation/r9u_study.py",
    "src/defensive_network_disruption/geometry/r9t_adapter.py",
    "src/defensive_network_disruption/geometry/r9t_transition.py",
    "src/defensive_network_disruption/geometry/r9r_adapter.py",
    "src/defensive_network_disruption/geometry/r9r_localization.py",
    "src/defensive_network_disruption/geometry/r9k_comparator.py",
    "src/defensive_network_disruption/validation/r9j_linear_publication.py",
    "src/defensive_network_disruption/validation/r9o_terminal.py",
    "src/defensive_network_disruption/validation/checkpoint_ci_authority.py",
    "tests/test_session14r9u.py",
)
HISTORICAL = {
    "docs/session_14r9j_r9i_blocker_diagnosis.md": "7b1f4a2ddd0c4b8dc3030aa156c7a4fe058298b0132a3934bf0a95c767af2465",
    "docs/session_14r9k_onset_only_comparator_repair.md": "3796f1e1403e7954e06a2a20213ee8cdf76c4b023dbc7f0e11d5e3f55e62519f",
    "docs/protocols/phase_14r9j_r9i_blocker_diagnosis.md": "8c205e768840260dc81ea7bb000d8edaa143de75eb0158d3a80bb7f3e43de9dd",
    "docs/protocols/phase_14r9k_onset_only_comparator_repair.md": "a065af8026f1e4e0da8387b0a3d354d8c24adc6447df83167b6922e1aab56f36",
    "outputs/continuous_occlusion_r9i_blocker_diagnosis/manifest.json": "cbe421fe0fec781e2456e811806e437ad0dc711f958f05a0d9f1ed7d13602a96",
    "outputs/continuous_occlusion_onset_comparator_repair/manifest.json": "bb50db6e665a13089d76079216bdd2a28596e98c7dbb97281807be39d81e6df5",
    "docs/session_14r9m_preaccess_authority_traceback_repair.md": "995378793b2bcd20a553190c7227fed42de8655273de956c5739c303d331baf2",
    "docs/protocols/phase_14r9m_preaccess_authority_traceback_repair.md": "4c17117ae483ffddcaa4859de292cba795a8682754f15474df811b007c7b1e28",
    "outputs/continuous_occlusion_preaccess_authority_repair/manifest.json": "222364223e3c6a9b4b9a91605794593d4ddacf2a42ba3cf509c2bd4ad0f41e26",
    "docs/session_14r9p_retained_journal_authority_reconciliation.md": "39afc9785f66e37c772d5499068b0dfb124469573593d60768ca883a043f65a6",
    "docs/protocols/phase_14r9p_retained_journal_authority_reconciliation.md": "5a8f39510d87454e02e0523ee562a595adf2f447ca9eb7dd1381d39d35df80a3",
    "outputs/continuous_occlusion_retained_journal_authority/manifest.json": "fdac49eece5fe3f2d545561bec1a98d73534a31c3a692705903fd58539f655f7",
    "docs/session_14r9q_expanding_switch_equality_diagnosis.md": "e378019d005cceba0f8d310741930b865dadf4a97d1987ae9400e9796ee1879e",
    "docs/protocols/phase_14r9q_expanding_switch_equality_diagnosis.md": "71a7268cc5f8c793a964eb31dab576b68b87c45e787ff167678bee0ca7d74651",
    "outputs/continuous_occlusion_expanding_switch_equality_diagnosis/manifest.json": "8d24c86ac54f8e2484dc7f77e796650cdfbe223eefaa0ce00cf4b9e223de1bc6",
    "docs/session_14r9r_switch_localization_repair.md": "14dae860c82471b355537c8575c07231203eabc9f248b4e1651de9b1c48b9870",
    "docs/protocols/phase_14r9r_switch_localization_repair.md": "55efc2d087904e6d2f13e203089022c22c812c4f5327e98f4efd0e228865ccfa",
    "outputs/continuous_occlusion_switch_localization_repair/manifest.json": "448b3a389b29b4d6a7e447cb8f72bf3b47a1061d39f85079ed978f1ac0281b07",
    "docs/session_14r9s_binary64_transition_trace_diagnosis.md": "86543925eaa01b9674de10d712e8b4202f16f10652f9dd50e7e34bb540f84206",
    "docs/protocols/phase_14r9s_binary64_transition_trace_diagnosis.md": "ae135b538eb2efbb722354cedd471ed25b56f5a44fa6e14e458c4e0e5b24aa05",
    "outputs/continuous_occlusion_binary64_transition_trace/manifest.json": "512901bfc5a56f2ae2afe9693149cad4a29c01e2fb7bb5c03878ff7948183aaa",
    "docs/session_14r9t_binary64_transition_contract_repair.md": "c459e09148bfbba070bc6a6d7eb7ce90ee39444f8c0896c5f298fff7199ffed8",
    "docs/protocols/phase_14r9t_binary64_transition_contract_repair.md": "f836d89afef8f4d053c20f4daf4d2c622a38e6ed91a5561d1c063931d7a93597",
    "outputs/continuous_occlusion_binary64_transition_contract_repair/manifest.json": "46a287059a94ae648254125771c06d8981de1f29b26f2c235ae86c25230c4c22",
    "src/defensive_network_disruption/geometry/r9t_adapter.py": "a40ce1af558d43bb0241d876c2a8dd3a0bcd9c57e457de6299bf1e70c9635aa1",
    "src/defensive_network_disruption/geometry/r9t_transition.py": "49991467b8492baf00a7588e2422c1ee8620aeb3b14cdf3b3601262a46e488c5",
    "src/defensive_network_disruption/geometry/r9r_adapter.py": "3327ce48954aed89124b3e2f9fbcb015591a4173146489342d2377fda0576941",
    "src/defensive_network_disruption/geometry/r9r_localization.py": "9768323ec258c18949faa1798781d6f67b635ad34c7d08d698ff67c8f8c11070",
    "src/defensive_network_disruption/geometry/r9k_comparator.py": "e5f0785f29a78e84c64c86266012aa5c9d9be462be382927de900cfdc979973b",
    "src/defensive_network_disruption/validation/r9j_linear_publication.py": "a242cb0921d1fd390cd2b74c9d15a0fdff3e2b82e46000dc8be0cbbba6d6c139",
    "src/defensive_network_disruption/validation/r9o_terminal.py": "90bc776409b41017b836ae07e04ff0a1a3c6e7241b53c9fe0087fb0808c3840f",
    "src/defensive_network_disruption/validation/checkpoint_ci_authority.py": "d66328abab8f0aa059fc84c405a409f5d6b621b8276561f127cc8789b0e1068b",
    "docs/protocols/phase_14r9_continuous_occlusion_empirical_retry.md": "e0ec4e3a3a92307c98970c8967426c7d908bd523345f8d1e8c5940495944bc61",
    "scripts/session_14r9_occlusion_study.py": "21d7cb219fcef9884700e119d15e2c9e131fb08485d1d1ed8d271b434cbb7912",
    "src/defensive_network_disruption/geometry/r7_representation.py": "b3de1fb1432ae97617d4a29c11694eba3b88e01dda0ba68be60b410372b8c542",
    "src/defensive_network_disruption/validation/r9_certificate_orchestration.py": "64268899b3e6f146e033dfe78f424d589dedc1101253e27d2b442f36e0f5a66a",
    "src/defensive_network_disruption/validation/independent_certificate_verifier.py": "be73a070e4dc290d2697f98146f495a9f4a05dfcf9b256ca57b255414e337789",
    "outputs/continuous_occlusion_empirical_retry_r9/manifest.json": "4673ac2a12847f4b52944e5913ed3b7c8df9fb29f83a19696b40c259b0819d87",
    "outputs/continuous_occlusion_empirical_retry_r9/preaccess_contract.json": "ddda6154b493b0acc4e6576a73d30c81011bfc716ae3f812f2cf431801ce6aa0",
    "outputs/continuous_occlusion_empirical_retry_r9/retained_observation_certificate_gate.json": "3f40a16e967d3a3f38f26185517dd692a85bd13797c89cfd4a05a9179c8265c7",
    "outputs/continuous_occlusion_empirical_retry_r9/runner_failure_oracles.json": "a6149b7d2e1fa48c9faf3b0a7a49dfed3ec8aa63e6159bed5eafaab7f4735c5f",
    "outputs/continuous_occlusion_empirical_retry_r9/runner_success_oracle.json": "99509282e9b1064e10ef5c298147d4d912bfea2dde7bb74881eb492c4309625f",
    "outputs/continuous_occlusion_empirical_retry_r9/synthetic_acceptance.json": "05ca51d437f71615d2856c59ffd97be0ba57b83a9eb5ddfba47cf66c4a0b2255",
    "outputs/continuous_occlusion_empirical_retry_r9/evidence_type_summary.json": "86de722e05a17893af06aba96a259e3540fcbb269c7d68b3ba31a9785796df41",
    "outputs/continuous_occlusion_empirical_retry_r9/visual_qa.json": "3a14eeaa10bdcb68b8eec555408645d3357c8ee23ce3f082f3fa9b50367cdc55",
    "outputs/continuous_occlusion_empirical_retry_r9/synthetic_stress_summary.json": "1d6c1c86c4bde130508030c1d371fc3f69e3860209ca416c81bf41557a8cd550",
    "outputs/continuous_occlusion_empirical_retry_r9/synthetic_field_comparison.svg": "8ddd9b97223927bfa3f5ebf36c7123d8b85e154fb67f683cd2f598b675c9128f",
    "docs/protocols/phase_14r9a_publication_contract_reconciliation.md": "902fee5e1a253e6bc04c0a6c2335bb209793489f1d41c8bd7cf16f4c8794cb20",
    "src/defensive_network_disruption/validation/r9a_publication.py": "348fabac32d1ca0d01c81733b277717622f44fc09f537611580a231f35bf2e52",
    "outputs/continuous_occlusion_empirical_retry_r9a/manifest.json": "39ba0732240483c54593cdb99aa010b3d55e953b9ba0cfe6e6e82219255df8e4",
    "outputs/continuous_occlusion_empirical_retry_r9a/revalidation.json": "30e4fe81bcc9806f0cf6417e719f9a7d17c45d7a706e94b08d8cb0b82c9fe2f4",
    "uv.lock": "c9e4da0781770b9e72b8a5b10a7c514f2259b7e63dc1b67604ee481934db0a0c",
    "pyproject.toml": "75b12da56981460a2a44dcae2c7961bbf97bc84937ceadc486a2581438525d8e",
}

PROGRESS = None


class StoredAuthority:
    """Validated linear authority restored from its immutable receipt."""
    def __init__(self, record): self._record = record
    def record(self): return self._record
    legacy = property(lambda self: self._record["legacy"])
    exposure = property(lambda self: self._record["exposure"])
    selected_receipt = property(lambda self: self._record.get("selected_receipt"))
    records = property(lambda self: self._record["records"])
    failure = property(lambda self: self._record.get("failure"))
    def progress(self, mode):
        expected = {"empirical_success": "success", "empirical_failure": "failure"}.get(mode)
        snapshot = self.legacy["snapshot"]["snapshot"]
        if expected is None or snapshot["status"] != expected: raise ValueError("authority_mode")
        return {"schema_version": 3, "mode": mode,
                "journal_sha256": self.legacy["journal_sha256"],
                "snapshot_sha256": self.legacy["snapshot_sha256"],
                "snapshot": snapshot, "exposure": self.exposure}


def retain_authority(authority):
    durable_write(safe(LOCAL / "linear_authority.json"), authority.record())
    return authority


def _load_r9():
    spec = importlib.util.spec_from_file_location("session14r9_pure_helpers", ROOT / "scripts/session_14r9_occlusion_study.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


SCIENCE = _load_r9()


def safe(path: Path) -> Path:
    target = ROOT / path
    if any(item.is_symlink() for item in (target, *target.parents)) or not target.resolve().is_relative_to(ROOT.resolve()):
        raise PermissionError("unsafe_path")
    return target


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with safe(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1_048_576), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*arguments: str) -> str:
    return subprocess.check_output(("git", *arguments), cwd=ROOT, text=True).strip()


def committed(path: Path) -> None:
    raw = subprocess.check_output(("git", "show", "HEAD:" + path.as_posix()), cwd=ROOT)
    if raw != safe(path).read_bytes():
        raise RuntimeError("uncommitted_source:" + path.as_posix())


def environment() -> dict:
    return {"python": platform.python_version(), "numpy": version("numpy"),
            "scipy": version("scipy"), "matplotlib": version("matplotlib"),
            "lock": sha(Path("uv.lock"))}


def code_hashes() -> dict:
    return {name: sha(Path(name)) for name in CODE}


def atomic_copy(source: Path, destination: Path) -> None:
    target = safe(destination)
    if target.exists():
        raise FileExistsError("immutable_record_exists")
    target.parent.mkdir(parents=True, exist_ok=True)
    pending = target.with_name("." + target.name + ".pending")
    with safe(source).open("rb") as incoming, pending.open("xb") as outgoing:
        for block in iter(lambda: incoming.read(1_048_576), b""):
            outgoing.write(block)
        outgoing.flush(); os.fsync(outgoing.fileno())
    os.link(pending, target); pending.unlink()


def verify_inherited() -> dict:
    for name, expected in HISTORICAL.items():
        if sha(Path(name)) != expected:
            raise RuntimeError("inherited_authority_changed:" + name)
    r9 = json.loads(safe(R9 / "manifest.json").read_text())
    if r9["status"] != "failure" or r9["progress_authority"]["mode"] != "pre_access":
        raise RuntimeError("r9_authority_status")
    acceptance = json.loads(safe(R9 / "synthetic_acceptance.json").read_text())
    if (acceptance["cases"], acceptance["references"], acceptance["permutations"], acceptance["passed"]) != (108, 366, 399, True):
        raise RuntimeError("r9_acceptance_authority")
    visual = json.loads(safe(R9 / "visual_qa.json").read_text())
    if visual["status"] != "approved" or not visual["byte_identical"]:
        raise RuntimeError("r9_visual_authority")
    reconciliation = json.loads(safe(R9A / "revalidation.json").read_text())
    receipt = reconciliation.get("validator_receipt", {})
    if (not reconciliation.get("preaccess_evidence_revalidated_without_recomputation")
            or receipt.get("result") != "valid" or receipt.get("artifact_count") != 19):
        raise RuntimeError("r9a_reconciliation_authority")
    r9j = json.loads(safe(Path("outputs/continuous_occlusion_r9i_blocker_diagnosis/qc.json")).read_text())
    if r9j.get("publication") != "PA" or not r9j.get("execution_valid"):
        raise RuntimeError("r9j_authority_status")
    r9k = json.loads(safe(Path("outputs/continuous_occlusion_onset_comparator_repair/qc.json")).read_text())
    if r9k.get("classification") != "A" or r9k.get("readiness") != 1 or not r9k.get("execution_valid"):
        raise RuntimeError("r9k_authority_status")
    r9m = json.loads(safe(Path("outputs/continuous_occlusion_preaccess_authority_repair/qc.json")).read_text())
    if (r9m.get("classification") != "A" or r9m.get("readiness") != 1
            or r9m.get("empirical_access") != {"states": 0, "edges": 0}):
        raise RuntimeError("r9m_authority_status")
    r9p = json.loads(safe(Path("outputs/continuous_occlusion_retained_journal_authority/qc.json")).read_text())
    if (r9p.get("classification") != "A" or r9p.get("readiness") != 1
            or not r9p.get("execution_valid") or r9p.get("states_opened") != 0
            or r9p.get("edges_opened") != 0):
        raise RuntimeError("r9p_authority_status")
    r9q = json.loads(safe(Path("outputs/continuous_occlusion_expanding_switch_equality_diagnosis/qc.json")).read_text())
    if (r9q.get("numerical") != "NC" or r9q.get("publication") != "PA"
            or r9q.get("topology") != "I" or not r9q.get("execution_valid")):
        raise RuntimeError("r9q_authority_status")
    r9r = json.loads(safe(Path("outputs/continuous_occlusion_switch_localization_repair/qc.json")).read_text())
    if (r9r.get("classification") != "D" or r9r.get("readiness") != 3
            or not r9r.get("execution_valid") or r9r.get("counts", {}).get("cases_passed") != 108
            or r9r.get("counts", {}).get("references_passed") != 366
            or r9r.get("counts", {}).get("permutations_passed") != 399):
        raise RuntimeError("r9r_authority_status")
    r9s = json.loads(safe(Path("outputs/continuous_occlusion_binary64_transition_trace/qc.json")).read_text()).get("data", {})
    if (r9s.get("diagnosis") != "BC" or r9s.get("publication") != "PA"
            or r9s.get("diagnostic_readiness") != 1 or r9s.get("trace_count") != 65
            or not r9s.get("execution_valid")):
        raise RuntimeError("r9s_authority_status")
    r9t = json.loads(safe(Path("outputs/continuous_occlusion_binary64_transition_contract_repair/qc.json")).read_text()).get("data", {})
    if (r9t.get("classification") != "A" or r9t.get("readiness") != 1
            or not r9t.get("execution_valid") or not r9t.get("trace_resolved")
            or r9t.get("cases_passed") != 108 or r9t.get("references_passed") != 366
            or r9t.get("permutations_passed") != 399):
        raise RuntimeError("r9t_authority_status")
    return {"r9_manifest_sha256": HISTORICAL[(R9 / "manifest.json").as_posix()],
            "r9a_manifest_sha256": HISTORICAL[(R9A / "manifest.json").as_posix()],
            "historical_hashes": HISTORICAL}


def ci_expectation() -> CIExpectation:
    implementation = hashlib.sha256(json.dumps(code_hashes(), sort_keys=True).encode()).hexdigest()
    return CIExpectation(
        checkpoint_commit=git("rev-parse", "HEAD"),
        protocol_sha256=sha(PROTOCOL),
        runner_implementation_sha256=implementation,
        lockfile_sha256=sha(Path("uv.lock")),
        workflow_sha256=sha(Path(".github/workflows/ci.yml")),
    )


def offline_ci_authority() -> dict:
    digest = safe(CI_RECEIPT_HASH).read_text().strip()
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ValueError("ci_receipt_sidecar")
    authority = validate_receipt(safe(CI_RECEIPT), ci_expectation(), expected_sha256=digest)
    return {"authority_id": "checkpoint_ci_authority_v1", "checkpoint_commit": authority.checkpoint_commit,
            "receipt_sha256": authority.receipt_sha256, "run_id": authority.run_id,
            "jobs": [{"name": name, "job_id": job_id} for name, job_id in authority.jobs],
            "validated_offline": True, "network_required": False}


def preflight() -> dict:
    if git("status", "--porcelain"):
        raise RuntimeError("dirty_tree")
    git("merge-base", "--is-ancestor", START, "HEAD")
    if git("rev-parse", "v0.1.0^{}") != TAG:
        raise RuntimeError("release_changed")
    if Path(sys.prefix).resolve() != safe(Path(".venv")).resolve():
        raise RuntimeError("project_interpreter")
    committed(PROTOCOL)
    for item in map(Path, CODE):
        committed(item)
    authority = verify_inherited()
    for marker in (LOCAL / "preaccess.marker", LOCAL / "empirical_attempt.marker",
                   LOCAL / "preparation.marker", LOCAL / "execution.marker"):
        if safe(marker).exists():
            raise FileExistsError("fresh_marker_exists:" + marker.name)
    ci = offline_ci_authority()
    return {"schema_version": 1, "status": "ready", "start": START,
            "head": git("rev-parse", "HEAD"), "release": TAG,
            "protocol": sha(PROTOCOL), "implementation": code_hashes(),
            "environment": environment(), "inherited": authority, "checkpoint_ci": ci}


def observe() -> EnvironmentObservation:
    return EnvironmentObservation(platform.python_version(), platform.python_implementation(),
        True, "uv-locked-project-environment", sha(Path("uv.lock")),
        tuple((name, version(name)) for name in ("numpy", "scipy", "matplotlib")))


def expectation(env: EnvironmentObservation) -> PrerequisiteExpectation:
    implementation = hashlib.sha256(json.dumps(code_hashes(), sort_keys=True).encode()).hexdigest()
    return PrerequisiteExpectation(sha(PROTOCOL), implementation, sha(Path("uv.lock")),
                                   env.fingerprint(), TEST_COMMAND)


def produce_tests(path: Path, expected: PrerequisiteExpectation) -> None:
    result = subprocess.run((sys.executable, *TEST_COMMAND), cwd=ROOT, text=True, capture_output=True)
    durable_write(path, test_record(expected, result.stdout + result.stderr, result.returncode))


def mean(values):
    return math.fsum(values) / len(values) if values else None


def calculate_edge(candidate, origin, receiver, defenders, alias, state, ordinal):
    if PROGRESS is None:
        raise PermissionError("guarded_empirical_callback_required")
    PROGRESS.call_start(str(state), str(ordinal), candidate)
    result = evaluate_edge(candidate, origin, receiver, defenders, root=ROOT,
        authority_context={"alias": alias, "state": str(state), "edge": str(ordinal)},
        record=lambda **detail: PROGRESS.numerical_stage(**detail))
    PROGRESS.call_complete()
    return result


def summarize_state(row, state_index, collector, across):
    alias, receivers, defenders, origin = row["alias"], row["receivers"], row["defenders"], row["carrier"]
    state = OptionState(origin, tuple(f"R{i+1}" for i in range(len(receivers))), receivers, defenders)
    mapping = map_defender_edges(state); geometry = summarize_edge_involvement(mapping)
    edges = geometry["edge_summaries"]; relations = [mapping.for_receiver(i) for i in range(len(receivers))]
    receiver_distance = [min(item.receiver_distance for item in rows) for rows in relations]
    segment_distance = [min(item.segment_distance for item in rows) for rows in relations]
    gaps = {name: [item["segment_" + name] for item in edges] for name in ("d2_d1", "d3_d1")}
    descriptor = {name: mean([value for value in values if value is not None]) for name, values in gaps.items()}
    for top in (1, 2, 3):
        descriptor[f"top{top}_jaccard"] = mean(geometry["segment_pair_jaccard"][f"top{top}"])
        descriptor[f"top{top}_distinct"] = float(len({item.defender_index for item in mapping.relations if item.membership("segment", top) > 0}))
        descriptor[f"top{top}_maximum_involvement"] = max(item[f"segment_top{top}_involvement"] for item in geometry["defender_summaries"].values())

    def add(file, metric, values, **kwargs):
        unit = kwargs.get("unit", "edge")
        kwargs.setdefault("source_observations", len(receivers) if unit == "edge" else 1 if unit == "state" else len(values))
        collector.add(file, alias, state_index, metric, values, **kwargs)

    for metric in ("nearest_intersects", "nearest_equal", "nearest_jaccard"):
        add("receiver_corridor_ordering.csv", metric, [item[metric] for item in edges])
    pairs = discordant_pairs(receiver_distance, segment_distance)
    valid_pairs = [(i, j) for i in range(len(receiver_distance)) for j in range(i + 1, len(receiver_distance))
                   if block_ranks(receiver_distance, False)[i] != block_ranks(receiver_distance, False)[j]
                   and block_ranks(segment_distance, False)[i] != block_ranks(segment_distance, False)[j]]
    discord = {(i, j) for i, j, _ in pairs}
    add("receiver_corridor_ordering.csv", "raw_order_disagreement",
        [float(pair in discord) for pair in valid_pairs], unit="state_pair_proportion")
    fields = {}; qc = []
    for candidate in CANDIDATES:
        results = [calculate_edge(candidate, origin, receiver, defenders, alias, state_index, ordinal)
                   for ordinal, receiver in enumerate(receivers)]
        qc.extend((result.intervals, result.convergence_change, result.maximum_reference_error) for result in results)
        fields[candidate] = {}
        for summary in ("receiver", "segment"):
            union = [getattr(result, summary + "_union") for result in results]
            maximum = [getattr(result, summary + "_maximum") for result in results]
            overlap = [a - b for a, b in zip(union, maximum)]
            pv.require(min(overlap) >= -1e-12, "union_less_than_maximum")
            add("union_vs_max.csv", "difference", overlap, candidate=candidate, summary=summary)
            add("union_vs_max.csv", "numerically_equal", [float(abs(value) <= 1e-12) for value in overlap], candidate=candidate, summary=summary)
            if summary == "segment":
                for name, gap in gaps.items():
                    kept = [(value, other) for value, other in zip(overlap, gap) if other is not None]
                    add("overlap_redundancy.csv", "overlap_vs_" + name,
                        [spearman([a for a, _ in kept], [b for _, b in kept])],
                        candidate=candidate, summary=summary, unit="state")
                across.append((alias, state_index, candidate, mean(overlap), descriptor))
            for combination, values in (("union", union), ("maximum", maximum)):
                kwargs = {"candidate": candidate, "summary": summary, "combination": combination}
                fields[candidate][summary, combination] = values
                add("match_summary.csv", "field", values, **kwargs)
                distances = receiver_distance if summary == "receiver" else segment_distance
                add("structural_correspondence.csv", "field_vs_negative_distance",
                    [spearman(values, [-value for value in distances])], unit="state", **kwargs)
                for metric, values2 in follows(values, pairs).items():
                    add("receiver_corridor_ordering.csv", metric, values2, unit="state_pair_proportion", **kwargs)
            individual = [getattr(result, summary + "_individual") for result in results]
            sets = [maximum_set(value) for value in individual]; available = [item for item in sets if item]
            involvement = Counter(defender for item in available for defender in item)
            kwargs = {"candidate": candidate, "summary": summary}
            add("multi_edge_summary.csv", "distinct_maximum_defenders", [float(len(involvement))] if available else [], unit="state", **kwargs)
            add("multi_edge_summary.csv", "multi_edge", [float(max(involvement.values()) >= 2)] if available else [], unit="state", **kwargs)
            add("multi_edge_summary.csv", "maximum_involvement", [float(max(involvement.values()))] if available else [], unit="state", **kwargs)
            add("multi_edge_summary.csv", "field_owner_available", [float(bool(item)) for item in sets], **kwargs)
            for kind in ("receiver", "segment"):
                intersections = []; jaccards = []; fractions = {top: [] for top in (1, 2, 3)}
                for related, values, owners in zip(relations, individual, sets):
                    nearest = {item.defender_index for item in related if getattr(item, kind + "_block") == 0}
                    if owners:
                        intersections.append(float(bool(owners & nearest)))
                        jaccards.append(len(owners & nearest) / len(owners | nearest))
                    total = math.fsum(values)
                    for top in fractions:
                        if total > 0:
                            fractions[top].append(math.fsum(values[item.defender_index] * item.membership(kind, top) for item in related) / total)
                add("multi_edge_summary.csv", kind + "_nearest_intersection", intersections, **kwargs)
                add("multi_edge_summary.csv", kind + "_nearest_jaccard", jaccards, **kwargs)
                for top, values in fractions.items():
                    add("multi_edge_summary.csv", kind + f"_top{top}_strength_fraction", values, **kwargs)
    for candidate in CANDIDATES:
        for combination in ("union", "maximum"):
            first = fields[candidate]["receiver", combination]; second = fields[candidate]["segment", combination]
            kwargs = {"candidate": candidate, "comparison": "receiver_to_segment", "combination": combination}
            add("receiver_corridor_ordering.csv", "field_summary_spearman", [spearman(first, second)], unit="state", **kwargs)
            for metric, values in order_categories(first, second).items():
                add("receiver_corridor_ordering.csv", metric, values, unit="state_pair_proportion", **kwargs)
    for first_name, second_name in itertools.combinations(CANDIDATES, 2):
        for summary in ("receiver", "segment"):
            for combination in ("union", "maximum"):
                first = fields[first_name][summary, combination]; second = fields[second_name][summary, combination]
                kwargs = {"comparison": first_name + "_to_" + second_name,
                          "summary": summary, "combination": combination}
                add("candidate_pair_comparison.csv", "paired_difference",
                    [b - a for a, b in zip(first, second)], unit="state_pair_mean", **kwargs)
                add("candidate_pair_comparison.csv", "candidate_pair_spearman",
                    [spearman(first, second)], unit="state", **kwargs)
                for metric, values in order_categories(first, second).items():
                    add("candidate_pair_comparison.csv", metric, values, unit="state_pair_proportion", **kwargs)
    return qc


def prepare() -> None:
    if PROGRESS is None:
        raise PermissionError("single_launch_required")
    if sha(POP) != POP_SHA:
        raise RuntimeError("population_hash")
    durable_write(safe(LOCAL / "preparation.marker"), {"schema_version": 1, "status": "reserved"})
    counts = Counter(); seen = set(); total = 0
    prepared = safe(LOCAL / "prepared.jsonl")
    with safe(POP).open() as source, prepared.open("x") as destination:
        for index, line in enumerate(source):
            state = str(index); key, edges = SCIENCE.discover_line(line)
            if key in seen:
                raise RuntimeError("duplicate_observation")
            seen.add(key); PROGRESS.discover_state(state, edges)
            projected_key, row = PROGRESS.project(state, lambda line=line: project_line(line))
            pv.require(projected_key == key and len(row["receivers"]) == len(edges), "projection_membership")
            counts[row["alias"]] += 1; total += 1
            destination.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
            destination.flush(); os.fsync(destination.fileno())
            PROGRESS.prepare_state(state)
    pv.require(total == 7227 and tuple(counts[alias] for alias in ALIASES) == COUNTS, "population_counts")
    pv.require(sha(POP) == POP_SHA, "population_changed")
    durable_write(safe(LOCAL / "population.json"), {"schema_version": 1, "states": total,
        "counts": dict(counts), "population_sha256": POP_SHA,
        "prepared_sha256": sha(LOCAL / "prepared.jsonl"), "protocol": sha(PROTOCOL),
        "implementation": code_hashes()})


def analyze():
    if PROGRESS is None:
        raise PermissionError("single_launch_required")
    population = json.loads(safe(LOCAL / "population.json").read_text())
    pv.require(population["prepared_sha256"] == sha(LOCAL / "prepared.jsonl"), "prepared_hash")
    durable_write(safe(LOCAL / "execution.marker"), {"schema_version": 1, "status": "reserved"})
    collector = SCIENCE.Collect(); across = []; qc = []; completed = 0
    with safe(LOCAL / "prepared.jsonl").open() as source:
        for index, line in enumerate(source):
            row = json.loads(line); PROGRESS.start_state(str(index))
            qc.extend(summarize_state(row, index, collector, across))
            durable_write(safe(LOCAL / "state_summaries" / f"{index}.json"), {
                "records": [{"key": list(key), "value": value[-1]} for key, value in collector.data.items()],
                "across": [item for item in across if item[1] == index]})
            PROGRESS.retain_and_complete_edges(str(index)); PROGRESS.complete_state(str(index)); completed += 1
    pv.require(completed == 7227, "analysis_count")
    SCIENCE.add_across(collector, across)
    staging = LOCAL / "staging"
    for name, rows in collector.tables().items():
        write_csv(name, rows, staging)
    durable_write(safe(staging / "candidate_summary.json"), {
        "schema_version": 1, "status": "closed_descriptive_evidence",
        "candidates": list(CANDIDATES), "scope": "label_free_spent_development_geometry",
        "origin": "carrier-position proxy for ball origin", "states": completed,
        "counts": dict(zip(ALIASES, COUNTS))})
    SCIENCE.validate_tables(staging, complete=True)
    return staging, qc


def write_csv(name, rows, directory):
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=SCIENCE.COLUMNS, lineterminator="\n")
    writer.writeheader(); writer.writerows(rows)
    target = safe(directory / name)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError("immutable_record_exists")
    with target.open("x", newline="") as handle:
        handle.write(buffer.getvalue()); handle.flush(); os.fsync(handle.fileno())


def copy_inherited() -> None:
    for name in INHERITED_PUBLIC:
        atomic_copy(R9 / name, OUT / name)


def _private_package(authority, status, stage, exception, staging=None) -> Path:
    mode = "empirical_success" if status == "success" else "empirical_failure"
    progress = authority.progress(mode)
    package = LOCAL / ("closed_package" if status == "success" else "failure_package")
    if staging is not None:
        for name in (*CSV_FILES, "candidate_summary.json"): atomic_copy(staging / name, package / name)
    acceptance = numerical_publication.package(authority.legacy, accepted=status == "success",
        checks={"complete_processing": status == "success"})
    for name in ("qc", "manifest", "evidence"):
        durable_write(safe(package / "numerical_publication" / (name + ".json")), acceptance)
    durable_write(safe(package / "progress_authority.json"), progress)
    base = {"schema_version": 1, "status": status, "progress_authority": progress}
    durable_write(safe(package / "qc.json"), {**base, "stage": stage, "exception": exception,
        "scientific_comparisons_available": status == "success"})
    durable_write(safe(package / "evidence.json"), base)
    files = [item.name for item in safe(package).iterdir() if item.is_file()]
    durable_write(safe(package / "manifest.json"), {**base,
        "outputs": {name: sha(package / name) for name in files}})
    return package


def publish(authority, status, stage, exception, staging=None, *, traceback_path=None) -> dict:
    mode = "empirical_success" if status == "success" else "empirical_failure"
    progress = authority.progress(mode); package = _private_package(authority, status, stage, exception, staging)
    if staging is not None:
        for name in (*CSV_FILES, "candidate_summary.json"): atomic_copy(staging / name, OUT / name)
    available = [name for name in FINAL_FILES if safe(OUT / name).exists()]
    if status != "success" and any(name in available for name in (*CSV_FILES, "candidate_summary.json")):
        raise RuntimeError("partial_science_public")
    durable_write(safe(OUT / "qc.json"), {"schema_version": 1, "status": status,
        "progress_authority": progress, "stage": stage, "exception": exception,
        "scientific_comparisons_available": status == "success"})
    available = [name for name in FINAL_FILES if safe(OUT / name).exists()]
    durable_write(safe(OUT / "manifest.json"), {"schema_version": 1, "status": status,
        "progress_authority": progress, "start": START, "protocol": sha(PROTOCOL),
        "implementation": code_hashes(), "environment": environment(),
        "outputs": {name: sha(OUT / name) for name in available},
        "unavailable": [name for name in FINAL_FILES if name not in available],
        "private_evidence_sha256": sha(package / "evidence.json"),
        "private_manifest_sha256": sha(package / "manifest.json")})
    return validate_linear_public(safe(OUT), package, authority, mode,
                                  traceback_path=traceback_path)

def close_failure(stage: str, error: BaseException, controller: FailureController,
                  closure: TerminalClosure | None) -> None:
    if safe(OUT / "manifest.json").exists():
        return
    if closure is None:
        controller.capture(error, stage, context=None if PROGRESS is None else PROGRESS.context)
        return
    if closure.closed:
        if not controller.original_path.exists():
            controller.capture(error, stage, context=None if PROGRESS is None else PROGRESS.context)
        if not (controller.directory / "publication_failure.json").exists():
            controller.publication_failure(error)
        return
    try:
        closure.fail(error, stage, lambda authority, trace: publish(
            retain_authority(authority), "failure", stage, type(error).__name__,
            traceback_path=trace))
    except BaseException:
        # TerminalClosure preserves the original and any publication failure.
        return


def run() -> None:
    global PROGRESS
    stage = "startup"
    controller = FailureController(safe(LOCAL))
    closure = None
    try:
        bindings = preflight()
        copy_inherited()
        launch = Launch(safe(LOCAL / "launch"))

        def verify(_context):
            nonlocal stage
            stage = "preaccess_authority"
            verify_inherited()
            strict_prerequisite(safe(LOCAL / "launch" / "prerequisite.json"), expectation(observe()))
            ci = offline_ci_authority()
            durable_write(safe(LOCAL / "preaccess_authority.json"), {**bindings, "checkpoint_ci": ci})
            durable_write(safe(LOCAL / "preaccess.marker"), {"schema_version": 1,
                "status": "passed", "head": git("rev-parse", "HEAD"),
                "checkpoint_ci_receipt_sha256": ci["receipt_sha256"]})
            durable_write(safe(LOCAL / "empirical_attempt.marker"), {"schema_version": 1,
                "status": "reserved", "head": git("rev-parse", "HEAD"),
                "checkpoint_ci_receipt_sha256": ci["receipt_sha256"]})
            return True

        def access(_context):
            nonlocal stage
            stage = "preparation"
            PROGRESS.authorize_access(); prepare()
            stage = "analysis"
            staging, _ = analyze()
            stage = "publication"
            def publisher(authority, trace):
                receipt = publish(retain_authority(authority), "success", "closed", None,
                                  staging, traceback_path=trace)
                durable_write(safe(LOCAL / "validator_receipt.json"), receipt)
                return receipt
            closure.succeed(publisher)

        journal = Journal(safe(LOCAL / "journal.jsonl")); PROGRESS = Progress(journal)
        closure = TerminalClosure(PROGRESS, safe(LOCAL))
        launch.execute(discover=observe, expected=expectation, produce=produce_tests,
                       verify=verify, access=access)
        PROGRESS.journal.close()
        print("R9U empirical execution closed and publication validated")
    except BaseException as error:
        close_failure(stage, error, controller, closure)
        if PROGRESS is not None:
            PROGRESS.journal.close()
        raise


def publication_check() -> dict:
    manifest = json.loads(safe(OUT / "manifest.json").read_text())
    package = LOCAL / ("closed_package" if manifest["status"] == "success" else "failure_package")
    mode = "empirical_success" if manifest["status"] == "success" else "empirical_failure"
    authority = StoredAuthority(json.loads(safe(LOCAL / "linear_authority.json").read_text()))
    traceback_path = safe(LOCAL / "numerical_traceback.txt") if mode == "empirical_failure" else None
    return validate_linear_public(safe(OUT), package, authority, mode,
                                  traceback_path=traceback_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "run", "publication-check"))
    command = parser.parse_args().command
    if command == "preflight":
        print(json.dumps(preflight(), sort_keys=True, allow_nan=False))
    elif command == "run":
        run()
    else:
        print(json.dumps(publication_check(), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
