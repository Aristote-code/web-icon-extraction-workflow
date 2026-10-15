"""Dependency order must not depend on Python's randomized set ordering."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ReproducibilityTest(unittest.TestCase):
    def test_two_hash_seeds_produce_identical_exports(self):
        snapshots = []
        with tempfile.TemporaryDirectory() as temp:
            for seed in ('1', '2'):
                output = Path(temp) / seed
                subprocess.run([
                    sys.executable, str(ROOT / 'scripts/package_assets.py'),
                    '--input', str(ROOT / 'data/clickup'), '--output', str(output)
                ], check=True, env=dict(os.environ, PYTHONHASHSEED=seed), stdout=subprocess.DEVNULL)
                manifest = json.loads((output / 'manifest.json').read_text())
                snapshots.append(sorted(a['sha256'] for a in manifest['assets']))
            self.assertEqual(snapshots[0], snapshots[1])
            self.assertEqual(len(snapshots[0]), 2209)

if __name__ == '__main__':
    unittest.main()
