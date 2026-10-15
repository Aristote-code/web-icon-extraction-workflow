import pathlib,json,html,shutil,hashlib,zipfile,ctypes.util,io,collections
from PIL import Image,ImageDraw
old=ctypes.util.find_library
if pathlib.Path('/opt/homebrew/lib/libcairo.2.dylib').exists():
 ctypes.util.find_library=lambda name:'/opt/homebrew/lib/libcairo.2.dylib' if name in ['cairo','cairo-2','libcairo-2'] else old(name)
import cairosvg
import argparse
parser=argparse.ArgumentParser(description='Finalize the recorded ClickUp case study (not a generic coverage assessment)')
parser.add_argument('--input',type=pathlib.Path,required=True)
parser.add_argument('--output',type=pathlib.Path,required=True)
args=parser.parse_args()
DATA=args.input.resolve();O=args.output.resolve();B=O.parent
B.mkdir(parents=True,exist_ok=True)
m=json.loads((O/'manifest.json').read_text());s=json.loads((O/'summary.json').read_text());coverage=json.loads((O/'coverage.json').read_text())
# Quarantine incomplete reference closures and update every path.
(O/'incomplete-svg').mkdir(exist_ok=True)
g=(O/'gallery.html').read_text()
for a in m['assets']:
 if a['unresolvedReferences']:
  before=a['file'];a['file']=before.replace('svg/','incomplete-svg/',1);shutil.move(O/before,O/a['file']);g=g.replace(before,a['file'])
(O/'gallery.html').write_text(g.replace(str(s['standaloneSvgs'])+' standalone SVGs',str(s['standaloneSvgs']-s['unresolvedSvgReferences'])+' SVGs with complete local references; '+str(s['unresolvedSvgReferences'])+' incomplete exports are listed in the manifest'))
# Render all complete exports; this is a parser/renderability check, not proof of pixel identity.
errors=[];success=[];blank=[];samples=[]
for a in m['assets']:
 if a['unresolvedReferences']:continue
 try:
  png=cairosvg.svg2png(url=str(O/a['file']),output_width=64,output_height=64)
  im=Image.open(io.BytesIO(png)).convert('RGBA')
  a['renderCheck']='rasterized at 64px with CairoSVG; visual identity to browser not asserted'
  if im.getbbox() is None:blank.append(a['file'])
  success.append(a['file'])
  kind=a['kinds'][0]
  if sum(k==kind for k,_ in samples)<24:samples.append((kind,im))
 except Exception as e:
  errors.append({'file':a['file'],'error':str(e)});a['renderCheck']='renderer error; see validation.json'
contact=Image.new('RGB',(960,100+100*((len(samples)+9)//10)), '#f5f5fa');d=ImageDraw.Draw(contact)
d.text((24,18),'ClickUp: actual extracted SVGs | sample preview',fill='#272238')
d.text((24,40),'Original sprite symbols, application icons and picker pictograms',fill='#655b77')
for i,(kind,im) in enumerate(samples):
 x=24+(i%10)*94;y=90+(i//10)*100
 contact.paste(im,(x+12,y),im);d.text((x,y+66),kind.replace('original-','')[:15],fill='#655b77')
contact.save(B/'clickup-preview.png');shutil.copy(B/'clickup-preview.png',O/'evidence/preview.png')
proof=DATA/'picker-browser.png'
if proof.exists():shutil.copy(proof,O/'evidence/picker-browser.png')
v={'xmlParseErrors':m['parseErrors'],'rasterizedExports':len(success),'rendererErrors':errors,'transparentAt64px':blank,'incompleteLocalReferences':[{'file':a['file'],'name':a['name'],'missing':a['unresolvedReferences']} for a in m['assets'] if a['unresolvedReferences']],'note':'All complete SVGs were rasterized; a sample contact sheet was inspected. This does not guarantee pixel equivalence, CSS theme fidelity, or resolution of external images.'}
(O/'validation.json').write_text(json.dumps(v,indent=2));(O/'manifest.json').write_text(json.dumps(m,indent=2))
# Explicit evidence boundary for every state.
for c in coverage:
 if '(navigation partial)' in c['state']:c['status']='navigation timed out; DOM captured; main content not fully verified'
 if c['capture'] in [7,8,9,10]:c['status']='initial loading shell; later capture of section exists'
 if c['capture']==5:c['state']='Global Search panel'
(O/'coverage.json').write_text(json.dumps(coverage,indent=2))
links={}
for p in (DATA/'captures').glob('*.json*'):
 import gzip
 c=json.loads(gzip.open(p,'rt').read() if p.suffix=='.gz' else p.read_text())
 for l in c['dom']['links']:
  if l['href'].startswith('https://app.clickup.com/9014555051/'):links.setdefault(l['href'],l['text'].strip())
visited={c['url'] for c in coverage};remaining=[{'url':u,'text':t,'status':'discovered link; no exact-URL capture (may be route alias)'} for u,t in links.items() if u not in visited]
(O/'discovered-unvisited-links.json').write_text(json.dumps(remaining,indent=2))
downloads=json.loads((O/'download-failures.json').read_text());recovered={u.split('#')[0] for o in m['originalFiles'] for u in o['urls']}
for f in downloads:f['laterDownloadedSameBaseUrl']=f['url'].split('#')[0] in recovered
(O/'download-failures.json').write_text(json.dumps(downloads,indent=2))
rows=''.join('<tr><td>'+str(c['capture'])+'</td><td>'+html.escape(c['state'])+'</td><td>'+html.escape(c['status'])+'</td><td>'+str(c['inlineSvgCount'])+'</td><td><a href="'+html.escape(c['url'],quote=True)+'">'+html.escape(c['url'])+'</a></td></tr>' for c in coverage)
missing=''.join('<li>'+html.escape(a['name'])+': '+html.escape(', '.join(a['unresolvedReferences']))+'</li>' for a in m['assets'] if a['unresolvedReferences'])
report=f'''<!doctype html><html lang="en"><meta charset="utf-8"><title>ClickUp extraction — coverage and verification</title><style>body{{font:16px/1.55 system-ui;color:#282236;max-width:1200px;margin:40px auto;padding:0 24px;background:#faf9fc}}h1,h2{{line-height:1.2}}.stats{{padding:22px;background:#ece7fa;border-radius:14px}}table{{border-collapse:collapse;width:100%;font-size:12px}}td,th{{padding:10px;border-bottom:1px solid #ddd;text-align:left;vertical-align:top}}td:last-child{{overflow-wrap:anywhere;max-width:400px}}a{{color:#6042ad}}img{{max-width:100%}}</style>
<h1>ClickUp icon & pictogram extraction</h1><p>15 October 2026 · authenticated workspace 9014555051 · read-only navigation.</p>
<div class="stats"><b>{s['standaloneSvgs']:,} deduplicated SVG exports</b> ({s['standaloneSvgs']-s['unresolvedSvgReferences']:,} complete local reference closures; {s['unresolvedSvgReferences']} incomplete).<br>1,321 symbols in the downloaded original sprite · 603 unique picker pictograms · {s['domSymbols']} unique DOM symbol exports · {s['originalFiles']} original downloaded image files.<br>{s['captures']} captured UI states across {s['uniqueUrls']} distinct final URLs. These categories overlap and must not be added together.</div>
<p><a href="gallery.html">Searchable gallery</a> · <a href="manifest.json">Full provenance manifest</a> · <a href="manifest.csv">CSV index</a> · <a href="coverage.json">Coverage data</a> · <a href="validation.json">Validation details</a></p>
<h2>What was actually extracted</h2><p>The authenticated ClickUp application was opened at the supplied Inbox URL. Original network images were downloaded through the browser asset inventory. Inline SVG geometry and DOM sprite symbols were captured from the rendered application. The original <code>map-CGEPKKMI.svg</code> sprite was successfully retrieved and all 1,321 symbol elements were exported, with available referenced definitions copied into standalone SVGs. Presence in the downloaded sprite is verified; individual use on a screen is not assumed. Original downloaded bytes and raw extracted symbol/inline markup remain in the package.</p>
<p>The Color &amp; Icon picker was opened without choosing an icon. It was scrolled through 12 successive positions until the bottom and item count stabilized at 608 SVG entries; normalization reduced these to 603 unique pictograms. File hashes identify pictograms whose human-readable names were unavailable. The collection also includes interface icons and integration logos encountered in App Center.</p>
<h2>Coverage and limits</h2><p>Visited sections include Inbox Primary/Other/Later/Cleared and filters, global search, Planner, AI, Teams, Docs, Dashboards, Whiteboards, Forms, Clips, Goals, Timesheets, Assigned Comments, Skills, Artifacts, Meetings, My Tasks, All Tasks, Product Design and Team Space, Sprints and Projects folders, Project 1/2 and sprint view tabs, three task detail pages, two documents, view catalog, list menus, icon picker and App Center.</p>
<p><b>This is broad verified extraction, not a claim that every accessible page and UI state was exhausted.</b> Calendar connection/onboarding, empty hubs and disabled controls limited the states exposed without creating content, connecting external accounts or changing configuration. Some navigation attempts timed out while a DOM capture remained possible; those states are marked below. Initial loading shells were recaptured where recorded. A rendered shell or mounted symbol definition proves asset availability, not successful loading of all page content.</p>
<p>No tasks, documents, integrations, icons or views were created, deleted or edited. Menus and tabs were inspected only. Normal last-viewed history may have changed. Other workspaces, private content not exposed by this session, permission-gated features, creation flows, every menu/hover/theme/mobile variant and every hub subtab were not exhausted. <a href="discovered-unvisited-links.json">Discovered URLs without exact captures</a> include routing aliases; they are not asserted inaccessible.</p>
<h2>Normalization and validation</h2><p>Deduplication uses SHA-256 of normalized SVG markup, stripping framework attributes/presentation classes while preserving geometry, viewBox, fixed colors and definition IDs. Downloaded originals use byte hashes. This is not perceptual deduplication: visually equal files with different paths or IDs may remain. CSS variable fallbacks were resolved where present; currentColor remains reusable and can differ from the original theme. Raw markup is retained for comparison. Sprite exports wrap original vector geometry; they are not invented redrawings.</p>
<p>XML parse errors: {s['parseErrors']}. Successfully rasterized complete exports: {len(success)}. Renderer errors: {len(errors)}. Fully transparent at 64px: {len(blank)} (listed for review; not silently removed). Rasterization verifies renderability, not pixel identity to ClickUp. The gallery excludes incomplete reference closures. <a href="download-failures.json">Download failure log</a> preserves failed attempts and flags URLs later downloaded successfully. Some originals are auxiliary illustrations, loading images, favicon or a tracking pixel rather than icons.</p>
<h2>Incomplete SVGs</h2><p>These remain in <code>incomplete-svg/</code> and are flagged in the manifest; missing paints, clipping or patterns may affect appearance.</p><ul>{missing}</ul>
<h2>Preview sample</h2><img src="evidence/preview.png" alt="Extracted SVG sample grid">
<h2>Captured states</h2><p>SVG counts below describe mounted DOM elements, including shared sprite definitions; they are not counts of visible icons or additional unique assets.</p><table><thead><tr><th>ID</th><th>State</th><th>Verification boundary</th><th>SVG elements</th><th>Final URL</th></tr></thead><tbody>{rows}</tbody></table></html>'''
(O/'coverage-report.html').write_text(report)
(O/'README.txt').write_text('ClickUp extraction, 15 October 2026\nOpen coverage-report.html for findings and limits; gallery.html to browse and download.\nsvg/: normalized standalone exports. incomplete-svg/: missing local definitions.\noriginals/: exact downloaded files, including original sprite map and auxiliary images.\nraw-symbols/ and raw-inline/: extracted unnormalized geometry.\nmanifest.json: hashes, provenance, symbol IDs, source types, verification.\ncoverage.json: captured states. download-failures.json: failed requests and recovery flags.\nThe extraction does not establish ownership or a license to reuse these assets.\n')
# CSV paths must match quarantined files.
p=O/'manifest.csv';txt=p.read_text()
for a in m['assets']:
 if a['unresolvedReferences']:txt=txt.replace('svg/'+pathlib.Path(a['file']).name,a['file'])
p.write_text(txt)
# Validate file hashes and package all user-facing assets.
for a in m['assets']:
 assert hashlib.sha256((O/a['file']).read_bytes()).hexdigest()==a['sha256']
for a in m['originalFiles']:assert hashlib.sha256((O/a['file']).read_bytes()).hexdigest()==a['sha256']
z=B/'clickup-icons-and-pictograms.zip'
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as archive:
 for p in sorted(O.rglob('*')):
  if p.is_file():archive.write(p,str(pathlib.Path('clickup-assets')/p.relative_to(O)))
with zipfile.ZipFile(z) as archive:assert archive.testzip() is None
print(json.dumps({'stats':s,'rasterized':len(success),'renderErrors':errors,'blankCount':len(blank),'zipBytes':z.stat().st_size},indent=2))
