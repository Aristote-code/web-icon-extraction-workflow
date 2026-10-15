"""Exercise the complete flow against unrelated origins and synthetic SVG systems."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPRITE = '''<svg xmlns="http://www.w3.org/2000/svg"><defs>
<linearGradient id="paint"><stop stop-color="red"/></linearGradient>
<symbol id="star" viewBox="0 0 32 32"><path fill="url(#paint)" d="M0 0h32v32z"/></symbol>
</defs></svg>'''

class UniversalPipelineTest(unittest.TestCase):
    def test_unrelated_sites_produce_their_own_reports(self):
        with tempfile.TemporaryDirectory() as temp:
            for host in ('alpha.example', 'beta.example'):
                source = Path(temp) / host
                (source / 'captures').mkdir(parents=True)
                (source / 'originals').mkdir()
                (source / 'originals/sprite.svg').write_text(SPRITE)
                (source / 'originals/standalone.svg').write_text('<svg width="40" height="20"><path d="M0 0h40v20z"/></svg>')
                meta = {'name': host + ' extraction', 'entryUrl': 'https://' + host + '/app/', 'date': '2025-01-02',
                        'scope': {'origin': 'https://' + host, 'pathPrefix': '/app/'}, 'limitations': ['Login-only states were not assessed.']}
                (source / 'run.json').write_text(json.dumps(meta))
                local = '<svg><use href="#local"/></svg>'
                symbol = '<symbol id="local" viewBox="0 0 16 16"><circle r="4" cx="8" cy="8"/></symbol>'
                pictogram = '<svg viewBox="0 0 48 48"><rect width="10" height="10"/></svg>'
                capture = {'label': 'Menu from ' + host, 'dom': {'url': meta['entryUrl'], 'title': host,
                    'svgs': [local, '<svg><use href="/sprite.svg#star"/></svg>', '<svg><use href="#missing"/></svg>', pictogram],
                    'symbols': [symbol], 'pictogramSvgs': [pictogram], 'links': [
                        {'text': 'Next', 'href': 'https://' + host + '/app/next'},
                        {'text': 'External', 'href': 'https://outside.example/app/no'},
                        {'text': 'Out of path', 'href': 'https://' + host + '/other'}]},
                    'bundle': {'assets': [
                        {'kind': 'image', 'contentType': 'image/svg+xml; charset=utf-8', 'url': 'https://' + host + '/sprite.svg', 'name': 'sprite.svg', 'path': 'originals/sprite.svg'},
                        {'kind': 'image', 'contentType': 'image/svg+xml', 'url': 'https://' + host + '/original.svg', 'name': 'original.svg', 'path': 'originals/standalone.svg'}
                    ], 'failures': []}}
                (source / 'captures/0.json').write_text(json.dumps(capture))
                out = Path(temp) / (host + '-assets')
                subprocess.run([sys.executable, str(ROOT / 'scripts/run.py'), '--input', str(source), '--output', str(out)],
                               check=True, stdout=subprocess.DEVNULL)
                manifest = json.loads((out / 'manifest.json').read_text())
                self.assertEqual(manifest['name'], meta['name'])
                self.assertEqual(manifest['date'], '2025-01-02')
                coverage = json.loads((out / 'coverage.json').read_text())
                self.assertIn('not assessed', coverage[0]['status'])
                self.assertEqual(coverage[0]['state'], capture['label'])
                report = (out / 'coverage-report.html').read_text()
                self.assertIn(host, report)
                self.assertNotIn('ClickUp', report)
                self.assertNotIn('9014555051', report)
                self.assertIn('Login-only states were not assessed.', report)
                remaining = json.loads((out / 'discovered-unvisited-links.json').read_text())
                self.assertEqual([r['url'] for r in remaining], ['https://' + host + '/app/next'])
                self.assertEqual(json.loads((out / 'summary.json').read_text())['pickerPictograms'], 1)
                incomplete = [a for a in manifest['assets'] if a['unresolvedReferences']]
                self.assertEqual(len(incomplete), 1)
                self.assertTrue(incomplete[0]['file'].startswith('incomplete-svg/'))
                # The external use was reconstructed from the original map; paint is copied.
                reconstructed = [a for a in manifest['assets'] if 'inline-svg' in a['kinds'] and not a['unresolvedReferences']]
                self.assertTrue(any('linearGradient' in (out / a['file']).read_text() for a in reconstructed))
                self.assertTrue(any(ET.parse(out/a['file']).getroot().get('viewBox') == '0 0 40 20' for a in manifest['assets'] if 'original-svg' in a['kinds']))
                self.assertFalse(json.loads((out / 'validation.json').read_text())['renderingRequested'])
                with zipfile.ZipFile(out.parent / (out.name + '.zip')) as archive:
                    self.assertIsNone(archive.testzip())
                # Repeated builds must not leave stale incomplete exports.
                subprocess.run([sys.executable, str(ROOT / 'scripts/run.py'), '--input', str(source), '--output', str(out)],
                               check=True, stdout=subprocess.DEVNULL)
                self.assertEqual(len(list((out/'incomplete-svg').glob('*.svg'))), 1)

if __name__ == '__main__':
    unittest.main()
