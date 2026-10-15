"""Generate a source-backed report and ZIP for any packaged capture run."""
import argparse
import csv
import gzip
import hashlib
import html
import io
import os
import json
from pathlib import Path
import shutil
from urllib.parse import urlparse, urldefrag
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--render', action='store_true', help='Optional CairoSVG/Pillow checks; external references are skipped')
    args = parser.parse_args()
    source, out = args.input.resolve(), args.output.resolve()
    manifest = json.loads((out / 'manifest.json').read_text())
    stats = json.loads((out / 'summary.json').read_text())
    coverage = json.loads((out / 'coverage.json').read_text())
    config = manifest.get('run', {})
    name = manifest['name']
    esc = lambda value: html.escape(str(value), quote=True)
    (out / 'incomplete-svg').mkdir(exist_ok=True)
    for asset in manifest['assets']:
        if asset['unresolvedReferences'] and asset['file'].startswith('svg/'):
            before = asset['file']
            asset['file'] = 'incomplete-svg/' + Path(before).name
            shutil.move(out / before, out / asset['file'])
    validation = {'renderingRequested': args.render, 'rasterizedExports': 0,
                  'rendererErrors': [], 'transparentAt64px': [], 'renderSkipped': [],
                  'incompleteLocalReferences': [], 'xmlParseErrors': manifest['parseErrors'],
                  'note': 'Extraction and file integrity are verified separately from visual fidelity. Unchecked rendering is not treated as a pass.'}
    if args.render:
        # Optional native-library override for environments whose loader cannot find Cairo.
        library=os.environ.get('CAIRO_LIBRARY_PATH')
        if library:
            import ctypes.util
            native=Path(library).expanduser().resolve(strict=True)
            find_library=ctypes.util.find_library
            ctypes.util.find_library=lambda name: str(native) if name in ('cairo','cairo-2','libcairo-2') else find_library(name)
        try:
            import cairosvg
            from PIL import Image
        except (ImportError, OSError) as error:
            raise SystemExit('Rendering dependencies unavailable; install requirements and native Cairo, or omit --render: ' + str(error))
    for asset in manifest['assets']:
        if asset['unresolvedReferences']:
            validation['incompleteLocalReferences'].append({'file': asset['file'], 'missing': asset['unresolvedReferences']})
            asset['renderCheck'] = 'skipped: unresolved local references'
        elif asset.get('externalReferences'):
            validation['renderSkipped'].append({'file': asset['file'], 'reason': 'external references are not fetched'})
            asset['renderCheck'] = 'skipped: external dependencies'
        elif not args.render:
            asset['renderCheck'] = 'not requested'
        else:
            try:
                im = Image.open(io.BytesIO(cairosvg.svg2png(url=str(out / asset['file']), output_width=64, output_height=64))).convert('RGBA')
                validation['rasterizedExports'] += 1
                asset['renderCheck'] = 'rasterized at 64px; browser fidelity not asserted'
                if im.getbbox() is None:
                    validation['transparentAt64px'].append(asset['file'])
            except Exception as error:
                asset['renderCheck'] = 'renderer error'
                validation['rendererErrors'].append({'file': asset['file'], 'error': str(error)})
    links = {}
    entry = manifest['entryUrl']
    parsed = urlparse(entry)
    scope = config.get('scope', {})
    origin = scope.get('origin', parsed.scheme + '://' + parsed.netloc)
    prefix = scope.get('pathPrefix', '/')
    for path in sorted((source / 'captures').glob('*.json*')):
        capture = json.loads(gzip.open(path, 'rt').read() if path.suffix == '.gz' else path.read_text())
        for link in capture['dom'].get('links', []):
            url = urlparse(link['href'])
            if url.scheme + '://' + url.netloc == origin and url.path.startswith(prefix):
                links.setdefault(link['href'], link.get('text', '').strip())
    visited = {item['url'] for item in coverage}
    remaining = [{'url': url, 'text': label, 'status': 'discovered; no exact URL capture (may be an alias)'}
                 for url, label in sorted(links.items()) if url not in visited]
    failures = json.loads((out / 'download-failures.json').read_text())
    downloaded = {urldefrag(url)[0] for asset in manifest['originalFiles'] for url in asset['urls']}
    for failure in failures:
        failure['laterDownloadedSameBaseUrl'] = urldefrag(failure['url'])[0] in downloaded
    for filename, data in [('manifest.json', manifest), ('validation.json', validation),
                           ('discovered-unvisited-links.json', remaining), ('download-failures.json', failures)]:
        (out / filename).write_text(json.dumps(data, indent=2))
    with (out / 'manifest.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['file', 'name', 'kinds', 'sha256', 'source_count', 'unresolved_references', 'render_check'])
        for asset in manifest['assets']:
            writer.writerow([asset['file'], asset['name'], ';'.join(asset['kinds']), asset['sha256'],
                             len(asset['sources']), ';'.join(asset['unresolvedReferences']), asset['renderCheck']])
    rows = ''.join('<tr><td>' + str(c['capture']) + '</td><td>' + esc(c['state']) + '</td><td>' + esc(c['status']) +
                   '</td><td>' + esc(c.get('notes', '')) + '</td><td><a href="' + esc(c['url']) + '">' + esc(c['url']) + '</a></td></tr>' for c in coverage)
    limitations = config.get('limitations', [])
    if not limitations:
        limitations = ['No manual limitations assessment was supplied. Coverage completeness is unknown.']
    notes = ''.join('<li>' + esc(note) + '</li>' for note in config.get('notes', []))
    limits = ''.join('<li>' + esc(note) + '</li>' for note in limitations)
    counters = ''.join('<tr><td>' + esc(key) + '</td><td>' + str(value) + '</td></tr>' for key, value in stats.items())
    report = f'''<!doctype html><html lang="en"><meta charset="utf-8"><title>{esc(name)} — coverage</title>
<style>body{{font:16px/1.55 system-ui;max-width:1100px;margin:36px auto;padding:24px;color:#282236}}table{{border-collapse:collapse;width:100%}}td,th{{padding:10px;border-bottom:1px solid #ddd;text-align:left;vertical-align:top;overflow-wrap:anywhere}}td:last-child{{max-width:350px}}a{{color:#6042ad}}</style>
<h1>{esc(name)}</h1><p>{esc(manifest['date'])} · {esc(manifest['timezone'])}</p><p>Entry: <a href="{esc(entry)}">{esc(entry)}</a></p>
<p><a href="gallery.html">Gallery</a> · <a href="manifest.json">Provenance manifest</a> · <a href="manifest.csv">CSV</a> · <a href="validation.json">Validation</a> · <a href="discovered-unvisited-links.json">Unvisited discovered URLs</a> · <a href="download-failures.json">Download failures</a></p>
<h2>Extracted assets</h2><table>{counters}</table><p>Categories overlap and must not be added together. Counts include mounted definitions and auxiliary graphics. Sprite presence verifies availability, not visible usage. Originals retain downloaded bytes; reconstructed exports retain source geometry and raw markup.</p>
<h2>Coverage boundary</h2><p>The report lists recorded states only. It does not establish that every accessible page, menu, theme or responsive variant was visited. No claim about changes made on the website is inferred from capture data.</p><ul>{limits}</ul><ul>{notes}</ul>
<h2>Validation</h2><p>Rendering requested: {args.render}. Rasterized exports: {validation['rasterizedExports']}. Renderer errors: {len(validation['rendererErrors'])}. Transparent at 64px: {len(validation['transparentAt64px'])}. Missing local definitions: {len(validation['incompleteLocalReferences'])}. External dependencies skipped: {len(validation['renderSkipped'])}.</p>
<p>XML parsing, local reference closure, downloaded bytes and rendering are separate checks. Browser appearance may depend on styles, fonts, colors, masks or external resources. Classes are removed from normalized exports; originals and raw markup remain available. Dimensions are inferred when a viewBox is absent and flagged in the manifest. Deduplication is normalized XML hashing, not perceptual equivalence. Downloads that failed once but later succeeded are flagged in the failure log.</p>
<h2>Captured states</h2><table><thead><tr><th>ID</th><th>State</th><th>Observed status</th><th>Notes</th><th>Final URL</th></tr></thead><tbody>{rows}</tbody></table></html>'''
    (out / 'coverage-report.html').write_text(report)
    (out / 'README.txt').write_text(name + '\nOpen coverage-report.html for findings and limitations; gallery.html to browse assets.\nOriginals retain downloaded bytes. Raw XML and manifests preserve provenance. Incomplete SVGs are separated.\nExtraction does not grant ownership or a reuse license.\n')
    for asset in manifest['assets'] + manifest['originalFiles']:
        assert hashlib.sha256((out / asset['file']).read_bytes()).hexdigest() == asset['sha256']
    archive_path = out.parent / (out.name + '.zip')
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as archive:
        generated_files={'manifest.json','manifest.csv','summary.json','coverage.json','coverage-report.html','gallery.html','validation.json','discovered-unvisited-links.json','download-failures.json','README.txt'}
        generated_dirs={'svg','incomplete-svg','originals','raw-symbols','raw-inline','evidence'}
        for path in sorted(out.rglob('*')):
            relative=path.relative_to(out)
            if path.is_file() and (str(relative) in generated_files or relative.parts[0] in generated_dirs):
                archive.write(path, str(Path(out.name) / path.relative_to(out)))
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
    print(json.dumps({'archive': str(archive_path), 'capturedStates': len(coverage), 'discoveredUnvisitedUrls': len(remaining),
                      'rasterizedExports': validation['rasterizedExports'], 'rendererErrors': len(validation['rendererErrors'])}, indent=2))


if __name__ == '__main__':
    main()
