"""Verify generated or unzipped artifacts without network access."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('directory', type=Path)
args = parser.parse_args()
root = args.directory.resolve()
manifest = json.loads((root / 'manifest.json').read_text())
seen = set()
for asset in manifest['assets'] + manifest['originalFiles']:
    target = (root / asset['file']).resolve()
    if not target.is_relative_to(root):
        raise SystemExit('Asset escapes package directory')
    assert target.is_file(), str(target)
    assert hashlib.sha256(target.read_bytes()).hexdigest() == asset['sha256'], str(target)
    if asset in manifest['assets']:
        assert asset['sha256'] not in seen, 'Duplicate normalized export'
        seen.add(asset['sha256'])
        ET.parse(target)
for asset in manifest['assets']:
    if asset.get('raw'):
        assert (root / asset['raw']).is_file(), asset['raw']
coverage = json.loads((root / 'coverage.json').read_text())
assert all(a['sources'] for a in manifest['assets'])
assert all(c['url'].startswith(('https://', 'http://')) for c in coverage)
print(f"Verified {len(manifest['assets'])} SVG exports, {len(manifest['originalFiles'])} originals, {len(coverage)} captured states.")
