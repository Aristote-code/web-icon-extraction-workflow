"""Package, report and verify any browser capture directory in one command."""
import argparse
from pathlib import Path
import subprocess
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--input', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--config', type=Path)
parser.add_argument('--render', action='store_true')
args = parser.parse_args()
scripts = Path(__file__).resolve().parent
common = ['--input', str(args.input), '--output', str(args.output)]
package = [sys.executable, str(scripts / 'package_assets.py'), *common]
if args.config:
    package += ['--config', str(args.config)]
subprocess.run(package, check=True)
subprocess.run([sys.executable, str(scripts / 'finalize_run.py'), *common, *(['--render'] if args.render else [])], check=True)
subprocess.run([sys.executable, str(scripts / 'verify_package.py'), str(args.output)], check=True)
