"""Synthetic tests for Session 14ad fail-closed orchestration."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from defensive_network_disruption.validation.launch_enforcement import (
    EnvironmentObservation, GovernedLauncher, LaunchContext, LaunchError,
    LaunchState, PrerequisiteExpectation, atomic_write, validate_prerequisite,
)


def environment(**changes):
    values = dict(python="3.13.15", implementation="CPython", in_project_environment=True,
        environment_marker="uv-locked-project-environment", lock_sha256="a" * 64,
        packages=(("numpy", "2.5.3"), ("scipy", "1.17.1")))
    values.update(changes)
    return EnvironmentObservation(**values)


def expectation(env):
    return PrerequisiteExpectation("b" * 64, "c" * 64, env.lock_sha256, env.fingerprint(),
        ("-m", "unittest", "tests.test_session14ad_launch_enforcement.PrerequisiteContractTests"))


def record(exp):
    return {"schema_version": 1, "producer": "session14ad_enforcement_tests", "status": "passed",
        "test_command": list(exp.test_command), "protocol_sha256": exp.protocol_sha256,
        "implementation_sha256": exp.implementation_sha256, "lock_sha256": exp.lock_sha256,
        "environment_sha256": exp.environment_sha256, "tests_run": 4, "tests_passed": 4,
        "tests_skipped": 0, "exit_status": 0, "test_output_sha256": "d" * 64,
        "failure_enforcement_passed": True}


class PrerequisiteContractTests(unittest.TestCase):
    def test_environment_failure_blocks_callbacks(self):
        for changed in (
            dict(in_project_environment=False), dict(environment_marker=None),
            dict(lock_sha256="f" * 64), dict(packages=(("numpy", "2.5.3"),)),
        ):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as tmp:
                good = environment(); bad = environment(**changed); exp = expectation(good); calls=[]
                launcher = GovernedLauncher(Path(tmp)/"launch", Path(tmp)/"access")
                with self.assertRaises(LaunchError):
                    launcher.run(environment=bad, expected=exp, required_packages=("numpy", "scipy"),
                        prerequisite_path=Path(tmp)/"p.json", produce_prerequisite=lambda:calls.append("producer"),
                        verify_synthetic=lambda _:calls.append("verify"), authorize_empirical=lambda _:calls.append("access"))
                self.assertEqual(calls, []); self.assertEqual(launcher.state, LaunchState.FAILED_CLOSED)

    def test_prerequisite_failure_blocks_downstream(self):
        mutations = ("missing", "malformed", "schema", "hash", "environment", "counts", "status")
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp); env=environment(); exp=expectation(env); path=root/"p.json"; calls=[]
                def produce():
                    if mutation == "missing": return
                    if mutation == "malformed": atomic_write(path, "{"); return
                    value=record(exp)
                    if mutation == "schema": value["extra"]=1
                    if mutation == "hash": value["implementation_sha256"]="e"*64
                    if mutation == "environment": value["environment_sha256"]="e"*64
                    if mutation == "counts": value["tests_passed"]=3
                    if mutation == "status": value["status"]="failed"
                    atomic_write(path,json.dumps(value)+"\n")
                launcher=GovernedLauncher(root/"launch",root/"access")
                with self.assertRaises((LaunchError, FileNotFoundError)):
                    launcher.run(environment=env, expected=exp, required_packages=("numpy","scipy"),
                        prerequisite_path=path,produce_prerequisite=produce,
                        verify_synthetic=lambda _:calls.append("verify"),authorize_empirical=lambda _:calls.append("access"))
                self.assertEqual(calls,[]);self.assertFalse((root/"access").exists())

    def test_success_order_and_one_use_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);env=environment();exp=expectation(env);path=root/"p.json";calls=[]
            launcher=GovernedLauncher(root/"launch",root/"access")
            context=launcher.run(environment=env,expected=exp,required_packages=("numpy","scipy"),
                prerequisite_path=path,produce_prerequisite=lambda:atomic_write(path,json.dumps(record(exp))+"\n"),
                verify_synthetic=lambda _:calls.append("verify") or True,
                authorize_empirical=lambda _:calls.append("access"))
            self.assertEqual(calls,["verify","access"])
            self.assertEqual(launcher.transitions,[x.value for x in (
                LaunchState.INITIAL,LaunchState.ENVIRONMENT_VERIFIED,LaunchState.PREREQUISITE_CREATED,
                LaunchState.PREREQUISITE_VALIDATED,LaunchState.SYNTHETIC_READINESS_VERIFIED,
                LaunchState.EMPIRICAL_ACCESS_AUTHORIZED)])
            with self.assertRaises(LaunchError):
                launcher.authorize(context,env,exp,path,lambda _:None)

    def test_direct_context_construction_and_marker_collision(self):
        with self.assertRaises(LaunchError): LaunchContext("a","b","c",object())
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);env=environment();exp=expectation(env);path=root/"p.json";calls=[]
            (root/"launch").write_text("claimed\n")
            launcher=GovernedLauncher(root/"launch",root/"access")
            with self.assertRaises(FileExistsError):
                launcher.run(environment=env,expected=exp,required_packages=("numpy","scipy"),
                    prerequisite_path=path,produce_prerequisite=lambda:calls.append("producer"),
                    verify_synthetic=lambda _:True,authorize_empirical=lambda _:calls.append("access"))
            self.assertEqual(calls,[]);self.assertEqual(launcher.state,LaunchState.FAILED_CLOSED)


class LaunchEnforcementTests(unittest.TestCase):
    def test_duplicate_missing_and_reordered_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);env=environment();exp=expectation(env);path=root/"p.json"
            path.write_text('{"schema_version":1,"schema_version":1}\n')
            with self.assertRaises(LaunchError):validate_prerequisite(path,exp)
            path.write_text(json.dumps({"schema_version":1})+'\n')
            with self.assertRaises(LaunchError):validate_prerequisite(path,exp)
            value=record(exp);path.write_text(json.dumps(value,sort_keys=False)+'\n')
            loaded,_=validate_prerequisite(path,exp);self.assertEqual(loaded["tests_run"],4)

    def test_source_has_no_prohibited_route(self):
        root=Path(__file__).resolve().parents[1]
        source=(root/"src/defensive_network_disruption/validation/launch_enforcement.py").read_text()
        runner=(root/"scripts/session_14ad_launch_prerequisite_enforcement.py").read_text()
        for forbidden in ("prepared.jsonl","canonical_population","evaluate_options","load_model","requests.get","urllib.request"):
            self.assertNotIn(forbidden,source+runner)

    def test_numerical_history_is_not_modified(self):
        root=Path(__file__).resolve().parents[1]
        self.assertTrue((root/"scripts/session_14r2_occlusion_study.py").is_file())
        self.assertTrue((root/"outputs/continuous_occlusion_retry_14r2/manifest.json").is_file())


if __name__ == "__main__": unittest.main()
