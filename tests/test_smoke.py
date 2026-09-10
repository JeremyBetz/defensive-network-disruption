"""Check installed imports without competition data or analysis side effects."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


IMPORTS = """
import defensive_network_disruption
import defensive_network_disruption.data
import defensive_network_disruption.geometry
import defensive_network_disruption.networks
import defensive_network_disruption.validation
import defensive_network_disruption.visualization
"""


class PackageSmokeTests(unittest.TestCase):
    def test_installed_namespaces_import_from_empty_directory(self):
        # -I excludes the working directory and PYTHONPATH: install the package
        # first so a source-tree import cannot mask a packaging problem.
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, "-I", "-c", IMPORTS],
                cwd=directory,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_imports_do_not_access_local_data_or_network(self):
        # Guard the repository's local-data boundary in a fresh process. Source
        # and bytecode reads remain allowed for normal Python import machinery.
        repository_data = Path(__file__).resolve().parents[1] / "data"
        guard = """
from pathlib import Path
import os
import sys

protected = (Path(sys.argv[1]).resolve(), Path.cwd() / 'data')

def audit(event, args):
    if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
        path = Path(os.fsdecode(args[0])).resolve()
        if any(path.is_relative_to(root) for root in protected):
            raise AssertionError('Package import attempted local data access')
    if event in ('socket.connect', 'socket.getaddrinfo'):
        raise AssertionError('Package import attempted network access')

sys.addaudithook(audit)
"""
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, "-I", "-c", guard + IMPORTS, str(repository_data)],
                cwd=directory,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
